<p align="center">
  <img src="docs/banner-animated.svg" width="100%" alt="0xPDFForge Animated Banner" />
</p>

<p align="center">
  <a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&weight=700&size=22&pause=1000&color=0F172A&center=true&vCenter=true&width=600&lines=Turn+any+codebase+into+beautiful+docs;ZIP+%E2%86%92+Analyze+%E2%86%92+PDF;Deterministic+%E2%80%A2+Evidence-based" alt="Typing SVG" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/0xPDFForge-v1.0-0f172a?style=for-the-badge" alt="0xPDFForge"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/AI_DISABLED-true-10a37f?style=flat-square" alt="AI Disabled"/>
  <img src="https://img.shields.io/badge/PDF-ReportLab-FF6B6B?style=flat-square" alt="PDF"/>
</p>

<p align="center">
  <img src="docs/demo-animated.svg" width="800" alt="0xPDFForge Demo — ZIP to PDF flow" />
</p>

> <p align="center"><strong>Upload a ZIP → deterministic static analysis → 19-template engine → professional PDF.</strong><br/>No API key. No hallucination. Evidence-based only.</p>

# 0xPDFForge

**Turn any codebase into beautiful documentation.**

---

## Overview

**0xPDFForge** is a production-grade, portfolio-ready developer tool that converts real project source into polished PDF documentation. Unlike toy generators, every statistic, framework, feature, and diagram is derived from **actual file contents** — with a confidence model:

`Confirmed` → manifest evidence  
`Detected` → import / config evidence  
`Inferred` → heuristic  
`Unknown` / `N/A` → explicitly marked or omitted

**Example:** `contact.js` alone does **not** mean a contact form — the analyzer inspects source before claiming.

---

## Features

### 📦 Pipeline
```
ZIP Upload → Secure Extraction → Project Scanner → Language Detection → Framework Detection
→ Dependency Detection → Source Analysis → Architecture Analysis → Feature Detection
→ Project Statistics → Security Scan → Structured Project Model → Template Engine → PDF Renderer
```

### 🔍 Deterministic Analyzer
- **Languages:** HTML, CSS, JS, TS, JSON, Python, PHP, Java, C/C++, Vue, Svelte, Go, Rust, etc. — stats by **bytes + LOC**, not file count
- **Frameworks:** Vite, React, Next.js, Vue, Angular, Svelte, Express, Flask, Django, FastAPI, Tailwind, Bootstrap, GSAP, Three.js, Chart.js, Framer Motion, Prisma, Mongoose, etc. (30+ rules)
- **Manifests:** `package.json`, `requirements.txt`, `pyproject.toml`, `Pipfile`, `composer.json`, `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`
- **Website analysis:** nav, hero, about, services, portfolio, testimonials, pricing, FAQ, contact, footer, forms, modals, cards, sliders, theme toggle, responsive CSS, media queries, animations, DOM, localStorage, API calls, SEO, a11y
- **API detection:** `fetch`, `axios`, `XHR`, `WebSocket`, REST, GraphQL — with redacted endpoints
- **Database detection:** SQLite, MySQL, Postgres, MongoDB, Redis, Supabase, Firebase, Prisma, Sequelize, etc.
- **Security:** hard-coded secrets, exposed keys, `eval`, `innerHTML`, CORS `*`, etc. — **never prints secrets verbatim**
- **Architecture:** inferred diagram `User → Frontend → API → Backend → DB` (evidence-based)
- **Structure:** collapsible tree, intelligent summarization for large repos
- **Statistics:** files, source files, LOC, bytes, deps, frameworks, assets/images/tests/docs, largest files/dirs, build scripts

### 🎨 Template Engine — 18 distinct templates

| Category | Templates |
|---|---|
| **Developer** | Terminal, GitHub, Cyber, Architecture, Minimal Code |
| **Professional** | Corporate, Executive, Modern Portfolio, Case Study |
| **Academic** | College Project, Internship Report, Research Report, Technical Report |
| **Creative** | Neon, Glass, Editorial, Magazine, Timeline |

Each has **unique** typography, spacing, cover, section layouts, cards, diagrams, headers/footers — not just color swaps.

### 📄 PDF Content (20 dynamic sections)
Cover, Executive Summary, Overview, Goals, Tech Stack, Statistics, Architecture, Structure, Features, UI Preview, Dependencies, API, Database, Security, Testing, Setup, Usage, Limitations, Future Improvements, Conclusion  
→ Sections omitted or marked unavailable when no evidence. Fully reorderable/hidable in editor.

### ✏️ PDF Editor
Reorder (drag-drop), hide/show, edit text per section, switch template, change page size (A4/Letter), add custom text/images, preview live, regenerate.

### 🖼️ Live Preview (optional)
If runnable (`npm run dev` etc.), starts isolated process, captures desktop + mobile screenshots via browser automation, embeds in PDF.  
Fallback: *“Live preview unavailable — static project analysis completed.”* — never fails the pipeline.

---

## Tech Stack

- **Frontend:** HTML, CSS (custom design tokens + Tailwind CDN), vanilla JS — no build step, fully responsive
- **Backend:** Python 3.10+, FastAPI, Uvicorn, python-multipart
- **Analysis:** Python stdlib + regex, deterministic (no ML)
- **PDF:** ReportLab 4.x (Platypus, charts, drawings), Pillow
- **Browser preview:** Playwright stub (graceful fallback, optional)

---

## Supported Technologies (detected)

`Vite, React, Next.js, Vue, Nuxt, Angular, Svelte, SvelteKit, Astro, Remix, Tailwind, Bootstrap, Sass, Styled Components, GSAP, Three.js, Chart.js, Framer Motion, D3, Express, FastAPI, Flask, Django, Laravel, Spring Boot, Prisma, Mongoose, SQLAlchemy, Jest, Vitest, Playwright, Cypress, TypeScript, ESLint, Prettier, Axios, Redux, Zustand, Firebase, Supabase`

*Architecture makes adding new detectors trivial — see `analyzer/detectors/`.*

---

## Installation

```bash
git clone https://github.com/your-org/0xPDFForge.git
cd 0xPDFForge
pip install -r requirements.txt
cp .env.example .env   # optional, works with AI_DISABLED=true by default
```

### Run

**Windows:**
```bash
start.bat
```
**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```
Or directly:
```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000

---

## Usage

1. **Landing** → “Analyze Project”
2. **Upload** → drag & drop ZIP (validated, max 50 MB, 10k files, 10 MB/file)
3. **Analysis** → live progress (8 stages, real pipeline callbacks)
4. **Results** → stack, stats, features, architecture, tree, APIs, DBs, security
5. **Templates** → filter by category, search, select (18 previews)
6. **Editor** → reorder/hide, edit text, change template/page size, add custom, preview
7. **Generate** → download PDF (A4/Letter, page numbers, metadata)

Try the included sample:
```
examples/sample-project/  → ZIP it and upload
```

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | SPA frontend |
| `/api/health` | GET | Health + AI status |
| `/api/templates` | GET | List 18 templates |
| `/api/upload` | POST | Upload ZIP → analyze → `job_id` + `project` |
| `/api/status/{job_id}` | GET | Progress polling |
| `/api/project/{job_id}` | GET | Full project model |
| `/api/generate` | POST | Generate PDF `{job_id, template_id, page_size, sections}` |
| `/assets/*` | GET | Static assets |

All limits configurable via env: `MAX_ZIP_SIZE`, `MAX_EXTRACTED_SIZE`, `MAX_FILE_COUNT`, `MAX_SINGLE_FILE`.

---

## Security

- **ZIP:** traversal (`..`), absolute paths, drive letters, symlinks, bomb (compression ratio >1000), oversized, file count — all rejected with clear errors
- **Secrets:** redacted (`***`) in analysis and PDF; never printed verbatim. Patterns: API keys, AWS, Stripe, GitHub PAT, passwords
- **Execution:** uploaded files **never** executed; preview only via explicit sandboxed `npm run dev` with timeout
- **Cleanup:** temp extracted dirs auto-removed after 10 min; ZIP deleted after analysis
- **Headers:** CORS restricted, no arbitrary command execution

**Wording:** “Static scan detected…” — never “This project is secure.”

---

## Project Structure

```
0xPDFForge/
├── analyzer/
│   ├── config.py              # limits & ignored dirs
│   ├── pipeline.py            # orchestration
│   ├── models.py              # ProjectModel dataclasses
│   ├── scanners/
│   │   ├── safe_extract.py    # bomb/traversal protection
│   │   └── walker.py          # file walk + tree builder
│   └── detectors/
│       ├── language.py
│       ├── framework.py
│       ├── dependencies.py
│       ├── features.py
│       ├── api_detector.py
│       ├── database.py
│       ├── security.py
│       └── architecture.py
├── templates/
│   └── definitions.py         # 18 templates
├── pdf/
│   └── engine.py              # reportlab renderer
├── backend/
│   └── app.py                 # FastAPI
├── frontend/
│   ├── index.html
│   └── assets/app.js
├── tests/
├── examples/
│   └── sample-project/        # runnable demo
├── requirements.txt
├── start.bat / start.sh
├── .env.example
└── README.md
```

---

## Testing

```bash
pytest tests/ -v
```

Covers: ZIP extraction, traversal/bomb protection, language/framework/dependency/feature/API/DB detection, secret redaction, statistics, project model, template rendering, PDF generation, invalid ZIP, empty/large projects.

---

## Performance

- Ignored dirs configurable (`node_modules`, `.git`, `venv`, `dist`, …)
- Streaming copy (64 KB chunks), lazy reading (first 8 KB for import scan), file-size caps
- Parallel where safe, incremental walk, caching
- Large repos don’t freeze UI — tree collapses at 800 nodes, tree preview truncated at 55 lines

---

## Limitations

- Static analysis only — runtime behavior may differ
- Live screenshots require runnable project + Playwright; fallback is static analysis
- Feature claims require evidence — some heuristics may miss heavily obfuscated code
- Not a full security audit

---

## Roadmap

- [ ] Playwright screenshot engine (sandboxed)
- [ ] More language analyzers (Dart, Swift, Kotlin)
- [ ] AI optional enhancement (env var `OPENAI_API_KEY`, deterministic fallback)
- [ ] PDF diff / version history
- [ ] CLI `pdfforge analyze ./my-project --template corporate`

---

## Contributing

PRs welcome. Keep analysis deterministic and evidence-based. Run tests before submitting.

---

## License

MIT — see [LICENSE](LICENSE)

---

**Built with deterministic static analysis — no hallucination. `AI_DISABLED=true` ready.**
