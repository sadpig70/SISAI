# Design Review Protocol

## Purpose

After DESIGN is complete → before the PLAN transition, verify design quality from multiple perspectives.
Catching problems at the design stage is 10x cheaper than rework after implementation.

## When to Trigger

- After the 4 completion criteria of the `design` mode are met (explicit user invocation)
- In `full-cycle` / `create` mode, **only when the `--with-review[=N]` flag is present**, just before the design → plan transition (opt-in, disabled by default)
- When the user requests `/PGF design-review` or `/PGF review --design`

> The default full cycle does not include a review gate, for stability. Apply the flag explicitly only for work that needs review.

## Loop Contract (when full-cycle is invoked with `--with-review[=N]`)

The entry point that `full_cycle()` invokes is `run_design_review_loop(design_path, max_iterations, status_path)`, which guarantees the following:

1. **Iteration cap**: at most N (`max_iterations`) review-revise cycles. The default value of N is 1
2. **Pass criterion**: `Critical=0 AND High≤2` → return `status="passed"` immediately
3. **revise behavior**: on pass failure, call `AI_revise_design(design_path, issues)` then re-review
4. **When N is exceeded**: return `status="needs_user_ack"` + enclose `unresolved_issues` (not a hard block)
5. **status JSON update**: add only `review_iterations` (int) and `unresolved_issues` (list[Issue]) — existing keys unchanged
6. **Skip automation**: Level 1 (≤3 nodes) / `micro` mode → skip the call itself

## 3-Perspective Design Review

Select 3 perspectives from the existing 14 personas for a lightweight review:

| Reviewer | Persona Base | Focus |
|----------|-------------|-------|
| **Feasibility Reviewer** | P5 (Field Operator) | implementation feasibility, technology choice, complexity |
| **Risk Reviewer** | P7 (Contrarian Critic) | critical weaknesses, hidden assumptions, scalability risk |
| **Architecture Reviewer** | P8 (Convergence Architect) | structural consistency, module coupling, evolvability |

## Review Process

```
def design_review(design_path: str) -> ReviewResult:
    design = Read(design_path)

    [parallel]
        feasibility = Agent(
            persona = "P5 Field Operator",
            prompt = f"""
            Review this PGF DESIGN for implementation feasibility:
            {design}

            Check:
            1. Can every node be implemented with available tools?
            2. Are there hidden dependencies not captured in @dep?
            3. Is the complexity estimate realistic (15-min atomic rule)?
            4. Are there missing error handling paths?

            Output: PASS / CONCERN (with specific issues)
            """
        )

        risk = Agent(
            persona = "P7 Contrarian Critic",
            prompt = f"""
            Challenge this PGF DESIGN — find its weakest points:
            {design}

            Attack from:
            1. What assumptions will break first?
            2. What's the single point of failure?
            3. What happens at 10x scale?
            4. What's missing that the designer didn't think of?

            Output: PASS / CONCERN (with specific risks)
            """
        )

        architecture = Agent(
            persona = "P8 Convergence Architect",
            prompt = f"""
            Review this PGF DESIGN for architectural quality:
            {design}

            Evaluate:
            1. Gantree hierarchy — proper decomposition?
            2. PPR def blocks — AI_ functions well-defined?
            3. Module boundaries — clean interfaces?
            4. Future extensibility — can this evolve?

            Output: PASS / CONCERN (with specific improvements)
            """
        )

    # Aggregate results
    if all_pass([feasibility, risk, architecture]):
        return ReviewResult(status="APPROVED", notes=aggregate_notes)
    else:
        concerns = collect_concerns([feasibility, risk, architecture])
        return ReviewResult(status="REVISE", concerns=concerns)
```

## Result Actions

| Result | Action |
|--------|--------|
| 3/3 PASS | Proceed to PLAN |
| 2/3 PASS | Address concerns, proceed if non-critical |
| 1/3 or 0/3 PASS | Revise DESIGN before proceeding |

## Integration with PGF Modes

- **design** → design-review → plan (manual trigger: `/PGF design-review`)
- **full-cycle** → auto-trigger after design completion criteria met
- **create** → auto-trigger (autonomous mode)

## Lightweight Mode

For Level 1-2 tasks (≤10 nodes), skip multi-agent review. Single-perspective self-review sufficient:
- Read the design
- Ask: "Would P7 (Contrarian Critic) find a fatal flaw?"
- If yes → address it. If no → proceed.
