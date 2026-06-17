# NIST AI RMF mapping — PI-001 (THR-0b24f8ec)

> Adapted from the external control `nist-ai-rmf-mapping`. Maps the PI-001 control set
> onto the four NIST AI RMF functions so the adopted defense is auditable/governable.

| RMF function | How PI-001 satisfies it |
|---|---|
| **GOVERN** | Defensive-only scope + human-review gate for irreversible actions (AGENTS.md). Controls versioned in `defenses/`, provenance recorded in ledger. |
| **MAP** | Threat THR-0b24f8ec (Prompt injection LLM01, CVSS 9.8, CVE-2025-54135) mapped to techniques `indirect-injection`, `rce-via-readme`; attack surface = ingested external text. |
| **MEASURE** | `verify_pi_001.py` quantifies detection accuracy (recall/precision over a labeled suite). Gate: recall==1.0, precision>=0.85. Current: 1.0 / 1.0. |
| **MANAGE** | `incident-playbook-PI.md` defines isolate → quarantine → human review → triage; idempotent ledger prevents poisoned-sample re-amplification. |

## Residual risk
Regex detection is signature-based: novel obfuscations may evade until added to the
sample suite. Mitigation is layered, not sole — the deterministic boundary (`core/`
never executes ingested text) remains the primary defense; PI-001 is a detection signal
on top of it.
