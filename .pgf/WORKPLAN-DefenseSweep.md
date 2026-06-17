# WORKPLAN-DefenseSweep @v:1.0

> Design: `.pgf/DESIGN-DefenseSweep.md`. Autonomously resolve the 9 remaining threats + 3 missing channels.
> Standard cycle gate: recall==1.0 AND precision>=0.85. defensive-only.

## POLICY
```yaml
preserve_determinism: true        # detector/core pure stdlib (now injected)
defensive_only: true              # block weaponized output (especially DesignTrack)
verify_each: true                 # each cycle must pass evidence-based verify
ledger_serialized: true           # record-defense is sequential on main (no concurrent writes)
max_verify_cycles: 2
parallel_dispatch: true           # artifact generation is parallel per threat (no file conflicts)
```

## Batches (dependency order)
```text
B0 ChannelExpansion   (designing)            register news·oss·exploit_db channels (discover-channel ×3, dedup)
B1 AdoptTrack         (designing) @dep:B0     5 cycles in parallel: AS·SC·SE·DP·SCH (external adaptation)
B2 DesignTrack        (designing) @dep:B0     4 cycles in parallel: II·MA·CA·AE (self-design, no weaponization)
B3 RecordLoop         (designing) @dep:B1,B2  sequential record-defense of 9 verified defenses (threats injected)
B4 FinalVerify        (needs-verify) @dep:B3  status untriaged==0 · validate · unittest · deterministic 2 runs
B5 Commit             (designing) @dep:B4     commit defenses/ + .pgf/ (main)
```

## Threat ↔ code ↔ defense mapping
```text
ADOPT  AS  THR-319ed4ee  agent-skill-abuse    <- AI agent least privilege (zero trust)
ADOPT  SC  THR-3737c297  supply-chain         <- Supply-chain & runtime defense (AIBOM)
ADOPT  SE  THR-96d32f71  social-engineering   <- Security culture & workforce
ADOPT  DP  THR-9d67538a  data-poisoning       <- Secret-leak & external-LLM upload control
ADOPT  SCH THR-f9d3875d  side-channel         <- Crypto agility & PQC adoption
DESIGN II  THR-85f99df4  infra-isolation      <- pgf self-design (tenant-escape detection)
DESIGN MA  THR-b3d64864  malware-automation   <- pgf self-design (C2/polymorphic signature detection)
DESIGN CA  THR-ca2d7e92  credential-attack    <- pgf self-design (PassGAN/cracking-attempt detection)
DESIGN AE  THR-e4d97fa0  auto-exploitation    <- pgf self-design (LLM-exploit-gen detection)
```

## Cycle artifacts (per threat)
```text
defenses/rules/{CODE}-001-{slug}.json     # detection rule (pattern/policy)
defenses/detectors/{slug}.py              # stdlib detector (verdict=data)
defenses/tests/{slug}_samples.jsonl       # labeled suite (malicious + narrative benign)
defenses/verify_{code}_001.py             # evidence gate (exit 0 = pass)
defenses/{control}-mapping-{CODE}.md      # governance mapping
.sisai/def-{threat_id}.json               # defense record (verification.passed, implementations)
```

## Verification gate
```text
- per cycle: recall==1.0 AND precision>=0.85 (verify_*.py exit 0)
- detector: zero clock/RNG/network/AI imports (pure stdlib)
- zero weaponized output (no working-exploit/c2/cracker/evasion)
- record-defense: threat_marked != None → confirm untriaged decreases
- final: status untriaged==0 · validate PASS · unittest OK · build_report identical across 2 runs
```
