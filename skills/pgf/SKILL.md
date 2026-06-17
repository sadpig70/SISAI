---
name: pgf
description: "PGF (PPR/Gantree Framework) — AI-native design/execution framework. Supports system architecture design, work planning, autonomous execution, idea discovery, and full creation cycles. Gantree hierarchical decomposition + PPR pseudo-code for AI-comprehensible specifications. Triggers: design this, structural design, task decomposition, architecture, module separation, work planning, WORKPLAN, project structuring, Gantree, PPR, PGF, discover, create, design, plan, execute, discover, create"
user-invocable: true
argument-hint: "design|plan|execute|full-cycle|loop|discover|create [project-name|start|cancel|status]"
---

# PGF (PPR/Gantree Framework) v2.5

> If PG is a programming language, PGF is a library.
> It normalizes useful patterns frequently executed in PG (design, execution, verification, discovery, creation, etc.).

## PG-Based Dependency

**PGF uses PG (PPR/Gantree Notation) as its base language.** PG's core properties (Parser-Free, Co-evolutionary, DL/OCME, AI_ functions, → pipelines, [parallel], Gantree node syntax) are defined in the PG skill, and PGF inherits them.

> **PG notation reference**: Load the PG skill to review Gantree node syntax, PPR syntax (AI_/AI_make_ prefixes, → pipelines, [parallel], acceptance_criteria, Convergence Loop, Failure Strategy), data types, and atomic-node criteria.

What PGF adds on top of PG:
- **Execution modes** — design, plan, execute, full-cycle, loop, discover, create, micro, delegate
- **WORKPLAN + POLICY** — execution plan and policy blocks
- **status JSON** — per-node execution state tracking
- **Phase transition** — automatic transition conditions between modes
- **Session Learning** — cross-session learning and strategy adaptation
- **Epigenetic PPR** — context-adaptive execution, automatic extract-ppr.py integration
- **Runtime Continuation** — long-run protection via per-runtime adapters (hook/heartbeat/manual, etc.)
- **Design Review** — 3-perspective pre-implementation validation

---

## Current Project PGF State

To check the current PGF state, scan the project's `.pgf/` directory:
- List `*.md` and `*.json` files in `.pgf/`
- Read `status-*.json` for execution progress (`summary.done / summary.total`)
- Check `.pgf/runtime/pgf-loop-state.json` for active pgf-loop status. Runtime adapters may mirror this state elsewhere, but `.pgf/runtime/` is canonical.

---

## PGF Notation Extensions

PG defines the canonical Gantree node syntax and 6 base status codes (`done`, `in-progress`, `designing`, `blocked`, `decomposed`, `needs-verify`). PGF adds **3 delegation status codes** used in `delegate` mode and AI-to-AI handoffs:

| Status | Meaning | Execution Rule |
|---|---|---|
| `(delegated)` | Handed off to another agent | Skip — executing remotely |
| `(awaiting-return)` | Delegation sent, result pending | Poll or wait for callback |
| `(returned)` | Result received, integration pending | Validate + integrate result |

State transition: `(designing) → (delegated) → (awaiting-return) → (returned) → (done)` (or `(blocked)` on validation failure).

All other notation rules (5-level depth, `[parallel]`, `@dep:`, PPR `def` blocks, Convergence Loop, Failure Strategy, atomicity 15-minute rule) follow PG skill verbatim.

---

## Reference Document Guide

> **Path convention**: `{SKILL_DIR}` is a runtime-neutral placeholder denoting **this skill's root directory** (the directory containing `SKILL.md`). Every agent runtime (Claude Code, Kimi, Gemini, MCP, Agent SDK, etc.) substitutes it with the local path where the `pgf` skill is installed. Use `{SKILL_DIR}/...` for all internal references — never hard-code absolute paths or runtime-specific env vars.

Reference documents for this skill are located in the `{SKILL_DIR}` directory. Load the appropriate file with the Read tool depending on the execution mode and need.

### Base Notation (PG skill)

The core syntax of PG notation is defined in the PG skill. The PG skill is auto-loaded when PGF runs.

| Source | Content |
|--------|---------|
| **PG skill** (`PG/SKILL.md`) | Gantree node syntax, status codes, PPR syntax (AI_/AI_make_, →, [parallel]), data types, atomic-node judgment, Convergence Loop, Failure Strategy, checklist |

> Content defined in the PG skill is not redefined in any PGF reference document. When a duplication is found, the PG skill is the canonical source.

### Always Reference

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/pgf-format.md` | PGF file format (DESIGN/WORKPLAN .md structure, naming conventions) |

### Execution Discipline & Playbooks (execution discipline — leveraging the essentials)

> What a mode *does* is given by the per-Phase references below; **how to perform it without mistakes** is given by these three.

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/execution-discipline.md` | Execution discipline for finishing without mistakes — decompose → persist (.pgf) → batch gate → resume from status, evidence-based verify (GATE-EVIDENCE), 3-perspective, determinism boundary |
| `{SKILL_DIR}/reference/large-work-playbook.md` | Large-scale (>30 nodes) and multi-file work — pgxf index + batch migration + atomic safe substitution (preserving line breaks, improvements, cross-references) |
| `{SKILL_DIR}/reference/integration-doctrine.md` | Integration/fusion judgment — select-or-integrate, fuse vs federate, idea-layer meta closed loop (a spiral that closes but does not narrow) |

### Design Phase (design mode)

> For Gantree node syntax, PPR syntax (`AI_`/`→`/`[parallel]`, etc.), data types, Convergence Loop, Failure Strategy, atomic-node judgment (15-minute rule), and the base checklist, refer to the **PG skill (canonical)**. For notation/check items that PGF adds, see the "PGF Notation Extensions" and "PGF Execution Checklist" sections below.

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/analyze-reference.md` | design --analyze reverse engineering — codebase → auto-generate DESIGN |
| `{SKILL_DIR}/reference/design-review-reference.md` | 3-perspective design review — feasibility/risk/architecture pre-implementation validation |

### Execution Phase (plan / execute / loop mode)

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/workplan-reference.md` | WORKPLAN conversion, POLICY block, Loop algorithm, error recovery |
| `{SKILL_DIR}/loop/loop-reference.md` | Runtime-adapter loop engine — node selection, prompt composition, error recovery |
| `{SKILL_DIR}/reference/verify-reference.md` | 3-perspective cross-verification — acceptance/quality/architecture, rework rules |
| `{SKILL_DIR}/reference/cycle-reference.md` | full-cycle + create unified spec — DESIGN→PLAN→EXECUTE→VERIFY pipeline, optional DISCOVER prepend, rework regression, session resumption |
| `{SKILL_DIR}/reference/review-reference.md` | review mode — iterative analysis, prioritization, fix, re-verification |
| `{SKILL_DIR}/reference/evolve-reference.md` | evolve mode — self-evolution cycle, capability audit, stabilization detection |

### Discovery/Creation Phase (discover / create mode)

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/discovery/discovery-reference.md` | IdeaFirst 7-stage pipeline, Agent parallel execution, result integration |
| `{SKILL_DIR}/discovery/archive-discovery.py` | Discovery artifact date-based archive script |

> `create` mode (5-phase autonomous: DISCOVER + DESIGN→VERIFY) and `full-cycle` mode (4-phase) share the same pipeline spec — see `reference/cycle-reference.md` in the Execution Phase table above.

### Agent Communication & Delegation

| Document | Purpose |
|----------|---------|
| `{SKILL_DIR}/reference/agent-protocol.md` | PG-based inter-agent communication specification — TaskSpec format, parallel dispatch, result integration |
| `{SKILL_DIR}/reference/delegate-reference.md` | DELEGATE mode — AI-to-AI handoff, authority bounds, delegation chain |
| `{SKILL_DIR}/reference/micro-reference.md` | MICRO mode — zero-overhead execution for ≤10 nodes, automatic promotion |
| `{SKILL_DIR}/reference/session-learning-reference.md` | Session Learning — cross-session learning, pattern accumulation, strategy adaptation |

### Advanced Reference (as needed)

> **Future protocols** (vision, no current implementation): PGF-MCP (typed intent execution over MCP), PGF-A2A (typed subtree handoff between agents). Use the existing execution modes and `agent-protocol.md` TaskSpec for current AI-to-AI communication needs.

### Persona Agents (discover/create mode)

Discovery Engine's 14 personas are independently defined as agent files in `{SKILL_DIR}/agents/`:

| Agent | Cognitive Style | Domain | Horizon |
|-------|----------------|--------|---------|
| `pgf-persona-p1.md` — Disruptive Engineer | creative | technology | long |
| `pgf-persona-p2.md` — Cold-eyed Investor | analytical | market | short |
| `pgf-persona-p3.md` — Regulatory Architect | critical | policy | long |
| `pgf-persona-p4.md` — Connecting Scientist | intuitive | science | long |
| `pgf-persona-p5.md` — Field Operator | analytical | technology | short |
| `pgf-persona-p6.md` — Future Sociologist | intuitive | society | long |
| `pgf-persona-p7.md` — Contrarian Critic | critical | market | short |
| `pgf-persona-p8.md` — Convergence Architect | creative | science_technology | long |
| `pgf-persona-p9.md` — Practical Agency Ethicist | critical | ethics | long |
| `pgf-persona-p10.md` — Embodied UX Anthropologist | intuitive | human_experience | short |
| `pgf-persona-p11.md` — Adversarial Robustness Analyst | critical | security | short |
| `pgf-persona-p12.md` — Regenerative Systems Ecologist | intuitive | ecology | long |
| `pgf-persona-p13.md` — Historical Cycle Analyst | analytical | history | long |
| `pgf-persona-p14.md` — Mechanism Designer | creative | economics | long |

---

## Execution Modes

PGF supports the following execution modes via `$ARGUMENTS`.

**Invocation examples:** `/PGF design MyProject`, `/PGF full-cycle ChatApp`, `/PGF loop start`, `/PGF discover`, `/PGF create`

| Mode | Trigger | Action |
|------|---------|--------|
| `design` | "design this", "structural design" | Gantree structure design + PPR detailing → generate DESIGN-{Name}.md |
| `design --analyze` | "analyze this", "structure analysis" | (sub-option of design) Reverse-engineer existing system into PGF → read code → extract Gantree + PPR |
| `plan` | "work planning", "WORKPLAN" | DESIGN → WORKPLAN conversion + POLICY configuration |
| `execute` | "execute this", "implement this" | Sequential node execution based on WORKPLAN |
| `full-cycle` | "run the whole thing", "full cycle" | Full process: design → plan → execute → verify. **Opt-in gate**: the `--with-review[=N]` flag inserts review right after design (max N revisions, default N=1) |
| `loop` | "loop", "auto-run" | Automatic or guided node traversal/execution via runtime-adapter WORKPLAN |
| `discover` | "discover this", "ideas" | IdeaFirst 7-stage × 14 personas → idea discovery |
| `create` | "create this", "autonomous creation" | **Full autonomous execution: discover → design → plan → execute → verify** |
| `micro` | "keep it simple", "quickly" | Zero-overhead execution for ≤10 nodes — bypass WORKPLAN |
| `review` | "review this", "do a review" | Iterative review & improvement — closely review, revise, and re-verify existing artifacts repeatedly |
| `evolve` | "evolve this", "self-improve" | Self-evolution cycle — repeatedly discover capability gaps, design, implement, verify, and record |
| `delegate` | "delegate this", "hand this off" | AI-to-AI task handoff with PG TaskSpec, authority bounds, delegation chain |

**$ARGUMENTS parsing rules:**
- `$ARGUMENTS[0]`: mode keyword
- `$ARGUMENTS[1:]`: project name or target description
- No mode keyword → infer from context (e.g., presence of files in `.pgf/` directory)
- Project name only → defaults to `design` mode

### File Path Rules

```text
<project-root>/
    .pgf/
        DESIGN-{Name}.md          # System design (Gantree + PPR)
        WORKPLAN-{Name}.md        # Executable work plan
        status-{Name}.json        # Execution state tracking
```

`{Name}` = CamelCase project/task name. Multiple tasks can coexist in the same `.pgf/`.

### Progress Reporting

```text
[PGF] ✓ NodeName (done) | 3/12 nodes done | next: NextNode
[PGF] ✗ NodeName (blocked) | blocker: reason | skip → NextNode
```

---

## Integrated Execution Process

> The Steps below are **independent modes, not a sequential process**. Run only what is needed according to user instructions or the PGF mode. Only the full-cycle/create modes chain multiple Steps sequentially.

### Step 1: design — Gantree Structure Design

Top-Down BFS hierarchical decomposition → down to atomic nodes. Reference: **PG skill** (Gantree/PPR canonical) + this SKILL.md "PGF Notation Extensions" section for PGF-specific status codes.

**Completion criteria:** (1) All leaves = atomic nodes (2) PPR def written for complex nodes (3) No circular @dep (4) Checklist passed

### Step 2: plan — WORKPLAN Generation

DESIGN-{Name}.md → WORKPLAN-{Name}.md conversion. Reference: `workplan-reference.md §2`

### Step 3: execute — Sequential Node Execution

Node execution based on WORKPLAN-{Name}.md. For `[parallel]` nodes, use the current runtime's parallel subagent/worktree capability when available; otherwise execute sequentially while preserving dependency order. Reference: `workplan-reference.md §4`

### Step 4: verify — Cross-Verification

Details: `{SKILL_DIR}/reference/verify-reference.md`

3-perspective verification:
1. **Acceptance Criteria** — Re-check acceptance_criteria from DESIGN PPR (Lightweight: `# criteria:` inline)
2. **Code Quality** — runtime review/simplify capability or direct inspection, verifying reuse/quality/efficiency of changed code
3. **Architecture** — Compare DESIGN Gantree ↔ actual implementation structure (Lightweight: skip)

Result: `passed` → complete / `rework` → rollback target node + re-execute subtree / `blocked` → report to user.
Rework iterations are allowed up to `POLICY.max_verify_cycles`.

### full-cycle

Details: `{SKILL_DIR}/reference/cycle-reference.md` (covers both `full-cycle` and `create` modes)

Automatically execute design → plan → execute → verify as one continuous process. On rework during verify, roll back only the affected subtree and re-execute (up to `POLICY.max_verify_cycles` times). On session interruption, resume from the last Phase recorded in WORKPLAN/status JSON.

**Phase transition conditions:**

| Transition | Condition | On failure |
|------------|-----------|------------|
| discover → design | `auto_select_idea()` succeeds (**create mode only**) | 0 votes → abort |
| design → plan | All 4 completion criteria met | continue design |
| plan → execute | WORKPLAN + status JSON generated | report error |
| execute → verify | All nodes terminal | continue execute |
| verify → complete | passed | rework or report |

**Opt-in design review (`--with-review[=N]`)**

The default full cycle is not changed. A review gate is inserted between design → plan only when the user explicitly passes the `--with-review` flag.

| Invocation | Behavior |
|---|---|
| `/PGF full-cycle X` | Default behavior (no review) |
| `/PGF full-cycle X --with-review` | Insert one review (default N=1) |
| `/PGF full-cycle X --with-review=3` | Up to 3 review-revise iterations |
| `/PGF create X --with-review=2` | The same flag applies to create mode |

**Review gate behavior** (see `reference/design-review-reference.md`):
1. Right after design completes, run a multi-perspective SubAgent review (PG/PGF notation, security, protocol, architecture)
2. Classify results: `Critical=0, High≤2` → proceed to plan. Otherwise → revise DESIGN and re-review
3. Revision count ≤ N. When N is exceeded, report remaining issues + proceed to plan upon user approval (not a hard block)
4. Add only `review_iterations` and `unresolved_issues` to the status JSON — existing keys unchanged

**Skip rules** (auto-skipped because forcing it on Level 1/Micro is excessive):
- Level 1 (≤3 nodes) → ignore the flag, skip review
- `micro` mode → ignore the flag
- Level 2 and above → apply the flag

### Step 5: loop — Runtime-Adapter Auto-Execution

Details: `{SKILL_DIR}/loop/loop-reference.md`

| Command | Action |
|---------|--------|
| `/PGF loop start` | Initialize loop + execute first node |
| `/PGF loop cancel` | Cancel active loop |
| `/PGF loop status` | Report progress status |

On `/PGF loop start` or natural-language equivalent: (1) Verify WORKPLAN exists (2) initialize `.pgf/runtime/pgf-loop-state.json` (3) Determine mode (DESIGN exists → Standard / absent → Lightweight) (4) Select first node + load execution spec (5) Begin implementation. Afterwards, a runtime adapter continues the next node automatically when supported, or emits the next-node prompt for manual/agent continuation.

**Lightweight mode**: Loop execution with WORKPLAN only, without DESIGN. `#` inline comments under WORKPLAN nodes serve as PPR substitutes. Suitable for simple tasks, documentation, refactoring, etc.

### Step 6: discover — IdeaFirst Persona Multi-Agent Discovery

Details: `{SKILL_DIR}/discovery/discovery-reference.md`

| Command | Action |
|---------|--------|
| `/PGF discover` | Execute all 7 stages |
| `/PGF discover --from-step N` | Restart from stage N |
| `/PGF discover --personas N` | Use N personas |

Invoke 14 `{SKILL_DIR}/agents/pgf-persona-p*.md` personas in parallel when the runtime supports subagents. If not, simulate personas sequentially in the current runtime. Model hints inside persona files are advisory only. Integrate results from each stage → save to `.pgf/discovery/{step}.md`. HAO principle: do not enforce output format, preserve originals unedited.

### Step 7: create — Autonomous Creation Cycle

Details: `{SKILL_DIR}/reference/cycle-reference.md` (unified spec — `create` is the 5-phase autonomous variant)

| Command | Action |
|---------|--------|
| `/PGF create` | 5-Phase autonomous execution (DISCOVER→DESIGN→PLAN→EXECUTE→VERIFY) |
| `/PGF create --skip-discover` | Start from design using existing final_idea.md |

Fully autonomous execution without user approval. STEP 7 is replaced by `auto_select_idea` (vote-based automatic selection).

### Step 8: micro — Zero-Overhead Small Task Execution

Details: `{SKILL_DIR}/reference/micro-reference.md`

| Command | Action |
|---------|--------|
| `/PGF micro "task description"` | Inline decomposition → serial execution → minimal verify |

Entry: nodes ≤ 10, depth ≤ 3, no external deps, ≤ 30 min. Bypasses WORKPLAN/POLICY/status JSON. In-memory status only. Auto-promotes to full WORKPLAN if bounds exceeded.

### Step 9: delegate — AI-to-AI Task Handoff

Details: `{SKILL_DIR}/reference/delegate-reference.md`

Auto-triggered during execute when `should_delegate()` → True (capability gap, load balancing, parallel opportunity). Packages context into PG TaskSpec with AuthorityBounds → handshake → await result → validate → merge. Delegation chain tracks depth (max 3) and prevents cycles.

### Session Learning (cross-cutting — all modes)

Details: `{SKILL_DIR}/reference/session-learning-reference.md`

- **Session start**: Load `.pgf/patterns/` → adapt POLICY defaults
- **Session end**: Record `SessionOutcome` to `.pgf/sessions/{id}.outcome.json`
- **Every 10 sessions**: Re-accumulate patterns (successful strategies, common blockers)

---

## Scale Detection and Strategy

> PG defines 3 Levels (Level 1–3). PGF inherits these and adds Large/Multi-agent.

| Scale | Criteria | Strategy |
|-------|----------|----------|
| **Level 1** | nodes ≤ 3 | Natural-language inline execution — no PG files |
| **Level 2** | nodes 4–10 | Gantree + `#` comments — optional files |
| **Level 3** | nodes 11–30 | Full DESIGN + WORKPLAN + status JSON |
| **Large** | nodes > 30 or `(decomposed)` | Module separation + runtime-supported context compaction/checkpointing |
| **Multi-agent** | `[parallel]` with specialized tasks | `delegate` mode — AI-to-AI handoff |

> **Progressive Formalization**: Level determination is automatic. Natural-language input → AI evaluates complexity → selects the appropriate Level. State is preserved on promotion during execution.

## Execution Rules

1. Parse Gantree → determine hierarchy via indentation
2. Status codes → decide execute/skip
3. `@dep:` → determine execution order
4. `[parallel]` → concurrent processing
5. PPR `def` present → interpret and execute / `AI_` inline → execute directly / no PPR → recurse into children
6. Atomicity judgment → 15-minute rule
7. Failure → Failure Strategy + AI Redesign Authority
8. **Agent dispatch → PG TaskSpec** — when dispatching an agent, use the PG TaskSpec format from `agent-protocol.md` instead of natural language. Pass input/output types, acceptance_criteria, and failure_strategy in structured form
9. **Session start → load patterns** — load past patterns from `.pgf/patterns/` → auto-adapt POLICY
10. **Session end → record outcome** — automatically record SessionOutcome to `.pgf/sessions/{id}.outcome.json`

## Runtime Integration

| Capability | Runtime-neutral rule |
|-------|-------------|
| Parallel execution | Execute independent nodes within `[parallel]` blocks using available subagents, workers, worktrees, or sequential fallback |
| Code quality review | During verify, run the runtime's review/simplification tool if available; otherwise perform direct code review against acceptance criteria |
| Context compaction/checkpointing | For long runs, preserve WORKPLAN path, status JSON, and `.pgf/runtime/pgf-loop-state.json` before compaction or handoff |

---

## PGF Execution Checklist

> For the base Gantree/PPR authoring checklist, refer to the **PG skill**. Below are items specific to the PGF execution phase.

### Execution Phase

- [ ] Is every node's status in WORKPLAN-{Name}.md terminal (`done`/`blocked`)?
- [ ] Does the summary in status-{Name}.json match the WORKPLAN?
- [ ] Is a blocker reason recorded for each `(blocked)` node?

### Verify Phase (3-Perspective)

- [ ] **Acceptance**: Re-verify the `acceptance_criteria` of each completed node (Lightweight: `# criteria:` inline)
- [ ] **Code Quality**: Verify reuse/quality/efficiency of the changed code via the runtime's review/simplify tool or direct inspection
- [ ] **Architecture**: Compare DESIGN Gantree ↔ actual implementation structure (Lightweight: skip)
- [ ] Record Verdict: `passed` / `rework` / `blocked`
- [ ] On Rework: roll back the target node + children → re-execute → re-verify (within `max_verify_cycles`)
- [ ] On Blocked: document the reason + report to the user

### full-cycle Mode

- [ ] All 4 completion criteria met before the design → plan transition
- [ ] Confirm WORKPLAN + status JSON exist at the plan → execute transition
- [ ] Confirm all nodes are terminal at the execute → verify transition
- [ ] On verify rework, roll back only the target subtree (no full reset)
- [ ] On exceeding `max_verify_cycles`, preserve artifacts + report abort
- [ ] On session interruption, confirm resumability from the WORKPLAN/status JSON

### Discovery Archive

- [ ] Run the `archive-discovery` script after execution completes
- [ ] Is the archive directory separated by date (YYYY-MM-DD)?
- [ ] `create` mode: auto-archive right after Phase 1 completes

### Delegation & Micro Extensions

- [ ] Is the `AI_make_` causative pattern used where needed?
- [ ] Was `micro` mode considered for ≤10-node tasks?
- [ ] Was the PG TaskSpec format used when dispatching parallel agents?
- [ ] Were AuthorityBounds (can_create/can_modify/forbidden) specified on `delegate`?
- [ ] Was delegation chain depth ≤ 3 confirmed?
- [ ] Was SessionOutcome recorded on session completion?
- [ ] Were the `(delegated)`/`(awaiting-return)`/`(returned)` statuses used appropriately?
