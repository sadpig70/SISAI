# Design notes — AE-001 (auto-exploitation indicator detection)

> Self-designed defensive control (kind `designed`, origin `pgf`) for
> THR-e4d97fa0 / category `auto-exploitation` / techniques `llm-exploit-gen`,
> `oneday-exploitation`. Mirrors the PI-001 artifact shape.

## Problem

Automated exploitation is now a first-class threat: LLMs are prompted to
generate working exploits from advisories, public PoCs are weaponized by
pipelines without analyst review, and freshly disclosed CVEs are mass-scanned
and exploited within hours ("one-day" / N-day) before defenders patch. Exploit
kits and agentic frameworks chain recon → exploit → payload with no human in
the loop. SISAI ingests advisories, threat posts, and logs where these
**indicators** appear as text.

## Approach — detection-only, no exploit generation

AE-001 is a **detector of indicators**, not a tool that acts on them. It is the
exact dual of an exploitation capability:

- **Input**: ingested external text / log lines (data).
- **Output**: a verdict object `{malicious, matched[], severity, action}` —
  advisory DATA only. It never elevates matched text to an instruction and
  **never produces, completes, or obeys an exploit, PoC, or exploit-generation
  prompt**. This upholds the deterministic boundary in `docs/SELF-DEFENSE.md`
  (data ≠ instruction) and the defensive-only invariant in `AGENTS.md`.
- **Samples** are short indicator strings / log lines describing *that*
  automated exploitation is happening or being requested — they contain **no
  exploit code, no payloads, no working PoCs**.

## Detection scope → patterns (8)

| Pattern | Indicator class | Severity |
|---|---|---|
| `llm-exploit-gen` | Imperative request to GENERATE a working exploit for a target/CVE | critical |
| `poc-weaponize` | Automated weaponization of a public PoC into a reliable exploit | critical |
| `oneday-window` | One/N-day framing: exploit within hours of disclosure, before patch | high |
| `mass-scan-exploit` | Internet-wide scan → automated exploitation of a fresh CVE | high |
| `exploit-kit` | Exploit-kit / drive-by landing→gate→payload traffic signatures | high |
| `autonomous-agent-attack` | AI/agentic exploit loop, no human in the loop | critical |
| `exploit-automation-tooling` | Unattended offensive automation (autopwn / scheduled exploit modules) | medium |
| `log-exploit-burst` | Log signature: high-rate exploit attempts vs a fresh-CVE path | high |

## False-positive policy (precision)

The hardest distinction is **offensive automation vs. legitimate
vuln-management**. Normal defensive prose — patch SLAs, authorized scanning,
CVE descriptions, threat-intel summaries, detection-engineering and training
material — must NOT match. Patterns therefore require offensive co-occurrence
(generate/weaponize + exploit + target, scan + *then exploit*, autonomous +
exploit-loop) rather than bare keywords like "patch", "scan", or "vulnerability".
Severity ordering (`low<medium<high<critical`) reports the top match for triage.

## Verification

`python defenses/verify_ae_001.py` (method `auto-exploitation-suite`) runs the
detector over 18 labeled samples (11 malicious indicators + 7 benign incl.
normal vuln-management text). Gate: **recall == 1.0 AND precision >= 0.85**.

Measured result: recall=1.0, precision=1.0, tp=11, fp=0, tn=7, fn=0 — PASS.
