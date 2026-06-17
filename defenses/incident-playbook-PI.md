# Incident Playbook — Prompt Injection / Doc-borne RCE (THR-0b24f8ec)

> Adapted from the external control `incident-playbook` (defense "Adversarial testing
> & governance") to SISAI's deterministic-boundary architecture. Defensive-only:
> detect, isolate, report. No exploit reproduction.

## Trigger
PI-001 detector (`defenses/detectors/pi_detector.py`) flags ingested external text
(README, CVE/advisory body, scanned web/source) as `malicious`.

## Response (deterministic, data-stays-data)
1. **Isolate** — keep the flagged text as *data*. It MUST NOT be promoted into the
   runtime's instruction/control flow (docs/SELF-DEFENSE.md invariant #1). `core/`
   never branches on ingested content; the detector only annotates.
2. **Quarantine** — do not feed the flagged blob to any tool-invoking context. Strip
   or escape it before any downstream summarization.
3. **Record provenance** — capture source channel + fingerprint so the same poisoned
   sample cannot re-amplify (idempotent ledger, invariant #3).
4. **Human review gate** — `action_on_match` includes `require_human_review`; an
   irreversible/outbound action stays blocked until the operator approves (AGENTS.md gate).
5. **Triage & report** — attach the verdict (matched pattern ids + severity) to the
   threat record; no defense enters the corpus until verified (invariant #2).

## Severity → action
| Top severity | Action |
|---|---|
| `critical` (embedded-exec / secret-exfil) | block downstream use + human review |
| `high` (override / role-hijack / prompt-exfil / agent-address) | isolate + flag |
| `medium` (hidden-marker) | flag + log for pattern tuning |

## Recovery / tuning
False negatives or positives feed back into `defenses/tests/pi_samples.jsonl`; re-run
`python defenses/verify_pi_001.py` (recall==1.0, precision>=0.85 gate) before any
rule change is recorded.
