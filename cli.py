#!/usr/bin/env python3
"""
0xPDFForge CLI - real-world usage without browser.
Everyone can use it: ZIP -> analyze -> PDF in one command.

Usage:
  python cli.py --zip project.zip --template corporate --output docs.pdf --page-size A4
  python cli.py --zip examples/sample-project.zip --template github
  python cli.py --list-templates
"""
import argparse, os, sys, tempfile, zipfile, json, pathlib, re

# Ensure imports work when run from root
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from analyzer.scanners.safe_extract import safe_extract, cleanup
from analyzer.pipeline import analyze_project
from pdf.engine import generate_pdf
from templates.definitions import list_templates

DEFAULT_SECS = [
    {"id":"cover","title":"Cover","subtitle":"","enabled":True},
    {"id":"executive","title":"Executive Summary","subtitle":"","enabled":True},
    {"id":"overview","title":"Project Overview","subtitle":"","enabled":True},
    {"id":"goals","title":"Project Goals","subtitle":"","enabled":True},
    {"id":"stack","title":"Technology Stack","subtitle":"","enabled":True},
    {"id":"statistics","title":"Project Statistics","subtitle":"","enabled":True},
    {"id":"architecture","title":"Architecture","subtitle":"","enabled":True},
    {"id":"structure","title":"Project Structure","subtitle":"","enabled":True},
    {"id":"features","title":"Features","subtitle":"","enabled":True},
    {"id":"uipreview","title":"UI Preview","subtitle":"","enabled":True},
    {"id":"dependencies","title":"Dependencies","subtitle":"","enabled":True},
    {"id":"api","title":"API Integration","subtitle":"","enabled":True},
    {"id":"database","title":"Database","subtitle":"","enabled":True},
    {"id":"security","title":"Security Findings","subtitle":"","enabled":True},
    {"id":"testing","title":"Testing","subtitle":"","enabled":True},
    {"id":"setup","title":"Development Setup","subtitle":"","enabled":True},
    {"id":"usage","title":"Usage","subtitle":"","enabled":True},
    {"id":"limitations","title":"Limitations","subtitle":"","enabled":True},
    {"id":"future","title":"Future Improvements","subtitle":"","enabled":True},
    {"id":"conclusion","title":"Conclusion","subtitle":"","enabled":True},
]

def main():
    ap = argparse.ArgumentParser(description="0xPDFForge - ZIP to PDF")
    ap.add_argument("--zip", dest="zip_path", help="Path to project ZIP")
    ap.add_argument("--project", dest="project_path", help="Path to project folder (alternative to --zip)")
    ap.add_argument("--template", default="github", help="Template id (see --list-templates)")
    ap.add_argument("--output", default=None, help="Output PDF path")
    ap.add_argument("--page-size", default="A4", choices=["A4","Letter"])
    ap.add_argument("--list-templates", action="store_true", help="List templates and exit")
    args = ap.parse_args()

    if args.list_templates:
        for t in list_templates():
            print(f"{t['id']:18} {t['category']:12} {t['name']:20} {t['description']}")
        return

    source = args.zip_path or args.project_path
    if not source:
        ap.error("Provide --zip or --project")
    if not os.path.exists(source):
        print(f"Not found: {source}", file=sys.stderr); sys.exit(1)

    # Prepare root
    tmp_extract = None
    if args.zip_path:
        tmp_extract = tempfile.mkdtemp(prefix="pdfforge_cli_")
        try:
            root, _ = safe_extract(source, tmp_extract)
        except Exception as e:
            print(f"Extraction failed: {e}", file=sys.stderr); sys.exit(1)
    else:
        root = os.path.abspath(source)

    print(f"Analyzing {root} ...")
    model = analyze_project(root)
    project = model.to_dict()
    print(f"  Found {project['statistics']['total_files']} files, {len(project['languages'])} languages, {len(project['frameworks'])} frameworks")
    print(f"  Primary: {project['languages'][0]['language'] if project['languages'] else 'unknown'}")
    print(f"  Stack: {', '.join([f['name'] for f in project['frameworks'][:4]]) or 'none'}")

    raw_out = project['project_name'] if project.get('project_name') else 'project'
    safe_out = re.sub(r'[^A-Za-z0-9._-]', '_', raw_out).strip('_') or 'project'
    safe_out = safe_out[:80]
    out = args.output or f"{safe_out}_{args.template}.pdf"
    print(f"Generating PDF ({args.template}, {args.page_size}) -> {out}")
    try:
        generate_pdf(project, args.template, DEFAULT_SECS, page_size=args.page_size, output_path=out)
    except Exception as e:
        print(f"PDF failed: {e}", file=sys.stderr); import traceback; traceback.print_exc(); sys.exit(1)
    print(f"Done - {os.path.getsize(out)} bytes")

    if tmp_extract:
        cleanup(tmp_extract)

if __name__ == "__main__":
    main()
