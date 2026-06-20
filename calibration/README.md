# calibration — cross-model rule-quality scoring (canonical)

**This package is the canonical, in-repo home for cross-model calibration** (VERDICT M2). It replaces
the exploratory `_workspace/cm_test` sandbox: anything authoritative lives here, committed and tested.
`_workspace/cm_test` (gitignored) remains a scratch area only and is **not** an authoritative path.

## Contract

- **Canonical fixtures**: categories and their `tune` / `holdout` splits come from
  `seed/sample-suite.json` (the committed corpus). There is no separate sandbox fixture tree.
- **Holdout independence is structural**: the loop can never write a `holdout` row
  (`core/sisai_detect.atomic_append_samples` refuses it); label-level role disjointness
  (author ≠ holdout-curator ≠ judge) is enforced by `core/sisai_verify.roles_disjoint` over the
  committed `seed/role-registry.json`.
- **Pure / deterministic**: no clock/network/AI; scoring is a pure function of (rule/submission,
  fixtures). The nested-quantifier ReDoS refusal lives here at the edge, not in `core/`.
- **Calibration evidence only**: nothing here records into the ledger/corpus or makes a production
  claim.

## Modules

| Module | Purpose |
|---|---|
| `score.py` | Single-rule author scoring: `score_rule` (gated_f1, precision floor, degenerate/leakage), `safe_compile` (length + nested-quantifier ReDoS refusal), `aggregate` (mean+min), `dogfood` self-test. |
| `battery.py` | Multi-task, multi-model harness: author / red / holdout / judge scoring of submissions against the canonical fixtures, aggregated per model (mean AND min). |
| `robustness.py` | Per-detector adversarial recall + benign FP over the `split=adversarial` variants (generalization beyond the holdout). |

## Honest gap

Most fixtures are **single-author** (the same meta-layer authored the rule and the holdout), so a
passing gate proves internal consistency and paraphrase-robustness, **not** independent validation.
Independent curation (a distinct holdout curator / judge, real labeled data) remains the open work —
tracked as a backlog gap, surfaced rather than hidden.

## Run

```bash
python calibration/score.py --dogfood
python calibration/robustness.py
python calibration/battery.py --submissions <subs.json>
```
