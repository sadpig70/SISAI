# pgf-loop Execution Engine Specification

## 1. Overview

pgf-loop is a self-contained loop engine that traverses and executes nodes in WORKPLAN-{Name}.md through a runtime adapter. The core state and selection logic are runtime-neutral; automatic reinjection is available only when the current runtime provides a hook, heartbeat, scheduler, or equivalent continuation mechanism.

### Execution Modes

| Mode | DESIGN-{Name}.md | Execution Spec Source | Purpose |
|------|-----------|---------------|------|
| **Standard** | Required | PPR def blocks in DESIGN-{Name}.md | Complex system implementation |
| **Lightweight** | Not required | Inline `#` comments in WORKPLAN-{Name}.md | Simple tasks, documentation, refactoring |

In Lightweight mode, `#` comments written under WORKPLAN nodes serve as the PPR equivalent.

### Core Principle

```
AI runtime completes current node work → continuation trigger fires
    ↓
Runtime adapter (for example stop-hook.py) reads loop state
    ↓
Selects next executable node from status-{Name}.json
    ↓
Extracts execution spec (Strategy 1: DESIGN PPR → Strategy 2: WORKPLAN inline)
    ↓
Constructs dynamic prompt → reinjects/returns it to the AI runtime → executes next node
    ↓
... repeats until all nodes complete ...
```

---

## 2. File Structure

### Standard Mode

```
<project-root>/
    .pgf/
        DESIGN-{Name}.md              ← System design (Gantree + PPR)
        WORKPLAN-{Name}.md            ← Execution plan
        status-{Name}.json             ← Per-node execution status
        runtime/
            pgf-loop-state.json        ← Canonical loop runtime state (exists only when active)
    <runtime-adapter-state>/           ← Optional mirror/config for a specific host runtime
```

### Lightweight Mode

```
<project-root>/
    .pgf/
        WORKPLAN-{Name}.md            ← Execution plan + inline task specs
        status-{Name}.json             ← Per-node execution status
        runtime/
            pgf-loop-state.json        ← Canonical loop runtime state
    <runtime-adapter-state>/           ← Optional mirror/config for a specific host runtime
```

---

## 3. Commands

### `/PGF loop start`

Initializes the loop and starts executing the first node.

**Prerequisites**: `.pgf/WORKPLAN-{Name}.md` must exist. `.pgf/DESIGN-{Name}.md` is optional.

**Behavior**:
1. Creates `.pgf/runtime/pgf-loop-state.json` (state initialization + mode determination)
2. Registers or activates a runtime adapter when the host supports automatic continuation; otherwise prints the first next-node prompt for manual continuation
3. Checks `status-{Name}.json` — applies the following rules:
   - If already created by `plan` mode → use as-is (authoritative copy)
   - If missing → AI auto-generates from WORKPLAN-{Name}.md
   - If exists but inconsistent with WORKPLAN-{Name}.md → sync to WORKPLAN-{Name}.md
4. Selects first executable node → outputs prompt → AI runtime starts execution

**Automatic Mode Determination**:
- `--design PATH` specified + file exists → Standard mode
- `--design PATH` specified + file missing → warning output, falls back to Lightweight mode
- `--design` not specified → Lightweight mode

> **status-{Name}.json Creation Authority Rule**: `plan` mode's `convert_design_to_workplan()` is the primary creator. `loop start` is the fallback creator when missing. No conflict even if both run — `loop start` does not touch an existing file.

**Options**:
- `--max-iterations N`: Maximum iteration count (0 = unlimited, default)
- `--workplan PATH`: WORKPLAN path (default: `.pgf/WORKPLAN-{Name}.md`)
- `--design PATH`: DESIGN path (omit for Lightweight mode)

### `/PGF loop cancel`

Cancels the active loop.

**Behavior**:
1. Deletes `.pgf/runtime/pgf-loop-state.json`
2. Reports current iteration and last node

### `/PGF loop status`

Reports loop progress status.

**Behavior**:
1. Reads `pgf-loop-state.json`
2. Reads `status-{Name}.json`
3. Reports progress, current node, iteration, mode (standard/lightweight)

---

## 4. Runtime Adapter Protocol

The adapter protocol is intentionally small. A host runtime may implement it as a Stop Hook, heartbeat wakeup, scheduled job, MCP tool callback, or manual CLI command. `stop-hook.py` is one adapter implementation; it reads the canonical state file and emits the next-node directive.

### Input (stdin)

```json
{
    "session_id": "unique session ID",
    "transcript_path": "conversation transcript file path"
}
```

### Output (stdout)

**Loop continues** (execute next node):
```json
{
    "decision": "block",
    "reason": "next node execution prompt",
    "systemMessage": "[pgf-loop] iteration N | node: NodeName | done/total done"
}
```

**Loop terminates** (all nodes complete or error):
```
(exit 0 with no output)
```

---

## 5. Node Selection Algorithm (select_next_node)

```
1. If a node with "in-progress" status exists → return that node (retry incomplete)
2. Among nodes with "designing" status where all @dep: are "done" → return first in tree order
3. If no candidates → None (triggers loop termination)
```

---

## 6. Execution Spec Extraction (extract-ppr.py)

### Epigenetic PPR (v2.4)

Context-adaptive PPR execution. When pgf-loop activates a node, `extract-ppr` reads the node's PPR `def` block from `DESIGN-{Name}.md` and injects it into the runtime adapter prompt. The PPR (the "gene") is fixed in DESIGN, but its expression at runtime varies with the surrounding context — available tools, prior node outputs, and current session patterns — so the same PPR can yield different execution behavior across sessions. The name mirrors biological epigenetics: fixed gene, environment-dependent expression.

### 2-Stage Fallback Strategy

```
Strategy 1: Extract PPR def block from DESIGN-{Name}.md
    ├─ "### [PPR] NodeName" header → child ```python code block
    └─ "def snake_name(" pattern → corresponding code block
    ↓ (empty result)
Strategy 2: Extract inline # comments from WORKPLAN-{Name}.md
    ├─ Search for "NodeName // description (status)" line
    └─ Collect # comment lines with deeper indentation → return as task spec
    ↓ (empty result)
Atomic node prompt ("Read node description from WORKPLAN and implement directly")
```

### WORKPLAN Inline Task Spec Format

```
NodeName // node description (status)
    # task: work to perform
    # target: file path or module
    # output: result file
    # criteria: completion criteria
```

`#` comments are free-form. No enforced structure — sufficient as long as AI can understand the intent.

---

## 7. Prompt Construction Rules

Prompt constructed by stop-hook at each iteration:

### Standard Mode

```
[pgf-loop] Node Execution Directive

Project: {project}
Current node: {node_name}
Progress: {done}/{total} nodes done
WORKPLAN: {workplan_path}
DESIGN: {design_path}
status-{Name}.json: {status_path}

## PPR Implementation Spec for This Node
{ppr_block}

## Required Post-Completion Tasks
1. Change this node's status to (done) in WORKPLAN-{Name}.md
2. Update status-{Name}.json
3. Progress report
```

### Lightweight Mode

```
[pgf-loop] [Lightweight] Node Execution Directive

Project: {project}
Current node: {node_name}
Progress: {done}/{total} nodes done
WORKPLAN: {workplan_path}
status-{Name}.json: {status_path}

## Task Spec for This Node (WORKPLAN Inline)
{inline_spec}

## Required Post-Completion Tasks
...
```

---

## 8. Session Isolation

- `session_id` recorded in `pgf-loop-state.json`
- Runtime adapter compares input `session_id` at execution time when the host provides one
- On mismatch, loop is ignored (protects other sessions)

---

## 9. Termination Conditions

| Condition | Action |
|------|------|
| All nodes "done" or "blocked" (see POLICY.completion) | Normal termination |
| `max_iterations` reached | Forced termination |
| `pgf-loop-state.json` deleted (`/PGF loop cancel`) | Immediate termination |
| `status-{Name}.json` parse failure | Error termination + state file cleanup |

---

## 10. Error Recovery

### On Node Execution Failure
- AI runtime yields, stops, or returns without completing the node
- Runtime adapter detects the node is still "in-progress" in status-{Name}.json
- Reissues the same node directive (retry)
- retry_count tracked in pgf-loop-state.json
- When max_retry exhausted, POLICY.on_blocked policy applies

### On State File Corruption
- JSON parse failure → delete state file → terminate loop
- User can restart with `/PGF loop start`

---

## 11. Continuation Resilience

### Problem
Long-running pgf-loop sessions may trigger context window compaction, process restart, or runtime handoff. Without protection, the loop state (current node, iteration, progress) can be lost.

### Solution: Canonical State + Runtime Adapter Checkpoint

```
[Context full / session handoff] → continuation boundary
    ↓
[Runtime adapter checkpoint]
    Saves .pgf/runtime/pgf-loop-state.json → .pgf/runtime/pgf-loop-state.backup.json
    Logs continuation event when supported
    ↓
[Session resumes]
    ↓
[Runtime adapter restore]
    Restores state from backup
    Outputs recovery info to stdout or runtime context
    ↓
[Loop adapter continues normally]
```

### Scripts
- `post-compact-hook.py` — Compatibility adapter stub for runtimes that expose post-compaction hooks
- `restore-pgf-state.py` — Compatibility adapter stub for runtimes that expose session restore hooks

### Adapter Configuration Example

```json
{
  "runtime_adapter": {
    "state_file": ".pgf/runtime/pgf-loop-state.json",
    "post_compact_command": "python \"{SKILL_DIR}/loop/post-compact-hook.py\"",
    "restore_command": "python \"{SKILL_DIR}/loop/restore-pgf-state.py\""
  }
}
```

Note: restore support is optional. A runtime without hooks can still continue by reading `.pgf/runtime/pgf-loop-state.json` and asking the AI runtime to execute the next-node directive.
