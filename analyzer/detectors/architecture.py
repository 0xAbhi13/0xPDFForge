from typing import List, Dict
from ..models import FrameworkEvidence

def infer_architecture(frameworks: List[FrameworkEvidence], languages: List, apis: List, databases: List, features: List) -> Dict:
    fw_names=[f.name for f in frameworks]
    lang_names=[l.language for l in languages]
    has_frontend = any(x in fw_names for x in ["React","Vue","Angular","Svelte","Next.js","Nuxt","SvelteKit","Astro","Remix"]) or "HTML" in lang_names
    has_backend = any(x in fw_names for x in ["Express","FastAPI","Flask","Django","Laravel","Spring Boot"]) or "Python" in lang_names and any(x in ["Flask","Django","FastAPI"] for x in fw_names)
    # Alternative: if Python present without frontend frameworks, infer backend
    has_db = len(databases)>0
    has_api = len(apis)>0
    has_tailwind = "Tailwind CSS" in fw_names

    nodes=[]
    edges=[]
    description=""

    if has_frontend and has_backend:
        nodes=[
            {"id":"user","label":"User / Browser","kind":"actor","evidence":["frontend frameworks detected"]},
            {"id":"frontend","label":"Frontend\n" + ("/".join([f for f in fw_names if f in ["React","Vue","Next.js","Angular","Svelte"]][:2]) or "Web UI"),"kind":"frontend","evidence":["HTML/CSS/JS present"]},
            {"id":"api","label":"API Layer\n" + (f"{len(apis)} endpoints" if has_api else "REST"),"kind":"api","evidence":[f"{len(apis)} detected" if has_api else "inferred"]},
            {"id":"backend","label":"Backend\n" + ("/".join([f for f in fw_names if f in ["Express","FastAPI","Flask","Django","Laravel"]][:1]) or "Server"),"kind":"backend","evidence":["backend framework detected"]},
            {"id":"db","label":"Database\n" + (databases[0].technology if has_db else "Storage"),"kind":"database","evidence":[databases[0].evidence[0] if has_db else "inferred"]},
        ]
        edges=[
            {"from":"user","to":"frontend","label":"HTTPS"},
            {"from":"frontend","to":"api","label":"fetch / axios"},
            {"from":"api","to":"backend","label":"JSON"},
            {"from":"backend","to":"db","label":"queries"},
        ]
        description="Full-stack architecture detected: browser → frontend → API → backend → database. Based on frameworks and data-access patterns."
    elif has_frontend:
        # Determine external APIs
        external = "External APIs" if has_api else "Static Assets"
        nodes=[
            {"id":"user","label":"User","kind":"actor","evidence":["browser"]},
            {"id":"browser","label":"Browser","kind":"browser","evidence":["HTML/CSS"]},
            {"id":"frontend","label":"Frontend\n" + ("/".join([f for f in fw_names if f in ["React","Vue","Next.js"]][:1]) or "HTML/CSS/JS"),"kind":"frontend","evidence":["frontend detected"]},
            {"id":"static","label":external,"kind":"api","evidence":[f"{len(apis)} endpoints" if has_api else "static"]},
        ]
        edges=[
            {"from":"user","to":"browser","label":"visit"},
            {"from":"browser","to":"frontend","label":"loads"},
            {"from":"frontend","to":"static","label":"requests" if has_api else "assets"},
        ]
        description="Frontend-only architecture: static site rendered in browser, optionally calling external APIs. Evidence: HTML/CSS/JS without server framework."
    elif has_backend:
        nodes=[
            {"id":"client","label":"Client / Consumer","kind":"actor","evidence":["API consumer"]},
            {"id":"api","label":"API Server\n" + (fw_names[0] if fw_names else "Python API"),"kind":"backend","evidence":["backend detected"]},
            {"id":"db","label":"Database\n" + (databases[0].technology if has_db else "SQLite / Storage"),"kind":"database","evidence":[databases[0].evidence[0] if has_db else "inferred from models"]},
        ]
        edges=[
            {"from":"client","to":"api","label":"HTTP"},
            {"from":"api","to":"db","label":"ORM / queries"},
        ]
        description="Backend/service architecture: API server with data layer. Based on server framework and DB evidence."
    else:
        # Unknown / script
        primary = lang_names[0] if lang_names else "Code"
        nodes=[
            {"id":"code","label":primary+" Project","kind":"code","evidence":["languages: "+",".join(lang_names[:3])]},
            {"id":"runtime","label":"Runtime","kind":"runtime","evidence":["execution environment"]},
        ]
        edges=[
            {"from":"code","to":"runtime","label":"runs on"},
        ]
        description="Generic project structure: source executes in runtime with no clear frontend/backend separation."

    return {"nodes": nodes, "edges": edges, "description": description, "type": "fullstack" if (has_frontend and has_backend) else ("frontend" if has_frontend else ("backend" if has_backend else "generic"))}
