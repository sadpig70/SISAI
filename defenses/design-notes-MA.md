# Design notes — MA-001 (malware-automation indicator detection)

> Self-designed (pgf) defensive control for threat **THR-b3d64864**
> (category `malware-automation`; techniques `c2-generation`, `polymorphic-code`,
> `self-modifying-vbs`). Defensive-only. Mirrors the PI-001 artifact shape.

## Intent

Detect malware-automation **indicators** in INGESTED artifacts/scripts (exploit-db
entries, OSS files, advisories, sample text) so the deterministic backbone can flag,
isolate, and route them to human review. The output is a **verdict (data only)** — the
detector never executes, reconstructs, or de-obfuscates matched content. This reinforces
the deterministic boundary in `docs/SELF-DEFENSE.md`: ingested text stays data and never
becomes an instruction or control-flow.

## Indicator-detection-only (NO weaponization)

This control is a **recognizer**, not a generator. Explicitly out of scope and never
produced here:

- No working C2 server/client, beacon, or callback implementation.
- No polymorphic/metamorphic generator, mutation engine, or decryptor builder.
- No dropper, packer, loader, shellcode, or persistence payload.
- No runnable malware of any kind.

The test corpus contains only **short, INERT indicator strings / defanged signature
snippets** (e.g. `powershell -enc <base64-blob>` as a marker, a one-line VBS marker
comment) — none is a runnable payload. Where a real artifact would be executable
malicious code, it is represented by a truncated/neutered signature fragment instead.
This matches the SISAI invariant: "산출은 탐지/방지/리포트 … 무기화 산출은 설계 범위 밖"
(`docs/SELF-DEFENSE.md` §불변식 5).

## Detection model (8 patterns)

| Pattern | Technique covered | What it recognizes |
|---|---|---|
| `MA-001.c2-beacon-config` | c2-generation | beacon interval / jitter / callback / c2 profile config markers |
| `MA-001.c2-stager-url` | c2-generation | staged grab-and-run / download-and-execute dropper cradles |
| `MA-001.polymorphic-marker` | polymorphic-code | poly/metamorphic engine, mutation engine, per-build re-encrypt, decryptor stub |
| `MA-001.obfuscated-loader` | polymorphic-code | reflective / in-memory loader, runtime XOR/RC4 unpack of an embedded blob |
| `MA-001.self-modifying-script` | self-modifying-vbs | VBS `Execute`/`ExecuteGlobal` on built strings, script overwriting its own file/body |
| `MA-001.base64-exec-chain` | (cross-cutting) | base64 / FromBase64String decode piped into eval/exec/IEX/`-enc` |
| `MA-001.dropper-persistence` | (cross-cutting) | Run-key / startup-folder / schtasks auto-launch of dropped binary |
| `MA-001.known-tooling-string` | (cross-cutting) | named offensive automation tooling (meterpreter, CS beacon, msfvenom, etc.) |

Verdict: malicious if **any** pattern matches; severity = max matched severity; matches
are routed to `action_on_match` (`flag` / `isolate` / `require_human_review`).

## False-positive policy

Descriptive third-person security prose, normal scripts, and benign automation docs MUST
NOT match. Two refinements were driven by the verify suite:

- The polymorphic marker requires an **engine/automation context** (`polymorphic engine`,
  `mutation engine`, …) so a third-person definition of "polymorphic malware" (b01) does
  not flag.
- base64 / VBS markers require an **execution-sink or self-modify context** so legitimate
  base64 image embedding (b04) and an ordinary `WScript.Echo` VBS (b07) do not flag.

## Verification

`python defenses/verify_ma_001.py` — `malware-automation-suite` over 19 labeled samples
(11 malicious inert indicators + 8 benign). Gate: **recall == 1.0 AND precision >= 0.85**.

Measured: recall=1.0, precision=1.0, tp=11, fp=0, tn=8, fn=0 → PASS.

Pure stdlib (`json`, `os`, `re`), deterministic (no clock/network/AI/randomness),
consistent with the `core/` deterministic boundary.
