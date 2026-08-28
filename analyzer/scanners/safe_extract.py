"""
Safe ZIP extraction with traversal, bomb, symlink protections
"""
import os
import zipfile
import pathlib
import tempfile
import shutil
from typing import Tuple, List
from ..config import MAX_ZIP_SIZE, MAX_EXTRACTED_SIZE, MAX_FILE_COUNT, MAX_SINGLE_FILE

class ExtractionError(Exception):
    pass

def validate_zip(path: str):
    size = os.path.getsize(path)
    if size > MAX_ZIP_SIZE:
        raise ExtractionError(f"ZIP too large: {size} bytes > limit {MAX_ZIP_SIZE}")
    if size == 0:
        raise ExtractionError("Empty ZIP file")
    try:
        with zipfile.ZipFile(path, 'r') as z:
            # test for bad zip
            bad = z.testzip()
            if bad:
                raise ExtractionError(f"Corrupt entry: {bad}")
    except zipfile.BadZipFile:
        raise ExtractionError("Invalid or corrupted ZIP file")

def safe_extract(zip_path: str, dest_dir: str = None) -> Tuple[str, List[str]]:
    """
    Extract zip safely to a temp dir.
    Returns (extracted_root, list_of_files)
    Raises ExtractionError on violation.
    """
    validate_zip(zip_path)
    if dest_dir is None:
        dest_dir = tempfile.mkdtemp(prefix="pdfforge_")
    else:
        os.makedirs(dest_dir, exist_ok=True)

    dest_real = os.path.realpath(dest_dir)
    total_size = 0
    file_count = 0
    extracted_files: List[str] = []

    with zipfile.ZipFile(zip_path, 'r') as z:
        infos = z.infolist()
        if len(infos) > MAX_FILE_COUNT:
            raise ExtractionError(f"Too many files: {len(infos)} > {MAX_FILE_COUNT}")
        if len(infos) == 0:
            raise ExtractionError("ZIP contains no files")

        for info in infos:
            # Check individual compressed size? Use file_size
            if info.file_size > MAX_SINGLE_FILE:
                raise ExtractionError(f"File too large: {info.filename} ({info.file_size} bytes)")
            total_size += info.file_size
            if total_size > MAX_EXTRACTED_SIZE:
                raise ExtractionError(f"Extracted size exceeds limit {MAX_EXTRACTED_SIZE}")

            # Path traversal check
            # Normalize
            filename = info.filename

            # Reject absolute paths - explicit leading slash (Windows isabs is unreliable for /tmp)
            if os.path.isabs(filename) or filename.startswith("/") or filename.startswith("\\"):
                raise ExtractionError(f"Absolute path rejected: {filename}")
            # Reject traversal
            # Use pathlib to resolve .. ?
            parts = pathlib.Path(filename).parts
            if ".." in parts:
                raise ExtractionError(f"Path traversal detected: {filename}")
            # Reject Windows drive letters
            if ":" in filename:
                raise ExtractionError(f"Invalid filename (colon): {filename}")

            # Symlink check: if external_attr indicates symlink (unix), reject
            # ZipInfo external_attr >>16 is file mode; 0xA000 is symlink
            if (info.external_attr >> 16) & 0xA000 == 0xA000:
                raise ExtractionError(f"Symlink rejected: {filename}")

            # Strip leading / or ./
            filename = filename.lstrip("/\\")
            if filename.startswith("./"):
                filename = filename[2:]

            if not filename or filename.endswith("/"):
                # directory
                target = os.path.join(dest_real, filename)
                # ensure inside dest
                abs_target = os.path.realpath(target)
                if not abs_target.startswith(dest_real + os.sep) and abs_target != dest_real:
                    raise ExtractionError(f"Directory traversal: {filename}")
                os.makedirs(target, exist_ok=True)
                continue

            target_path = os.path.join(dest_real, filename)
            abs_target = os.path.realpath(target_path)
            # must be inside dest
            if not abs_target.startswith(dest_real + os.sep):
                raise ExtractionError(f"Path traversal: {filename}")

            # Ensure parent exists
            os.makedirs(os.path.dirname(abs_target), exist_ok=True)

            # Prevent overwriting via zip bomb with huge compression ratio check
            # Check ratio where compressed vs uncompressed suspicious
            if info.compress_size > 0 and info.file_size / max(info.compress_size, 1) > 1000:
                # Suspicious ratio, but allow small files? flag
                if info.file_size > 1024*1024:
                    raise ExtractionError(f"Suspicious compression ratio: {filename}")

            # Actually extract file content
            with z.open(info, 'r') as src, open(abs_target, 'wb') as dst:
                shutil.copyfileobj(src, dst, length=1024*64)
            extracted_files.append(abs_target)
            file_count += 1
            if file_count > MAX_FILE_COUNT:
                raise ExtractionError("File count exceeded during extraction")

    # Handle single top-level folder case: unwrap one level if only one dir at root
    try:
        entries = os.listdir(dest_real)
        if len(entries) == 1:
            single = os.path.join(dest_real, entries[0])
            if os.path.isdir(single):
                # Move contents up? Keep as is but return logical root
                # We return dest_real, but caller should handle unwrapping
                pass
    except:
        pass

    return dest_real, extracted_files

def cleanup(path: str):
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except:
        pass
