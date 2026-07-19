# AK Labs OS — MVP

The Founder Pyramid, actually running. One command in, a real file out,
policy gates deciding what's automatic and what stops for you.

## Quickstart (free, no API key needed)

```bash
pip install -r requirements.txt
python orchestrator.py "Build a function that validates an email address" --mock
```

Watch it run Architect → Developer → Verify → Commit message, entirely
offline, using canned responses. This is how you test pipeline changes
without spending a token.

## Quickstart (real, calls Groq)

```bash
cp .env.example .env
# paste your GROQ_API_KEY into .env
python orchestrator.py "Build a function that reverses a string"
```

Same four steps, but the Architect and Developer calls hit Groq for real,
using whatever models are set under `route_model_by_task` in `policies.yaml`.

## What each file does

| File | Role |
|---|---|
| `ARCHITECTURE.md` | The project's constitution — vision, architectural principles, current status against them |
| `culture.yaml` | Organization-wide engineering standards — what "good" looks like here, not procedure |
| `policies.yaml` | Every policy: trigger, action, capability needed, `interrupt_level`, and what counts as "this needs AK" |
| `capabilities.yaml` | The ONLY file that names actual models. Maps `reasoning_high` → `claude-sonnet-5`, etc. |
| `capability_router.py` | Resolves a capability name to a live provider + model |
| `policy_engine.py` | Loads policies, evaluates escalation, logs every decision to SQLite |
| `historian.py` | Reads that log, computes real evidence per policy, surfaces repeated escalations as candidates for AK to decide — never edits policy itself |
| `llm_router.py` | Calls whatever model `capability_router` resolved (Groq or Claude) |
| `orchestrator.py` | The actual pipeline: scope → code → verify → commit → log |
| `dev_tools.py` | Verification helpers (`check-log`, `break-output`, `simulate-escalations`) — proves each guarantee with one plain command, no inline scripting needed |
| `PROJECT_CONTEXT.md` | Auto-created/appended after every run — your durable run history |
| `ak_labs_os.db` | Auto-created SQLite (WAL) — `policy_log` (audit trail) + `policy_candidates` (Historian's output) |

## Using Historian

```bash
python historian.py stats verify_output   # real evidence: run count, escalation rate, top reasons
python historian.py scan                  # scan policy_log, surface new repeated-escalation candidates
python historian.py review                # list candidates awaiting your decision
python historian.py decide 1 approve      # record your decision — does NOT touch policies.yaml
```

Approving a candidate never edits `policies.yaml` for you. It closes the loop
in organizational memory so the same pattern doesn't get re-surfaced — but if
you decide a policy should actually change, you make that edit yourself. That
split is deliberate, not a missing feature (see `ARCHITECTURE.md`, Principle 3).

## Why capabilities.yaml exists

`policies.yaml` never names a model — it names a capability
(`reasoning_high`, `coding_fast`, `summarization_cheap`). When Groq
deprecates a model — which has already happened twice on this project —
you edit **one line** in `capabilities.yaml`. Nothing else in the repo
changes. Proved this live: swapped `qwen/qwen3.6-27b` for
`openai/gpt-oss-120b` in `capabilities.yaml` only, and the full pipeline
kept running without touching `policies.yaml`.

## interrupt_level

Every policy carries `none | review | approval | emergency` instead of
a flat escalate/proceed flag:

- `none` — never escalates (e.g. creating a feature branch)
- `review` — proceeds with a fallback, flagged for you to glance at later (e.g. a capability resolution hiccup)
- `approval` — stops and blocks until you look (e.g. verify_output failing, a staging deploy)
- `emergency` — stops, blocks, highest consequence (schema migrations)

## Deliberately NOT in this version

- **Confidence scores.** The idea (>95% proceed, <70% escalate) is
  right, but only if the confidence number comes from something real —
  retry counts, pass/fail on a hard check, historical success rate.
  A model self-reporting "I'm 96% confident" is the same fabrication
  risk this whole system exists to catch, just wearing a number instead
  of a sentence. Worth adding once the Historian (below) has real
  outcome data to compute confidence from.
- **Policy inheritance** (staging → production). Right instinct, but at
  8 policies explicit beats resolved. YAML anchors (`<<: *base`) get
  you most of this for free once duplication actually starts hurting.
- **Ownership field.** You own 100% of your policies today — the field
  is dead weight until there's a team or a Security Agent to point it at.
- **Historian v0 is built** (see above) — the deferral from the last round is
  resolved. What's still deferred: Historian only detects *repeated escalations*
  so far. It doesn't yet track engineering standards, project outcomes, or
  lessons learned in prose form (Principle 3's fuller scope) — that's the
  natural next expansion once there's more real execution history to learn from.
- **Work orders / structured department-to-department communication**
  (Principle 5). This is a real redesign of how Architect and Developer pass
  context to each other, not a small addition — deserves its own pass.

## Try breaking it on purpose

This is the part worth actually doing — prove the anti-fabrication gate
is real, not decorative:

```bash
python3 -c "
from pathlib import Path
from policy_engine import load_policies
from orchestrator import verify_output
Path('output').mkdir(exist_ok=True)
bad = Path('output/broken.py')
bad.write_text('def broken(:')          # invalid syntax on purpose
print(verify_output(bad, load_policies()))
"
```

You should see `passed: False` and an escalation reason. If you ever see
this pipeline claim success on broken or missing output, that's a bug in
`verify_output()`, not a policy problem — file it as priority one.

## Wiring this into your real AK Labs OS repo

This MVP is deliberately standalone so you can run and trust it today.
To merge it into your existing Orchestrator → Architect → Developer code:

1. Drop `policies.yaml` + `policy_engine.py` in as-is — they have no
   dependency on the rest of this MVP.
2. Replace `developer_generate_code()`'s single-file write with your real
   repo-aware code generation.
3. Replace the `verify_output()` syntax check with a call to your actual
   test runner once one exists — the policy (`run_tests_on_commit`) is
   already defined in `policies.yaml`, just not exercised yet.
4. Wire `deploy_staging` / `deploy_production` / `schema_migration` to
   your real git + deploy hooks when you're ready — they're already
   modeled as `irreversible` with `escalate_if: always`, so they'll
   default to safe (always ask you) the moment you connect them.

## Next things worth adding (not in this MVP)

- Real `git commit` + branch creation using `create_feature_branch`
- A `last_reviewed` column so `policies_due_for_review()` has real data
- Cost tracking per model call (the gap you already flagged) — cheapest
  spot to add it is inside `llm_router.py`, right where each call returns
