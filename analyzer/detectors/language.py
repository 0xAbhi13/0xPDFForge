import os
from collections import Counter, defaultdict
from typing import List, Dict
from ..config import EXT_LANG, BINARY_EXTS, IGNORED_DIRS
from ..models import LanguageStat

def detect_languages(root: str, files: List[str]) -> List[LanguageStat]:
    """
    Deterministic language stats using bytes + LOC weighted.
    Ignores binary and vendor dirs already pruned, but double-check.
    """
    lang_bytes = Counter()
    lang_files = Counter()
    lang_loc = Counter()
    ext_map = defaultdict(list)

    for f in files:
        # skip ignored still?
        parts = f.replace(root, "").split(os.sep)
        if any(p in IGNORED_DIRS for p in parts):
            continue
        ext = os.path.splitext(f)[1].lower()
        # special Dockerfile
        base = os.path.basename(f).lower()
        if base == "dockerfile" or base.startswith("dockerfile."):
            lang = "Dockerfile"
        else:
            lang = EXT_LANG.get(ext)
            if not lang:
                # No lang, skip for stats (but count under Unknown? we ignore)
                continue
            # JSON counts separately but we include
        try:
            sz = os.path.getsize(f)
        except:
            sz = 0
        # skip huge minified files >1MB and binary
        if ext in BINARY_EXTS:
            continue
        if sz > 2*1024*1024:
            # check if minified: single line huge?
            pass

        lang_bytes[lang] += sz
        lang_files[lang] += 1

        # LOC - count lines for source types only, not too large
        if lang not in ["JSON","YAML","TOML","Markdown"] and sz < 1*1024*1024:
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                    loc = sum(1 for line in fh if line.strip() != "")
                    lang_loc[lang] += loc
            except:
                pass
        else:
            # For json etc, just count lines quickly
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                    lang_loc[lang] += sum(1 for _ in fh)
            except:
                pass

    total_bytes = sum(lang_bytes.values()) or 1
    # Build stats sorted by bytes desc
    stats: List[LanguageStat] = []
    for lang, b in lang_bytes.most_common():
        loc = lang_loc.get(lang, 0)
        cnt = lang_files.get(lang, 0)
        pct = (b / total_bytes) * 100
        # collect extensions belonging
        exts = [e for e, l in EXT_LANG.items() if l == lang]
        stats.append(LanguageStat(
            language=lang,
            extensions=exts[:4],
            files=cnt,
            bytes=b,
            loc=loc,
            percentage=round(pct, 1)
        ))

    # If no languages detected but files exist, mark Unknown?
    if not stats and files:
        stats.append(LanguageStat(language="Unknown", extensions=[], files=len(files), bytes=1, loc=0, percentage=100))

    return stats
