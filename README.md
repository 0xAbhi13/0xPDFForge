<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0F172A,100:00FF88&height=220&section=header&text=0xPDFForge&fontSize=72&fontColor=ffffff&fontAlignY=38&desc=Turn%20any%20codebase%20into%20beautiful%20documentation.&descAlignY=58&descSize=18&animation=fadeIn" width="100%"/>

<br/>

<a href="https://github.com/0xAbhi13/0xPDFForge">
  <img src="https://readme-typing-svg.demolab.com/?lines=%F0%9F%93%A6+Upload+any+ZIP...;%F0%9F%94%8D+Deterministic+static+analysis...;%F0%9F%8E%A8+19+templates+%E2%80%A2+20+sections...;%E2%9C%85+No+API+key.+No+hallucination.;%F0%9F%9A%80+ZIP+%E2%86%92+Analyze+%E2%86%92+PDF&font=JetBrains%20Mono&center=true&width=680&height=45&duration=2600&pause=900&color=00E5FF&vCenter=true&size=20" alt="Typing SVG" />
</a>

<br/><br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ReportLab](https://img.shields.io/badge/ReportLab-4.x-FF6B6B?style=for-the-badge&logo=adobe&logoColor=white)](https://www.reportlab.com/)
[![Pillow](https://img.shields.io/badge/Pillow-10-0f172a?style=for-the-badge&logo=python&logoColor=white)](https://pillow.readthedocs.io/)

![Stars](https://img.shields.io/github/stars/0xAbhi13/0xPDFForge?style=for-the-badge&color=fbbf24&logo=github)
![Forks](https://img.shields.io/github/forks/0xAbhi13/0xPDFForge?style=for-the-badge&color=f472b6&logo=github)
![Last Commit](https://img.shields.io/github/last-commit/0xAbhi13/0xPDFForge?style=for-the-badge&color=a855f7)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-34D399?style=for-the-badge)
![AI Disabled](https://img.shields.io/badge/AI_DISABLED-true-10a37f?style=for-the-badge)
![PDF](https://img.shields.io/badge/PDF-Professional-FF6B6B?style=for-the-badge)

<br/>

**Created by Abhishek Jadhav — [@0xAbhi13](https://github.com/0xAbhi13)**

</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

<div align="center">

### 📚 Table of Contents

[⚡ About](#-what-is-0xpdfforge) • [✨ Features](#-features) • [🎨 Templates](#-template-gallery) • [🧠 How It Works](#-how-it-works) • [📦 Install](#-installation) • [▶️ Usage](#️-usage) • [⌨️ Editor Shortcuts](#️-editor-shortcuts) • [🗂️ Structure](#️-project-structure) • [🔒 Security](#-security) • [🛣️ Roadmap](#️-future-roadmap) • [📄 License](#-license)

</div>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif" width="100%">

<div align="center">

<img src="docs/banner-animated.svg" width="100%" alt="0xPDFForge Banner"/>

</div>

<br/>

## ⚡ What is 0xPDFForge?

**0xPDFForge** turns any project ZIP into a polished, professional PDF — no API key, no hallucination, no guesswork. Every number, framework, feature and diagram is derived from **actual file contents** with a confidence model:

`Confirmed` → manifest evidence &nbsp;|&nbsp; `Detected` → import / config &nbsp;|&nbsp; `Inferred` → heuristic &nbsp;|&nbsp; `Unknown` / `N/A` → explicitly marked or omitted

> **Example:** `contact.js` alone does **not** mean a contact form — the analyzer inspects source before claiming. Secrets are redacted with `***` and never appear verbatim in the PDF.

<div align="center">

```text
> Initializing 0xPDFForge...
> ZIP validated               ✓  (no traversal / bomb / symlink)
> Files discovered            ✓  42 files • 6 dirs
> Languages detected          ✓  JS 62% • HTML 18% • CSS 12%
> Frameworks detected         ✓  React • Vite • Tailwind
> Architecture inferred       ✓  Browser → Frontend → API
> PDF generated               ✓  Corporate • A4 • 20 sections
> 0xPDFForge ready. Download PDF ↓
```

</div>

<br/>

<div align="center">
<img src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/gifs/pixel-line.gif" width="100%">
</div>

<div align="center">

<img src="docs/demo-animated.svg" width="800" alt="0xPDFForge Demo — ZIP to PDF flow"/>

</div>

## ✨ Features

<table>
<tr>
<td width="33%" align="center">

### 🔍
**Deterministic Analyzer**
Languages by bytes + LOC, 30+ frameworks, manifests, website UI, APIs, DBs, security — all evidence-based.

</td>
<td width="33%" align="center">

### 🎨
**19 Templates**
Developer / Professional / Academic / Creative — each with unique typography, cover, spacing, headers/footers.

</td>
<td width="33%" align="center">

### 📄
**20 Dynamic Sections**
Cover → Executive Summary → … → Conclusion. Omitted or marked “No evidence” when absent.

</td>
</tr>
<tr>
<td width="33%" align="center">

### ✏️
**Visual PDF Editor**
Reorder (drag-drop), hide/show, edit text per section, switch template, A4/Letter, live preview.

</td>
<td width="33%" align="center">

### 🛡️
**Secure ZIP Pipeline**
Traversal, bomb (ratio >1000), symlink, oversize (50 MB / 10 MB per file / 10k files) — all blocked.

</td>
<td width="33%" align="center">

### 🔒
**Secret Redaction**
API keys, AWS, Stripe, GitHub PAT, passwords → `***` before analysis and never in PDF.

</td>
</tr>
<tr>
<td width="33%" align="center">

### 📊
**Real Statistics**
Files, source files, LOC, bytes, deps, frameworks, assets/images/tests/docs, largest files/dirs, build scripts — measured, not invented.

</td>
<td width="33%" align="center">

### 🧩
**Architecture Diagram**
Inferred `User → Frontend → API → Backend → DB` from detected layers, rendered as vector.

</td>
<td width="33%" align="center">

### ⚡
**Local-First**
`AI_DISABLED=true` by default. No cloud, no execution, no upload. Works offline on a normal PC.

</td>
</tr>
</table>

<div align="center">

### 🔒 Local Processing

All analysis happens on your machine. **Nothing is uploaded or executed.** The PDF is rendered locally with ReportLab.

</div>

## 🎨 Template Gallery

<div align="center">

| Category | Templates | Vibe |
|:---|:---|:---|
| **Developer** | Terminal, GitHub, Cyber, Architecture, Minimal Code | Mono, dark, blueprint, minimal |
| **Professional** | Corporate, Executive, Modern Portfolio, Case Study | Navy+gold, charcoal+teal, cream, left-rule |
| **Academic** | College Project, Internship Report, Research Report, Technical Report | Crest, certificate, serif, spec-sheet |
| **Creative** | Neon, Glass, Editorial, Magazine, Timeline, **ChatGPT** | Synthwave, frosted, editorial, grid, timeline, chat bubbles |

*Each has unique typography (Helvetica/Times/Courier), spacing (compact/comfortable/airy), cover, section layouts, cards, diagrams, headers/footers — not just color swaps.*

</div>

> **ChatGPT template** — clean Inter, chat bubbles, code blocks with `copy`, green `#10A37F` accent — same quality standards ChatGPT uses for professional PDFs.

## 🧠 How It Works

```mermaid
flowchart TD
    A[📦 ZIP Upload] --> B[🛡️ Secure Extraction<br/>traversal / bomb / symlink checks]
    B --> C[🔍 Project Scanner<br/>walk + ignore node_modules/.git/venv]
    C --> D[📊 Language Detection<br/>bytes + LOC weighting]
    D --> E[🧩 Framework Detection<br/>manifest + import + config]
    E --> F[📚 Feature / API / DB / Security<br/>evidence-based]
    F --> G[🏗️ Architecture Inference<br/>Frontend / Backend / Fullstack]
    G --> H[📄 Structured ProjectModel<br/>to_dict]
    H --> I[🎨 Template Engine<br/>19 designs]
    I --> J[📑 PDF Renderer<br/>ReportLab Platypus]

    style A fill:#0f172a,color:#fff
    style B fill:#00e5ff,color:#04222b
    style D fill:#a855f7,color:#fff
    style E fill:#0891b2,color:#fff
    style G fill:#f472b6,color:#04222b
    style J fill:#34d399,color:#04222b
```

The analyzer never executes uploaded code. The PDF renderer consumes only the structured `ProjectModel` — analysis stays separate from presentation. Every table uses header shading + zebra rows, every code block uses dark `#0F172A` with language label, every image has a caption box.

## 🧰 Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![ReportLab](https://img.shields.io/badge/-ReportLab-FF6B6B?style=flat-square&logo=adobe&logoColor=white)
![Pillow](https://img.shields.io/badge/-Pillow-0f172a?style=flat-square&logo=python&logoColor=white)
![Uvicorn](https://img.shields.io/badge/-Uvicorn-2C5BB4?style=flat-square&logo=uvicorn&logoColor=white)
![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![Tailwind](https://img.shields.io/badge/-Tailwind-38BDF8?style=flat-square&logo=tailwindcss&logoColor=white)
![JavaScript](https://img.shields.io/badge/-Vanilla%20JS-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

</div>

## 📦 Installation

<details open>
<summary><b>🖱️ Click to expand setup steps</b></summary>

<br/>

**1. Clone the repo**

```bash
git clone https://github.com/0xAbhi13/0xPDFForge.git
cd 0xPDFForge
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

<table>
<tr><th>Windows</th><th>macOS / Linux</th></tr>
<tr>
<td>

```bash
venv\Scripts\activate
```

</td>
<td>

```bash
source venv/bin/activate
```

</td>
</tr>
</table>

**3. Install dependencies**

```bash
pip install -r requirements.txt
# or editable install with CLI
pip install -e .
```

**4. Run (choose one)**

```bash
# Windows double-click
start.bat
# macOS / Linux
chmod +x start.sh && ./start.sh
# Direct
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
# CLI (no browser)
python cli.py --zip examples/sample-project.zip --template corporate --output docs.pdf
```

Then open `http://127.0.0.1:8000` — try **“Try sample project →”** for instant demo.

> Works with `AI_DISABLED=true` by default. No `OPENAI_API_KEY` needed.

</details>

## ▶️ Usage

```text
1. Landing → “Analyze Project”
2. Upload → drag & drop ZIP (max 50 MB, 10k files, 10 MB/file — bombs/traversal blocked)
3. Analysis → live 8-stage progress (real pipeline callbacks)
4. Results → stack, stats, features, architecture, tree, APIs, DBs, security
5. Templates → filter by category, search, select (19 previews)
6. Editor → reorder/hide (drag-drop), edit text, switch template, A4/Letter, add custom, live preview
7. Generate → download PDF (page numbers, metadata, redacted secrets)

Try: examples/sample-project/ → ZIP it and upload, or click “Try sample project →”
```

## ⌨️ Editor Shortcuts

<div align="center">

| Action | How | Action | How |
|:---|:---|:---|:---|
| Reorder sections | Drag `≡` | Hide / Show | Toggle switch |
| Edit text | Click `✎` | Add custom | Bottom textarea → `+ Add section` |
| Change template | Right panel → Template | Page size | Top bar `A4` / `Letter` |
| Reset | `Reset` top of left panel | Generate | `Generate PDF` → download |

</div>

## 🗂️ Project Structure

```text
0xPDFForge/
│
├── frontend/                 # SPA — no build step, fully responsive
│   ├── index.html
│   └── assets/{app.js,favicon.svg}
├── backend/
│   └── app.py                # FastAPI — upload, analyze, generate, serve
├── analyzer/
│   ├── config.py             # limits & ignored dirs (configurable)
│   ├── pipeline.py           # orchestration with progress callbacks
│   ├── models.py             # ProjectModel dataclasses
│   ├── scanners/{safe_extract.py,walker.py}
│   └── detectors/{language,framework,dependencies,features,api_detector,database,security,architecture}.py
├── templates/
│   └── definitions.py        # 19 templates (Developer/Professional/Academic/Creative)
├── pdf/
│   └── engine.py             # ReportLab — ChatGPT-quality tables, code blocks, headers/footers
├── cli.py                    # CLI —  python cli.py --zip proj.zip --template corporate
├── docs/{banner-animated.svg,demo-animated.svg}
├── examples/{sample-project/,sample-project.zip,example-*.pdf}
├── tests/                    # pytest — extraction, detectors, pdf, api
├── screenshots/capture.py    # Playwright stub (graceful fallback)
├── requirements.txt / pyproject.toml / Dockerfile
├── start.bat / start.sh
└── README.md
```

## 🔒 Security

- **ZIP:** traversal (`..`), absolute `/`, drive `:`, symlink `0xA000`, bomb ratio >1000, oversize, count — rejected with `ExtractionError`
- **Secrets:** `api_key`, `AWS`, `sk_live`, `ghp_`, `password` → `***` via `analyzer/detectors/security.py:12`; never in PDF (`pdf/engine.py:22 esc()` + `_safe_para`)
- **Filenames:** `re.sub(r'[^A-Za-z0-9._-]','_', name)` — `test & demo <app>` → `test___demo__app` for safe `Content-Disposition`
- **Execution:** never `eval` uploaded files; preview sandboxed `npm run dev` with timeout, fallback static
- **Cleanup:** extracted dirs auto-removed after 10 min, ZIP deleted

**Wording:** “Static scan detected…” — never “This project is secure.”

## 📊 PDF Quality — ChatGPT Standards

ChatGPT-level best practices applied in `pdf/engine.py:650`:

- **Typography:** scale `Cover 32/36`, `H1 16/18`, `H2 12/14`, `Body 8.5/12` (justified for Academic), `Mono 6.5/8` dark `#0F172A` for code, `Caption 7/9`
- **Layout:** `A4/Letter` `36/48` margins, `KeepTogether`, `Spacer` baseline grid, `HRFlowable` dividers
- **Tables:** `_styled_table` — header `primary`/`white` `Helvetica-Bold`, `ROWBACKGROUNDS` zebra, `BOX 0.5` + `INNERGRID 0.25`, caption `italic 6pt`
- **Code:** `_code_block` — header `language — copy` + body `Courier` on `#0F172A`/`#E2E8F0` with `esc()` + `&nbsp;` + `<br/>`
- **Images:** `_image_placeholder` bordered `card` box with caption
- **Callouts:** `_callout` left `3pt` border (note/warning/danger) for security findings
- **Page design:** `SimpleDocTemplate` + `_cover_background` per template (grid for dark, gold bar for Corporate, blueprint border for Architecture) + `_header_footer` (page `— N —`, `Confidential`)

## 🛣️ Future Roadmap

- [x] 19 templates + ChatGPT quality
- [ ] Playwright screenshot engine (sandboxed desktop + mobile)
- [ ] More analyzers (Dart, Swift, Kotlin) — see `analyzer/detectors/`
- [ ] AI optional (`OPENAI_API_KEY` env, `AI_DISABLED=false` fallback)
- [ ] PDF diff / version history
- [x] CLI `python cli.py --zip` + Docker `Dockerfile:1`

<div align="center">
<img src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/gifs/pixel-line.gif" width="100%">
</div>

## 👨‍💻 Author

<div align="center">

### Abhishek Jadhav

Creator of **0xPDFForge** & **0xAirCanvas** — building creative projects with Python, AI, computer vision, and web technologies.

[![GitHub](https://img.shields.io/badge/GitHub-%400xAbhi13-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/0xAbhi13)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/0xAbhi13)

</div>

## 📄 License

Released under the [MIT License](LICENSE).

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00E5FF,100:A855F7&height=120&section=footer&text=0xPDFForge&fontSize=30&fontColor=ffffff&animation=fadeIn" width="100%"/>

**Made with 📄 and deterministic analysis.**

</div>
