"""
Screenshot engine stub — graceful fallback when project not runnable.
When Playwright is available and project has a start command, this would:
  1. Detect startup command from package.json / pyproject / etc.
  2. Start isolated process (timeout 15s)
  3. Wait for localhost URL
  4. Capture desktop + mobile via Playwright
  5. Return image paths for PDF embedding

For now: returns unavailable gracefully — static analysis only.
This keeps pipeline deterministic and sandbox-safe.
"""

import os, subprocess, time, tempfile
from typing import Dict

def try_capture_screenshots(root: str, timeout=12) -> Dict:
    """
    Returns {"available": bool, "message": str, "images": []}
    Evidence-based: only attempts if package.json has dev/start script or index.html exists.
    """
    # Heuristic: check for runnable signals
    has_dev = False
    has_html = False
    try:
        # check package.json
        import json, pathlib
        pkg = os.path.join(root, "package.json")
        if os.path.exists(pkg):
            with open(pkg) as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                if any(k in scripts for k in ["dev","start","serve","preview"]):
                    has_dev = True
        if any(os.path.exists(os.path.join(root, f)) for f in ["index.html","src/index.html","public/index.html"]):
            has_html = True
    except:
        pass

    if not (has_dev or has_html):
        return {"available": False, "message": "Live preview unavailable — static project analysis completed.", "images": []}

    # If we had Playwright, we'd attempt run here with strict timeout and sandbox
    # For portfolio safety, we return unavailable but with a helpful note — never fail pipeline
    return {
        "available": False,
        "message": "Live preview unavailable — static project analysis completed. (Playwright capture stub: would attempt `npm run dev` + browser capture when enabled)",
        "images": []
    }
