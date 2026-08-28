import os, tempfile, sys, json, textwrap
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analyzer.detectors.language import detect_languages
from analyzer.detectors.framework import detect_frameworks
from analyzer.detectors.dependencies import detect_dependencies
from analyzer.detectors.features import analyze_features
from analyzer.detectors.api_detector import detect_apis
from analyzer.detectors.database import detect_databases
from analyzer.detectors.security import scan_security
from analyzer.pipeline import analyze_project
from analyzer.scanners.walker import walk_project

def make_temp_project(files: dict):
    tmp = tempfile.mkdtemp()
    for rel, content in files.items():
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full,'w', encoding='utf-8') as f:
            f.write(content)
    return tmp

def test_language_detection_by_bytes():
    proj = make_temp_project({
        "index.html": "<html>" + "a"*1000 + "</html>",
        "style.css": "body { color: red; } "*200,
        "app.js": "console.log(1)\n"*500,
    })
    files, _, _ = walk_project(proj)
    langs = detect_languages(proj, files)
    # Should have 3 langs, with percentages summing ~100
    assert len(langs) >= 3
    total = sum(l.percentage for l in langs)
    assert 99 <= total <= 101
    # JS should have highest due to more bytes? Actually html 1000 vs css 4000 vs js 7000 so JS dominant
    langs_by_pct = sorted(langs, key=lambda x: x.percentage, reverse=True)
    assert langs_by_pct[0].language == "JavaScript"

def test_framework_detection_react():
    proj = make_temp_project({
        "package.json": json.dumps({"name":"x","dependencies":{"react":"^18.0.0","vite":"^4.0.0"}}),
        "src/App.jsx": 'import React from "react";',
        "vite.config.js": "import {defineConfig} from 'vite'"
    })
    files, _, _ = walk_project(proj)
    fws = detect_frameworks(proj, files)
    names = [f.name for f in fws]
    assert "React" in names
    assert "Vite" in names

def test_dependency_parsing():
    proj = make_temp_project({
        "requirements.txt": "flask==2.3.0\nrequests>=2.0\n# comment\n",
        "package.json": json.dumps({"dependencies":{"axios":"^1.0.0"}})
    })
    files, _, _ = walk_project(proj)
    deps = detect_dependencies(proj, files)
    dep_names = [d.name.lower() for d in deps]
    assert "flask" in dep_names
    assert "axios" in dep_names

def test_feature_detection_hero_and_contact():
    proj = make_temp_project({
        "index.html": textwrap.dedent("""
        <nav>nav</nav>
        <section id="hero">hero</section>
        <section id="contact"><form><input type="email"></form></section>
        <footer>foot</footer>
        """)
    })
    files, _, _ = walk_project(proj)
    feats = analyze_features(proj, files)
    names = [f.name for f in feats]
    assert "Navigation" in names
    assert "Hero Section" in names
    assert "Contact Form" in names

def test_contact_js_alone_not_contact_form():
    # Only filename contact.js, no actual form/handler — should NOT claim contact form (principle)
    proj = make_temp_project({
        "contact.js": "// just a file\nconsole.log('contact')\n",
        "index.html": "<html><body>hello</body></html>"
    })
    files, _, _ = walk_project(proj)
    feats = analyze_features(proj, files)
    # Contact Form should not be detected because no html evidence
    assert not any(f.name=="Contact Form" for f in feats)

def test_api_detection_fetch():
    proj = make_temp_project({
        "app.js": 'fetch("/api/users").then(r=>r.json()); axios.get("/api/posts")'
    })
    files, _, _ = walk_project(proj)
    apis = detect_apis(proj, files)
    endpoints = [a.endpoint for a in apis]
    # redacted but should contain /api/users etc
    assert any("/api/users" in e for e in endpoints)
    assert any("/api/posts" in e for e in endpoints)

def test_database_detection_postgres():
    proj = make_temp_project({
        "package.json": json.dumps({"dependencies":{"pg":"^8.0.0"}}),
        "db.js": "const { Client } = require('pg');"
    })
    files, _, _ = walk_project(proj)
    deps = detect_dependencies(proj, files)
    dbs = detect_databases(proj, files, [d.name for d in deps])
    assert any(d.technology=="PostgreSQL" for d in dbs)

def test_security_redaction_no_secret_in_output():
    proj = make_temp_project({
        "config.js": 'const key = "sk_live_1234567890abcdef12345678"; eval("bad")',
        ".env.example": "API_KEY=xxx"
    })
    files, _, _ = walk_project(proj)
    findings = scan_security(proj, files)
    # Should detect at least one high severity
    assert any(f.severity=="high" for f in findings)
    # Ensure raw secret not in evidence_snippet
    for f in findings:
        if f.evidence_snippet:
            assert "1234567890abcdef" not in f.evidence_snippet
            assert "sk_live" not in f.evidence_snippet or "***" in f.evidence_snippet

def test_pipeline_empty_project():
    proj = make_temp_project({})
    model = analyze_project(proj)
    assert model.project_name is not None
    assert model.statistics.total_files == 0

def test_pipeline_full_sample():
    proj = os.path.join(os.path.dirname(__file__), "..", "examples", "sample-project")
    proj = os.path.abspath(proj)
    model = analyze_project(proj)
    assert model.project_name == "acme-portfolio"
    assert len(model.languages) > 0
    assert len(model.frameworks) > 0
    assert model.statistics.total_files >= 5
