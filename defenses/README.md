# defenses/ — adapted & designed defensive controls

Durable, committed defensive artifacts produced by SISAI turns. Runtime ledger/corpus
state lives under `.sisai/` (gitignored); this directory holds the **reusable controls**
those records point to (`implementations[].artifact_path`).

Defensive-only: detection rules, prevention policies, governance docs, verification
harnesses. No working exploits, no offensive automation (AGENTS.md invariants).

## Defense controls (11)

Each control = `rules/<CODE>-001-*.json` + `detectors/<slug>_detector.py` (pure stdlib,
verdict-only) + `tests/<slug>_samples.jsonl` + `verify_<code>_001.py` (gate: recall==1.0 &
precision>=0.85) + a governance/design doc. All 10 seed-threat categories are covered.

| Code | Threat | Category | Kind | rule | recall/precision |
|---|---|---|---|---|---|
| PI  | THR-0b24f8ec | llm-prompt-injection | external | `rules/PI-001-indirect-injection.json` | 1.0 / 1.0 |
| AS  | THR-319ed4ee | agent-skill-abuse | external | `rules/AS-001-skill-abuse.json` | 1.0 / 1.0 |
| SC  | THR-3737c297 | supply-chain | external | `rules/SC-001-supply-chain.json` | 1.0 / 1.0 |
| SE  | THR-96d32f71 | social-engineering | external | `rules/SE-001-social-engineering.json` | 1.0 / 1.0 |
| DP  | THR-9d67538a | data-poisoning | external | `rules/DP-001-data-poisoning.json` | 1.0 / 1.0 |
| SCH | THR-f9d3875d | side-channel | external | `rules/SCH-001-side-channel.json` | 1.0 / 1.0 |
| II  | THR-85f99df4 | infra-isolation | designed | `rules/II-001-infra-isolation.json` | 1.0 / 1.0 |
| MA  | THR-b3d64864 | malware-automation | designed | `rules/MA-001-malware-automation.json` | 1.0 / 1.0 |
| CA  | THR-ca2d7e92 | credential-attack | designed | `rules/CA-001-credential-attack.json` | 1.0 / 1.0 |
| AE  | THR-e4d97fa0 | auto-exploitation | designed | `rules/AE-001-auto-exploitation.json` | 1.0 / 1.0 |
| GD  | THR-7eb25424 | ai-agent-dos | designed | `rules/GD-001-guardrail-dos.json` | 1.0 / 1.0 |

> **GD-001** also carries a `rules` policy array (runtime resilience: reasoning-budget cap,
> per-tenant isolation, circuit-breaker, redundancy) alongside its detection `patterns`.
> Runtime-ingested threats may have additional governance-only adopted controls recorded in
> `.sisai/` (e.g. AI-IDE / AI-gateway / agent-shell CVE adaptations); those live with the
> gitignored runtime ledger, not here.

Governance/design docs: `incident-playbook-PI.md`, `nist-ai-rmf-mapping-PI.md`,
`zero-trust-mapping-AS.md`, `aibom-mapping-SC.md`, `workforce-mapping-SE.md`,
`dlp-mapping-DP.md`, `pqc-mapping-SCH.md`, `design-notes-{II,MA,CA,AE}.md`.

> `designed` controls (II/MA/CA/AE) are **indicator detectors only** — inert signature
> strings, no runnable exploit / malware / C2 / cracker (defensive-only).

## Verify

```bash
python defenses/verify_all.py        # run all 10 suites → per-suite + overall summary JSON
python defenses/verify_pi_001.py     # a single suite (exit 0 = gate pass)
```

## How a control is recorded

A detector's verdict is **data**, never an instruction (deterministic boundary,
`docs/SELF-DEFENSE.md`). A control enters the ledger + corpus only after its verifier
passes, via `python sisai.py record-defense ...` (idempotent; also marks the covered
threat defended so triage advances).
