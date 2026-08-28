import os, re
from typing import List
from ..models import SecurityFinding

# Redaction: we never include secret values
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key\s*[:=]\s*["\'])([^"\']{8,})', "Hard-coded API key", "high"),
    (r'(?i)(secret\s*[:=]\s*["\'])([^"\']{6,})', "Hard-coded secret", "high"),
    (r'(?i)(aws[_-]?access[_-]?key[^"\']*["\']\s*[:=]\s*["\'])([^"\']+)', "AWS Access Key", "high"),
    (r'(?i)(aws[_-]?secret[^"\']*["\']\s*[:=]\s*["\'])([^"\']+)', "AWS Secret", "high"),
    (r'AKIA[0-9A-Z]{16}', "Potential AWS Access Key ID", "high"),
    (r'(?i)sk_(live|test)_[A-Za-z0-9]{16,}', "Stripe Secret Key", "high"),
    (r'(?i)ghp_[A-Za-z0-9]{36}', "GitHub PAT", "high"),
    (r'(?i)password\s*[:=]\s*["\']([^"\']{4,})["\']', "Hard-coded password", "medium"),
    (r'(?i)passwd\s*[:=]\s*["\']([^"\']+)["\']', "Hard-coded password", "medium"),
]

CODE_PATTERNS = [
    (r'\beval\s*\(', "Use of eval()", "high", "eval() can execute arbitrary code. Avoid with user input."),
    (r'innerHTML\s*=', "innerHTML assignment", "medium", "Direct innerHTML can lead to XSS if user data is inserted without sanitization."),
    (r'document\.write\s*\(', "document.write", "medium", "document.write is considered unsafe; prefer DOM APIs."),
    (r'cors.*\*\s*', "Wildcard CORS", "medium", "CORS set to '*' allows any origin. Restrict in production."),
    (r'Access-Control-Allow-Origin\s*:\s*\*', "Wildcard ACAO header", "medium", "Static scan detected ACAO: *"),
    (r'(?i)process\.env.*\|\|\s*["\'](admin|password|123)', "Fallback default secret", "medium", "Environment variable fallback appears to be a hard-coded default."),
    (r'(?i) dangerouslySetInnerHTML', "React dangerouslySetInnerHTML", "medium", "Usage requires sanitization to prevent XSS."),
    (r'(?i)sql\s*=\s*["\'].*\$\{', "Potential SQL string interpolation", "high", "String-interpolated SQL suggests possible injection; use parameterized queries."),
]

def scan_security(root: str, files: List[str]) -> List[SecurityFinding]:
    findings: List[SecurityFinding]=[]
    # Limit scan to source + config files
    candidates=[f for f in files if os.path.splitext(f)[1].lower() in [".js",".jsx",".ts",".tsx",".py",".php",".java",".go",".env",".env.example",".json",".js"]][:80]
    # Also include .env files even if ignored? check root directly
    for pat, title, sev in SECRET_PATTERNS:
        regex=re.compile(pat)
        for f in candidates:
            try:
                # Skip .env.example should be safe but scan anyway
                if os.path.getsize(f) > 600*1024:
                    continue
                with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                    lines=fh.readlines()
                    for idx, line in enumerate(lines, start=1):
                        m=regex.search(line)
                        if m:
                            # Redact value: don't include capture group 2
                            # Create redacted snippet: show prefix only
                            snippet = line.strip()[:80]
                            # Redact
                            snippet = re.sub(r'["\'][^"\']{6,}["\']', '"***"', snippet)
                            snippet = re.sub(r'[A-Za-z0-9_\-]{16,}', '***', snippet)
                            findings.append(SecurityFinding(
                                severity=sev,
                                title=title,
                                description=f"Static scan detected potential hard-coded secret pattern in {os.path.relpath(f, root)}:{idx}. Rotate and move to environment variables.",
                                file=os.path.relpath(f, root),
                                line=idx,
                                evidence_snippet=snippet[:120]
                            ))
                            break  # one per file per pat to avoid flooding
            except:
                continue

    for pat, title, sev, desc in CODE_PATTERNS:
        regex=re.compile(pat)
        for f in candidates:
            try:
                if os.path.getsize(f) > 600*1024:
                    continue
                with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                    for idx, line in enumerate(fh, start=1):
                        if regex.search(line):
                            snippet=line.strip()[:120]
                            # redact possible secrets in snippet
                            snippet=re.sub(r'["\'][^"\']{8,}["\']', '"***"', snippet)
                            findings.append(SecurityFinding(
                                severity=sev,
                                title=title,
                                description=f"Static scan detected '{title}'. {desc}",
                                file=os.path.relpath(f, root),
                                line=idx,
                                evidence_snippet=snippet
                            ))
                            break
            except:
                continue

    # Only keep up to 12 to avoid overwhelming
    # Sort by severity
    order={"high":0,"medium":1,"low":2,"info":3}
    findings.sort(key=lambda x: (order.get(x.severity,9), x.title))
    # Deduplicate by title+file
    seen=set()
    uniq=[]
    for f in findings:
        key=(f.title, f.file)
        if key not in seen:
            seen.add(key)
            uniq.append(f)
        if len(uniq)>=10:
            break
    return uniq
