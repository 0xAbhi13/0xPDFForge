"""
Main pipeline — orchestrates deterministic analysis
"""
import os, time, datetime, json
from typing import Dict
from .scanners.walker import walk_project, build_tree, get_project_name
from .detectors.language import detect_languages
from .detectors.framework import detect_frameworks
from .detectors.dependencies import detect_dependencies
from .detectors.features import analyze_features, analyze_website_details
from .detectors.api_detector import detect_apis
from .detectors.database import detect_databases
from .detectors.security import scan_security
from .detectors.architecture import infer_architecture
from .models import ProjectModel, ProjectStats
from .config import IGNORED_DIRS

def analyze_project(root: str, progress_callback=None) -> ProjectModel:
    """
    Progress callback receives (stage, message)
    """
    start=time.time()
    errors=[]
    warnings=[]
    try:
        if progress_callback: progress_callback("scan", "Scanning project")
        # Unwrap single top-level folder if needed?
        # If root contains single dir, use that as logical root
        try:
            entries=[e for e in os.listdir(root) if not e.startswith(".")]
            if len(entries)==1 and os.path.isdir(os.path.join(root, entries[0])):
                maybe=os.path.join(root, entries[0])
                # check if maybe contains typical files (package.json, index.html, etc.) and root doesn't
                if any(os.path.exists(os.path.join(maybe, f)) for f in ["package.json","index.html","README.md","requirements.txt","pyproject.toml"]) and not any(os.path.exists(os.path.join(root,f)) for f in ["package.json","index.html"]):
                    root=maybe
        except: pass

        files, ignored, total_bytes = walk_project(root)
        flat_rel=[os.path.relpath(f, root) for f in files]
        project_name=get_project_name(root, files)

        if progress_callback: progress_callback("languages", "Languages detected")
        languages=detect_languages(root, files)

        if progress_callback: progress_callback("frameworks", "Frameworks detected")
        try:
            frameworks=detect_frameworks(root, files)
        except Exception as e:
            frameworks=[]; errors.append(f"framework detection failed: {e}")

        if progress_callback: progress_callback("dependencies", "Dependencies analyzed")
        try:
            deps=detect_dependencies(root, files)
        except Exception as e:
            deps=[]; errors.append(f"dependency detection failed: {e}")

        if progress_callback: progress_callback("features", "Features detected")
        try:
            features=analyze_features(root, files)
            website_details=analyze_website_details(root, files)
        except Exception as e:
            features=[]; website_details={}; errors.append(f"feature detection failed: {e}")

        if progress_callback: progress_callback("apis", "APIs scanned")
        try:
            apis=detect_apis(root, files)
        except Exception as e:
            apis=[]; errors.append(f"api detection failed: {e}")

        if progress_callback: progress_callback("databases", "Databases scanned")
        try:
            dbs=detect_databases(root, files, [d.name for d in deps])
        except Exception as e:
            dbs=[]; errors.append(f"db detection failed: {e}")

        if progress_callback: progress_callback("security", "Security scan")
        try:
            security=scan_security(root, files)
        except Exception as e:
            security=[]; errors.append(f"security scan failed: {e}")

        if progress_callback: progress_callback("architecture", "Architecture analyzed")
        try:
            arch=infer_architecture(frameworks, languages, apis, dbs, features)
        except Exception as e:
            arch={"nodes":[],"edges":[],"description":"Architecture analysis unavailable","type":"generic"}; errors.append(f"arch failed: {e}")

        if progress_callback: progress_callback("stats", "Statistics compiled")
        # Statistics
        total_loc=sum(l.loc for l in languages)
        # counts
        exts_img={".png",".jpg",".jpeg",".gif",".webp",".svg",".ico"}
        exts_config={".json",".yaml",".yml",".toml",".ini",".env",".config",".xml"}
        assets=0; images=0; tests=0; docs=0; configs=0
        largest_files=[]
        for f in files:
            ext=os.path.splitext(f)[1].lower()
            base=os.path.basename(f).lower()
            if ext in exts_img: images+=1
            if "assets" in f or "public" in f or "static" in f: assets+=1
            if "test" in base or base.startswith("test_") or base.endswith(".test.js") or base.endswith(".spec.js") or "/tests/" in f or "/__tests__/" in f: tests+=1
            if base.startswith("readme") or base.startswith("changelog") or base.endswith(".md"): docs+=1
            if ext in exts_config or base in ["dockerfile","makefile","package.json","tsconfig.json","vite.config.js"]:
                configs+=1
            try:
                sz=os.path.getsize(f)
                largest_files.append({"path":os.path.relpath(f,root),"size":sz})
            except: pass
        largest_files.sort(key=lambda x: x["size"], reverse=True)
        largest_files=largest_files[:8]

        # largest dirs
        from collections import Counter
        dir_sizes=Counter()
        for f in files:
            try:
                sz=os.path.getsize(f)
                d=os.path.dirname(os.path.relpath(f,root)).split(os.sep)[0] or "."
                dir_sizes[d]+=sz
            except: pass
        largest_dirs=[{"name":k,"size":v} for k,v in dir_sizes.most_common(6)]

        # build scripts
        build_scripts={}
        for f in files:
            if os.path.basename(f)=="package.json":
                try:
                    with open(f,'r',encoding='utf-8') as fh:
                        data=json.load(fh)
                        build_scripts=data.get("scripts",{}) or {}
                        break
                except: pass

        source_exts={".js",".jsx",".ts",".tsx",".py",".php",".java",".go",".rs",".c",".cpp",".html",".css",".vue",".svelte"}
        source_files=sum(1 for f in files if os.path.splitext(f)[1].lower() in source_exts)

        stats=ProjectStats(
            total_files=len(files),
            source_files=source_files,
            total_loc=total_loc,
            total_bytes=total_bytes,
            languages=languages,
            dependencies_count=len(deps),
            frameworks_count=len(frameworks),
            assets_count=assets,
            image_count=images,
            test_files=tests,
            doc_files=docs,
            config_files=configs,
            largest_files=largest_files,
            largest_dirs=largest_dirs,
            build_scripts=build_scripts,
            ignored_files=len(ignored)
        )

        # File tree
        try:
            tree=build_tree(root, files)
        except Exception as e:
            tree=None; errors.append(f"tree failed: {e}")

        # Metadata
        metadata={
            "project_name": project_name,
            "total_files": len(files),
            "website_details": website_details,
            "has_readme": any(os.path.basename(f).lower().startswith("readme") for f in files),
            "readme_excerpt": "",
            "env_example": any("env.example" in f or ".env.example" in f for f in files),
        }
        # Readme excerpt
        for f in files:
            if os.path.basename(f).lower().startswith("readme"):
                try:
                    if os.path.getsize(f) < 200*1024:
                        with open(f,'r',encoding='utf-8',errors='ignore') as fh:
                            metadata["readme_excerpt"]=fh.read(800)[:800]
                            break
                except: pass

        documentation={
            "has_readme": metadata["has_readme"],
            "readme_excerpt": metadata["readme_excerpt"],
            "doc_files": docs,
            "has_env_example": metadata["env_example"],
        }

        # Screenshots placeholder
        screenshots={"available": False, "message": "Live preview unavailable — static project analysis completed.", "images":[]}

        duration=int((time.time()-start)*1000)
        model=ProjectModel(
            project_name=project_name,
            analyzed_at=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
            analysis_duration_ms=duration,
            metadata=metadata,
            languages=languages,
            frameworks=frameworks,
            dependencies=deps,
            file_tree=tree,
            flat_files=flat_rel[:1000],  # limit
            statistics=stats,
            features=features,
            apis=apis,
            databases=dbs,
            architecture=arch,
            security=security,
            documentation=documentation,
            screenshots=screenshots,
            errors=errors,
            warnings=warnings
        )
        if progress_callback: progress_callback("done", "Documentation generated")
        return model
    except Exception as e:
        errors.append(str(e))
        raise
