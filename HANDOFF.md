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
  measures/gates independence **honestly** — factual (curator ≠ rule author) + `roles_disjoint`.
  `require_independent()` gates real independence; an EXAMPLE entry demonstrates the path.
- **Independent validation — EXECUTED** (`calibration/independent_eval.py`, `seed/independent-holdouts/`,
  `docs/INDEPENDENT-VALIDATION-RESULTS.md`): seven runtimes (grok-4.3, antigravity, deepseek, kimi, qwen,
  codex, claude-sonnet-4.6), each distinct from the rule author and blind to the rules, curated a frozen
  holdout per category. Re-grading the detectors on them: **0 / 7 cleared** — recall collapses to
  0.17–0.33 (config-tampering 0.0) vs 1.0 on the single-author holdouts. The single-author gate vastly
  overstated quality. Rules were **NOT** hardened to these (no teach-to-the-test); the seven are now a
  frozen independent benchmark.

- **Independent validation Phase 2 — EXECUTED, 7/7 hybrid-independent** (`calibration/semantic_ingest.py`,
  `seed/independent-holdouts/semantic/`): seven semantic judges (kimi, deepseek, claude-sonnet-4.6,
  codex, antigravity, grok-4.3, qwen — each 3-way distinct from author and curator, blind) classified
  every holdout row by meaning and agreed with the curators' labels **100%**. Injected as the hybrid's
  semantic layer, recall went 0.17–0.33 → **1.0 / precision 1.0 / FP 0** on all 7. Semantic detection
  generalizes; keyword does not. (docs/INDEPENDENT-VALIDATION-RESULTS.md, Phase 2.)

## Honest gaps (what code alone can't close)

- **The pass is the AI semantic layer, not the keyword rules**: keyword detectors remain 0/7
  independent; the 7/7 is driven by the injected meta-layer/AI semantic judgment. Productionizing means
  detection via meta-layer semantic cognition over the deterministic gate (SISAI's design), re-validated
  each round with a distinct curator + judge. Ground truth is one curator's labels per category; the
  judges' 100% match is strong two-model concordance, not an absolute oracle.
- **Real labeled domain data**: B2 (fraud/AML, trust&safety, pharmacovigilance, RegTech) runs on
  synthetic fixtures; production needs real labeled data + domain SME + regulatory review.
- **Live fetcher / channel scanner**: collection/external search is the AI meta-layer's job, simulated
  via injected provenance/cognition; not deterministic code.

## Next

- **Semantic detection** — the 0/7 result shows keyword bundles don't generalize. The principled fix is
  meta-layer (AI) detection over the deterministic core gate, re-validated on FRESH independent rounds.
- **Second independent round** — after any detector improvement, request NEW curator submissions (never
  reuse `seed/independent-holdouts/`) and re-run `calibration/independent_eval.py --verify`.
- Real-data onboarding for B2 (gated: SME + regulatory), and a live fetcher interface for collection.

## Branches

- `origin/main` — backbone + all of the above (merged).
- `feat/b2-regtech-evidence` (origin) — per-PoC B2 history (merged into main).
- Local feature branches were merged via `--no-ff`; history grouped per phase.
