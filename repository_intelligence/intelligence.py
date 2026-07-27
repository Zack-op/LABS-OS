from __future__ import annotations
from collections import defaultdict
from pathlib import Path

from repository_intelligence.models import (
    EntryPointRule,
    FileCategory,
    FrameworkRule,
    FrameworkSummary,
    LanguageSummary,
    RepositoryProfile,
    RepositorySnapshot,
    RepositoryStatistics,
    RepositoryType,
    TechnologyStack,
)

# Extensible Registries
FRAMEWORK_RULES = [
    FrameworkRule(
        name="FastAPI",
        dependency_indicators=["fastapi"],
        source_indicators=["from fastapi", "import fastapi"]
    ),
    FrameworkRule(
        name="Django",
        file_indicators=["manage.py"],
        dependency_indicators=["django"],
    ),
    FrameworkRule(
        name="React",
        file_indicators=["vite.config.ts", "vite.config.js"],
        dependency_indicators=["react"],
        source_indicators=["import React", "from 'react'"]
    ),
    FrameworkRule(
        name="Next.js",
        file_indicators=["next.config.js", "next.config.ts", "next.config.mjs"],
        dependency_indicators=["next"]
    ),
    FrameworkRule(
        name="Tailwind CSS",
        file_indicators=["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"],
        dependency_indicators=["tailwindcss"]
    )
]

ENTRY_POINT_RULES = [
    EntryPointRule("Python Standard", match_names=["main.py", "app.py", "manage.py"]),
    EntryPointRule("Node Standard", match_names=["index.js", "index.ts", "server.js", "server.ts"]),
    EntryPointRule("Next.js App Router", match_paths=["app/page.tsx", "app/layout.tsx", "pages/index.tsx"]),
    EntryPointRule("Rust Standard", match_paths=["src/main.rs", "src/lib.rs"]),
    EntryPointRule("Go Standard", match_names=["main.go"]),
]

PACKAGE_MANAGERS = {
    "package.json": "npm/yarn/pnpm",
    "requirements.txt": "pip",
    "pyproject.toml": "poetry/pip",
    "Cargo.toml": "cargo",
    "go.mod": "go modules"
}

class RepositoryIntelligence:
    """Consumes a RepositorySnapshot and deterministically interprets project structure."""

    def build_profile(self, snapshot: RepositorySnapshot) -> RepositoryProfile:
        # Precompute Deterministic Lookup Indexes
        files_by_ext = defaultdict(list)
        files_by_lang = defaultdict(list)
        files_by_cat = defaultdict(list)
        files_by_dir = defaultdict(list)
        
        filenames = set()
        
        for f in snapshot.files:
            filenames.add(f.name)
            files_by_ext[f.extension].append(f.relative_path)
            if f.language:
                files_by_lang[f.language].append(f.relative_path)
            files_by_cat[f.category.value].append(f.relative_path)
            files_by_dir[f.parent_dir].append(f.relative_path)
            
        stats = self._compute_statistics(snapshot)
        
        # Extracted contents for multi-indicator evaluation
        deps_content, source_content = self._extract_indicator_contents(snapshot)
        
        stack = self._compute_stack(snapshot, filenames, deps_content, source_content)
        entry_points = self._detect_entry_points(snapshot)
        is_monorepo = self._detect_monorepo(snapshot)
        
        repo_type = self._determine_repository_type(
            frameworks=[fw.name for fw in stack.frameworks], 
            stats=stats, 
            is_monorepo=is_monorepo, 
            deps_content=deps_content
        )

        return RepositoryProfile(
            name=snapshot.root_path.split("/")[-1].split("\\")[-1],
            root=snapshot.root_path,
            repository_type=repo_type,
            is_monorepo=is_monorepo,
            is_workspace=is_monorepo,
            stats=stats,
            stack=stack,
            entry_points=entry_points,
            tests=files_by_cat[FileCategory.TEST.value],
            configs=files_by_cat[FileCategory.CONFIG.value],
            documentation=files_by_cat[FileCategory.DOC.value],
            infrastructure=files_by_cat[FileCategory.INFRA.value],
            files_by_extension=dict(files_by_ext),
            files_by_language=dict(files_by_lang),
            files_by_category=dict(files_by_cat),
            files_by_directory=dict(files_by_dir)
        )

    def _extract_indicator_contents(self, snapshot: RepositorySnapshot) -> tuple[str, str]:
        """Reads lightweight dependency files and a sample of source files to support deterministic rules."""
        deps_content = ""
        source_content = ""
        
        for f in snapshot.files:
            if f.category == FileCategory.DEPENDENCY and f.size_bytes < 100000:
                try:
                    deps_content += Path(f.absolute_path).read_text(encoding="utf-8") + "\n"
                except Exception:
                    pass
            elif f.category == FileCategory.SOURCE and f.size_bytes < 50000 and len(source_content) < 500000:
                try:
                    source_content += Path(f.absolute_path).read_text(encoding="utf-8") + "\n"
                except Exception:
                    pass
                    
        return deps_content, source_content

    def _compute_statistics(self, snapshot: RepositorySnapshot) -> RepositoryStatistics:
        counts = defaultdict(int)
        lang_dist = defaultdict(int)
        total_size = 0
        max_size = 0
        
        for f in snapshot.files:
            counts[f.category.value] += 1
            if f.language:
                lang_dist[f.language] += 1
            total_size += f.size_bytes
            if f.size_bytes > max_size:
                max_size = f.size_bytes
                
        total_files = len(snapshot.files)
        
        return RepositoryStatistics(
            total_files=total_files,
            total_directories=len(snapshot.directories),
            total_size_bytes=total_size,
            average_file_size=(total_size // total_files) if total_files > 0 else 0,
            largest_file_bytes=max_size,
            source_files=counts[FileCategory.SOURCE.value],
            test_files=counts[FileCategory.TEST.value],
            config_files=counts[FileCategory.CONFIG.value],
            doc_count=counts[FileCategory.DOC.value],
            asset_count=counts[FileCategory.ASSET.value],
            language_distribution=dict(lang_dist),
            category_distribution=dict(counts)
        )

    def _compute_stack(self, snapshot: RepositorySnapshot, filenames: set[str], deps: str, src: str) -> TechnologyStack:
        lang_counts = defaultdict(int)
        for f in snapshot.files:
            if f.language and f.category == FileCategory.SOURCE:
                lang_counts[f.language] += 1
                
        sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        languages = [
            LanguageSummary(name=name, file_count=count, primary=(i==0))
            for i, (name, count) in enumerate(sorted_langs)
        ]

        frameworks = []
        for rule in FRAMEWORK_RULES:
            matched = []
            if any(ind in filenames for ind in rule.file_indicators):
                matched.append("file")
            if any(ind in deps for ind in rule.dependency_indicators):
                matched.append("dependency")
            if any(ind in src for ind in rule.source_indicators):
                matched.append("source")
                
            if matched:
                frameworks.append(FrameworkSummary(name=rule.name, indicators=matched))

        pkg_managers = [v for k, v in PACKAGE_MANAGERS.items() if k in filenames]

        return TechnologyStack(
            languages=languages,
            frameworks=frameworks,
            package_managers=pkg_managers,
            build_systems=[]
        )

    def _detect_entry_points(self, snapshot: RepositorySnapshot) -> list[str]:
        entry_points = []
        for f in snapshot.files:
            for rule in ENTRY_POINT_RULES:
                if f.name in rule.match_names or any(p in f.relative_path.replace("\\", "/") for p in rule.match_paths):
                    entry_points.append(f.relative_path)
        return list(set(entry_points))

    def _detect_monorepo(self, snapshot: RepositorySnapshot) -> bool:
        pkg_files = [f for f in snapshot.files if f.name in {"package.json", "pyproject.toml", "Cargo.toml"}]
        return len([p for p in pkg_files if p.depth > 1]) > 0

    def _determine_repository_type(self, frameworks: list[str], stats: RepositoryStatistics, is_monorepo: bool, deps_content: str) -> RepositoryType:
        if is_monorepo:
            return RepositoryType.MONOREPO
            
        backend_fws = {"FastAPI", "Django", "Flask", "Spring", "Express"}
        frontend_fws = {"Next.js", "React", "Vue", "Angular"}
        
        has_back = any(f in backend_fws for f in frameworks)
        has_front = any(f in frontend_fws for f in frameworks)
        
        if has_back and has_front:
            return RepositoryType.MONOLITH
        if has_back:
            return RepositoryType.BACKEND_SERVICE
        if has_front:
            return RepositoryType.FRONTEND_APP
            
        if '"bin":' in deps_content or 'console_scripts' in deps_content:
            return RepositoryType.CLI_TOOL
            
        if stats.doc_count > 0 and stats.doc_count > (stats.source_files * 2):
            return RepositoryType.DOCUMENTATION
            
        if stats.config_files > 0 and stats.source_files == 0:
            return RepositoryType.CONFIG_REPO
            
        if stats.source_files > 0:
            return RepositoryType.SDK_LIBRARY

        return RepositoryType.UNKNOWN