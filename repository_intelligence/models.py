from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class FileCategory(str, Enum):
    SOURCE = "SOURCE"
    TEST = "TEST"
    CONFIG = "CONFIG"
    DOC = "DOC"
    ASSET = "ASSET"
    INFRA = "INFRA"
    SCRIPT = "SCRIPT"
    DATABASE = "DATABASE"
    MIGRATION = "MIGRATION"
    CI_CD = "CI_CD"
    DEPENDENCY = "DEPENDENCY"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value

class RepositoryType(str, Enum):
    BACKEND_SERVICE = "Backend Service"
    FRONTEND_APP = "Frontend Application"
    CLI_TOOL = "CLI Tool"
    SDK_LIBRARY = "SDK/Library"
    MONOLITH = "Monolith"
    MICROSERVICE = "Microservice"
    DOCUMENTATION = "Documentation"
    CONFIG_REPO = "Configuration Repository"
    MONOREPO = "Monorepo"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class RepositoryNode:
    relative_path: str
    absolute_path: str
    name: str
    depth: int
    is_hidden: bool
    parent_dir: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "name": self.name,
            "depth": self.depth,
            "is_hidden": self.is_hidden,
            "parent_dir": self.parent_dir,
        }

@dataclass(frozen=True)
class RepositoryFile(RepositoryNode):
    extension: str
    size_bytes: int
    is_binary: bool
    language: str | None
    category: FileCategory

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "type": "file",
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "is_binary": self.is_binary,
            "language": self.language,
            "category": self.category.value,
        })
        return base

@dataclass(frozen=True)
class RepositoryDirectory(RepositoryNode):
    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({"type": "directory"})
        return base

@dataclass(frozen=True)
class RepositorySnapshot:
    root_path: str
    files: list[RepositoryFile]
    directories: list[RepositoryDirectory]
    ignored_count: int
    snapshot_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_version": self.snapshot_version,
            "root_path": self.root_path,
            "files": [f.to_dict() for f in self.files],
            "directories": [d.to_dict() for d in self.directories],
            "ignored_count": self.ignored_count,
        }

@dataclass(frozen=True)
class LanguageSummary:
    name: str
    file_count: int
    primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "file_count": self.file_count, "primary": self.primary}

@dataclass(frozen=True)
class FrameworkSummary:
    name: str
    indicators: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "indicators": self.indicators}

@dataclass(frozen=True)
class TechnologyStack:
    languages: list[LanguageSummary]
    frameworks: list[FrameworkSummary]
    package_managers: list[str]
    build_systems: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "languages": [l.to_dict() for l in self.languages],
            "frameworks": [f.to_dict() for f in self.frameworks],
            "package_managers": self.package_managers,
            "build_systems": self.build_systems,
        }

@dataclass(frozen=True)
class RepositoryStatistics:
    total_files: int
    total_directories: int
    total_size_bytes: int
    average_file_size: int
    largest_file_bytes: int
    source_files: int
    test_files: int
    config_files: int
    doc_count: int
    asset_count: int
    language_distribution: dict[str, int]
    category_distribution: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "average_file_size": self.average_file_size,
            "largest_file_bytes": self.largest_file_bytes,
            "source_files": self.source_files,
            "test_files": self.test_files,
            "config_files": self.config_files,
            "doc_count": self.doc_count,
            "asset_count": self.asset_count,
            "language_distribution": dict(self.language_distribution),
            "category_distribution": dict(self.category_distribution),
        }

@dataclass(frozen=True)
class FrameworkRule:
    name: str
    file_indicators: list[str] = field(default_factory=list)
    dependency_indicators: list[str] = field(default_factory=list)
    source_indicators: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class EntryPointRule:
    name: str
    match_paths: list[str] = field(default_factory=list)
    match_names: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class RepositoryProfile:
    name: str
    root: str
    repository_type: RepositoryType | str
    is_monorepo: bool
    is_workspace: bool
    stats: RepositoryStatistics
    stack: TechnologyStack
    entry_points: list[str]
    tests: list[str]
    configs: list[str]
    documentation: list[str]
    infrastructure: list[str]
    
    # Deterministic Lookup Indexes
    files_by_extension: dict[str, list[str]] = field(default_factory=dict)
    files_by_language: dict[str, list[str]] = field(default_factory=dict)
    files_by_category: dict[str, list[str]] = field(default_factory=dict)
    files_by_directory: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "root": self.root,
            "repository_type": getattr(self.repository_type, "value", self.repository_type),
            "is_monorepo": self.is_monorepo,
            "is_workspace": self.is_workspace,
            "stats": self.stats.to_dict(),
            "stack": self.stack.to_dict(),
            "entry_points": self.entry_points,
            "tests": self.tests,
            "configs": self.configs,
            "documentation": self.documentation,
            "infrastructure": self.infrastructure,
            "indexes": {
                "by_extension": dict(self.files_by_extension),
                "by_language": dict(self.files_by_language),
                "by_category": dict(self.files_by_category),
                "by_directory": dict(self.files_by_directory),
            }
        }