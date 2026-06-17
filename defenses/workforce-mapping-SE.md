# Security culture & workforce mapping — SE-001 (THR-96d32f71)

> Adapted from the external controls `gamified-training` and `shadow-ai-elimination`
> (origin: ai-abuse-summary, channel CH-thehackernews). Maps the workforce/governance
> control set onto the SE-001 detection capability so the adopted defense against
> social-engineering / deepfake-BEC / vishing is auditable and governable.
> **Defensive-only**: this control produces detection signals, awareness, and policy —
> never offensive impersonation, pretext generation, or attack automation.

## Threat

| Field | Value |
|---|---|
| threat_id | THR-96d32f71 |
| category | social-engineering |
| techniques | deepfake-bec, voice-phishing |
| attack surface | ingested text — inbound emails, call transcripts, chat messages |
| typical lure | exec-impersonation wire request, urgency+secrecy, out-of-band channel switch, gift-card/crypto payment, credential/MFA pretext, spoofed banking-change |

## Control set → how it is satisfied

| Control | How SE-001 + workforce posture satisfies it |
|---|---|
| **gamified-training** | Recurring phishing/vishing simulations and deepfake-BEC drills with scoring/leaderboards build recognition of the exact lures SE-001 flags (urgency+secrecy, channel switch, gift-card/crypto, exec impersonation). The labeled sample suite (`defenses/tests/social_eng_samples.jsonl`) doubles as a training/eval corpus — malicious vs. benign business email. Detection alerts feed back as teachable moments. |
| **shadow-ai-elimination** | Inventory and gate unsanctioned AI tools (voice cloning, generative chat, autonomous email agents) that adversaries use to manufacture deepfake-BEC/vishing pretexts and that staff might paste sensitive context into. Enforce an approved-tool whitelist; route external/AI-touched correspondence through SE-001 scanning before action. Removes the unmonitored channels social engineers exploit. |
| **bec-vishing-detector (SE-001)** | `defenses/detectors/social_eng_detector.py` scans ingested text and emits an advisory verdict (DATA only — matched text is never elevated to an instruction, per docs/SELF-DEFENSE.md). On match → `flag`, `isolate`, `require_human_review`. |

## Detection capability

- **Rule**: `defenses/rules/SE-001-social-engineering.json` — 8 regex patterns
  (exec-impersonation, wire-transfer-request, urgency-secrecy, channel-switch,
  giftcard-crypto-lure, credential-request, deepfake-voice-pretext,
  spoofed-identity-marker).
- **Detector**: `defenses/detectors/social_eng_detector.py` — pure stdlib, deterministic.
- **Verification**: `defenses/verify_se_001.py` — gate `recall==1.0 AND precision>=0.85`
  over 18 labeled samples (11 malicious + 7 benign). Current result:
  **recall=1.0, precision=0.9167, tp=11, fp=1, tn=6, fn=0.**

## Governance posture (NIST AI RMF lens)

| RMF function | Coverage |
|---|---|
| **GOVERN** | Defensive-only scope + human-review gate for irreversible actions (e.g. wire approval). Controls versioned in `defenses/`, provenance recorded in ledger; approved-tool whitelist (shadow-ai-elimination). |
| **MAP** | THR-96d32f71 (social-engineering; deepfake-bec, voice-phishing) mapped to ingested-text attack surface and the eight SE-001 lure classes. |
| **MEASURE** | `verify_se_001.py` quantifies detection accuracy on a labeled benign/malicious suite; gamified-training simulations measure human click/report rates over time. |
| **MANAGE** | On match: isolate → quarantine → human review → out-of-band verification of the requester (callback to a known number, not the one in the message). Idempotent ledger prevents poisoned-sample re-amplification. |

## Residual risk

Regex detection is signature-based: novel phrasings, multilingual lures, or pure-voice
deepfakes with no text artifact may evade until added to the sample suite. The single
known false positive (`b07`, a negated fraud-awareness advisory containing "send
cryptocurrency") is accepted within the precision budget. Mitigation is layered:
SE-001 is a detection signal that complements — not replaces — workforce training,
out-of-band verification policy for payments, and the deterministic boundary
(`core/` never executes ingested text).
