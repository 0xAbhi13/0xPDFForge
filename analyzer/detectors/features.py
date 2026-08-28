"""
Feature / Website UI analysis — evidence-based only
"""
import os, re
from typing import List, Dict
from ..models import Feature

# Map feature -> patterns (regex or string)
FEATURE_PATTERNS = {
    "Navigation": [r"<nav", r"class=[\"'][^\"]*nav", r"id=[\"']nav", r"<header"],
    "Hero Section": [r"hero", r"class=[\"'][^\"]*hero", r"id=[\"']hero"],
    "About Section": [r"id=[\"']about", r"class=[\"'][^\"]*about"],
    "Services": [r"id=[\"']services", r"class=[\"'][^\"]*services"],
    "Portfolio / Projects": [r"id=[\"']portfolio", r"id=[\"']projects", r"class=[\"'][^\"]*portfolio"],
    "Testimonials": [r"testimonial", r"class=[\"'][^\"]*testimonial"],
    "Pricing": [r"id=[\"']pricing", r"class=[\"'][^\"]*pricing"],
    "FAQ": [r"faq", r"class=[\"'][^\"]*faq", r"<details"],
    "Contact Form": [r"<form[^>]*contact", r"id=[\"']contact", r"contact.*<form", r"<input[^>]*type=[\"']email"],
    "Footer": [r"<footer", r"class=[\"'][^\"]*footer"],
    "Forms": [r"<form", r"<input", r"<textarea", r"<select"],
    "Buttons": [r"<button", r"class=[\"'][^\"]*btn"],
    "Modals": [r"modal", r"dialog", r"<dialog"],
    "Cards": [r"class=[\"'][^\"]*card"],
    "Slider / Carousel": [r"carousel", r"slider", r"swiper", r"slick"],
    "Theme Toggle": [r"theme.*toggle", r"dark.*mode", r"localStorage.*theme"],
    "Search": [r"type=[\"']search", r"class=[\"'][^\"]*search"],
    "Authentication UI": [r"login", r"sign.?in", r"auth", r"class=[\"'][^\"]*auth"],
    "Responsive CSS": [r"@media", r"grid", r"flex"],
    "Animations": [r"@keyframes", r"animation:", r"transition:", r"gsap", r"framer-motion"],
    "DOM Manipulation": [r"document\.", r"querySelector", r"getElementById", r"addEventListener"],
    "LocalStorage": [r"localStorage", r"sessionStorage"],
    "API Requests": [r"fetch\s*\(", r"axios\.", r"XMLHttpRequest"],
    "SEO Metadata": [r"<meta[^>]*name=[\"']description", r"<meta[^>]*property=[\"']og:", r"<title>"],
    "Accessibility": [r"aria-", r"role=[\"']", r"alt=[\"']"],
}

# For CSS responsive detection separately
CSS_PATTERNS = {
    "Responsive CSS": [r"@media\s*\(.*max-width", r"@media\s*\(.*min-width"],
    "Animations": [r"@keyframes", r"animation\s*:"],
}

def analyze_features(root: str, files: List[str]) -> List[Feature]:
    html_files = [f for f in files if f.lower().endswith((".html",".jsx",".tsx",".vue",".svelte",".php"))]
    css_files = [f for f in files if f.lower().endswith((".css",".scss",".sass",".less"))]
    js_files = [f for f in files if f.lower().endswith((".js",".jsx",".ts",".tsx"))]

    # Read content blobs with file tracking
    html_content = {}
    for f in html_files[:40]:
        try:
            if os.path.getsize(f) > 800*1024: continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                txt=fh.read()
                html_content[f]=txt
        except: continue
    css_content = {}
    for f in css_files[:20]:
        try:
            if os.path.getsize(f) > 800*1024: continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                css_content[f]=fh.read()
        except: continue
    js_content = {}
    for f in js_files[:40]:
        try:
            if os.path.getsize(f) > 800*1024: continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                js_content[f]=fh.read()
        except: continue

    combined_html = "\n".join(html_content.values())
    combined_css = "\n".join(css_content.values())
    combined_js = "\n".join(js_content.values())
    combined_all = combined_html + "\n" + combined_css + "\n" + combined_js

    features: List[Feature] = []

    for feat, patterns in FEATURE_PATTERNS.items():
        evidences=[]
        files_evidence=[]
        confidence="unknown"
        for pat in patterns:
            try:
                # search in appropriate blob
                # heuristic: choose blob based on feat
                if feat in ["Responsive CSS","Animations"] and combined_css:
                    blob = combined_css + combined_js
                    file_map = {**css_content, **js_content}
                elif feat in ["DOM Manipulation","LocalStorage","API Requests"]:
                    blob = combined_js
                    file_map = js_content
                else:
                    blob = combined_all
                    file_map = {**html_content, **css_content, **js_content}

                if re.search(pat, blob, re.I):
                    # Find specific file
                    found_file=None
                    for fp, txt in file_map.items():
                        if re.search(pat, txt, re.I):
                            found_file=os.path.relpath(fp, root)
                            break
                    snippet = pat
                    evidences.append(f"pattern:{pat} found" + (f" in {found_file}" if found_file else ""))
                    if found_file and found_file not in files_evidence:
                        files_evidence.append(found_file)
            except re.error:
                if pat.lower() in combined_all.lower():
                    evidences.append(f"string:{pat}")
        if evidences:
            # Determine confidence
            # Strong evidence: tag existence <nav etc counts as detected, but need to ensure actual evidence
            if len(evidences)>=2:
                confidence="detected"
            elif any("id=" in e or "<nav" in e or "<footer" in e or "<form" in e for e in evidences):
                confidence="detected"
            else:
                confidence="inferred"
            # Deduplicate
            evidences=list(dict.fromkeys(evidences))[:3]
            features.append(Feature(name=feat, confidence=confidence, evidence=evidences, files=files_evidence[:3]))

    # Sort features: detected first then inferred
    order={"detected":0, "inferred":1, "unknown":2}
    features.sort(key=lambda x: (order.get(x.confidence,9), x.name))
    return features

def analyze_website_details(root: str, files: List[str]) -> Dict:
    """Additional website specifics for PDF"""
    details={}
    html_files=[f for f in files if f.lower().endswith((".html",".vue",".jsx",".tsx"))]
    css_files=[f for f in files if f.lower().endswith((".css",".scss",".sass",".less"))]
    js_files=[f for f in files if f.lower().endswith((".js",".jsx",".ts",".tsx"))]

    # Count media queries
    media_count=0
    for f in css_files:
        try:
            if os.path.getsize(f) > 1_000_000: continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                txt=fh.read()
                media_count+=len(re.findall(r"@media", txt))
        except: pass
    details["media_queries"]=media_count
    details["has_responsive"]=media_count>0

    # External resources
    external=[]
    for f in html_files[:10]:
        try:
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                txt=fh.read()
                for m in re.findall(r'src=["\'](https?://[^"\']+)["\']', txt):
                    external.append(m)
                for m in re.findall(r'href=["\'](https?://[^"\']+)["\']', txt):
                    if "cdn" in m or "google" in m or "cloudflare" in m:
                        external.append(m)
        except: pass
    details["external_resources"]=list(dict.fromkeys(external))[:10]

    # Event listeners count
    ev_count=0
    for f in js_files:
        try:
            if os.path.getsize(f) > 800*1024: continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                txt=fh.read()
                ev_count+=len(re.findall(r"addEventListener", txt))
        except: pass
    details["event_listeners"]=ev_count

    # Forms count
    form_count=0
    for f in html_files:
        try:
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                form_count+=len(re.findall(r"<form", fh.read(), re.I))
        except: pass
    details["forms"]=form_count

    return details
