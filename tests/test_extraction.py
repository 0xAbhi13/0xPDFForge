import os, tempfile, zipfile, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from analyzer.scanners.safe_extract import safe_extract, ExtractionError, cleanup

def make_zip(files: dict, path=None):
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    return path

def test_valid_zip_extracts():
    zp = make_zip({"hello.txt":"hello world", "src/index.js":"console.log(1)"})
    dest = tempfile.mkdtemp()
    try:
        root, files = safe_extract(zp, dest)
        assert os.path.exists(os.path.join(root, "hello.txt"))
        assert len(files)==2
    finally:
        cleanup(dest)
        os.unlink(zp)

def test_path_traversal_rejected():
    zp = make_zip({"../evil.txt":"hack"})
    dest = tempfile.mkdtemp()
    try:
        with pytest.raises(ExtractionError):
            safe_extract(zp, dest)
    finally:
        cleanup(dest)
        os.unlink(zp)

def test_absolute_path_rejected():
    zp = make_zip({"/tmp/evil.txt":"hack"})
    dest = tempfile.mkdtemp()
    try:
        # zipfile may store as /tmp/evil.txt; our validator should reject
        with pytest.raises(ExtractionError):
            safe_extract(zp, dest)
    finally:
        cleanup(dest)
        os.unlink(zp)

def test_empty_zip_rejected():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(path,'w') as z:
        pass
    dest=tempfile.mkdtemp()
    try:
        with pytest.raises(ExtractionError):
            safe_extract(path, dest)
    finally:
        cleanup(dest)
        os.unlink(path)

def test_invalid_zip_rejected():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with open(path,'wb') as f:
        f.write(b"not a zip")
    dest=tempfile.mkdtemp()
    try:
        with pytest.raises(ExtractionError):
            safe_extract(path, dest)
    finally:
        cleanup(dest)
        os.unlink(path)

def test_symlink_rejected():
    # Create a zip with symlink external attr
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(path,'w') as z:
        zi = zipfile.ZipInfo("link")
        zi.create_system = 3  # unix
        zi.external_attr = 0o120777 << 16  # symlink
        z.writestr(zi, "target")
    dest=tempfile.mkdtemp()
    try:
        with pytest.raises(ExtractionError):
            safe_extract(path, dest)
    finally:
        cleanup(dest)
        os.unlink(path)
