# control-flow-cookbook — Type I/O · Conditions · Branching · Loops · Contracting (Execution Guide)

> pg **defines a task's I/O as types** and controls flow with **conditions, branching, and loops**. This lets it program even
> **complex tasks like a factory production line**, where multiple contracting units (skills/agents) exchange materials via type contracts.
> Where SKILL.md *defines* the syntax, this document collects **patterns for using that syntax in complex-task orchestration**.

---

## 1. Type I/O — the "Materials" Flowing Down the Line

Define the materials that contracting units exchange as types (the heart of the contract). Python type hints + schema literals (allowed in PG).

```python
ChannelCatalog = dict = {"version": str, "channels": list[Channel], "total": int}
TrendReport    = dict = {"industry_trend_md": str, "domains_covered": int}
Idea           = dict = {"id": str, "title": str, "domains": list[str], "scores": Scores6}
DesignSeed     = dict = {"name": str, "single_question": str, "sources": list[str]}
```

## 2. Contractor — Input Contract → Output Contract + Inspection

Each unit = a subcontractor. It takes an input type, delivers an output type, and must pass acceptance to proceed to the next stage.

```python
Contractor = dict = {"name": str, "input_type": type, "output_type": type,
                     "acceptance": list[str], "failure_strategy": Literal["retry","redesign","handoff"],
                     "max_retry": int}
```

## 3. Conditions · Branching (Python Flow Control As Is)

```python
# swap the line by environment capability (branching)
if env["cross_model"] == "available":   line = full_line
elif env["cross_model"] == "unavailable": line = swap(line, {"cix":"sa-icx","evx":"sa-evx"})
else:                                    line = mark_partial(line)

# gate branching (block reuse)
if is_consumed(candidate, ledger)["consumed"]:
    return "reject:re-steer"            # discard → re-steer
```

## 4. Loops (4 Patterns)

```python
# ① stage retry (max_retry)
for attempt in range(c["max_retry"] + 1):
    out = AI_invoke(c["name"], material)
    if AI_verify(out, c["acceptance"]): return out
    if attempt >= 1 and c["failure_strategy"] == "redesign":
        c["ppr"] = AI_redesign(c, out.failure)

# ② Convergence Loop (generate-critique-evolve: until stabilization)
while True:
    eval = AI_evaluate(draft, criteria)
    if eval.score >= threshold: break
    draft = AI_revise(draft, eval.feedback)

# ③ island re-divergence (while diversity is below floor)
while unique_ratio(pool, sim) < floor:
    pool = regenerate(pool, focus=AI_find_untouched_axes(pool))

# ④ production round (until target/budget)
while len(out) < target and budget.remaining() > 0:
    out.append(run_one_round())
```

## 5. Main Program — Combining Types × Branching × Loops (Factory Line)

```python
def run_factory(target: int, budget: int, env: dict) -> list[DesignSeed]:
    seeds = []
    while len(seeds) < target and budget_left(budget) > 0:        # loop ④
        line = AI_route_by_capability(env, LINE)                  # branching ①
        material = None
        for c in line:                                           # contractors in series
            material = run_stage(c, material)                    # loop ① (inspect + retry)
            if c["name"] == "cix":
                material = enforce_diversity(converge(material))  # loop ②③
        winner = material["winner"]
        if AI_gate(winner, ledger) == "reject:re-steer":         # branching (gate)
            continue                                              # re-steer then next round
        seeds.append(AI_to_seed(winner))
    return seeds
    # acceptance_criteria:
    #   - each contractor output satisfies output_type and acceptance (stage inspection)
    #   - loops guarantee termination (whichever of target/budget is reached first)
```

## 6. [parallel] — Parallel Independent Stages

```python
[parallel]
recombine = AI_recombine(inv)      # independent
mutate    = AI_mutate(inv)
transplant= AI_transplant(inv)
[/parallel]
pool = recombine + mutate + transplant     # merge
```
Rule: nodes inside `[parallel]` are **independent** (`@dep:` forbidden), no nesting.

## 7. Pre-Execution Simulation (dry-run the Contracting Line Too)

```python
def AI_simulate_factory(target, env) -> SimVerdict:
    line = AI_route_by_capability(env, LINE)   # in a standalone environment, predict it will be swapped to sa-*
    # check loop ④ termination, branching, and bottlenecks in advance without running the line → GO | REDESIGN
```

**Demonstration**: `D:/HELIX/specs/PRODUCTION-LINE.pg.md` (HELIX continuous production as a factory-contracting pg program),
`DESIGN-HELIX-UNIFIED-PIPELINE.pg.md` (a single closed loop over all aox·recreate features).

> Related: the 7 stages of programming the work itself → [`work-as-program.md`](./work-as-program.md).
> Inter-agent contracting handoff spec (TaskSpec) → pgf `reference/agent-protocol.md`.
