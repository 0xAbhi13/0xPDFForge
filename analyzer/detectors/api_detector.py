import os, re
from typing import List
from ..models import APICall

# Patterns for API detection
PATTERNS = [
    (r'fetch\s*\(\s*["\'`]([^"\'`]+)["\'`]', "fetch"),
    (r'axios\.(get|post|put|delete|patch)\s*\(\s*["\'`]([^"\'`]+)["\'`]', "axios"),
    (r'axios\s*\(\s*\{[^}]*url\s*:\s*["\'`]([^"\'`]+)["\'`]', "axios"),
    (r'\.ajax\s*\(\s*\{[^}]*url\s*:\s*["\'`]([^"\'`]+)["\'`]', "jQuery"),
    (r'XMLHttpRequest.*open\s*\(\s*["\'](GET|POST|PUT|DELETE|PATCH)["\']\s*,\s*["\'`]([^"\'`]+)["\'`]', "xhr"),
    (r'WebSocket\s*\(\s*["\'`]([^"\'`]+)["\'`]', "websocket"),
    (r'new\s+GraphQLClient\s*\(\s*["\'`]([^"\'`]+)["\'`]', "graphql"),
    (r'fetch\s*\(\s*`([^`]+)\$\{', "fetch_template"),
]

ENDPOINT_RE = re.compile(r'(https?://[^\s"\'`]+|/api/[^\s"\'`]*|/v\d+/[^\s"\'`]*|/graphql[^\s"\'`]*|wss?://[^\s"\'`]+)', re.I)

def redact_endpoint(ep: str) -> str:
    # Redact query params that look like keys
    # Keep structure but hide values after ? and tokens
    if "?" in ep:
        base, qs = ep.split("?",1)
        # Redact values
        parts=[]
        for p in qs.split("&"):
            if "=" in p:
                k,_ = p.split("=",1)
                parts.append(f"{k}=***")
            else:
                parts.append(p)
        ep = base + "?" + "&".join(parts)
    # Redact possible tokens in path? Keep but if long hex, redact
    ep = re.sub(r'[A-Za-z0-9_\-]{32,}', '***', ep)
    return ep[:120]

def detect_apis(root: str, files: List[str]) -> List[APICall]:
    apis: List[APICall]=[]
    candidates=[f for f in files if os.path.splitext(f)[1].lower() in [".js",".jsx",".ts",".tsx",".vue",".py",".php",".java"]][:60]
    for f in candidates:
        try:
            if os.path.getsize(f) > 800*1024:
                continue
            with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                lines=fh.readlines()
                for idx, line in enumerate(lines, start=1):
                    stripped=line.strip()
                    if not stripped or stripped.startswith("//") or stripped.startswith("#"):
                        continue
                    # Check each pattern — find all matches per line (not just first)
                    for pat, lib in PATTERNS:
                        for m in re.finditer(pat, line):
                            # Extract endpoint and method
                            endpoint="unknown"
                            method="GET"
                            if lib=="axios" and len(m.groups())>=2:
                                # for axios.(get|post...) first group is method
                                try:
                                    method=m.group(1).upper() if m.group(1) else "GET"
                                    endpoint=m.group(2)
                                except:
                                    endpoint=m.group(1) if m.groups() else "unknown"
                            elif lib=="xhr" and len(m.groups())>=2:
                                method=m.group(1).upper()
                                endpoint=m.group(2)
                            else:
                                # first group is endpoint
                                endpoint=m.group(1) if m.groups() else "unknown"
                                # try detect method from nearby text
                                if "post" in line.lower():
                                    method="POST"
                                elif "put" in line.lower():
                                    method="PUT"
                                elif "delete" in line.lower():
                                    method="DELETE"
                                elif "patch" in line.lower():
                                    method="PATCH"
                            # Filter out non-endpoint strings (e.g., local variables)
                            if endpoint.startswith("http") or endpoint.startswith("/") or "api" in endpoint.lower() or "graphql" in endpoint.lower() or "ws" in endpoint.lower():
                                endpoint=redact_endpoint(endpoint)
                                apis.append(APICall(
                                    method=method,
                                    endpoint=endpoint,
                                    source_file=os.path.relpath(f, root),
                                    line=idx,
                                    library=lib,
                                    redacted=True
                                ))
                    # Also generic endpoint regex for fetch-like without our pattern? already covered
                    # Check for REST endpoint strings in JS comments? skip
        except:
            continue

    # Deduplicate by endpoint+method
    seen=set()
    uniq=[]
    for a in apis:
        key=(a.method, a.endpoint)
        if key not in seen:
            seen.add(key)
            uniq.append(a)
        if len(uniq)>=30:
            break
    return uniq
