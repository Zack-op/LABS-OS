from __future__ import annotations
import re
from collections import defaultdict
from pathlib import Path

from repository_intelligence.models import (
    AssetClass, DependencyEdge, EntryPointRule, FileCategory, FrameworkRule,
    FrameworkSummary, LanguageSummary, RelationshipType, RepositoryProfile,
    RepositorySnapshot, RepositoryStatistics, RepositoryType, TechnologyStack,
)

FRAMEWORK_RULES = [
    FrameworkRule("FastAPI", dependency_indicators=["fastapi"], source_indicators=["from fastapi", "import fastapi"]),
    FrameworkRule("Django", file_indicators=["manage.py"], dependency_indicators=["django"]),
    FrameworkRule("React", file_indicators=["vite.config.ts", "vite.config.js"], dependency_indicators=["react"], source_indicators=["import React", "from 'react'"]),
    FrameworkRule("Next.js", file_indicators=["next.config.js", "next.config.ts", "next.config.mjs"], dependency_indicators=["next"]),
    FrameworkRule("Tailwind CSS", file_indicators=["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"], dependency_indicators=["tailwindcss"])
]

ENTRY_POINT_RULES = [
    EntryPointRule("Python Standard", match_names=["main.py", "app.py", "manage.py"]),
    EntryPointRule("Node Standard", match_names=["index.js", "index.ts", "server.js", "server.ts"]),
    EntryPointRule("Next.js App Router", match_paths=["app/page.tsx", "app/layout.tsx", "pages/index.tsx"]),
    EntryPointRule("Rust Standard", match_paths=["src/main.rs", "src/lib.rs"]),
    EntryPointRule("Go Standard", match_names=["main.go"]),
]

PACKAGE_MANAGERS = {
    "package.json": "npm/yarn/pnpm", "requirements.txt": "pip", "pyproject.toml": "poetry/pip",
    "Cargo.toml": "cargo", "go.mod": "go modules"
}

class RepositoryIntelligence:
    def build_profile(self, snapshot: RepositorySnapshot) -> RepositoryProfile:
        files_by_ext = defaultdict(list)
        files_by_lang = defaultdict(list)
        files_by_cat = defaultdict(list)
        files_by_dir = defaultdict(list)
        files_by_asset = defaultdict(list)
        
        filenames = set()
        for f in snapshot.files:
            filenames.add(f.name)
            files_by_ext[f.extension].append(f.relative_path)
            if f.language: files_by_lang[f.language].append(f.relative_path)
            files_by_cat[getattr(f.category, "value", f.category)].append(f.relative_path)
            files_by_dir[f.parent_dir].append(f.relative_path)
            
            asset_class = self._classify_asset(f.name, f.extension, f.parent_dir)
            files_by_asset[asset_class.value].append(f.relative_path)
            
        stats = self._compute_statistics(snapshot)
        deps_content, source_content = self._extract_indicator_contents(snapshot)
        stack = self._compute_stack(snapshot, filenames, deps_content, source_content)
        entry_points = self._detect_entry_points(snapshot)
        is_monorepo = self._detect_monorepo(snapshot)
        
        repo_type = self._determine_repository_type(
            frameworks=[fw.name for fw in stack.frameworks], 
            stats=stats, is_monorepo=is_monorepo, deps_content=deps_content
        )

        m2f, f2m, aliases = self._build_module_indexes(snapshot)
        edges, index = self._build_dependencies(snapshot, m2f, f2m, aliases)
        centrality = self._compute_centrality(index)

        return RepositoryProfile(
            name=snapshot.root_path.split("/")[-1].split("\\")[-1], root=snapshot.root_path,
            repository_type=repo_type, is_monorepo=is_monorepo, is_workspace=is_monorepo,
            stats=stats, stack=stack, entry_points=entry_points,
            tests=files_by_cat[FileCategory.TEST.value],
            configs=files_by_cat[FileCategory.CONFIG.value],
            documentation=files_by_cat[FileCategory.DOC.value],
            infrastructure=files_by_cat[FileCategory.INFRA.value],
            dependency_edges=edges, dependency_index=index,
            module_to_file=m2f, file_to_module=f2m, module_aliases=aliases,
            centrality_metrics=centrality,
            files_by_extension=dict(files_by_ext), files_by_language=dict(files_by_lang),
            files_by_category=dict(files_by_cat), files_by_directory=dict(files_by_dir),
            files_by_asset_class=dict(files_by_asset)
        )

    def _classify_asset(self, filename: str, ext: str, rel_dir: str) -> AssetClass:
        path_lower = f"{rel_dir}/{filename}".replace("\\", "/").lower()
        gen_markers = ["/output/", "output/", "/dist/", "dist/", "/build/", "build/", "/target/", "target/", "/bin/", "bin/", "/out/", "out/"]
        if any(marker in path_lower for marker in gen_markers): return AssetClass.GENERATED
        temp_markers = ["/cache/", "cache/", "/tmp/", "tmp/", "/temp/", "temp/", "/logs/", "logs/"]
        if ext in {".log", ".pyc"} or any(marker in path_lower for marker in temp_markers): return AssetClass.TEMP
        return AssetClass.ENGINEERING

    def _build_module_indexes(self, snapshot: RepositorySnapshot) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        m2f, f2m, aliases = {}, {}, {}
        for f in snapshot.files:
            cat = getattr(f.category, "value", f.category)
            if cat == FileCategory.SOURCE.value:
                rel = f.relative_path.replace("\\", "/")
                parts = rel.rsplit('.', 1)[0].split('/')
                dotted = ".".join(parts)
                
                # Canonical 1:1 mappings
                m2f[dotted] = rel
                f2m[rel] = dotted
                
                # Alias registry
                aliases[f.name] = dotted
                base_name = f.name.rsplit('.', 1)[0]
                if base_name not in aliases: 
                    aliases[base_name] = dotted
        return m2f, f2m, aliases

    def _build_dependencies(self, snapshot: RepositorySnapshot, m2f: dict[str, str], f2m: dict[str, str], aliases: dict[str, str]) -> tuple[list[DependencyEdge], dict[str, list[str]]]:
        edges = []
        edge_set = set()
        
        source_files = {f.relative_path.replace("\\", "/"): f.absolute_path for f in snapshot.files if getattr(f.category, "value", f.category) == FileCategory.SOURCE.value}
        
        # 1. Build Canonical Dependency Graph
        for rel_path, abs_path in source_files.items():
            path_obj = Path(abs_path)
            if not path_obj.exists() or path_obj.stat().st_size > 500000: continue
            
            source_module = f2m.get(rel_path)
            if not source_module: continue
            
            try:
                content = path_obj.read_text(encoding="utf-8", errors="ignore")
                raw_imports = set(re.findall(r'(?:from|import)\s+([a-zA-Z0-9_\.]+)', content))
                raw_imports.update(re.findall(r'(?:require|import)\s*\(\s*[\'"]([^\'"]+)[\'"]', content))
                
                for imp in raw_imports:
                    clean_imp = imp.replace('/', '.').strip('.')
                    
                    # Resolve to canonical identifier
                    canonical_mod = clean_imp if clean_imp in m2f else aliases.get(clean_imp)
                    if not canonical_mod:
                        canonical_mod = aliases.get(clean_imp.split('.')[-1])
                    
                    # Store strictly canonical edges (no self-edges)
                    if canonical_mod and canonical_mod != source_module:
                        edge_tuple = (source_module, canonical_mod, RelationshipType.IMPORT)
                        if edge_tuple not in edge_set:
                            edge_set.add(edge_tuple)
                            edges.append(DependencyEdge(source=source_module, target=canonical_mod, relationship=RelationshipType.IMPORT))
            except Exception: pass

        # 2. Derive Runtime Dependency Index structurally from the canonical graph
        index = defaultdict(list)
        for edge in edges:
            src_file = m2f.get(edge.source)
            tgt_file = m2f.get(edge.target)
            if src_file and tgt_file:
                if tgt_file not in index[src_file]:
                    index[src_file].append(tgt_file)
                    
        return edges, dict(index)

    def _compute_centrality(self, dependency_index: dict[str, list[str]]) -> dict[str, float]:
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        for src, targets in dependency_index.items():
            out_degree[src] = len(targets)
            for t in targets:
                in_degree[t] += 1
                
        centrality = {}
        for node in set(out_degree.keys()).union(in_degree.keys()):
            c = min((out_degree[node] + in_degree[node]) * 0.1, 2.0)
            if c > 0:
                centrality[node] = round(c, 3)
        return centrality

    def _extract_indicator_contents(self, snapshot: RepositorySnapshot) -> tuple[str, str]:
        deps_content, source_content = "", ""
        for f in snapshot.files:
            cat = getattr(f.category, "value", f.category)
            if cat == FileCategory.DEPENDENCY.value and f.size_bytes < 100000:
                try: deps_content += Path(f.absolute_path).read_text(encoding="utf-8") + "\n"
                except Exception: pass
            elif cat == FileCategory.SOURCE.value and f.size_bytes < 50000 and len(source_content) < 500000:
                try: source_content += Path(f.absolute_path).read_text(encoding="utf-8") + "\n"
                except Exception: pass
        return deps_content, source_content

    def _compute_statistics(self, snapshot: RepositorySnapshot) -> RepositoryStatistics:
        counts, lang_dist = defaultdict(int), defaultdict(int)
        total_size, max_size = 0, 0
        for f in snapshot.files:
            cat = getattr(f.category, "value", f.category)
            counts[cat] += 1
            if f.language: lang_dist[f.language] += 1
            total_size += f.size_bytes
            if f.size_bytes > max_size: max_size = f.size_bytes
        total_files = len(snapshot.files)
        return RepositoryStatistics(
            total_files=total_files, total_directories=len(snapshot.directories),
            total_size_bytes=total_size, average_file_size=(total_size // total_files) if total_files > 0 else 0,
            largest_file_bytes=max_size, source_files=counts[FileCategory.SOURCE.value],
            test_files=counts[FileCategory.TEST.value], config_files=counts[FileCategory.CONFIG.value],
            doc_count=counts[FileCategory.DOC.value], asset_count=counts[FileCategory.ASSET.value],
            language_distribution=dict(lang_dist), category_distribution=dict(counts)
        )

    def _compute_stack(self, snapshot: RepositorySnapshot, filenames: set[str], deps: str, src: str) -> TechnologyStack:
        lang_counts = defaultdict(int)
        for f in snapshot.files:
            cat = getattr(f.category, "value", f.category)
            if f.language and cat == FileCategory.SOURCE.value: lang_counts[f.language] += 1
        sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        languages = [LanguageSummary(name=name, file_count=count, primary=(i==0)) for i, (name, count) in enumerate(sorted_langs)]
        frameworks = []
        for rule in FRAMEWORK_RULES:
            matched = []
            if any(ind in filenames for ind in rule.file_indicators): matched.append("file")
            if any(ind in deps for ind in rule.dependency_indicators): matched.append("dependency")
            if any(ind in src for ind in rule.source_indicators): matched.append("source")
            if matched: frameworks.append(FrameworkSummary(name=rule.name, indicators=matched))
        return TechnologyStack(languages=languages, frameworks=frameworks, package_managers=[v for k, v in PACKAGE_MANAGERS.items() if k in filenames], build_systems=[])

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
        if is_monorepo: return RepositoryType.MONOREPO
        backend_fws, frontend_fws = {"FastAPI", "Django", "Flask", "Spring", "Express"}, {"Next.js", "React", "Vue", "Angular"}
        has_back, has_front = any(f in backend_fws for f in frameworks), any(f in frontend_fws for f in frameworks)
        if has_back and has_front: return RepositoryType.MONOLITH
        if has_back: return RepositoryType.BACKEND_SERVICE
        if has_front: return RepositoryType.FRONTEND_APP
        if '"bin":' in deps_content or 'console_scripts' in deps_content: return RepositoryType.CLI_TOOL
        if stats.doc_count > 0 and stats.doc_count > (stats.source_files * 2): return RepositoryType.DOCUMENTATION
        if stats.config_files > 0 and stats.source_files == 0: return RepositoryType.CONFIG_REPO
        if stats.source_files > 0: return RepositoryType.SDK_LIBRARY
        return RepositoryType.UNKNOWN