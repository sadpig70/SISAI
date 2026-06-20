# SISAI — Handoff

Running record of substantial work beyond the core backbone. Per skill-authoring convention, cumulative
history lives here and in git commits, not in skill/spec docs.

## Status (2026-06-20)

`origin/main` carries the deterministic backbone (`core/`, `sisai.py`) **plus the entire
implementation-verification backlog and the depth passes on top of it**. Every increment passed the §0
gates: `python core/sisai_validate.py .` → PASS, `python -m unittest discover -s tests -q` → **232 OK**,
`tests/test_determinism_boundary.py` green, no regression (opt-in + grandfather).

All added code is **defensive-only** (detection / verification / evidence / triage; never weaponization,
never executing collected text) and lives at the **runtime edge** — `core/`+`engines/` stay pure
(no clock/network/AI/randomness; `now` injected). The single index of the fleet is
[`docs/TOOLS-CATALOG.md`](docs/TOOLS-CATALOG.md).

## What shipped

### Backlog — 14 PoCs (`_workspace/SISAI-implementation-verification-backlog.md`)

| Tier | PoCs | Where |
|---|---|---|
| **B0 (now)** | B0-1 PR/CI detector · B0-2 policy compiler · B0-3 control-drift monitor · B0-4 benchmark harness · B0-5 calibration · B0-6 education lab | `tools/`, `labs/`, `calibration/` |
| **B1 (near)** | B1-1 prompt-shield · B1-2 audit exporter · B1-3 SOC clustering · B1-4 toolchain sentinel (AIBOM) | `tools/` |
| **B2 (domain, DRAFT/synthetic)** | B2-1 RegTech (EU AI Act) · B2-2 Fraud/AML · B2-3 Trust&Safety · B2-4 PharmacoVigilance | `regtech/`, `domain/` |

Each detector is graded on a **frozen holdout** in `seed/sample-suite.json` (`verify_suite`: recall 1.0,
precision ≥ 0.85, ReDoS skipped 0). B2 packs are DRAFT skeletons on **synthetic** fixtures and carry
`DRAFT_STATUS` / `review_status` — they require real data + domain SME + regulatory sign-off and make
**no production/conformity claim**. B2-3 enforces judge≠author; B2-4 makes no autonomous clinical
decision and never feeds back before verification + human approval.

### Depth passes

- **Adversarial robustness** (`calibration/robustness.py`): paraphrase/synonym variants
  (`split=adversarial`) per detector. Baseline robustness was **0.0** (rules over-fit to holdout
  phrasing); hardened to **recall 1.0 / 0 FP** with no holdout regression.
- **Tools catalog + fleet regression** (`docs/TOOLS-CATALOG.md`, `tests/test_tools_catalog.py`): one
  index + a test that every catalogued module imports, exposes a CLI, gates green, and is documented.
- **cm_test formalization — VERDICT M2 CLOSED** (`calibration/battery.py`, `calibration/README.md`):
  canonical in-repo multi-task (author/red/holdout/judge) cross-model harness replacing the gitignored
  `_workspace/cm_test` sandbox; the contract is documented (calibration/ canonical; sandbox
  non-authoritative; holdout independence is structural + label-level).
- **Holdout independence protocol** (`calibration/independence.py`, `calibration/curation-provenance.json`):
  measures/gates independence **honestly** — factual (curator ≠ rule author) + `roles_disjoint`. Records
  the true current state: all 7 shipped detector categories are `single_author` (surfaced, not hidden).
  `require_independent()` gates real independence; an EXAMPLE entry demonstrates the path.

## Honest gaps (what code alone can't close)

- **Independent curation**: shipped fixtures are single-author (the meta-layer authored both rule and
  holdout). A passing gate proves internal consistency + paraphrase robustness, not independent
  validation. The protocol + gate to record/accept real independence now exist; executing it needs a
  **distinct curator/judge** (another runtime or human).
- **Real labeled domain data**: B2 (fraud/AML, trust&safety, pharmacovigilance, RegTech) runs on
  synthetic fixtures; production needs real labeled data + domain SME + regulatory review.
- **Live fetcher / channel scanner**: collection/external search is the AI meta-layer's job, simulated
  via injected provenance/cognition; not deterministic code.

## Next

- **(a) Independent-curation execution protocol** — drive a *distinct* runtime/agent as holdout
  curator/judge, score submissions with `calibration/battery.py`, and flip `curation-provenance`
  `independent` only when `roles_disjoint` + factual independence both hold. Turns the single-author
  gap from "measured" into "executed".
- Real-data onboarding for B2 (gated: SME + regulatory), and a live fetcher interface for collection.

## Branches

- `origin/main` — backbone + all of the above (merged).
- `feat/b2-regtech-evidence` (origin) — per-PoC B2 history (merged into main).
- Local feature branches were merged via `--no-ff`; history grouped per phase.
