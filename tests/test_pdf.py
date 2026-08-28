import os, sys, tempfile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analyzer.pipeline import analyze_project
from pdf.engine import generate_pdf
from templates.definitions import list_templates, get_template

def test_template_count():
    tpls = list_templates()
    assert len(tpls) >= 15
    ids = [t["id"] for t in tpls]
    assert "github" in ids
    assert "terminal" in ids
    assert "corporate" in ids

def test_pdf_generation_all_templates():
    proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample-project"))
    model = analyze_project(proj)
    project = model.to_dict()
    sections = [
        {"id":"cover","title":"Cover","subtitle":"","enabled":True},
        {"id":"executive","title":"Executive Summary","subtitle":"","enabled":True},
        {"id":"overview","title":"Overview","subtitle":"","enabled":True},
        {"id":"stack","title":"Stack","subtitle":"","enabled":True},
        {"id":"statistics","title":"Stats","subtitle":"","enabled":True},
        {"id":"architecture","title":"Arch","subtitle":"","enabled":True},
        {"id":"structure","title":"Structure","subtitle":"","enabled":True},
        {"id":"features","title":"Features","subtitle":"","enabled":True},
        {"id":"api","title":"API","subtitle":"","enabled":True},
        {"id":"security","title":"Security","subtitle":"","enabled":True},
        {"id":"conclusion","title":"Conclusion","subtitle":"","enabled":True},
    ]
    for tid in ["github","terminal","corporate","neon","college"]:
        out = tempfile.mktemp(suffix=".pdf")
        try:
            generate_pdf(project, tid, sections, page_size="A4", output_path=out)
            assert os.path.exists(out)
            assert os.path.getsize(out) > 5000
        finally:
            if os.path.exists(out):
                os.unlink(out)

def test_pdf_page_sizes():
    proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample-project"))
    model = analyze_project(proj)
    project = model.to_dict()
    sections = [{"id":"cover","title":"Cover","subtitle":"","enabled":True},{"id":"executive","title":"Exec","subtitle":"","enabled":True},{"id":"conclusion","title":"Conclusion","subtitle":"","enabled":True}]
    for ps in ["A4","Letter"]:
        out = tempfile.mktemp(suffix=".pdf")
        try:
            generate_pdf(project, "github", sections, page_size=ps, output_path=out)
            assert os.path.getsize(out) > 3000
        finally:
            if os.path.exists(out):
                os.unlink(out)

def test_pdf_with_section_override_and_hidden():
    proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample-project"))
    model = analyze_project(proj)
    project = model.to_dict()
    sections = [
        {"id":"cover","title":"Cover","subtitle":"","enabled":True},
        {"id":"executive","title":"Executive Summary","subtitle":"","enabled":True, "content_override": "Custom executive text for testing."},
        {"id":"overview","title":"Overview","subtitle":"","enabled":False},
        {"id":"conclusion","title":"Conclusion","subtitle":"","enabled":True},
    ]
    out = tempfile.mktemp(suffix=".pdf")
    try:
        generate_pdf(project, "github", sections, output_path=out)
        assert os.path.getsize(out) > 3000
    finally:
        if os.path.exists(out):
            os.unlink(out)

def test_pdf_redaction():
    # Create a project with a fake secret, ensure PDF does not contain raw secret
    import tempfile
    tmp = tempfile.mkdtemp()
    with open(os.path.join(tmp, "config.js"), "w") as f:
        f.write('const API_KEY = "sk_live_abcdef1234567890abcdef";')
    from analyzer.pipeline import analyze_project
    model = analyze_project(tmp)
    project = model.to_dict()
    sections = [{"id":"cover","title":"Cover","subtitle":"","enabled":True},{"id":"security","title":"Security","subtitle":"","enabled":True},{"id":"conclusion","title":"Conclusion","subtitle":"","enabled":True}]
    out = tempfile.mktemp(suffix=".pdf")
    try:
        generate_pdf(project, "github", sections, output_path=out)
        # Read pdf as binary and check secret not present
        data = open(out, 'rb').read()
        assert b"abcdef1234567890" not in data
    finally:
        if os.path.exists(out):
            os.unlink(out)
        import shutil; shutil.rmtree(tmp, ignore_errors=True)
