# Crypto-agility & PQC mapping — SCH-001 (THR-f9d3875d)

> Adapted from the external control set **Crypto agility & PQC adoption**
> (`hybrid-pqc`, `crypto-inventory`, `confidential-computing-tee`). Maps the SCH-001
> detection control onto a governance frame so the adopted defense is auditable.
> Defensive-only: SCH-001 emits a verdict (data) over ingested config / inventory /
> advisory text; it never elevates matched text to an instruction and produces no
> attack tooling.

## Threat

- **threat_id**: THR-f9d3875d — category `side-channel`
- **techniques**: `power-analysis`, `timing-packet-analysis`
- **attack surface**: ingested config / crypto-inventory / advisory text describing
  quantum-vulnerable algorithms, non-constant-time crypto, missing TEE, weak TLS,
  static IV/nonce — all of which widen power/timing side-channel exposure or block
  post-quantum migration.

## Control mapping

| External control | How SCH-001 operationalizes it |
|---|---|
| **crypto-inventory** | SCH-001 patterns `quantum-vulnerable-pubkey`, `deprecated-hash`, `weak-cipher`, `weak-tls` build an automated inventory signal — every ingested config line carrying RSA-1024/2048, ECDSA-P256 (no hybrid), SHA-1/MD5, 3DES/RC4/ECB, TLS 1.0/1.1 is flagged with severity and routed to `inventory` / `require_crypto_review`. |
| **hybrid-pqc** | Pattern `no-pqc-agility` flags configs that explicitly disable or omit post-quantum / hybrid-KEM migration (Kyber/ML-KEM, Dilithium/ML-DSA, crypto-agility=false). PQC-safe configs (TLS 1.3 + X25519 + hybrid-pqc enabled) deliberately do NOT match. |
| **confidential-computing-tee** | Pattern `missing-tee` flags sensitive key/compute material handled outside a TEE/enclave/HSM (tee=disabled, private key in plaintext/on disk). Reduces power-analysis exposure by steering key ops into attested enclaves. |
| **weak-crypto-detector** | Patterns `non-constant-time` and `static-iv-key` target the direct side-channel root causes: variable-time MAC/signature comparison, textbook/naive RSA modexp, hardcoded IV/nonce/key reuse — the primitives most exposed to timing- and power-analysis recovery. |

## Governance frame (GOVERN / MAP / MEASURE / MANAGE)

| Function | Satisfied by |
|---|---|
| **GOVERN** | Defensive-only scope + crypto-review gate (`require_crypto_review`); controls versioned in `defenses/`, provenance recorded in ledger. |
| **MAP** | THR-f9d3875d (side-channel: power-analysis, timing-packet-analysis) mapped to crypto-agility/PQC-readiness gaps in ingested config/inventory text. |
| **MEASURE** | `verify_sch_001.py` quantifies accuracy over a labeled suite. Gate: recall==1.0, precision>=0.85. Current: recall=1.0, precision=1.0 (tp=11, fp=0, tn=7, fn=0, 18 samples). |
| **MANAGE** | Matches routed to `flag` → `inventory` → `require_crypto_review`; idempotent ledger prevents poisoned-sample re-amplification. Remediation = migrate to RSA-4096/Ed25519, X25519 + hybrid-PQC, AES-256-GCM, SHA-256/384, TLS 1.3, constant-time comparisons, TEE/HSM-resident keys. |

## Residual risk

Regex detection is signature-based: novel obfuscations or unlisted weak-primitive
names may evade until added to the sample suite. SCH-001 is a detection signal layered
on top of the deterministic boundary (`core/` never executes ingested text), not a sole
control. PQC migration itself (key rotation, hybrid rollout) is an operational action
outside this detector's scope.
