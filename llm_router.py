"""
llm_router.py — thin dispatch layer over policy-selected models.

Reads the model assigned by route_model_by_task in policies.yaml and
calls the right provider. Supports mock=True so you can test the
whole pipeline for free before spending a single token.
"""

import os
from dotenv import load_dotenv
from capability_router import resolve

load_dotenv()

_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _groq_client


def call_model(policy_id: str, task_key: str, prompt: str, policies: dict,
                mock: bool = False, mock_response: str = "") -> str:
    """
    task_key = one of the keys under route_model_by_task.params in policies.yaml
    (architecture / coding_routine / coding_hard / review / commit_message)
    """
    if mock:
        return mock_response

    capability = policies[policy_id]["params"][task_key]
    target = resolve(capability)  # {"provider": "groq"/"claude", "model": "..."}

    if target["provider"] == "groq":
        return _call_groq(target["model"], prompt)
    if target["provider"] == "claude":
        return _call_claude(target["model"], prompt)

    raise ValueError(f"Unrecognized provider '{target['provider']}' for capability '{capability}'")


def _call_groq(model: str, prompt: str) -> str:
    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def _call_claude(model: str, prompt: str) -> str:
    """
    The escalation path — used for coding_hard / review.
    Off by default in practice: this costs real money, so routing to
    it should be a deliberate choice (see route_model_by_task's
    quarterly review_cadence), not something that happens silently.
    Requires: pip install anthropic, and ANTHROPIC_API_KEY set.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "This task routed to Claude but ANTHROPIC_API_KEY isn't set. "
            "Add it to .env when you're ready to spend on the escalation path."
        )
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text
