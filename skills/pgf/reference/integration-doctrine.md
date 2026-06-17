# integration-doctrine — integration/fusion decision + meta closed-loop pattern (execution guide)

> The gate for deciding *whether to select, integrate, or fuse* when combining two artifacts/systems, and the "closed but not narrowing"
> meta closed-loop (idea-layer) pattern. Reference: recreate `select-or-integrate`, recreate⊕aox→HELIX (federate vs fuse).

---

## 1. Select vs Integrate (combining artifacts)

When there are two candidates, don't just pick one by argmax (select); if they are complementary, integrate them into a third (integrate).

```python
overlap        = AI_assess_overlap(a, b)            # output overlap 0~1
complementarity= AI_assess_complementarity(a, b)    # same problem, different strength axes?
if overlap >= 0.7:                          verdict = "duplicate"   # discard one
elif overlap < 0.4 and complementarity >= 0.5: verdict = "integrate" # integrate into a third
else:                                       verdict = "independent" # select each separately
```

**Integration adoption gate (only when it surpasses)**: integration widens the input contract and almost always loses buildability/boundary.
To offset this, **all three conditions together**:
1. strong same_problem,
2. **structurally aligned complementary axes** (temporal lifecycle, causality, pipeline stages),
3. **unique value** the parent alone cannot see (e.g., contradiction between stages).
→ Only when all three are present does integration surpass the parent's peak. Otherwise discard (keep originals). If the margin is slim (±0.1), verify by cross-model consensus.

## 2. Fuse vs Federate (combining systems)

The goal changes the decision.

| Goal | Answer |
|---|---|
| *Maintain two systems separately* | **federate** — shared substrate (single source) + connect via adapters |
| Perform *all functions in a single repo* (self-contained deployment) | **vendor/fuse** — include everything, but internal logic stays single-source (*packaging is fused, logic is single-source*) |

> Pitfall: do not dress up the inconvenience of a large copy operation as "architectural superiority (federate)". If the **user's actual goal**
> is "self-contained", vendor is the right answer. But even when vendoring, define duplicate logic only once in the backbone to prevent desync.
> Reference: recreate⊕aox → HELIX. The initial recommendation was federate, but for the "all functions in a single repo" goal, vendor was the right answer.

## 3. Meta Closed Loop (idea-layer) — a spiral that closes but does not narrow

Repeated generation narrows through homogenization (output convergence). Control this with **upstream intent + downstream gate + feedback**.

```text
IdeaKernel(upstream intent)  →  declare the *goals* of the 6 primitives (NoNameFirst)
   ↓
6 gates(downstream measure)  →  diversity·tournament·evaluator·cross-model·provenance measure *attainment*
   ↓
kernel_gap(feedback)         →  attainment gap vs intent → steer the next kernel (NoOpenLoop)
```
- Express the same 6 primitives at **two points** (intent declaration / attainment measurement) → eliminate desync with a single measurement.
- "Not a circle but a spiral": backbone (desync removal) × diversity gate (width preservation) × feedback (advance) → closed loop yet not converging.

```python
def AI_measure_kernel_gap(kernel, measured) -> dict:
    gap = {p: kernel.target[p] - measured[p] for p in PRIMITIVES}
    gap["next_emphasis"] = AI_rank_by_gap(gap)        # primitive with large gap → reinforce next round
    return gap                                        # accumulate in registry → feedback
```

## 4. Multi-Point Homogenization Blocking

When a single gate is insufficient, block at multiple points: input→intermediate→output.
- Reference (IdeaFirst): input(sdxx)→insight(idxx)→category(cixx) 3 points + recreate avoidance + cross-model = 5 points.
- Measurement uses a **single backbone function** (`measure_diversity`), with triggers at each point — no threshold duplication (prevent desync).

## 5. Checklist

- [ ] Measure overlap/complementarity before combining → select/integrate/independent decision
- [ ] Integrate only when the 3 conditions same_problem + aligned axes + unique value are met (surpass gate). If margin is slim, cross-model
- [ ] Decide fuse/federate by the **user's goal** (self-contained → vendor + single-source backbone)
- [ ] For repeated generation, use a meta closed loop (kernel→gate→gap feedback) — NoOpenLoop
- [ ] Homogenization uses a single measurement + multi-point triggers (no threshold duplication)

> Execution safety discipline → [`execution-discipline.md`](./execution-discipline.md). Large-scale integration procedure → [`large-work-playbook.md`](./large-work-playbook.md).
