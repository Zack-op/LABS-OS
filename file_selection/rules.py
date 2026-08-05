import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any
from file_selection.models import RuleImportance
from repository_intelligence.models import AssetClass, FileCategory, RepositoryProfile, RepositoryType

@dataclass(frozen=True)
class SelectionRule:
    name: str
    stage: int
    importance: RuleImportance
    is_applicable: Callable[[Any, RepositoryProfile, dict], bool]
    evaluate: Callable[[Any, RepositoryProfile, dict], dict[str, Any]]

def _extract_keywords(text: str) -> set[str]:
    if not text: return set()
    words = re.findall(r'\b[a-z_]{3,}\b', str(text).lower())
    stop_words = {"the", "and", "for", "with", "this", "that", "implement", "create", 
                  "update", "delete", "add", "remove", "fix", "issue", "bug", "task", 
                  "feature", "not", "use", "when", "then", "given", "should", "return"}
    return {w for w in words if w not in stop_words}

def _rank_files(keywords: set[str], candidates: list[str], profile: RepositoryProfile, max_results: int = 5) -> list[str]:
    scores = {}
    
    # 1. Dynamic Stack Identity
    stack_identifiers = {fw.name.lower() for fw in profile.stack.frameworks}
    stack_identifiers.update(lang.name.lower() for lang in profile.stack.languages)
    targets_stack = any(k in stack_identifiers for k in keywords)

    # 2. Dependency Neighborhood Indexing (O(1) Reverse Traversal)
    in_edges = defaultdict(list)
    for edge in profile.dependency_edges:
        in_edges[edge.target].append(edge.source)

    config_files = set(profile.files_by_category.get(FileCategory.CONFIG.value, []))
    infra_files = set(profile.files_by_category.get(FileCategory.INFRA.value, []))

    # 3. Deterministic Evidence Evaluation
    for f in candidates:
        f_lower = f.lower()
        filename = f_lower.split('/')[-1]
        dir_parts = f_lower.rsplit('/', 1)[0].split('/') if '/' in f_lower else []
        canonical_mod = profile.file_to_module.get(f, "").lower()
        
        lexical_score = 0.0
        
        # A. Lexical & Canonical Identity Evidence
        for k in keywords:
            if k in filename:
                lexical_score += 5.0
            elif k in dir_parts:
                lexical_score += 3.0
            elif k in canonical_mod:
                lexical_score += 2.0
            elif k in f_lower:
                lexical_score += 1.0
                
        # B. Dependency Neighborhood Evidence
        neighborhood_score = 0.0
        neighbors = set(profile.dependency_index.get(f, []))
        neighbors.update(in_edges.get(f, []))

        for neighbor in neighbors:
            n_lower = neighbor.lower()
            n_filename = n_lower.split('/')[-1]
            for k in keywords:
                if k in n_filename:
                    neighborhood_score += 2.0
                elif k in n_lower:
                    neighborhood_score += 1.0
                    
        # C. Combine Primary Evidence
        total_relevance = lexical_score + (neighborhood_score * 0.5)
        
        if targets_stack and total_relevance == 0.0:
            total_relevance += 1.0
            
        if total_relevance > 0.0:
            # D. Category-Aware Centrality Evaluation
            centrality = min(profile.centrality_metrics.get(f, 0.0), 2.0)
            
            if (f in config_files or f in infra_files) and lexical_score == 0:
                centrality *= 0.1
                
            scores[f] = total_relevance + centrality
            
    sorted_files = sorted(scores.keys(), key=lambda x: (-scores[x], x))
    return sorted_files[:max_results]

# --- Rule Implementations ---
def _domain_applicable(wo, profile, state) -> bool:
    return profile.repository_type in [
        RepositoryType.BACKEND_SERVICE, 
        RepositoryType.FRONTEND_APP, 
        RepositoryType.CLI_TOOL
    ]

def _domain_evaluate(wo, profile, state) -> dict:
    keywords = _extract_keywords(getattr(wo, "title", "") + " " + getattr(wo, "objective", ""))
    domain_files = []
    
    eng_assets = set(profile.files_by_asset_class.get(AssetClass.ENGINEERING.value, []))
    
    if profile.repository_type == RepositoryType.BACKEND_SERVICE or profile.repository_type == RepositoryType.FRONTEND_APP:
        source_pool = [f for f in profile.files_by_category.get(FileCategory.SOURCE.value, []) if f in eng_assets]
        domain_files = _rank_files(keywords, source_pool, profile, 3)
        
    return {
        "primary": domain_files,
        "success": len(domain_files) > 0,
        "explanation": f"Domain Rule mapped {len(domain_files)} foundational files based on engineering relevance."
    }

def _constraint_applicable(wo, profile, state) -> bool:
    return len(getattr(wo, "constraints", [])) > 0

def _constraint_evaluate(wo, profile, state) -> dict:
    constraints_text = " ".join(getattr(wo, "constraints", [])).lower()
    excluded = set()
    
    if "database" in constraints_text or "schema" in constraints_text or "migration" in constraints_text:
        excluded.update(profile.files_by_category.get(FileCategory.DATABASE.value, []))
        excluded.update(profile.files_by_category.get(FileCategory.MIGRATION.value, []))
        
    if "ui" in constraints_text or "frontend" in constraints_text:
        if "no ui" in constraints_text or "do not modify frontend" in constraints_text:
            excluded.update(profile.files_by_category.get(FileCategory.ASSET.value, []))
            
    return {
        "excluded": list(excluded),
        "success": True, 
        "explanation": f"Constraint Rule excluded {len(excluded)} files based on strict task constraints."
    }

def _deliverable_applicable(wo, profile, state) -> bool:
    return True

def _deliverable_evaluate(wo, profile, state) -> dict:
    text = f"{getattr(wo, 'title', '')} {getattr(wo, 'objective', '')}"
    
    for d in getattr(wo, 'deliverables', []):
        if hasattr(d, 'description') and d.description:
            text += f" {d.description}"
        elif isinstance(d, dict) and d.get('description'):
            text += f" {d['description']}"
        else:
            text += f" {str(d)}"
            
    keywords = _extract_keywords(text)
    
    explicit_generated = any(w in keywords for w in ["output", "log", "generated", "artifact", "report", "cache"])
    explicit_docs = any(w in keywords for w in ["doc", "docs", "documentation", "readme", "architecture"])
    
    file_to_cat = {}
    for cat, files in profile.files_by_category.items():
        for f in files: file_to_cat[f] = cat
            
    pool = []
    for f in profile.files_by_asset_class.get(AssetClass.ENGINEERING.value, []):
        cat = file_to_cat.get(f, FileCategory.UNKNOWN.value)
        if cat == FileCategory.DOC.value and not explicit_docs: continue
        pool.append(f)
        
    if explicit_generated:
        pool.extend(profile.files_by_asset_class.get(AssetClass.GENERATED.value, []))
        pool.extend(profile.files_by_asset_class.get(AssetClass.TEMP.value, []))
        
    primary = _rank_files(keywords, pool, profile, 5)
        
    return {
        "primary": primary,
        "success": len(primary) > 0,
        "explanation": f"Deliverable Rule matched {len(primary)} primary files to engineering semantics."
    }

def _ac_applicable(wo, profile, state) -> bool:
    return hasattr(wo, 'acceptance_criteria') and len(wo.acceptance_criteria) > 0

def _ac_evaluate(wo, profile, state) -> dict:
    ac_text = " ".join([ac.description if hasattr(ac, 'description') else str(ac) for ac in wo.acceptance_criteria])
    keywords = _extract_keywords(ac_text)
    
    eng_assets = set(profile.files_by_asset_class.get(AssetClass.ENGINEERING.value, []))
    ac_pool = [f for f in profile.files_by_category.get(FileCategory.SOURCE.value, []) if f in eng_assets]
    supporting = _rank_files(keywords, ac_pool, profile, 3)
    
    return {
        "supporting": supporting,
        "success": len(supporting) > 0,
        "explanation": f"AC Rule identified {len(supporting)} supporting implementation files from acceptance criteria."
    }

def _dependency_applicable(wo, profile, state) -> bool:
    return len(state["primary"]) > 0

def _dependency_evaluate(wo, profile, state) -> dict:
    discovered = set()
    eng_assets = set(profile.files_by_asset_class.get(AssetClass.ENGINEERING.value, []))
    
    for pf in state["primary"]:
        targets = profile.dependency_index.get(pf, [])
        for target in targets:
            if target in eng_assets:
                discovered.add(target)
                
    supporting = list(discovered - state["primary"])
    return {
        "supporting": supporting,
        "success": len(supporting) > 0,
        "explanation": f"Dependency Rule discovered {len(supporting)} connected files via canonical dependency_index."
    }

def _supporting_applicable(wo, profile, state) -> bool:
    return len(state["primary"]) > 0

def _supporting_evaluate(wo, profile, state) -> dict:
    supporting = set()
    test_universe = [f for f in profile.files_by_category.get(FileCategory.TEST.value, []) if f in profile.files_by_asset_class.get(AssetClass.ENGINEERING.value, [])]
    
    for pf in state["primary"]:
        filename = pf.split('/')[-1].split('.')[0]
        for tf in test_universe:
            if filename in tf:
                supporting.add(tf)
                
    return {
        "supporting": list(supporting),
        "success": len(supporting) > 0,
        "explanation": f"Supporting Environment Rule attached {len(supporting)} test/utility files corresponding to primary targets."
    }

def _reference_applicable(wo, profile, state) -> bool:
    return len(profile.files_by_category.get(FileCategory.DOC.value, [])) > 0

def _reference_evaluate(wo, profile, state) -> dict:
    keywords = _extract_keywords(getattr(wo, "title", "") + " " + getattr(wo, "objective", ""))
    doc_universe = profile.files_by_category.get(FileCategory.DOC.value, [])
    reference = _rank_files(keywords, doc_universe, profile, 2)
    
    return {
        "reference": reference,
        "success": len(reference) > 0,
        "explanation": f"Reference Rule attached {len(reference)} documentation files for context."
    }

SELECTION_RULES = [
    SelectionRule("Domain Expansion", 1, RuleImportance.CONDITIONAL, _domain_applicable, _domain_evaluate),
    SelectionRule("Constraint Filtering", 2, RuleImportance.REQUIRED, _constraint_applicable, _constraint_evaluate),
    SelectionRule("Deliverable Matching", 3, RuleImportance.REQUIRED, _deliverable_applicable, _deliverable_evaluate),
    SelectionRule("AC Expansion", 4, RuleImportance.CONDITIONAL, _ac_applicable, _ac_evaluate),
    SelectionRule("Dependency Graph", 5, RuleImportance.CONDITIONAL, _dependency_applicable, _dependency_evaluate),
    SelectionRule("Supporting Environment", 6, RuleImportance.CONDITIONAL, _supporting_applicable, _supporting_evaluate),
    SelectionRule("Reference Discovery", 7, RuleImportance.OPTIONAL, _reference_applicable, _reference_evaluate),
]