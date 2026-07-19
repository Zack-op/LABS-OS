"""
capability_router.py — resolves an abstract capability to a live model.

This is the layer that absorbs model churn. When Groq deprecates a
model, or a better one ships, you edit ONE line in capabilities.yaml.
Nothing in policies.yaml, orchestrator.py, or llm_router.py changes.
"""

import yaml
from pathlib import Path

CAPABILITIES_PATH = "capabilities.yaml"


def load_capabilities(path: str = CAPABILITIES_PATH) -> dict:
    data = yaml.safe_load(Path(path).read_text())
    return data["capabilities"]


def resolve(capability: str, capabilities: dict = None) -> dict:
    """capability name -> {"provider": ..., "model": ...}"""
    capabilities = capabilities or load_capabilities()
    if capability not in capabilities:
        raise KeyError(
            f"Unknown capability '{capability}'. Known: {list(capabilities.keys())}"
        )
    return capabilities[capability]
