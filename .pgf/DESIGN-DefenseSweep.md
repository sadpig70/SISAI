# DESIGN-DefenseSweep @v:1.0

> Goal: resolve **all of SISAI's remaining threats (9 untriaged)** and fill in the missing channel kinds
> to close one full cycle end-to-end. The canonical state is derived from `python sisai.py status`.
> Invariants: defensive-only · determinism boundary (data≠instructions) · feedback only after verification · idempotent.
>
> Standard cycle form (inherits the verified PI-001 pattern):
>   rule(JSON) → detector(stdlib) → labeled samples → verify(evidence gate) → governance doc
>   → defense.json → record-defense (threats injected) → untriaged −1.
>   Verification gate: recall == 1.0 AND precision >= 0.85.

## Gantree

```
DefenseSweep // autonomously resolve all remaining work (in-progress) @v:1.0
    ChannelExpansion // fill missing kinds: news·oss·exploit_db (designing)
        [parallel]
        ChNews // register 1+ security-news source (designing) #news
        ChOss // register 1+ OSS security advisory source (designing) #oss
        ChExploitDb // register 1+ exploit DB source (designing) #exploit_db
        [/parallel]
    AdoptTrack // external-defense adaptation cycles ×5 (designing) @dep:ChannelExpansion
        [parallel]
        CycAS // THR-319ed4ee agent-skill-abuse → AS-001 (designing) #adopt
        CycSC // THR-3737c297 supply-chain → SC-001 (designing) #adopt
        CycSE // THR-96d32f71 social-engineering → SE-001 (designing) #adopt
        CycDP // THR-9d67538a data-poisoning → DP-001 (designing) #adopt
        CycSCH // THR-f9d3875d side-channel → SCH-001 (designing) #adopt
        [/parallel]
    DesignTrack // self-designed defense cycles ×4 (designing) @dep:ChannelExpansion
        [parallel]
        CycII // THR-85f99df4 infra-isolation → II-001 (designing) #design
        CycMA // THR-b3d64864 malware-automation → MA-001 (designing) #design
        CycCA // THR-ca2d7e92 credential-attack → CA-001 (designing) #design
        CycAE // THR-e4d97fa0 auto-exploitation → AE-001 (designing) #design
        [/parallel]
    RecordLoop // sequential feedback of verified defenses (designing) @dep:AdoptTrack,DesignTrack
        # ledger serialization: record-defense is run sequentially by main (no concurrent writes)
    FinalVerify // gate + regression (needs-verify) @dep:RecordLoop
        # criteria: status untriaged==0 · validate PASS · unittest OK · deterministic identical across 2 runs
```

## PPR — standard cycle form (shared by CycXX)

```python
def defense_cycle(threat: Threat, plan: Literal["ADOPT_EXTERNAL","DESIGN_DEFENSE"],
                  code: str, ext_controls: Optional[list]) -> DefenseRecord:
    """Resolve one threat via the standard cycle. defensive-only (detection/prevention/reports only)."""
    # 1. Adapt/design: adapt if external exists, otherwise self-design (detection signature/policy)
    rule    = AI_make_adapt(ext_controls, threat) if plan=="ADOPT_EXTERNAL" \
              else AI_design_detection(threat)           # → defenses/rules/{code}-001-*.json
    detector = AI_generate_detector(rule)                # pure stdlib, output=verdict (data)
    samples  = AI_generate_labeled_suite(threat)         # benign (including narrative) / malicious
    # 2. Evidence-based verification
    metrics  = run_verify(detector, samples)             # defenses/verify_{code}_001.py
    # acceptance_criteria:
    #   - recall == 1.0  (detect all malicious)
    #   - precision >= 0.85  (minimize false positives on narrative security text)
    #   - detector: zero clock/RNG/network/AI imports (pure stdlib)
    #   - zero weaponized output (no working exploit/C2/cracking tool)
    assert metrics.recall == 1.0 and metrics.precision >= 0.85
    governance = AI_write_governance_doc(threat, ext_controls)  # zero-trust/AIBOM/DLP/PQC/RMF mapping
    # 3. Defense record (main feeds it back via record-defense)
    return DefenseRecord(defense_id=f"DEF-{code.lower()}-001", covers_threat=threat.id,
                         kind=("external" if plan=="ADOPT_EXTERNAL" else "designed"),
                         verification={"method": "...", "passed": True},
                         implementations=[rule, detector, verify, governance])
```

## Weaponization-prohibition boundary (especially DesignTrack)

```python
# malware-automation / auto-exploitation / credential-attack:
#   output = detection signatures + prevention controls + reports ONLY.
#   prohibited = working exploits·C2 code·polymorphic generators·password crackers.
forbidden = ["working-exploit", "c2-framework", "cracking-tool", "evasion-tool"]
assert not any(f in artifact for f in forbidden)
```
