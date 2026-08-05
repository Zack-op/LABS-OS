from context_builder.models import EngineeringContext

class ContextBuilder:
    def build(self, wo, profile, selection) -> EngineeringContext:
        # --- Enforce Engineering Invariants ---
        if selection.status != "resolved":
            raise ValueError(f"Cannot build context: FileSelection status is '{selection.status}' (expected 'resolved').")
        if not selection.primary_files:
            raise ValueError("Cannot build context: No primary engineering files selected.")
        if selection.confidence <= 0:
            raise ValueError(f"Cannot build context: Insufficient engineering confidence ({selection.confidence}).")
        if selection.escalation_reason is not None:
            raise ValueError(f"Cannot build context: Unresolved escalation pending ({selection.escalation_reason}).")

        # --- Enforce File Existence ---
        snapshot_files = set()
        for cat, paths in profile.files_by_category.items():
            snapshot_files.update(paths)
        
        for f in selection.primary_files + selection.supporting_files:
            if f not in snapshot_files:
                raise ValueError(f"Selected file {f} does not exist in RepositorySnapshot")

        acs = []
        if hasattr(wo, 'acceptance_criteria'):
            acs = [{"id": ac.id, "description": ac.description, "mandatory": ac.mandatory} 
                   for ac in getattr(wo, 'acceptance_criteria', [])]

        return EngineeringContext(
            summary=getattr(wo, 'objective', getattr(wo, 'title', '')),
            repository_type=getattr(profile.repository_type, "value", profile.repository_type),
            technology_stack=profile.stack.to_dict() if hasattr(profile.stack, 'to_dict') else {},
            entry_points=sorted(profile.entry_points),
            primary_files=sorted(selection.primary_files),
            supporting_files=sorted(selection.supporting_files),
            reference_files=sorted(selection.reference_files),
            constraints=getattr(wo, 'constraints', []),
            acceptance_criteria=acs,
            deliverables=[],
            relevant_tests=sorted(profile.tests),
            known_risks=[],
            engineering_notes=[t.explanation for t in selection.traces if t.explanation],
            selection_confidence=selection.confidence
        )