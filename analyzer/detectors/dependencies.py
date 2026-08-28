import os, json, re
from typing import List
from ..models import Dependency

def parse_package_json(path: str) -> List[Dependency]:
    deps=[]
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data=json.load(fh)
            for sect, dev in [("dependencies",False),("devDependencies",True),("peerDependencies",False)]:
                for k,v in data.get(sect,{}).items():
                    deps.append(Dependency(name=k, version=v, source="package.json", dev=dev))
    except:
        pass
    return deps

def parse_requirements(path: str) -> List[Dependency]:
    deps=[]
    try:
        with open(path,'r',encoding='utf-8',errors='ignore') as fh:
            for line in fh:
                line=line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # split version
                m=re.match(r"([A-Za-z0-9_\-]+)(.*)", line)
                if m:
                    name=m.group(1)
                    ver=m.group(2).strip() or None
                    deps.append(Dependency(name=name, version=ver, source=os.path.basename(path)))
    except:
        pass
    return deps

def parse_pyproject(path: str) -> List[Dependency]:
    deps=[]
    try:
        with open(path,'r',encoding='utf-8',errors='ignore') as fh:
            txt=fh.read()
            # naive extract dependencies = [ ... ]
            for m in re.finditer(r'"([^"]+)"\s*', txt):
                pass
            # look for dependencies list
            m=re.search(r"dependencies\s*=\s*\[(.*?)\]", txt, re.S)
            if m:
                inner=m.group(1)
                for q in re.findall(r'"([^"]+)"', inner):
                    # q like "fastapi>=0.68"
                    name=re.split(r"[<>=!~\[]", q)[0].strip()
                    ver=q[len(name):].strip() or None
                    deps.append(Dependency(name=name, version=ver, source="pyproject.toml"))
            # poetry
            m2=re.search(r"\[tool\.poetry\.dependencies\](.*?)(?:\n\[|\Z)", txt, re.S)
            if m2:
                for line in m2.group(1).splitlines():
                    line=line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k,v=line.split("=",1)
                    k=k.strip().strip('"').strip("'")
                    v=v.strip().strip('"').strip("'")
                    if k=="python":
                        continue
                    deps.append(Dependency(name=k, version=v, source="pyproject.toml"))
    except:
        pass
    return deps

def parse_composer(path: str) -> List[Dependency]:
    deps=[]
    try:
        with open(path,'r',encoding='utf-8') as fh:
            data=json.load(fh)
            for sect,dev in [("require",False),("require-dev",True)]:
                for k,v in data.get(sect,{}).items():
                    deps.append(Dependency(name=k, version=v, source="composer.json", dev=dev))
    except:
        pass
    return deps

def parse_go_mod(path: str) -> List[Dependency]:
    deps=[]
    try:
        with open(path,'r',encoding='utf-8',errors='ignore') as fh:
            txt=fh.read()
            for m in re.finditer(r"^\s*([a-zA-Z0-9\.\-/_]+)\s+v?([0-9][^\s]*)", txt, re.M):
                deps.append(Dependency(name=m.group(1), version=m.group(2), source="go.mod"))
    except:
        pass
    return deps

def parse_cargo(path: str) -> List[Dependency]:
    deps=[]
    try:
        with open(path,'r',encoding='utf-8',errors='ignore') as fh:
            txt=fh.read()
            sect=re.search(r"\[dependencies\](.*?)(?:\n\[|\Z)", txt, re.S)
            if sect:
                for line in sect.group(1).splitlines():
                    line=line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    name=line.split("=")[0].strip()
                    ver=line.split("=",1)[1].strip().strip('"').strip("'")
                    deps.append(Dependency(name=name, version=ver, source="Cargo.toml"))
    except:
        pass
    return deps

def detect_dependencies(root: str, files: List[str]) -> List[Dependency]:
    all_deps: List[Dependency]=[]
    for f in files:
        base=os.path.basename(f)
        if base=="package.json":
            all_deps.extend(parse_package_json(f))
        elif base=="requirements.txt":
            all_deps.extend(parse_requirements(f))
        elif base=="Pipfile":
            # similar to requirements? try simple
            try:
                with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                    txt=fh.read()
                    for m in re.finditer(r'"([^"]+)"\s*=\s*"([^"]+)"', txt):
                        all_deps.append(Dependency(name=m.group(1), version=m.group(2), source="Pipfile"))
            except: pass
        elif base=="pyproject.toml":
            all_deps.extend(parse_pyproject(f))
        elif base=="composer.json":
            all_deps.extend(parse_composer(f))
        elif base=="go.mod":
            all_deps.extend(parse_go_mod(f))
        elif base=="Cargo.toml":
            all_deps.extend(parse_cargo(f))
        elif base=="pom.xml":
            try:
                with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                    txt=fh.read()
                    for m in re.finditer(r"<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>", txt):
                        all_deps.append(Dependency(name=m.group(1), version=m.group(2), source="pom.xml"))
            except: pass
        elif base=="build.gradle":
            try:
                with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                    txt=fh.read()
                    for m in re.finditer(r"implementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]", txt):
                        all_deps.append(Dependency(name=m.group(2), version=m.group(3), source="build.gradle"))
            except: pass
    # Deduplicate by (name, source)
    seen=set()
    uniq=[]
    for d in all_deps:
        key=(d.name.lower(), d.source)
        if key not in seen:
            seen.add(key)
            uniq.append(d)
    uniq.sort(key=lambda x: (x.source, x.name.lower()))
    return uniq
