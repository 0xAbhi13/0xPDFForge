import os, uuid, time, shutil, tempfile, json, threading, datetime, pathlib, re
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analyzer.scanners.safe_extract import safe_extract, cleanup as extract_cleanup, ExtractionError
from analyzer.pipeline import analyze_project
from templates.definitions import list_templates, get_template
from pdf.engine import generate_pdf

# Config
MAX_ZIP_BYTES = int(os.getenv("MAX_ZIP_SIZE", 50*1024*1024))
AI_DISABLED = os.getenv("AI_DISABLED", "true").lower() == "true"

app = FastAPI(title="0xPDFForge", version="1.0.0", description="Project-to-PDF documentation platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores
ANALYSIS_STORE: Dict[str, dict] = {}  # job_id -> {status, progress, project, error, temp_dir}
TEMPLATE_LIST = list_templates()

# Static frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

class SectionConfig(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = ""
    enabled: bool = True
    content_override: Optional[str] = None

class GenerateRequest(BaseModel):
    job_id: str
    template_id: str
    page_size: str = "A4"
    sections: List[SectionConfig]

DEFAULT_SECTIONS = [
    {"id":"cover","title":"Cover","subtitle":"Title & meta","enabled":True},
    {"id":"executive","title":"Executive Summary","subtitle":"High-level overview","enabled":True},
    {"id":"overview","title":"Project Overview","subtitle":"Name, purpose, vital stats","enabled":True},
    {"id":"goals","title":"Project Goals","subtitle":"Inferred purpose","enabled":True},
    {"id":"stack","title":"Technology Stack","subtitle":"Frameworks & languages","enabled":True},
    {"id":"statistics","title":"Project Statistics","subtitle":"Measured metrics","enabled":True},
    {"id":"architecture","title":"Architecture","subtitle":"Inferred diagram","enabled":True},
    {"id":"structure","title":"Project Structure","subtitle":"File tree","enabled":True},
    {"id":"features","title":"Features","subtitle":"UI & functional signals","enabled":True},
    {"id":"uipreview","title":"UI / Website Preview","subtitle":"Live or static","enabled":True},
    {"id":"dependencies","title":"Dependencies","subtitle":"Manifests","enabled":True},
    {"id":"api","title":"API Integration","subtitle":"Network calls","enabled":True},
    {"id":"database","title":"Database","subtitle":"Only if evidence","enabled":True},
    {"id":"security","title":"Security Findings","subtitle":"Static scan","enabled":True},
    {"id":"testing","title":"Testing","subtitle":"Tests & frameworks","enabled":True},
    {"id":"setup","title":"Development Setup","subtitle":"Run locally","enabled":True},
    {"id":"usage","title":"Usage","subtitle":"How to use","enabled":True},
    {"id":"limitations","title":"Limitations","subtitle":"Honest gaps","enabled":True},
    {"id":"future","title":"Future Improvements","subtitle":"Suggestions","enabled":True},
    {"id":"conclusion","title":"Conclusion","subtitle":"Wrap-up","enabled":True},
]

@app.get("/api/health")
def health():
    return {"status":"ok","ai_disabled":AI_DISABLED,"version":"1.0.0","templates":len(TEMPLATE_LIST)}

@app.get("/api/templates")
def get_templates():
    return {"templates": TEMPLATE_LIST}

@app.get("/api/sections/default")
def default_sections():
    return {"sections": DEFAULT_SECTIONS}

@app.post("/api/upload")
async def upload_zip(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")
    # Read to temp file with size check
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    size=0
    try:
        while True:
            chunk = await file.read(1024*64)
            if not chunk:
                break
            size+=len(chunk)
            if size > MAX_ZIP_BYTES:
                tmp_zip.close()
                os.unlink(tmp_zip.name)
                raise HTTPException(status_code=413, detail=f"ZIP exceeds {MAX_ZIP_BYTES//1024//1024} MB limit")
            tmp_zip.write(chunk)
        tmp_zip.close()

        job_id = str(uuid.uuid4())[:8]
        # Prepare progress store
        ANALYSIS_STORE[job_id] = {"status":"extracting","progress":[{"stage":"scan","label":"Scanning project","done":False}],"project":None,"error":None,"tmp_zip":tmp_zip.name,"temp_dir":None}

        # Extract safely
        try:
            tmp_extract = tempfile.mkdtemp(prefix="pdfforge_extract_")
            ANALYSIS_STORE[job_id]["temp_dir"]=tmp_extract
            root, _ = safe_extract(tmp_zip.name, tmp_extract)
        except ExtractionError as e:
            ANALYSIS_STORE[job_id]["status"]="error"
            ANALYSIS_STORE[job_id]["error"]=str(e)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            ANALYSIS_STORE[job_id]["status"]="error"
            ANALYSIS_STORE[job_id]["error"]=str(e)
            raise HTTPException(status_code=400, detail=f"Extraction failed: {e}")

        # Analyze with progress callback
        progress_stages=[]
        def cb(stage, msg):
            # Map to frontend stages
            stage_map={
                "scan":"Files discovered",
                "languages":"Languages detected",
                "frameworks":"Frameworks detected",
                "dependencies":"Dependencies analyzed",
                "features":"Features detected",
                "apis":"APIs scanned",
                "databases":"Databases scanned",
                "security":"Security scan",
                "architecture":"Architecture analyzed",
                "stats":"Statistics compiled",
                "done":"Documentation generated"
            }
            # update store
            ANALYSIS_STORE[job_id]["progress"].append({"stage":stage,"label":stage_map.get(stage, msg),"done":True})

        # Track stages for frontend polling notion: we will also store current stage
        ANALYSIS_STORE[job_id]["status"]="analyzing"
        ANALYSIS_STORE[job_id]["progress"]=[
            {"stage":"scan","label":"Files discovered","done":False},
            {"stage":"languages","label":"Languages detected","done":False},
            {"stage":"frameworks","label":"Frameworks detected","done":False},
            {"stage":"dependencies","label":"Dependencies analyzed","done":False},
            {"stage":"architecture","label":"Architecture analyzed","done":False},
            {"stage":"features","label":"Features detected","done":False},
            {"stage":"security","label":"Security scan","done":False},
            {"stage":"done","label":"Documentation generated","done":False},
        ]

        try:
            model = analyze_project(root, progress_callback=cb)
            # Mark all done
            for p in ANALYSIS_STORE[job_id]["progress"]:
                p["done"]=True
            ANALYSIS_STORE[job_id]["status"]="done"
            ANALYSIS_STORE[job_id]["project"]=model.to_dict()
            # Cleanup extracted after analysis? Keep for potential screenshot? we can delete after short delay
            # For now schedule cleanup after 30min via thread; immediate keep for debugging
            # Remove tmp_zip
            try:
                os.unlink(tmp_zip.name)
            except: pass
            return {"job_id":job_id, "project": model.to_dict(), "status":"done"}
        except Exception as e:
            ANALYSIS_STORE[job_id]["status"]="error"
            ANALYSIS_STORE[job_id]["error"]=str(e)
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
        finally:
            # Schedule cleanup of extracted dir after response? Keep for potential PDF gen that doesn't need it (model already captured)
            # We keep temp_dir path for reference but clean after 10 minutes in background thread
            def delayed_clean(path):
                time.sleep(600)
                extract_cleanup(path)
            threading.Thread(target=delayed_clean, args=(tmp_extract,), daemon=True).start()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    if job_id not in ANALYSIS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return ANALYSIS_STORE[job_id]

@app.get("/api/project/{job_id}")
def get_project(job_id: str):
    if job_id not in ANALYSIS_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    entry=ANALYSIS_STORE[job_id]
    if entry["status"]!="done":
        return {"status":entry["status"],"progress":entry.get("progress",[])}
    return {"status":"done","project":entry["project"]}

class GenerateBody(BaseModel):
    job_id: str
    template_id: str = "github"
    page_size: str = "A4"
    sections: Optional[List[SectionConfig]] = None
    project_override: Optional[Dict[str,Any]] = None

@app.post("/api/generate")
def generate(body: GenerateBody):
    # Validate template
    tmpl=get_template(body.template_id)
    if not tmpl:
        raise HTTPException(status_code=400, detail="Invalid template")
    if body.page_size not in ["A4","Letter"]:
        raise HTTPException(status_code=400, detail="Invalid page size")
    # Get project
    project=None
    if body.project_override:
        project=body.project_override
    elif body.job_id in ANALYSIS_STORE and ANALYSIS_STORE[body.job_id].get("project"):
        project=ANALYSIS_STORE[body.job_id]["project"]
    else:
        raise HTTPException(status_code=404, detail="Project not found. Upload first.")
    # Sections
    sections = body.sections or DEFAULT_SECTIONS
    # Normalize sections to list of dicts
    sections_list=[ s.model_dump() if isinstance(s, SectionConfig) else s for s in sections]
    # Generate PDF to temp file
    out_dir=tempfile.mkdtemp(prefix="pdfforge_pdf_")
    raw_name = project.get('project_name','project') or 'project'
    safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', raw_name).strip('_') or 'project'
    # limit length and avoid empty
    safe_name = safe_name[:80]
    out_path=os.path.join(out_dir, f"{safe_name}_{body.template_id}.pdf")
    try:
        generate_pdf(project, body.template_id, sections_list, page_size=body.page_size, output_path=out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    # Return file
    filename=os.path.basename(out_path)
    return FileResponse(out_path, media_type="application/pdf", filename=filename, headers={"X-Job-Id": body.job_id, "X-Template": body.template_id})

# Mount frontend static
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
if os.path.exists(EXAMPLES_DIR):
    app.mount("/examples", StaticFiles(directory=EXAMPLES_DIR), name="examples")
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
if os.path.exists(DOCS_DIR):
    app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")

@app.get("/favicon.ico")
@app.get("/favicon.svg")
def favicon():
    # Serve favicon from frontend/assets
    for cand in [os.path.join(FRONTEND_DIR, "assets", "favicon.svg"), os.path.join(FRONTEND_DIR, "favicon.ico")]:
        if os.path.exists(cand):
            media = "image/svg+xml" if cand.endswith(".svg") else "image/x-icon"
            return FileResponse(cand, media_type=media)
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    idx=os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        with open(idx, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Frontend not built</h1>", status_code=404)

@app.get("/{full_path:path}", response_class=HTMLResponse)
def catch_all(full_path: str):
    # Serve index for SPA routes, but preserve api
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    idx=os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        with open(idx, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    raise HTTPException(status_code=404, detail="Not found")
