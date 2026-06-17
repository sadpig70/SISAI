# Design notes — CA-001 credential-attack indicator detector

**Threat:** THR-ca2d7e92 · category `credential-attack` · techniques `gan-password-generation`, `ml-cracking`
**Defense:** DEF-ca-001 · kind `designed` · origin `pgf`
**Posture:** DEFENSIVE-ONLY. This is a *detector of attack indicators in ingested text*, not an attack tool.

## Why self-designed (pgf), not external

The external-first search surfaced generic guidance (rate limiting, MFA, breached-password
checks) but no drop-in, pure-stdlib detector that turns ingested auth-log / threat-intel text
into a verdict matching the SISAI artifact shape (PI-001). So the control was self-designed via
pgf to mirror PI-001 exactly: a JSON rule of regex indicators + a stdlib `load_rule`/`scan`
detector + a labeled verify suite gated on recall/precision.

## Detection-only scope (what it does)

CA-001 scans INGESTED external text (auth logs, advisories, SOC/threat-intel reports) and emits a
verdict object `{rule_id, malicious, matched[], severity, action[]}`. It flags *indicators* of a
credential attack:

- **Failed-login bursts** — high numeric counts of failed/invalid auth attempts in a short window.
- **Brute-force rate** — auth-failure rate exceeding a per-second/per-minute threshold.
- **Credential stuffing** — replay of breached/leaked combolist credentials (high failure ratio).
- **Password spraying** — one/few passwords tried across many distinct accounts.
- **Distributed auth anomaly** — failures from an unusually large number of distinct source IPs.
- **GAN/ML password-list markers** — PassGAN-style or ML-cracked candidate wordlist usage in attack context.
- **Account-lockout storm** — mass lockouts from a guessing storm.
- **High failure ratio** — near-100% failed-auth rate from a single source.

The verdict is **data**. Matched text is never elevated to an instruction or executed
(`docs/SELF-DEFENSE.md`, data != instruction). The detector is pure stdlib (`json`, `os`, `re`),
deterministic — no clock, network, AI, or randomness.

## What it deliberately is NOT (defensive-only constraint)

It is **not** a password cracker, GAN/PassGAN generator, credential-stuffing engine, or
password-spray tool. It contains no wordlists, no credentials, no auth-request code, and no
guessing logic. The `gan-password-generation` / `ml-cracking` techniques are *covered* only in the
sense that CA-001 **recognizes their footprints** in logs/text — it never produces or runs them.
Building offensive tooling for these techniques is out of scope and refused (AGENTS.md invariant).

## False-positive discipline

Benign samples model what must NOT match: successful auth lines, a single ordinary failed login,
third-person definitions of the attack class, policy/MFA prose, healthy daily metrics, and
defensive-control descriptions. Indicator patterns require attack-grade signals (high numeric
counts ≥100 for bursts, ≥2-digit account/IP fan-out, explicit stuffing/spray/PassGAN terms, or
≥90% failure ratios) so descriptive prose and normal logs stay clear.

## Verification

`python defenses/verify_ca_001.py` → method `credential-attack-suite`, 19 labeled samples
(11 malicious indicators + 8 benign). Gate: recall == 1.0 AND precision >= 0.85.
Result: **recall=1.0, precision=1.0, tp=11, fp=0, tn=8, fn=0, exit 0**.
