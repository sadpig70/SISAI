# SISAI — conventions & workspace map (on-demand)

Detail split out of `AGENTS.md` so the auto-injected bootstrap stays minimal. Load this only when you
need the workspace layout, the PoC fleet, skill-authoring rules, or the work guidelines.

## Workspace map

- **skills/** — vendored `pg`, `pgf`, `pgxf` (AI-runtime driving engines, parser-free; self-contained).
- **core/** — backbone (deterministic stdlib): `fingerprint·channels·ledger·triage·provenance·loop·io·schema·validate` · v1.4 `detect·verify`.
- **engines/** — `adapters.py` (backbone projection) · `adversarial.py` (v1.4 red/blue loop, injected cognition) · `detect_hybrid.py` (keyword prefilter + injected meta-layer semantic).
- **sisai.py** — driver (status / plan / discover-channel / record-defense / ingest-threats).
- **schemas/** — 7 contracts (channel/threat/defense/ledger/loop-state + v1.4 sample/role-registry).
- **seed/** — seed corpus (channels/threats/defenses + v1.4 sample-suite/role-registry; `independent-holdouts/` + `semantic/` — cross-model validation evidence).
- **PoC packs (edge — outside the determinism boundary)** — `tools/` (10 detection/evidence CLIs: detect ·
  detect_pr · policy_compile · control_drift · benchmark_harness · prompt_shield · audit_export · soc_cluster ·
  toolchain_sentinel · loop_feedback), `labs/` (education), `calibration/` (score · battery · robustness ·
  independence · independent_eval · semantic_ingest · rounds), `regtech/`·`domain/` (B2 domain, **DRAFT/synthetic**).
  Index: `docs/TOOLS-CATALOG.md`.
- **.sisai/** — runtime artifacts (`channels.json·ledger.json·corpus.json`, gitignored). Falls back to `seed/` if absent.
- **.pgf/** — design/plan/state sources of truth: `DESIGN-*.md` · `WORKPLAN-*.md` · `status-*.json` (active work lives here).
- **docs/** — TECHNICAL-GUIDE · TOOLS-CATALOG · ARCHITECTURE · SELF-DEFENSE · INSTRUCTIONS-sisai-cycle · RUNBOOK ·
  INDEPENDENT-CURATION-PROTOCOL · INDEPENDENT-VALIDATION-RESULTS · SEMANTIC-DETECTION-FINDING · this file.
  **README.md** at root; **HANDOFF.md** (status/gaps/next).

## Work specs live in `.pgf/` (not in AGENTS.md)

Keep `AGENTS.md` stable; put task specs in files the boot sequence points to:
- Ongoing/multi-step work → `.pgf/WORKPLAN-<Name>.md` (+ `status-<Name>.json` for resume), designed with `pgf`.
- One-off delegation/protocols → a dedicated doc (e.g. `docs/INDEPENDENT-CURATION-PROTOCOL.md`).

The boot sequence reads the relevant `.pgf/` plan and resumes from its status; swapping work means
swapping the plan file, not editing the bootstrap.

## Skill-authoring conventions

- Skill docs (`SKILL.md`·reference) keep **only the current spec**. **No cumulative-history sections**
  (`## Version History` / `## Change Log`) — they pollute context on skill load. History goes in git
  commits / `HANDOFF.md`.

## Guidelines (work rules)

- **Think Before Coding** — state assumptions; ask when uncertain; present multiple interpretations if they exist.
- **Surgical Changes** — keep existing style; don't improve unrelated code; remove only orphans your changes created.
- **Goal-Driven** — for multi-step tasks, start with a brief plan that has verification criteria. Design the
  work itself with `pgf` first, then execute.
- **§0 gates every increment** — `python core/sisai_validate.py .` → PASS, `python -m unittest discover -s tests -q`
  → OK, `tests/test_determinism_boundary.py` green; gates are opt-in + grandfather (no regression). Commit/push
  only when instructed (branch first if on `main`).
