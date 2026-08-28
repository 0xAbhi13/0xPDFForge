"""
Project walker — collects files deterministically
"""
import os
import pathlib
from typing import List, Dict, Tuple
from ..config import IGNORED_DIRS, BINARY_EXTS

def is_ignored_dir(dirname: str) -> bool:
    return dirname in IGNORED_DIRS or dirname.startswith(".")

def should_ignore_file(fname: str) -> bool:
    base = os.path.basename(fname)
    if base.startswith(".") and base not in [".env.example", ".gitignore"]:
        # allow some dotfiles? ignore hidden generally except configs
        if base not in [".env.example", "Dockerfile"]:
            pass
    return False

def walk_project(root: str, max_files=10000) -> Tuple[List[str], List[str], int]:
    """
    Returns (all_files, ignored_files, total_size)
    all_files are relative to root but we return absolute for analysis then convert
    """
    all_files: List[str] = []
    ignored: List[str] = []
    total_size = 0
    root = os.path.realpath(root)

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        # Filter dirs in-place
        # Don't follow symlinked dirs (followlinks=False) but also prune
        original = list(dirnames)
        dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]
        # track ignored
        for d in original:
            if d not in dirnames:
                ignored.append(os.path.join(dirpath, d))

        # Prune if too deep? limit depth to 12?
        rel_depth = dirpath.replace(root, "").count(os.sep)
        if rel_depth > 12:
            dirnames[:] = []
            continue

        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            # Skip if symlink
            try:
                if os.path.islink(fpath):
                    ignored.append(fpath)
                    continue
            except:
                continue
            # Skip binary large? we include but mark
            try:
                sz = os.path.getsize(fpath)
                total_size += sz
            except:
                sz = 0
            # Skip ignored file patterns?
            # e.g., .DS_Store
            if fname in [".DS_Store", "Thumbs.db"]:
                ignored.append(fpath)
                continue
            if len(all_files) >= max_files:
                ignored.append(fpath)
                continue
            all_files.append(fpath)

    return all_files, ignored, total_size

def build_tree(root: str, files: List[str], max_nodes=800):
    """
    Build FileNode tree, collapsible for large projects
    """
    from ..models import FileNode
    import os
    root_name = os.path.basename(os.path.realpath(root)) or "project"
    tree = FileNode(name=root_name, path=root, type="dir")
    # Use dict for dirs
    dir_map = {root: tree}
    # Sort files for deterministic
    files_sorted = sorted(files)
    count = 0
    for f in files_sorted:
        if count >= max_nodes:
            # Add overflow node
            overflow = FileNode(name=f"... +{len(files_sorted)-count} more files", path="", type="file", size=0)
            tree.children.append(overflow)
            break
        rel = os.path.relpath(f, root)
        parts = rel.split(os.sep)
        cur_path = root
        cur_node = tree
        for i, part in enumerate(parts):
            is_last = i == len(parts)-1
            cur_path = os.path.join(cur_path, part)
            if is_last:
                try:
                    sz = os.path.getsize(f)
                except:
                    sz = 0
                loc = None
                # quick loc for text files
                try:
                    if os.path.splitext(f)[1].lower() not in BINARY_EXTS and sz < 2*1024*1024:
                        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                            loc = sum(1 for _ in fh)
                except:
                    loc = None
                node = FileNode(name=part, path=rel, type="file", size=sz, loc=loc)
                cur_node.children.append(node)
                count += 1
            else:
                # dir
                found = None
                for c in cur_node.children:
                    if c.name == part and c.type == "dir":
                        found = c
                        break
                if found:
                    cur_node = found
                else:
                    nd = FileNode(name=part, path=os.path.relpath(cur_path, root), type="dir")
                    cur_node.children.append(nd)
                    dir_map[cur_path] = nd
                    cur_node = nd
    # Sort children dirs first, then files alpha
    def sort_node(n: FileNode):
        n.children.sort(key=lambda x: (0 if x.type=="dir" else 1, x.name.lower()))
        for c in n.children:
            if c.type=="dir":
                sort_node(c)
    sort_node(tree)
    return tree

def get_project_name(root: str, files: List[str]) -> str:
    # Try package.json name, then folder name, then README title
    import json, os, re
    for f in files:
        if os.path.basename(f) == "package.json":
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    j=json.load(fh)
                    if j.get("name"):
                        return j["name"]
            except:
                pass
    # Try pyproject
    for f in files:
        if os.path.basename(f) in ("pyproject.toml","setup.cfg"):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                    txt=fh.read()
                    m=re.search(r'name\s*=\s*["\']([^"\']+)["\']', txt)
                    if m:
                        return m.group(1)
            except:
                pass
    return os.path.basename(os.path.realpath(root)) or "0xProject"
