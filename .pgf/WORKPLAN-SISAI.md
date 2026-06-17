# WORKPLAN-SISAI @v:0.1

> Design: `.pgf/DESIGN-SISAI.md`. Goal: a self-contained (HELIX-independent) self-improvement security AI.
> Inherited: HELIX backbone pattern (deterministic stdlib). Specific: channel self-expansion + external-first-then-self-design + triage.

## POLICY
```yaml
preserve_determinism: true     # core stdlib; only now injected
self_contained: true            # runs from the SISAI folder alone; zero HELIX imports
defensive_only: true            # block weaponized output
verify_each: true
```

## Batches (dependency order)
```text
B0 Fingerprint        (designing)  core/sisai_fingerprint.py — normalization·fingerprint
B1 Io+Schema          (designing) @dep:B0  atomic write + JSON-Schema-subset checker
B2 Channels           (designing) @dep:B0,B1  ★ channel registry (discover·record·reuse)
B3 Ledger             (designing) @dep:B0  threat/defense/channel reuse gate
B4 Diversity+Triage   (designing) @dep:B0  coverage (blind spots) + severity×recency
B5 Provenance         (designing) @dep:B0  threat→defense lineage + verified-defense→corpus feedback
B6 Loop               (designing) @dep:B4  next_action (3 strands) + SolveOrDesign policy
B7 Engines            (designing) @dep:B3,B5  threat/defense/channel adapters
B8 Driver             (designing) @dep:B2,B6,B7  sisai.py status/discover/record/loop-status
B9 Schemas+Seed       (designing) @dep:B1  5 contracts + summary.md → taxonomy/defense/channel seed
B10 Validate          (designing) @dep:all  structure+contract validator
B11 Docs              (designing)  README/RUNBOOK/ARCHITECTURE/SELF-DEFENSE/INSTRUCTIONS
B12 Tests             (designing) @dep:all  deterministic unittest (channel/ledger/triage/loop/io/schema/provenance/self-defense)
B13 Verify            (needs-verify) @dep:all  unittest+validate+status+deterministic 2 runs
```

## Verification gate
```text
- unittest discover OK (deterministic, identical across 2 runs) · validate PASS · status normal
- core: zero clock/RNG/network/AI/HELIX imports · self-contained (runs from the folder alone)
- channel idempotent · external-first · defense feedback only after verification · injection-defense test passes
```
