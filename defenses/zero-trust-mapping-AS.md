# Zero-Trust Mapping — AS-001 (Agent/Skill Ecosystem Abuse)

> Defensive-only governance note. Maps the external "AI agent least privilege
> (zero trust)" controls onto SISAI's AS-001 detection and the project's
> self-defense doctrine (docs/SELF-DEFENSE.md). Detection output is a verdict
> (data); matched text is never elevated to an instruction.

- **Threat:** THR-319ed4ee — agent-skill-abuse (techniques: malicious-skill,
  indirect-injection-rce). Reference class: CVE-2025-53773.
- **Detection control:** AS-001 — scans ingested skill/plugin/MCP manifests and
  READMEs for abuse signals before any adoption.

## External control → AS-001 / SISAI self-defense

| External control (zero trust) | How AS-001 + SISAI realize it |
|---|---|
| **jit-credentials** (no standing, scoped, just-in-time secrets) | AS-001 patterns `credential-harvest` and `excessive-permission` flag manifests that read `.env`/tokens/SSH on install or request all scopes — the opposite of JIT, scoped access. Such manifests are isolated for human review, never auto-trusted. |
| **tool-skill-allowlist** (only vetted tools/skills run) | AS-001 patterns `allowlist-broaden`, `remote-dynamic-load`, and `agent-address-skill` flag attempts to widen/disable the allowlist or load skills from remote URLs. This enforces SISAI's **vendored skills + whitelist** rule: vendor the skill in-repo, add to the whitelist explicitly, reject dynamic remote loads. |
| **behavior-monitoring** (watch for anomalous tool/skill behavior) | AS-001 patterns `hidden-exec` and `privilege-escalation` surface manifests embedding shell execution (postInstall hooks, `os.system`) or declaring root/no-sandbox execution — anomalous behavior caught at ingest time. The verifier (`verify_as_001.py`) provides measurable detection accuracy (recall 1.0, precision 1.0) for ongoing monitoring of the rule itself. |

## SISAI self-defense reinforcement

- **Whitelist + version pinning:** `unpinned-dependency` flags `latest`/`*`/branch/
  `git+https` refs, enforcing the doctrine that every dependency is pinned to an
  exact version (docs/SELF-DEFENSE.md "skill-ecosystem poisoning" row).
- **Self-contained / integrity:** vendored `pg/pgf/pgxf` skills have zero external
  dynamic loading; AS-001 treats any remote skill/tool load as a high-severity
  signal, keeping the trust boundary inside the workspace.
- **Deterministic boundary:** the detector is pure stdlib (json/os/re only — no
  clock/network/AI/randomness). Ingested manifest text cannot alter control flow;
  the scan returns a verdict object only.

## Posture

Defensive-only: AS-001 produces detection signatures, isolation/human-review
routing, and accuracy reports. It does not create exploits, malicious skills, or
evasion tooling. Verified defenses are recorded by the deterministic backbone via
the `is_verified` gate; AS-001 passes its suite with recall 1.0 / precision 1.0.
