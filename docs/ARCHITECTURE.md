# Architecture

```
User uploads ZIP
  ↓
FastAPI /api/upload
  ↓
safe_extract (traversal/bomb/symlink checks, size/file-count limits)
  ↓
walker: walk_project (ignore node_modules, .git, venv, dist, etc.)
  ↓
pipeline.analyze_project(callback)
  ├─ language → bytes + LOC weighting
  ├─ framework → manifest + import + config (with evidence)
  ├─ dependencies → 8 manifest parsers
  ├─ features → 30+ UI signals (HTML/CSS/JS inspected)
  ├─ apis → fetch/axios/XHR/WS (redacted)
  ├─ databases → keyword + dep + schema
  ├─ security → secret + code patterns (redacted)
  └─ architecture → inferred nodes/edges
  ↓
ProjectModel → to_dict() (flat JSON)
  ↓
Frontend SPA (vanilla JS) → results + template gallery + editor
  ↓
/api/generate → pdf.engine.generate_pdf(project, template_id, sections, page_size)
  ↓
ReportLab Platypus → A4/Letter, cover per template, TOC, 18 section builders, charts, tables, headers/footers, page numbers, metadata
  ↓
FileResponse PDF download
```

## Separation

- `analyzer/` never imports `pdf/` or `templates/` — pure data.
- `pdf/engine.py` never scans files — consumes `ProjectModel` dict only.
- `templates/definitions.py` is declarative — engine interprets `cover_style`, `header_style`, `colors`, `fonts`.

## Determinism

All detectors are regex/manifest based, no randomness, no network, no AI. `AI_DISABLED=true` is the default.

## Limits (config.py / .env)

- MAX_ZIP_SIZE 50 MB
- MAX_EXTRACTED_SIZE 300 MB
- MAX_FILE_COUNT 10k
- MAX_SINGLE_FILE 10 MB
- IGNORED_DIRS configurable set
- Analysis file caps: 800 KB per file for content scan, sampled 80 files per detector
