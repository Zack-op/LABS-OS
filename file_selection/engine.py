from file_selection.models import FileSelection, RuleTrace, RuleImportance
from file_selection.rules import SELECTION_RULES

class FileSelectionEngine:
    def select(self, wo, profile) -> FileSelection:
        selection = FileSelection()
        state = {"primary": set(), "supporting": set(), "reference": set(), "excluded": set()}
        
        sorted_rules = sorted(SELECTION_RULES, key=lambda r: r.stage)
        
        for rule in sorted_rules:
            if rule.is_applicable(wo, profile, state):
                input_state = {k: list(v) for k, v in state.items()}
                result = rule.evaluate(wo, profile, state)
                
                is_success = result.get("success", False)
                output_state = {"success": is_success}
                
                for k in ["primary", "supporting", "reference", "excluded"]:
                    if result.get(k):
                        state[k].update(result[k])
                        output_state[k] = result[k]
                        
                selection.traces.append(RuleTrace(
                    stage=rule.stage,
                    rule_name=rule.name,
                    importance=rule.importance.value,
                    inputs=input_state,
                    outputs=output_state,
                    explanation=result.get("explanation", f"Rule executed but produced no outputs.")
                ))

        conflict = state["primary"].intersection(state["excluded"])
        if conflict:
            selection.traces.append(RuleTrace(
                stage=99, rule_name="Conflict Resolution", importance=RuleImportance.REQUIRED.value,
                inputs={"conflicts": list(conflict)}, outputs={"resolved": "exclusion"},
                explanation=f"CONFLICT: {conflict} resolved via strict exclusion."
            ))
        
        final_primary = state["primary"] - state["excluded"]
        final_supporting = state["supporting"] - final_primary - state["excluded"]
        final_reference = state["reference"] - final_primary - final_supporting - state["excluded"]
        
        selection.primary_files = sorted(list(final_primary))
        selection.supporting_files = sorted(list(final_supporting))
        selection.reference_files = sorted(list(final_reference))
        selection.excluded_files = sorted(list(state["excluded"]))
        
        has_primary = len(selection.primary_files) > 0
        required_failed = False
        conditional_app = 0
        conditional_succ = 0
        reference_succ = False

        for t in selection.traces:
            success = t.outputs.get("success", False)
            if t.importance == RuleImportance.REQUIRED.value:
                if not success: required_failed = True
            elif t.importance == RuleImportance.CONDITIONAL.value:
                conditional_app += 1
                if success: conditional_succ += 1
            elif t.importance == RuleImportance.OPTIONAL.value:
                if success: reference_succ = True

        breakdown = {
            "primary_evidence": 0.40 if has_primary else 0.0,
            "required_evidence": 0.30 if not required_failed else 0.0,
            "conditional_evidence": 0.20 if conditional_app == 0 else round(0.20 * (conditional_succ / conditional_app), 2),
            "reference_evidence": 0.10 if reference_succ else 0.0,
            "conflict_penalty": -1.0 if conflict else 0.0
        }

        total_confidence = sum(breakdown.values())
        
        if not has_primary or required_failed or conflict:
            total_confidence = 0.0

        selection.confidence = max(0.0, min(1.0, total_confidence))
        selection.confidence_breakdown = breakdown
        
        if len(selection.primary_files) == 0:
            selection.status = "needs_review"
            selection.escalation_reason = "zero_files_matched"
        elif selection.confidence < 0.5:
            selection.status = "needs_review"
            selection.escalation_reason = "low_rule_coverage"
        elif conflict:
            selection.status = "needs_review"
            selection.escalation_reason = "conflicting_rules"

        return selection