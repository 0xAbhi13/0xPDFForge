"""
0xPDFForge — Structured Project Model
Deterministic, evidence-based. No hallucinated fields.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
import time

class Confidence(str, Enum):
    CONFIRMED = "confirmed"   # direct manifest evidence
    DETECTED = "detected"     # import / pattern evidence
    INFERRED = "inferred"     # heuristic
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "n/a"

@dataclass
class LanguageStat:
    language: str
    extensions: List[str]
    files: int
    bytes: int
    loc: int
    percentage: float

@dataclass
class FrameworkEvidence:
    name: str
    category: str
    confidence: str
    evidence: List[str]
    version: Optional[str] = None

@dataclass
class Dependency:
    name: str
    version: Optional[str]
    source: str  # package.json, requirements.txt, etc.
    dev: bool = False

@dataclass
class FileNode:
    name: str
    path: str
    type: str  # file | dir
    size: int = 0
    loc: Optional[int] = None
    children: List['FileNode'] = field(default_factory=list)

@dataclass
class APICall:
    method: str
    endpoint: str
    source_file: str
    line: int
    library: str
    redacted: bool = True

@dataclass
class DBEvidence:
    technology: str
    confidence: str
    evidence: List[str]
    files: List[str]

@dataclass
class SecurityFinding:
    severity: str  # low | medium | high | info
    title: str
    description: str
    file: Optional[str]
    line: Optional[int]
    evidence_snippet: Optional[str] = None  # redacted

@dataclass
class Feature:
    name: str
    confidence: str
    evidence: List[str]
    files: List[str]

@dataclass
class ArchitectureNode:
    id: str
    label: str
    kind: str
    evidence: List[str]

@dataclass
class ArchitectureEdge:
    from_id: str
    to_id: str
    label: str

@dataclass
class ProjectStats:
    total_files: int
    source_files: int
    total_loc: int
    total_bytes: int
    languages: List[LanguageStat]
    dependencies_count: int
    frameworks_count: int
    assets_count: int
    image_count: int
    test_files: int
    doc_files: int
    config_files: int
    largest_files: List[Dict[str, Any]]
    largest_dirs: List[Dict[str, Any]]
    build_scripts: Dict[str, str]
    ignored_files: int

@dataclass
class ProjectModel:
    # top-level
    project_name: str
    analyzed_at: str
    analysis_duration_ms: int
    # core
    metadata: Dict[str, Any]
    languages: List[LanguageStat]
    frameworks: List[FrameworkEvidence]
    dependencies: List[Dependency]
    file_tree: Optional[FileNode]
    flat_files: List[str]
    statistics: ProjectStats
    features: List[Feature]
    apis: List[APICall]
    databases: List[DBEvidence]
    architecture: Dict[str, Any]  # nodes + edges + description
    security: List[SecurityFinding]
    documentation: Dict[str, Any]
    screenshots: Dict[str, Any]
    # raw
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self):
        # careful recursion for FileNode
        def node_to_dict(n: FileNode):
            d = {"name": n.name, "path": n.path, "type": n.type, "size": n.size}
            if n.loc is not None:
                d["loc"] = n.loc
            if n.children:
                d["children"] = [node_to_dict(c) for c in n.children]
            return d
        return {
            "project_name": self.project_name,
            "analyzed_at": self.analyzed_at,
            "analysis_duration_ms": self.analysis_duration_ms,
            "metadata": self.metadata,
            "languages": [asdict(l) for l in self.languages],
            "frameworks": [asdict(f) for f in self.frameworks],
            "dependencies": [asdict(d) for d in self.dependencies],
            "file_tree": node_to_dict(self.file_tree) if self.file_tree else None,
            "flat_files": self.flat_files,
            "statistics": asdict(self.statistics) if self.statistics else None,
            "features": [asdict(f) for f in self.features],
            "apis": [asdict(a) for a in self.apis],
            "databases": [asdict(d) for d in self.databases],
            "architecture": self.architecture,
            "security": [asdict(s) for s in self.security],
            "documentation": self.documentation,
            "screenshots": self.screenshots,
            "errors": self.errors,
            "warnings": self.warnings,
        }
