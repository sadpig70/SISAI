# Independent-Curation Protocol

Closes the single-author gap by **execution**: a runtime DISTINCT from the rule author (the SISAI
meta-layer) curates a frozen holdout for a category **blind to the detector rules**. The shipped
detector is then re-graded on it; only a passing, role-disjoint, distinct-curator holdout makes a
category **independently validated** (`calibration/independent_eval.verify_independence`).

Eligible curator runtimes: **grok, antigravity, kimi, deepseek, qwen, codex** (any runtime ≠ the rule
author). Assign different runtimes to different categories to maximise independence; never let a
runtime curate a category whose rules it authored.

## Curator TaskSpec (give this to each runtime)

```pg
TaskSpec CurateHoldout
  role: holdout_curator            # you are NOT the rule author; you will not see the detector rules
  input:
    category: one of [config-tampering, supply-chain-tampering, access-control-weakening,
                      llm-prompt-injection, fraud-aml, trust-safety, pharmacovigilance]
    your_model_id: str             # e.g. "grok-4", "kimi-k2", "deepseek-v3", "qwen-...", "codex-...", "antigravity-..."
  produce: a FROZEN holdout of inert, single-line, labeled indicator strings for that category
  acceptance_criteria:
    - sized: >= 5 malicious AND >= 4 benign rows
    - each row: {"label": "malicious"|"benign", "text": "<= 240 chars, single line, no newline"}
    - malicious = a directive/indicator that genuinely exhibits the category's threat
    - benign = HARD negatives that merely MENTION the topic without doing it
        (negation / quotation / policy statement / satire / third-person description / definition)
    - surface forms should be VARIED and NOT copied from public examples you recall
    - defensive-only: abstract typologies, NO real secrets/PII, NO working exploit payloads
  forbidden:
    - do NOT request, infer, or reverse-engineer the SISAI detector rules (curate blind)
    - do NOT generate weaponized content; indicators are short descriptive strings
  output_format: a single JSON object (see below)
```

### Category intent (one line each — curate to these, blind to the rules)

| category | malicious = | hard negatives = |
|---|---|---|
| config-tampering | disabling/bypassing a security control in CI/build | "must stay enabled", "prohibited", policy statements |
| supply-chain-tampering | unpinning/untrusted-source/integrity-off dependency acts | "lockfile must never be deleted", "verified before install" |
| access-control-weakening | making resources public / over-broad grants / no-auth exposure | "access is denied by policy", "RBAC is enforced" |
| llm-prompt-injection | override/jailbreak/prompt-exfil/secret-exfil directives | defensive citations, quoted examples, "never reveal..." |
| fraud-aml | structuring/layering/mule/mixing/over-invoicing directives | "structuring is prohibited", legitimate activity |
| trust-safety | harassment/threats/doxxing/self-harm/spam directives | satire, quotation, reporting, definitions |
| pharmacovigilance | serious adverse-event signals (death/hospitalization/...) | non-serious/resolved/negated/historical mentions |

## Submission format

```json
{
  "category": "config-tampering",
  "curator_model": "grok-4",
  "provenance": {"blind_to_rules": true, "note": "curated independently of SISAI detector rules"},
  "rows": [
    {"label": "malicious", "text": "..."},
    {"label": "benign", "text": "..."}
  ]
}
```

## Ingest & verify (SISAI side)

```bash
python calibration/independent_eval.py --ingest path/to/grok-config-tampering.json   # validates + stores
python calibration/independent_eval.py --verify --category config-tampering          # re-grades the detector
python calibration/independent_eval.py --verify                                      # fleet view
```

Ingestion **rejects** a submission whose curator == the rule author, that is not sized, or whose rows
are not inert/schema-valid. A category becomes `independent: true` only when the ingested holdout is
valid, the role registry roles are disjoint, and the shipped detector clears it (recall ≥ 0.8,
precision ≥ 0.85, FP = 0). Real independence is **earned by the data**, not declared.
