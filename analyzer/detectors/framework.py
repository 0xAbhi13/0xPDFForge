import os, json, re
from typing import List, Dict, Tuple
from ..models import FrameworkEvidence

# Master detection rules: name -> {category, manifest check, import check, config check}
RULES = [
    # Build tools
    {"name":"Vite", "category":"Build Tool", "manifests":["vite.config.js","vite.config.ts"], "deps":["vite"], "imports":["vite"], "confidence":"confirmed"},
    {"name":"Webpack", "category":"Build Tool", "manifests":["webpack.config.js"], "deps":["webpack"], "imports":[], "confidence":"detected"},
    {"name":"Turbo", "category":"Build Tool", "manifests":["turbo.json"], "deps":["turbo"], "imports":[], "confidence":"confirmed"},
    # Frontend frameworks
    {"name":"React", "category":"Frontend", "deps":["react","react-dom"], "imports":[r"from\s+['\"]react['\"]", r"import\s+React"], "manifests":[], "confidence":"confirmed"},
    {"name":"Next.js", "category":"Frontend", "deps":["next"], "imports":[r"from\s+['\"]next"], "manifests":["next.config.js","next.config.mjs"], "confidence":"confirmed"},
    {"name":"Vue", "category":"Frontend", "deps":["vue","nuxt"], "imports":[r"from\s+['\"]vue['\"]", r"<template>"], "manifests":["vue.config.js","nuxt.config.js"], "confidence":"confirmed"},
    {"name":"Nuxt", "category":"Frontend", "deps":["nuxt"], "manifests":["nuxt.config.js","nuxt.config.ts"], "imports":[], "confidence":"confirmed"},
    {"name":"Angular", "category":"Frontend", "deps":["@angular/core"], "manifests":["angular.json"], "imports":[r"from\s+['\"]@angular"], "confidence":"confirmed"},
    {"name":"Svelte", "category":"Frontend", "deps":["svelte"], "manifests":["svelte.config.js"], "imports":[r"from\s+['\"]svelte"], "confidence":"confirmed"},
    {"name":"SvelteKit", "category":"Frontend", "deps":["@sveltejs/kit"], "manifests":["svelte.config.js"], "imports":[], "confidence":"confirmed"},
    {"name":"Astro", "category":"Frontend", "deps":["astro"], "manifests":["astro.config.mjs"], "imports":[], "confidence":"confirmed"},
    {"name":"Remix", "category":"Frontend", "deps":["@remix-run/react"], "manifests":["remix.config.js"], "imports":[], "confidence":"confirmed"},
    # CSS
    {"name":"Tailwind CSS", "category":"CSS", "deps":["tailwindcss"], "manifests":["tailwind.config.js","tailwind.config.ts"], "imports":[r"@tailwind", r"tailwindcss"], "confidence":"confirmed"},
    {"name":"Bootstrap", "category":"CSS", "deps":["bootstrap"], "imports":[r"bootstrap"], "manifests":[], "confidence":"detected"},
    {"name":"Sass", "category":"CSS", "deps":["sass"], "imports":[r"\.scss"], "manifests":[], "confidence":"detected"},
    {"name":"Styled Components", "category":"CSS", "deps":["styled-components"], "imports":[r"styled-components"], "manifests":[], "confidence":"detected"},
    # JS libs
    {"name":"GSAP", "category":"Animation", "deps":["gsap"], "imports":[r"gsap"], "manifests":[], "confidence":"detected"},
    {"name":"Three.js", "category":"3D", "deps":["three"], "imports":[r"three"], "manifests":[], "confidence":"detected"},
    {"name":"Chart.js", "category":"Charts", "deps":["chart.js"], "imports":[r"chart\.js", r"Chart\.js"], "manifests":[], "confidence":"detected"},
    {"name":"Framer Motion", "category":"Animation", "deps":["framer-motion"], "imports":[r"framer-motion"], "manifests":[], "confidence":"detected"},
    {"name":"D3.js", "category":"Charts", "deps":["d3"], "imports":[r"from\s+['\"]d3['\"]"], "manifests":[], "confidence":"detected"},
    {"name":"GSAP ScrollTrigger", "category":"Animation", "deps":[], "imports":[r"ScrollTrigger"], "manifests":[], "confidence":"inferred"},
    # Backend
    {"name":"Express", "category":"Backend", "deps":["express"], "imports":[r"require\(['\"]express['\"]\)", r"from\s+['\"]express['\"]"], "manifests":[], "confidence":"confirmed"},
    {"name":"FastAPI", "category":"Backend", "deps":["fastapi"], "imports":[r"from\s+fastapi", r"import\s+fastapi"], "manifests":[], "confidence":"confirmed"},
    {"name":"Flask", "category":"Backend", "deps":["flask","Flask"], "imports":[r"from\s+flask", r"import\s+flask"], "manifests":[], "confidence":"confirmed"},
    {"name":"Django", "category":"Backend", "deps":["django","Django"], "imports":[r"from\s+django", r"import\s+django"], "manifests":["manage.py"], "confidence":"confirmed"},
    {"name":"Laravel", "category":"Backend", "deps":["laravel/framework"], "manifests":["artisan","composer.json"], "imports":[], "confidence":"confirmed"},
    {"name":"Spring Boot", "category":"Backend", "deps":["spring-boot"], "manifests":["pom.xml","build.gradle"], "imports":[r"org\.springframework"], "manifests_detect":["pom.xml"], "confidence":"detected"},
    # Databases ORM
    {"name":"Prisma", "category":"Database", "deps":["prisma","@prisma/client"], "manifests":["prisma/schema.prisma"], "imports":[r"@prisma/client"], "confidence":"confirmed"},
    {"name":"Mongoose", "category":"Database", "deps":["mongoose"], "imports":[r"mongoose"], "manifests":[], "confidence":"detected"},
    {"name":"SQLAlchemy", "category":"Database", "deps":["sqlalchemy"], "imports":[r"sqlalchemy"], "manifests":[], "confidence":"detected"},
    # Testing
    {"name":"Jest", "category":"Testing", "deps":["jest"], "manifests":["jest.config.js"], "imports":[], "confidence":"confirmed"},
    {"name":"Vitest", "category":"Testing", "deps":["vitest"], "manifests":["vitest.config.js"], "imports":[], "confidence":"confirmed"},
    {"name":"Playwright", "category":"Testing", "deps":["@playwright/test"], "imports":[r"playwright"], "manifests":["playwright.config.js","playwright.config.ts"], "confidence":"confirmed"},
    {"name":"Cypress", "category":"Testing", "deps":["cypress"], "manifests":["cypress.config.js"], "imports":[], "confidence":"confirmed"},
    # Others
    {"name":"TypeScript", "category":"Language", "deps":["typescript"], "manifests":["tsconfig.json"], "imports":[], "confidence":"confirmed"},
    {"name":"ESLint", "category":"Tooling", "deps":["eslint"], "manifests":[".eslintrc.js",".eslintrc.json","eslint.config.js"], "imports":[], "confidence":"confirmed"},
    {"name":"Prettier", "category":"Tooling", "deps":["prettier"], "manifests":[".prettierrc","prettier.config.js"], "imports":[], "confidence":"confirmed"},
    {"name":"Axios", "category":"Network", "deps":["axios"], "imports":[r"axios"], "manifests":[], "confidence":"detected"},
    {"name":"Redux", "category":"State", "deps":["redux","@reduxjs/toolkit"], "imports":[r"redux"], "manifests":[], "confidence":"detected"},
    {"name":"Zustand", "category":"State", "deps":["zustand"], "imports":[r"zustand"], "manifests":[], "confidence":"detected"},
    {"name":"Firebase", "category":"Backend", "deps":["firebase"], "imports":[r"firebase"], "manifests":[], "confidence":"detected"},
    {"name":"Supabase", "category":"Backend", "deps":["@supabase/supabase-js"], "imports":[r"supabase"], "manifests":[], "confidence":"detected"},
]

def detect_frameworks(root: str, files: List[str], file_content_cache: Dict[str,str]=None) -> List[FrameworkEvidence]:
    rel_map = {os.path.relpath(f, root): f for f in files}
    basenames = {os.path.basename(f): f for f in files}
    # Collect manifest contents where possible
    pkg_deps = set()
    pkg_dev = set()
    versions = {}
    # Parse package.json
    if "package.json" in basenames:
        try:
            import json
            with open(basenames["package.json"], 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                for k,v in {**data.get("dependencies",{}), **data.get("peerDependencies",{})}.items():
                    pkg_deps.add(k)
                    versions[k]=v
                for k,v in data.get("devDependencies",{}).items():
                    pkg_dev.add(k)
                    versions[k]=v
        except:
            pass
    # Also requirements etc for python?
    evidence_list: List[FrameworkEvidence] = []
    # Pre-read some file contents for import detection (sample only JS/TS/PY etc)
    sample_files = [f for f in files if os.path.splitext(f)[1].lower() in [".js",".jsx",".ts",".tsx",".vue",".py",".php"]][:80]
    content_blob = ""
    file_to_content = {}
    for f in sample_files:
        try:
            if os.path.getsize(f) > 500*1024:
                continue
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                txt = fh.read(8000)  # first 8k
                file_to_content[f]=txt
                content_blob += "\n" + txt
        except:
            continue

    # Also check presence of manifest files
    present_manifests = set(os.path.basename(f) for f in files)
    present_rel = set(rel_map.keys())

    for rule in RULES:
        name = rule["name"]
        category = rule["category"]
        deps = rule.get("deps", [])
        manifests = rule.get("manifests", [])
        imports = rule.get("imports", [])
        conf = rule.get("confidence", "detected")
        evidences: List[str] = []
        found = False
        version = None

        # manifest evidence
        for m in manifests:
            if m in present_manifests or any(p.endswith(m) for p in present_rel):
                evidences.append(f"config:{m}")
                found = True
        # deps evidence
        for d in deps:
            if d in pkg_deps or d in pkg_dev:
                evidences.append(f"dependency:{d}@{versions.get(d,'')}".strip("@"))
                found = True
                if d in versions:
                    version = versions[d]
            # also python check? for flask etc case insensitive
            if d.lower() in [x.lower() for x in pkg_deps]:
                pass

        # imports evidence (scan content)
        for pat in imports:
            try:
                if re.search(pat, content_blob):
                    # find which file
                    for fp, txt in file_to_content.items():
                        if re.search(pat, txt):
                            evidences.append(f"import:{pat} in {os.path.relpath(fp, root)}")
                            found = True
                            break
                    if not found:
                        evidences.append(f"pattern:{pat}")
                        found = True
            except re.error:
                if pat in content_blob:
                    evidences.append(f"string:{pat}")
                    found = True

        # Special handling for Spring etc with pom.xml content
        if name=="Spring Boot" and "pom.xml" in present_manifests:
            try:
                with open(basenames["pom.xml"], 'r', encoding='utf-8', errors='ignore') as fh:
                    pom = fh.read()
                    if "spring-boot" in pom:
                        evidences.append("pom.xml: spring-boot")
                        found=True
            except:
                pass

        if found:
            # Deduplicate evidences
            evidences = list(dict.fromkeys(evidences))[:4]
            # Confidence adjustment: if only pattern without manifest/deps, downgrade to inferred
            final_conf = conf
            if len(evidences)==1 and evidences[0].startswith("pattern:"):
                final_conf = "inferred"
            evidence_list.append(FrameworkEvidence(name=name, category=category, confidence=final_conf, evidence=evidences, version=version))

    # Sort by category then name
    evidence_list.sort(key=lambda x: (x.category, x.name))
    return evidence_list
