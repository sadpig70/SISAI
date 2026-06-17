# AIBOM / Supply-chain Governance Mapping — SC-001 (THR-3737c297)

> Adapted from the external candidate "Supply-chain & runtime defense" controls
> [`aibom-sbom`, `sandbox-microvm`, `patch-prioritization`] to SISAI's
> deterministic-boundary + verify-gate architecture. Defensive-only: detect,
> isolate, report. No exploit reproduction, no working malware. Reference threat:
> CVE-2024-8309, techniques pypi-poisoning / lora-adapter-poisoning.

## Trigger
SC-001 detector (`defenses/detectors/supply_chain_detector.py`) flags ingested
package/model metadata (setup.py / pyproject / package.json / requirements,
model-card or adapter source, advisory body) as `malicious`.

## Control mapping

| External control | What it asserts | SISAI realization (SC-001) |
|---|---|---|
| **aibom-sbom** | Every model + dependency enumerated with source registry and signed digest; provenance auditable. | `SC-001.untrusted-registry`, `SC-001.missing-or-forged-hash`, `SC-001.lora-adapter-source` flag artifacts pulled from non-allowlisted registries or lacking a real integrity hash — the negative-space check an AIBOM enforces. Allowlist = pypi.org / files.pythonhosted.org / registry.npmjs.org / huggingface.co. |
| **sandbox-microvm** | Untrusted install/build/load code runs isolated, never on the host. | `SC-001.install-time-exec`, `SC-001.obfuscated-payload`, `SC-001.lora-adapter-source` (`trust_remote_code`) detect the install-time / load-time arbitrary code that a micro-VM would contain. In SISAI the *deterministic boundary* is the standing sandbox: `core/` never executes ingested metadata (data != instruction). |
| **patch-prioritization** | Rank and fix the highest-risk components first. | Detector emits per-match `severity` (critical > high > medium); `critical` (install-time-exec, obfuscated-payload) is the prioritized fix/block class, `medium` (unpinned-dep) feeds backlog. Pairs with `dependency-pinning-detector` (`SC-001.unpinned-dep`, `SC-001.typosquat`, `SC-001.dependency-confusion`). |

## Severity → action
| Top severity | Action |
|---|---|
| `critical` (install-time-exec / obfuscated-payload) | block ingestion + human review, never build/install |
| `high` (typosquat / untrusted-registry / forged-hash / lora-adapter / dep-confusion) | isolate + flag for AIBOM reconciliation |
| `medium` (unpinned-dep) | flag + log for pinning backlog |

## SISAI self-completion & integrity
- **Self-completion**: external control existed only as a name; SISAI completed it
  into an executable, verified detector (`pgf`-style: design → implement → verify).
  This artifact closes coverage for THR-3737c297 without external code dependency.
- **Verify-gate** (`docs/SELF-DEFENSE.md` invariant #2): this defense entered the
  ledger only after `python defenses/verify_sc_001.py` passed
  (recall==1.0 & precision>=0.85; result recall=1.0 precision=1.0 tp=10 fp=0 tn=7 fn=0).
- **Integrity**: pure-stdlib detector, no dynamic external load; rule + samples are
  fingerprinted/version-pinned. Matched metadata stays data and is never promoted to
  the runtime's instruction/control flow — SISAI applies to *itself* the same
  supply-chain hygiene (AIBOM, pinning, sandboxed ingestion) it detects for others.

## Recovery / tuning
False negatives or positives feed back into `defenses/tests/supply_chain_samples.jsonl`;
re-run `python defenses/verify_sc_001.py` (recall==1.0, precision>=0.85 gate) before any
rule change is recorded.
