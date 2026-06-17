# DLP / secret-leak & external-LLM upload mapping — DP-001 (THR-9d67538a)

> Adapted from the external candidate **"Secret-leak & external-LLM upload control"**
> (controls: `dlp-proxy`, `secret-scanning-push-protection`, `private-coding-assistant`).
> Maps that control set + SISAI's fingerprint/provenance gate onto the DP-001
> data-poisoning detection so the adopted defense is auditable/governable.
> **Defensive-only**: output is a verdict, a quarantine action, and a corpus-feedback
> block. No exploit, no poisoning recipe, no exfiltration tooling is produced.

## Control mapping

| External control | Role against THR-9d67538a (data poisoning / secret leak) | SISAI realization |
|---|---|---|
| **dlp-proxy** | Inspect outbound/ingested content; block secrets and poisoned samples crossing the boundary. | `DP-001.secret-leak`, `DP-001.secret-assignment`, `DP-001.exfil-upload` detect credential material and external-LLM upload intent in ingested samples; `action_on_match` → `quarantine`. |
| **secret-scanning-push-protection** | Stop credentials/keys from entering the corpus or repo at write time. | `DP-001.secret-leak` matches AWS keys, GitHub/Slack/OpenAI tokens, PEM private keys, and DB connection strings before a sample is admitted. |
| **private-coding-assistant** | Keep code/data on a trusted, private assistant rather than uploading to an external LLM. | `DP-001.exfil-upload` flags "upload corpus / .env to ChatGPT/OpenAI/external" framing; governance routes such samples to `require_provenance_review`. |
| **poison-trigger-detector** (SISAI-native) | Detect backdoor triggers, label flips, repeated trigger stuffing, hidden-unicode triggers. | `DP-001.backdoor-trigger`, `DP-001.label-flip`, `DP-001.magic-trigger-token`, `DP-001.repeated-trigger`, `DP-001.hidden-unicode-trigger`. |

## Fingerprint / provenance gate (verified-only corpus doctrine)

DP-001 reinforces SISAI's core self-defense invariant (docs/SELF-DEFENSE.md): the
threat/defense corpus accepts **verified, provenance-bearing entries only**.

1. **Detect** — every ingested training/corpus sample is scanned by `data_poison_detector.scan`.
2. **Quarantine** — a malicious verdict triggers `quarantine` + `block_corpus_feedback`;
   the sample is **never** elevated to an instruction and **never** fed back to the corpus.
3. **Provenance review** — `require_provenance_review`: the sample's source signature/hash
   (provenance) must be verified before any human-approved reinstatement.
4. **Fingerprint idempotency** — `fingerprint` records each accepted item once, preventing
   a poisoned sample from being re-injected/amplified across cycles.

## NIST AI RMF alignment (governance)

| RMF function | How DP-001 satisfies it |
|---|---|
| **GOVERN** | Defensive-only scope; quarantine + human provenance review for reinstatement; controls versioned in `defenses/`. |
| **MAP** | Threat THR-9d67538a (data-poisoning) mapped to techniques `backdoor-poisoning`, `trigger-sample`; attack surface = ingested training/corpus samples. |
| **MEASURE** | `verify_dp_001.py` quantifies recall/precision over a labeled suite. Gate: recall==1.0, precision>=0.85. Current: 1.0 / 1.0 (tp=11, fp=0, tn=7, fn=0, n=18). |
| **MANAGE** | `action_on_match` (flag → quarantine → block_corpus_feedback → require_provenance_review); idempotent ledger prevents poisoned-sample re-amplification. |

## Residual risk
Regex detection is signature-based: novel triggers, re-encoded secrets, or adaptive
label-flip schemes may evade until added to the sample suite. Mitigation is layered,
not sole — the deterministic boundary (`core/` never executes ingested text) and the
verified-only corpus gate remain the primary defenses; DP-001 is a detection signal on top.
