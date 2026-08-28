"""
Analyzer configuration — limits & ignored patterns
"""
import os

# Security limits (configurable via env)
MAX_ZIP_SIZE = int(os.getenv("MAX_ZIP_SIZE", 50 * 1024 * 1024))  # 50 MB
MAX_EXTRACTED_SIZE = int(os.getenv("MAX_EXTRACTED_SIZE", 300 * 1024 * 1024))  # 300 MB
MAX_FILE_COUNT = int(os.getenv("MAX_FILE_COUNT", 10000))
MAX_SINGLE_FILE = int(os.getenv("MAX_SINGLE_FILE", 10 * 1024 * 1024))  # 10 MB
MAX_ANALYSIS_TIME = int(os.getenv("MAX_ANALYSIS_TIME", 60))  # seconds per file walk?

IGNORED_DIRS = set([
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".env", "env",
    ".next", ".nuxt", "dist", "build", ".build", "out", "coverage",
    ".pytest_cache", ".mypy_cache", ".turbo", ".parcel-cache", "vendor",
    ".idea", ".vscode", ".gradle", "target", "bin", "obj", ".hg", ".svn",
    "cache", ".cache", "logs", "tmp", "temp"
])

IGNORED_FILES = set([
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitkeep"
])

# Extensions that are binary / not source
BINARY_EXTS = {".png",".jpg",".jpeg",".gif",".webp",".ico",".pdf",".zip",".tar",".gz",".mp4",".mp3",".woff",".woff2",".ttf",".eot",".otf",".exe",".dll",".so",".dylib"}

# Language map: ext -> language
EXT_LANG = {
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".py": "Python",
    ".php": "PHP",
    ".java": "Java",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".json": "JSON",
    ".xml": "XML",
    ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown", ".mdx": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell", ".bash": "Shell",
    ".dockerfile": "Dockerfile",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# Framework detection rules quickly - more in framework detector
