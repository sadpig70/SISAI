# SISAI Tools Catalog

The detection / verification / evidence PoCs built on the deterministic backbone. Every tool reuses
pure `core/` primitives (`sisai_detect.compile_rule`/`scan`, `sisai_verify.verify_suite`/`metrics`/
`roles_disjoint`, `sisai_provenance.*`, `sisai_triage.*`, `sisai_fingerprint.*`) and lives at the
**runtime edge** — outside the determinism boundary (`core/`+`engines/` stay pure). Output is always
**data** (verdicts/reports); nothing here executes collected text or weaponizes anything
(**defensive-only**).

Each detector is graded on a **frozen holdout** in `seed/sample-suite.json` (`verify_suite` gate:
recall 1.0, precision ≥ 0.85, ReDoS skipped 0) and on **adversarial paraphrase variants**
(`split=adversarial`, measured by `calibration/robustness.py`). Tiers follow the implementation
backlog: **now (B0)** → **near (B1)** → **domain (B2, DRAFT/synthetic)**.

## Tier B0 — "now"

| ID | Module | Purpose | CLI | Gate / status |
|---|---|---|---|---|
| B0-1 | `tools/detect_pr.py` | PR/CI defense-weakening detector (config-tampering, supply-chain-tampering, access-control-weakening); negation-aware rule bundles | `--text/--file [--category] [--json]` | 3 holdouts pass |
| B0-2 | `tools/policy_compile.py` | Policy spec → negation-aware detection rule skeleton + `verify_suite` auto-gate | `--policy [--gate --category]` | ≥1 category gated pass |
| B0-3 | `tools/control_drift.py` | Config/IaC diff → drift detection → `ingest_threats` quarantine gate → deterministic drift trend | `--diff [--fetch-provenance] / --trend` | anti-fail-open + fp-dedup |
| B0-4 | `tools/benchmark_harness.py` | Drives `engines.adversarial_verify`; holdout proposals → separate human-curation queue; fail-closed | (programmatic) `--show-candidates` | holdout unwritable + fail-closed |
| B0-5 | `calibration/score.py` | Cross-model rule scoring (gated_f1, precision floor, degenerate/leakage, nested-quantifier ReDoS refusal), aggregate mean+min | `--dogfood [--category]` | DOGFOOD pass |
| B0-6 | `labs/defense_rule_lab/` | Education lab: grade student rules on frozen holdout (`grade_rule.py`) + GUIDE + naive→negation-aware examples | `grade_rule.py --rule --category` | reproduces the lesson |

## Tier B1 — "near"

| ID | Module | Purpose | CLI | Gate / status |
|---|---|---|---|---|
| B1-1 | `tools/prompt_shield.py` | AI-gateway middleware: injection/jailbreak/policy-override detection + provenance gate; collected text is always `treat_as:data` | `--text/--file [--source-url ...]` | injection holdout pass |
| B1-2 | `tools/audit_export.py` | GRC/audit evidence report from corpus+ledger (lineage, fingerprint, verification) + tamper-evident `content_sha256` + Annex IV mapping | `[--corpus] [--ledger] [--md]` | reproducible + tamper-evident |
| B1-3 | `tools/soc_cluster.py` | SOC alert clustering by `threat_fingerprint` (idempotent by alert_id) + triage + coverage blind-spots | `--alerts [--store] / --trend` | dedup idempotent |
| B1-4 | `tools/toolchain_sentinel.py` | AIBOM integrity: per-component provenance gate (host-derived authority + sha256 pin) + manifest scan; verdicts verified/quarantined/rejected | `--components [--measured] [--manifest]` | anti-fail-open |

## Tier B2 — "domain" (DRAFT / synthetic — NOT production/conformity)

> Each carries `DRAFT_STATUS` / `review_status`: real data + domain SME + regulatory sign-off required.

| ID | Module | Purpose | CLI | Distinctive safeguard |
|---|---|---|---|---|
| B2-1 | `regtech/evidence_chain.py` | EU AI Act Annex IV requirement → evidence coverage dossier (provenance enforced) | `[--corpus] [--ledger] [--json]` | tamper-evident; "NOT a conformity assessment" |
| B2-2 | `domain/fraud_aml.py` | Fraud/AML typology detection-as-code + no-regress adoption gate | `--text / --gate` | regression rejection |
| B2-3 | `domain/trust_safety.py` | Moderation eval with hard-negative precision (satire/quote/negation) | `--text / --gate / --eval` | judge≠author enforced (`roles_disjoint`) |
| B2-4 | `domain/pharmacovigilance.py` | Serious-AE triage to human review | `--text / --gate` | no autonomous clinical decision; no feedback before verify+human-approval |

## Cross-cutting

| Module | Purpose | CLI |
|---|---|---|
| `calibration/robustness.py` | Measures each detector's adversarial recall + benign FP over `split=adversarial` variants (generalization beyond the holdout) | `[--json]` |
| `calibration/battery.py` | Canonical cross-model battery (VERDICT M2): author/red/holdout/judge scoring of submissions vs canonical fixtures, aggregated mean+min. See `calibration/README.md` | `--submissions <subs.json>` |
| `calibration/independence.py` | Holdout independence protocol: factual curator≠author + `roles_disjoint` → verdict independent/single_author/roles_conflict/unprovisioned. Honestly reports the single-author gap; gates real independence | `[--json]` |
| `calibration/independent_eval.py` | Independent-curation execution: ingest an external curator's holdout, re-grade the detector, decide independence (data-driven). See `docs/INDEPENDENT-CURATION-PROTOCOL.md` | `--ingest <sub.json> / --verify [--category]` |
| `calibration/semantic_ingest.py` | Phase 2: ingest an external semantic JUDGE's per-row verdicts (3-way distinct author≠curator≠judge), grade keyword-vs-hybrid via `engines/detect_hybrid`, majority-vote consensus | `--ingest <sub.json> / --verify [--category]` |
| `calibration/rounds.py` | Round freshness: re-validation must use a FRESH holdout; `independent_eval.ingest` rejects a stale (identical) re-submission (no teach-to-the-benchmark) | `--check <new> --against <existing>` |
| `engines/detect_hybrid.py` | Two-layer detection combiner: keyword prefilter + injected semantic layer (semantic adjudicates, keyword audited) | (library) |
| `tools/detect.py` | Unified detection entry across all detectors: keyword prefilter + injected meta-layer semantic verdict; emits `semantic_recommended` escalation when none supplied | `--text/--file [--category]` |
| `tools/loop_feedback.py` | Close the spiral: findings→threats, and the INDEPENDENTLY-verified two-layer detector→defense corpus (honest — unverified categories rejected). `--plan` dry-run, `--commit` records | `--plan / --commit / --findings` |

## Invariants (every tool)

- **Deterministic boundary**: detection logic is pure `core/`; tools read argv/files only at the edge. `core/`+`engines/` carry no clock/network/AI/randomness (`now` injected).
- **defensive-only**: verdicts/reports/triage only; never weaponization, never executing collected text.
- **Frozen holdout**: the adversarial/tune splits are train-only; the holdout is structurally unwritable by the loop (`atomic_append_samples`).
- **Honest gaps**: single-author fixtures (author == holdout curator for most), synthetic domain data — surfaced in `DRAFT_STATUS` and the backlog gap list; not independent validation.

## Verify the fleet

```bash
python core/sisai_validate.py .
python -m unittest discover -s tests -q          # 213 tests
python calibration/robustness.py                 # adversarial recall per detector
```
