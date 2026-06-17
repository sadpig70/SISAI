# work-as-program — How to Program the Work Itself with pg (Execution Guide)

> The essence of PG: **it makes "the work itself" a first-class program. The AI is the runtime.** Work in a form
> that the library (pgf) does not have is *programmed as work* with pg — design, simulation, execution, redesign. Where SKILL.md *defines* the notation,
> this document provides **the procedure for handling the work process itself** with that notation.

---

## 0. Isomorphism (Why "Programming")

```
ordinary programming:  source code → compiler → machine executes
pg:                    Gantree (structure) + PPR (logic) → AI runtime executes
                       ├ verify *before* execution via PPR simulation (predict pass/fail without running)
                       ├ verify *after* execution via acceptance_criteria
                       └ debug the work itself via AI_redesign
```
→ The work process becomes a program that can be designed, simulated, tested, verified, and redesigned. pgf is the stdlib on top of it.

## 1. 7-Stage Loop (Standard for Large/New Work)

Work that does not fall into a library mode (design/full-cycle, etc.) is *programmed* with this loop:

```text
① Analyze     reverse-engineer the target with pgf design --analyze → store structure as pg (Gantree)
② Design      design and store the integrated/target structure as pg
③ Work design design a concrete work plan (WORKPLAN) as pg → persist in .pgf/ (resumable)
④ Simulation  ★ symbolically execute the work plan with PPR → predict risks *before* execution (§2)
⑤ Execute     batch-execute per the work plan + per-batch verification gate
⑥ Redesign    on error, redesign with pg (Failure Strategy / AI_redesign — preserve public interface)
⑦ Checkpoint  update status JSON → lossless resume despite interruption/context loss
```

Principle: **keep state in files (`.pgf/`)** (no hardcoding in memory or documents). Isolate so that one stage's failure does not corrupt the accumulated state.

## 2. ★ PPR Simulation — Pre-Execution Verification (the Most Underrated Capability)

*Before running* the work plan, symbolically execute each node with PPR to predict outcomes and catch risks in advance.

```python
def AI_simulate_workplan(plan: Gantree, env: dict) -> SimVerdict:
    """Symbolically execute each batch → predict output/risk/acceptance. No actual file changes."""
    risks, checks = [], []
    for node in plan.topological_order():
        out = AI_predict_outcome(node, env)            # what does this node produce
        risks += AI_find_risks(node, env)              # omission/conflict/ordering risks
        checks.append(Check(node.id, predict=out.acceptance_pass))
    verdict = "GO" if not any(r.severity == "high" for r in risks) else "REDESIGN"
    return SimVerdict(verdict, risks, checks)
    # acceptance_criteria:
    #   - 0 high-severity risks → GO
    #   - if post-execution measurement matches the predicted check, simulation trust is confirmed
```

**Prediction table format** (simulation output → compare after execution):

| Prediction (node) | Value | Post-execution measurement | Match |
|---|---|---|---|
| ... | ... | ... | ✅/❌ |

**Demonstration**: In the HELIX monorepo migration, the simulation caught the risk *"the Path parts of `.py` paths (`".agents" / "skills"`) are missed by string replacement alone"* **before execution** → pre-applied a regex in the replacement script to pass with 0 omissions. (`D:/HELIX/specs/META-PROGRAM.pg.md` §5.)

## 3. Redesign (Debugging on Error)

```python
for batch in plan.topological_order():
    if batch.status == "done": continue              # idempotent — resume
    result = AI_execute(batch)
    if not AI_verify(result, batch.gate):
        batch.ppr = AI_redesign(batch, result.failure, constraint="preserve_gate")  # redesign with pg
        result = AI_execute(batch)                   # re-execute
    record_status(".pgf/status.json", batch, result) # persist → resume point
```
Key: **preserve the public interface (gate)** and let the AI redesign only the internal implementation.

## 4. Checklist

- [ ] Did you decompose the large/new work into a Gantree and persist it in `.pgf/`?
- [ ] Did you build a risk prediction table via PPR simulation before execution (0 high risk → GO)?
- [ ] Did you place a verification gate per batch and make it resumable via status JSON?
- [ ] Did you debug errors with `AI_redesign` (preserving the gate)?
- [ ] Do you reload state from files each time (no hardcoding in memory/documents)?

> Related: control-flow / contracting patterns → [`control-flow-cookbook.md`](./control-flow-cookbook.md). Execution discipline (persistence, evidence verification, determinism) → pgf `reference/execution-discipline.md`.
