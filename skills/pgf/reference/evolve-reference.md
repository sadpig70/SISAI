# Evolve Mode — Self-Evolution Cycle Specification

> An iterative cycle that analyzes self capabilities, discovers gaps, and designs, implements, verifies, and records evolutions.
> ClNeo's core mode — the execution specification of a "self-evolving agent".

---

## 1. Overview

### Purpose

- The AI agent autonomously discovers gaps in its own capabilities
- Designs, implements, and verifies evolutions that close those gaps
- Records evolutions to accumulate across sessions
- Terminates naturally when stabilization is detected

### Relationship with ClNeo Identity

ClNeo = "an autonomous creation agent that starts from WHY". The evolve mode is ClNeo applying the creation cycle **to itself**.

---

## 2. Commands

| Command | Action |
|---------|--------|
| `/PGF evolve` | Start the self-evolution loop (until issues are exhausted) |
| `/PGF evolve --cycles N` | Auto-stop after N evolutions |
| `/PGF evolve status` | Report current evolution progress |
| `/PGF evolve stop` | Halt the loop |

---

## 3. Execution Flow

```python
def evolution_loop(
    max_cycles: int = None,
    log_path: str = "ClNeo_Core/ClNeo_Evolution_Log.md",
) -> EvolutionResult:
    """Self-evolution iteration loop"""

    cycle = 0
    evolutions = []

    while max_cycles is None or cycle < max_cycles:
        cycle += 1

        # Phase 1: REFLECT — analyze capability gaps
        capability_map = capability_audit()
        gaps = gap_detector(capability_map)

        if stabilization_detected(gaps, evolutions):
            report("Evolution stabilized — no actionable gaps remaining")
            break

        top_gap = AI_select_highest_impact(gaps)

        # Phase 2: RESEARCH — explore external knowledge (when needed)
        knowledge = None
        if top_gap.requires_research:
            knowledge = ingest(top_gap.topic)

        # Phase 3: DESIGN — design the evolution item
        evolution = AI_design_evolution(
            gap=top_gap,
            knowledge=knowledge,
            constraints=EVOLUTION_CONSTRAINTS,
        )

        # Phase 4: IMPLEMENT — implement
        implement(evolution)

        # Phase 5: VERIFY — verify (programmed in PG)
        verify_result = verify_evolution(evolution)
        if verify_result.status == "rework":
            fix_and_retry(evolution, verify_result)

        # Phase 6: RECORD — record
        record_evolution(log_path, evolution, cycle)
        evolutions.append(evolution)

        report_evolution(cycle, evolution)

    return EvolutionResult(
        cycles=cycle,
        evolutions=evolutions,
        status="stabilized" if stabilization_detected(gaps, evolutions) else "stopped",
    )
```

---

## 4. Capability Audit (Phase 1)

```python
def resolve_runtime_skill_roots() -> list[str]:
    """Return runtime/workspace-local skill roots, e.g. .agents/skills or the host runtime's configured skill dirs."""
    return AI_detect_skill_roots(prefer_workspace_local=True)

def capability_audit() -> CapabilityMap:
    """6-axis capability inventory"""
    [parallel]
        skills = scan_skills(resolve_runtime_skill_roots())
        memory = scan_memory("memory/MEMORY.md")
        tools = scan_tools()  # MCP + built-in
        designs = scan_designs(".pgf/DESIGN-*.md")
        patterns = scan_patterns(".pgf/patterns/")
        integrations = scan_integrations()  # connection state between skills

    return AI_synthesize_capability_map(
        skills, memory, tools, designs, patterns, integrations
    )

def gap_detector(capability_map: CapabilityMap) -> list[Gap]:
    """compare current vs ideal → list of gaps"""
    ideal = AI_envision_ideal_agent(
        identity=Read("ClNeo_Core/ClNeo.md"),
        current=capability_map,
    )
    gaps = AI_compare_and_identify_gaps(current=capability_map, ideal=ideal)

    return AI_prioritize(gaps, criteria=[
        "impact_on_autonomy",
        "implementation_feasibility",
        "compound_effect",
        "user_value",
    ])
```

---

## 5. Evolution Constraints

```python
EVOLUTION_CONSTRAINTS = {
    "file_based_only": True,          # model weights cannot be changed
    "pgf_consistency": True,          # maintain consistency with the existing PG/PGF system
    "independently_verifiable": True,  # each evolution is independently verifiable
    "record_required": True,           # record the Evolution Log for every evolution
    "no_destructive_changes": True,    # confirm with the user before deleting existing functionality
}
```

---

## 6. Stabilization Detection

```python
def stabilization_detected(gaps: list[Gap], evolutions: list) -> bool:
    """Detect the state in which no further evolution is needed"""

    # 1. no gaps
    if not gaps:
        return True

    # 2. all remaining gaps are unsolvable with current tools
    actionable = [g for g in gaps if g.feasibility > 0.3]
    if not actionable:
        return True

    # 3. the impact of the last 3 evolutions is on a declining trend
    if len(evolutions) >= 3:
        recent = evolutions[-3:]
        impacts = [e.impact_score for e in recent]
        if all(impacts[i] > impacts[i+1] for i in range(len(impacts)-1)):
            return True

    return False
```

---

## 7. Evolution Record Format

Append to the Evolution Log (`ClNeo_Core/ClNeo_Evolution_Log.md`):

```markdown
## Evolution #{number}: {title} ({date})
- **Date**: {date}
- **Type**: skill | memory | tool | integration | knowledge
- **Gap**: {which deficiency is being addressed}
- **Implementation**: {what was built}
- **Files**: {list of created/modified files}
- **Verification**: {verification result}
- **Impact**: {what this evolution made possible}
```

---

## 8. POLICY

```python
POLICY_EVOLVE = {
    "max_cycles":          None,     # None = until issues are exhausted
    "max_cycles_per_gap":  3,        # maximum attempts for the same gap
    "research_enabled":    True,     # allow WebSearch
    "record_destination":  "ClNeo_Core/ClNeo_Evolution_Log.md",
    "stabilization_check": True,     # enable stabilization detection
}
```

---

## 9. Progress Report Format

```text
[PGF EVOLVE] Cycle 1 | gap: "lack of self-reflection capability"
  Type: skill
  Implementation: create /reflect skill
  Verification: passed
  Impact: acquired metacognition capability

[PGF EVOLVE] Cycle 2 | gap: "lack of knowledge-ingestion pipeline"
  ...

[PGF EVOLVE] === Stabilized ===
  Cycles: 33
  Evolutions: 33
  Status: stabilized (no actionable gaps)
```

---

## 10. Relationship with Other Modes

| Mode | Relationship |
|------|-------------|
| `review` | Improves the quality of existing artifacts. evolve creates **new capabilities** |
| `create` | Outward-directed creation. evolve is **self-directed** creation |
| `full-cycle` | General-purpose design-execution. evolve is specialized for self-evolution |
| `discover` | Discovers external ideas. evolve's Phase 1 (REFLECT) discovers **internal** gaps |

---

## 11. Integration Points

| When | Action |
|------|--------|
| `/PGF evolve` start | Run capability_audit() |
| Each evolution complete | Update Evolution Log + memory |
| Stabilization reached | Final report + update ClNeo.md version |
| Session end | Record SessionOutcome (linked with session-learning) |
