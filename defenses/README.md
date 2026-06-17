# defenses/ — adapted & designed defensive controls

Durable, committed defensive artifacts produced by SISAI turns. Runtime ledger/corpus
state lives under `.sisai/` (gitignored); this directory holds the **reusable controls**
those records point to (`implementations[].artifact_path`).

Defensive-only: detection rules, prevention policies, governance docs, verification
harnesses. No working exploits, no offensive automation (AGENTS.md invariants).

## Index

| Artifact | Kind | Covers |
|---|---|---|
| `rules/PI-001-indirect-injection.json` | detection rule | THR-0b24f8ec — indirect prompt injection / doc-borne RCE |
| `detectors/pi_detector.py` | detector (stdlib) | runs PI-001 over ingested text → verdict (data) |
| `tests/pi_samples.jsonl` | labeled suite | 10 malicious / 8 benign |
| `verify_pi_001.py` | verification harness | TP/FP gate (recall==1.0, precision>=0.85) |
| `incident-playbook-PI.md` | governance | response/quarantine/human-review |
| `nist-ai-rmf-mapping-PI.md` | governance | NIST AI RMF function mapping |

## Provenance (this control)
- **defense_plan**: `ADOPT_EXTERNAL` — external "Adversarial testing & governance"
  (controls: ai-red-team, nist-ai-rmf-mapping, incident-playbook), origin `ai-abuse-summary`.
- **adaptation**: governance controls instantiated as concrete, runnable SISAI artifacts
  bound to the deterministic boundary (data != instruction).
- **verification**: `pi-detection-suite` → recall 1.0, precision 1.0 (18 samples, 0 FP/0 FN).
