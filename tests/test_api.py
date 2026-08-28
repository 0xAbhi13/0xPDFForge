import os, sys, tempfile, zipfile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def make_zip_bytes(files: dict):
    import io
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    bio.seek(0)
    return bio

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_templates_endpoint():
    r = client.get("/api/templates")
    assert r.status_code == 200
    assert len(r.json()["templates"]) >= 15

def test_upload_invalid_not_zip():
    r = client.post("/api/upload", files={"file": ("test.txt", b"hello", "text/plain")})
    assert r.status_code == 400

def test_upload_valid_zip():
    bio = make_zip_bytes({"hello.txt":"hello", "package.json": '{"name":"x"}'})
    r = client.post("/api/upload", files={"file": ("proj.zip", bio, "application/zip")})
    assert r.status_code == 200
    j = r.json()
    assert "job_id" in j
    assert "project" in j

def test_upload_traversal_rejected():
    bio = make_zip_bytes({"../evil.txt":"hack"})
    r = client.post("/api/upload", files={"file": ("proj.zip", bio, "application/zip")})
    assert r.status_code == 400

def test_generate_pdf_requires_job():
    r = client.post("/api/generate", json={"job_id":"notfound","template_id":"github","page_size":"A4","sections":[]})
    assert r.status_code in [404,400]

def test_full_flow_upload_then_generate():
    bio = make_zip_bytes({
        "package.json": '{"name":"demo","dependencies":{"react":"^18.0.0"}}',
        "index.html": "<html><body><nav>nav</nav><section id='hero'>hi</section></body></html>"
    })
    r = client.post("/api/upload", files={"file": ("proj.zip", bio, "application/zip")})
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    # generate
    payload = {"job_id": job_id, "template_id":"github","page_size":"A4","sections":[{"id":"cover","title":"Cover","subtitle":"","enabled":True},{"id":"executive","title":"Exec","subtitle":"","enabled":True},{"id":"conclusion","title":"Conclusion","subtitle":"","enabled":True}]}
    r2 = client.post("/api/generate", json=payload)
    assert r2.status_code == 200
    assert r2.headers["content-type"] == "application/pdf"
    assert len(r2.content) > 2000
