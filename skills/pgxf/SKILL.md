---
name: pgxf
description: "PGXF (PPR/Gantree IndeX Framework) — file-based index system for ultra-large PG structures. Enables lazy-load subtree access, O(1) node lookup, cross-file status aggregation, and automatic sync with (decomposed) splits. Triggers: index, large-scale design, find node, structure overview, status aggregate, pgxf, index, large-scale, node lookup, status aggregate, grasp full structure, where is it, node search. Use this skill whenever a PG/PGF project exceeds 30 nodes, spans multiple files, uses (decomposed) splits, or when the user needs to locate/navigate/aggregate across a large PG tree without loading everything into context."
user-invocable: true
argument-hint: "build|lookup|sync|status|prune [project-name|node-name]"
---

# PGXF — PPR/Gantree IndeX Framework v1.0

> If PG is the language and PGF is the library, then **PGXF is the file-system index**.
> It accesses only the nodes you need with precision, without loading the entire tree into the context window.

## Background: Why PGXF Is Needed

As a PG/PGF project grows, it reaches the following limits:

| Limit | Symptom | PGXF Solution |
|------|------|-----------|
| Context explosion | 50+ nodes → cannot load the entire tree | **Lazy Load** — load only the index, fetch subtrees on demand |
| Navigation cost | "Which file is this node in?" → full scan | **O(1) Lookup** — node name → file:line returned instantly |
| No status visibility | manually aggregating scattered status | **Aggregate** — overall done/total at the index level, instantly |
| Lost `(decomposed)` tracking | broken references to split trees | **Cross-ref** — automatically tracks decomposed links |

## PG-Based Dependencies

**PGXF is built on the PG (PPR/Gantree) notation and the PGF (Framework).**

- PG skill: Gantree node syntax, PPR syntax, `(decomposed)` rules
- PGF skill: DESIGN/WORKPLAN/status file formats, execution modes

PGXF adds an **index layer** on top of these. It does not redefine the PG/PGF syntax or rules.

---

## Quick Start

```bash
# 1. Build the project index
/pgxf build MyProject

# 2. Find a node
/pgxf lookup PaymentProcessor

# 3. Overview the full status
/pgxf status MyProject

# 4. Sync the index after source changes
/pgxf sync MyProject

# 5. Prune deleted nodes
/pgxf prune MyProject
```

---

## Core Concepts

### Index Entry (per-node index)

The smallest unit of PGXF. **One PG node = one Index Entry**.

```python
IndexEntry = {
    "node":        str,              # CamelCase node name (unique identifier)
    "status":      str,              # done | in-progress | designing | blocked | decomposed | ...
    "file":        str,              # containing file path (relative)
    "line":        int,              # starting line number within the file
    "depth":       int,              # tree depth (0 = root)
    "parent":      Optional[str],    # parent node name
    "children":    list[str],        # list of child node names
    "deps":        list[str],        # @dep: dependencies
    "has_ppr":     bool,             # whether a PPR def block exists
    "ppr_file":    Optional[str],    # PPR definition file (if in a separate file)
    "ppr_line":    Optional[int],    # PPR starting line
    "decomposed_to": Optional[str],  # split tree file when (decomposed)
    "tags":        list[str],        # list of #tags
}
```

### Index File (project index)

```
.pgxf/
    INDEX-{Name}.json          # project index (node registry)
    MANIFEST.json              # multi-project manifest (optional)
```

### Manifest (multi-project)

When multiple PGF projects coexist in one workspace, the MANIFEST provides an overview of all of them.

```json
{
  "workspace": "SeAAI",
  "projects": [
    {
      "name": "AionEngine",
      "index": ".pgxf/INDEX-AionEngine.json",
      "design": ".pgf/DESIGN-AionEngine.md",
      "total_nodes": 47,
      "done": 31,
      "status_summary": {"done": 31, "in-progress": 8, "designing": 5, "blocked": 3}
    },
    {
      "name": "PGTPProtocol",
      "index": ".pgxf/INDEX-PGTPProtocol.json",
      "design": ".pgf/DESIGN-PGTPProtocol.md",
      "total_nodes": 23,
      "done": 23,
      "status_summary": {"done": 23}
    }
  ],
  "global_summary": {"total": 70, "done": 54, "in-progress": 8, "designing": 5, "blocked": 3},
  "updated_at": "2026-04-11T09:00:00"
}
```

---

## Execution Modes

| Mode | Trigger | Action |
|------|---------|--------|
| `build` | "index build", "build index" | scan PGF sources → generate INDEX-{Name}.json |
| `lookup` | "find node", "where is it" | node name → file:line, PPR location, status |
| `sync` | "sync", "refresh index" | detect source changes → incremental index update |
| `status` | "status overview", "overall status" | index-based status aggregation + tree summary output |
| `prune` | "prune", "remove deleted nodes" | remove nodes that disappeared from the source from the index |

### $ARGUMENTS Parsing

- `$ARGUMENTS[0]`: mode keyword
- `$ARGUMENTS[1:]`: project name or node name
- e.g.: `/pgxf build SeAAI`, `/pgxf lookup PaymentProcessor`, `/pgxf status`

---

## Build Process

### Input Sources

```python
def pgxf_build(project_name: str) -> Index:
    """Scan the PGF source files and generate the index."""

    # 1. Collect sources: DESIGN, WORKPLAN files in the .pgf/ directory
    sources = scan_pgf_dir(".pgf/", project_name)
    # → ["DESIGN-MyProject.md", "WORKPLAN-MyProject.md", ...]

    # 2. Gantree parsing: extract nodes from each file's ## Gantree section
    gantree_nodes = []
    for src in sources:
        nodes = extract_gantree_nodes(src)
        # each node: name, status, depth, parent, children, deps, tags, line_number
        gantree_nodes.extend(nodes)

    # 3. PPR mapping: link def blocks in the ## PPR section to nodes
    for node in gantree_nodes:
        ppr = find_ppr_def(sources, node.name)
        if ppr:
            node.has_ppr = True
            node.ppr_file = ppr.file
            node.ppr_line = ppr.line

    # 4. (decomposed) tracking: link references to split tree files
    for node in gantree_nodes:
        if node.status == "decomposed":
            node.decomposed_to = resolve_decomposed_target(node, sources)

    # 5. Build + save the index
    index = build_index(project_name, gantree_nodes)
    save_json(f".pgxf/INDEX-{project_name}.json", index)
    return index
```

### Gantree Node Extraction Rules

Indentation-based parsing — applies PG's 4-space rule:

```
RootNode // desc (status) @v:1.0          → depth=0, parent=None
    ChildA // desc (done)                 → depth=1, parent=RootNode
        GrandchildA1 // desc (done)       → depth=2, parent=ChildA
    ChildB // desc (designing) @dep:ChildA → depth=1, parent=RootNode, deps=[ChildA]
```

**Node name uniqueness rule**: duplicate node names within the same project are forbidden. When a duplicate is found, build emits a warning + shows file:line.

### PPR def Block Matching

```python
# Node name → PPR function name matching rule
# CamelCase → snake_case conversion
# PaymentProcessor → payment_processor
# AI_ExtractKeywords → ai_extract_keywords (inline — matching not required)

def match_node_to_ppr(node_name: str, def_name: str) -> bool:
    return camel_to_snake(node_name) == def_name
```

---

## Lookup Process

```python
def pgxf_lookup(node_name: str, project: Optional[str] = None) -> LookupResult:
    """Instantly return location, status, PPR, and dependencies by node name."""

    # When no project is specified → search across all in the MANIFEST
    if not project:
        project = find_project_containing(node_name)

    index = load_index(project)
    entry = index.nodes[node_name]

    return LookupResult(
        node=entry.node,
        status=entry.status,
        location=f"{entry.file}:{entry.line}",
        ppr_location=f"{entry.ppr_file}:{entry.ppr_line}" if entry.has_ppr else None,
        parent=entry.parent,
        children=entry.children,
        deps=entry.deps,
        decomposed_to=entry.decomposed_to,
    )
```

### Lookup Output Example

```
[PGXF] PaymentProcessor
  📍 .pgf/DESIGN-OrderSystem.md:45
  📊 status: in-progress
  🔗 PPR: .pgf/DESIGN-OrderSystem.md:112  (def payment_processor)
  ⬆ parent: OrderSystem
  ⬇ children: ValidateCard, ChargeCard, SendReceipt
  ➡ deps: UserAuth, Database
  📦 decomposed: —
```

---

## Sync Process

```python
def pgxf_sync(project_name: str) -> SyncResult:
    """Detect source changes and incrementally update the index."""

    old_index = load_index(project_name)
    new_index = pgxf_build(project_name)  # full rebuild

    diff = compute_diff(old_index, new_index)
    # diff.added:    newly added nodes
    # diff.removed:  deleted nodes
    # diff.modified: nodes with changed status/location/PPR

    save_json(f".pgxf/INDEX-{project_name}.json", new_index)

    return SyncResult(
        added=len(diff.added),
        removed=len(diff.removed),
        modified=len(diff.modified),
        details=diff,
    )
```

### Sync Output Example

```
[PGXF] sync OrderSystem
  ✚ added: RefundFlow, RefundValidator (2)
  ✎ modified: ChargeCard (designing → in-progress), SendReceipt (designing → done) (2)
  ✖ removed: LegacyGateway (1)
  📊 total: 15 nodes | done: 9 | in-progress: 3 | designing: 2 | blocked: 1
```

---

## Status Process

```python
def pgxf_status(project: Optional[str] = None) -> StatusReport:
    """Index-based status aggregation. When no project is specified, the entire MANIFEST."""

    if project:
        index = load_index(project)
        return aggregate_single(index)
    else:
        manifest = load_manifest()
        return aggregate_all(manifest)
```

### Status Output Example (single project)

```
[PGXF] OrderSystem status
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  done         ████████████░░░░  9/15 (60%)
  in-progress  ████░░░░░░░░░░░░  3/15 (20%)
  designing    ██░░░░░░░░░░░░░░  2/15 (13%)
  blocked      █░░░░░░░░░░░░░░░  1/15 (7%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🔴 blocked: PaymentGateway (blocker: external API)
  🟡 decomposed: ShippingFlow → .pgf/DESIGN-ShippingFlow.md
  📁 files: 3 (DESIGN-OrderSystem.md, DESIGN-ShippingFlow.md, WORKPLAN-OrderSystem.md)
```

### Status Output Example (multi-project — MANIFEST)

```
[PGXF] workspace status
  ┌─────────────────┬───────┬──────┬────────┬──────────┬─────────┐
  │ Project         │ Total │ Done │ In-Prg │ Designing│ Blocked │
  ├─────────────────┼───────┼──────┼────────┼──────────┼─────────┤
  │ AionEngine      │    47 │   31 │      8 │        5 │       3 │
  │ PGTPProtocol    │    23 │   23 │      0 │        0 │       0 │
  │ SeAAIHub        │    18 │   12 │      4 │        2 │       0 │
  ├─────────────────┼───────┼──────┼────────┼──────────┼─────────┤
  │ TOTAL           │    88 │   66 │     12 │        7 │       3 │
  └─────────────────┴───────┴──────┴────────┴──────────┴─────────┘
  global: 75% complete
```

---

## Prune Process

```python
def pgxf_prune(project_name: str) -> PruneResult:
    """Remove nodes that have disappeared from the source from the index."""

    index = load_index(project_name)
    current_nodes = scan_current_nodes(project_name)
    orphans = [n for n in index.nodes if n not in current_nodes]

    for orphan in orphans:
        del index.nodes[orphan]

    save_json(f".pgxf/INDEX-{project_name}.json", index)
    return PruneResult(removed=orphans)
```

---

## (decomposed) Automatic Tracking

The core value of PGXF: the index automatically cross-references `(decomposed)` nodes.

### Scenario

```
# DESIGN-OrderSystem.md
OrderSystem // order system (in-progress)
    PaymentFlow // payment flow — see DESIGN-PaymentFlow.md (decomposed)
    ShippingFlow // shipping flow (designing)

# DESIGN-PaymentFlow.md (split tree)
PaymentFlow // payment flow details (in-progress)
    ValidateCard // card validation (done)
    ChargeCard // card charge (in-progress) @dep:ValidateCard
    SendReceipt // receipt dispatch (designing) @dep:ChargeCard
```

### PGXF build Result

```json
{
  "project": "OrderSystem",
  "files": [
    ".pgf/DESIGN-OrderSystem.md",
    ".pgf/DESIGN-PaymentFlow.md"
  ],
  "nodes": {
    "OrderSystem": {
      "node": "OrderSystem", "status": "in-progress",
      "file": ".pgf/DESIGN-OrderSystem.md", "line": 3,
      "depth": 0, "parent": null,
      "children": ["PaymentFlow", "ShippingFlow"],
      "deps": [], "has_ppr": false,
      "decomposed_to": null, "tags": []
    },
    "PaymentFlow": {
      "node": "PaymentFlow", "status": "decomposed",
      "file": ".pgf/DESIGN-OrderSystem.md", "line": 4,
      "depth": 1, "parent": "OrderSystem",
      "children": ["ValidateCard", "ChargeCard", "SendReceipt"],
      "deps": [], "has_ppr": false,
      "decomposed_to": ".pgf/DESIGN-PaymentFlow.md",
      "tags": []
    },
    "ValidateCard": {
      "node": "ValidateCard", "status": "done",
      "file": ".pgf/DESIGN-PaymentFlow.md", "line": 4,
      "depth": 2, "parent": "PaymentFlow",
      "children": [], "deps": [], "has_ppr": false,
      "decomposed_to": null, "tags": []
    }
  },
  "summary": {"total": 6, "done": 1, "in-progress": 2, "designing": 1, "decomposed": 1, "blocked": 0},
  "updated_at": "2026-04-11T09:00:00"
}
```

**Key point**: `PaymentFlow`'s `children` include the children from the split file. The index reconstructs the tree across file boundaries.

---

## Lazy Load Pattern

The standard pattern an AI uses to leverage PGXF when working on large projects:

```python
def work_with_large_project(task: str, project: str):
    """Perform a specific task in a large project — without loading everything."""

    # Step 1: load only the index (lightweight)
    index = pgxf_load_index(project)

    # Step 2: identify the target nodes for the task
    target_nodes = AI_identify_relevant_nodes(task, index.summary)

    # Step 3: load only the sources for those nodes
    for node_name in target_nodes:
        entry = index.nodes[node_name]
        source = load_file_range(entry.file, entry.line, estimate_end(entry))
        if entry.has_ppr:
            ppr = load_file_range(entry.ppr_file, entry.ppr_line, estimate_ppr_end(entry))

    # Step 4: perform the task, then sync the index
    execute_task(task, loaded_sources)
    pgxf_sync(project)
```

---

## File Path Rules

```text
<project-root>/
    .pgf/                              # PGF sources (existing)
        DESIGN-{Name}.md
        WORKPLAN-{Name}.md
        status-{Name}.json
    .pgxf/                             # PGXF index (new)
        INDEX-{Name}.json              # per-project index
        MANIFEST.json                  # workspace manifest (optional)
```

- `.pgxf/` sits at the **same level** as `.pgf/`
- The INDEX file is a **derived artifact**, not a source — it can be rebuilt at any time
- The MANIFEST is a **meta-index** that aggregates multiple INDEXes

---

## PGF Integration

| PGF Event | PGXF Action |
|------------|-----------|
| `pgf design` completes | `pgxf build` auto-triggered |
| `pgf execute` node status change | `pgxf sync` recommended (manual) |
| `pgf loop` starts | load the index to grasp the full structure before execution |
| `pgf full-cycle` completes | `pgxf sync` + `pgxf status` |
| `(decomposed)` split occurs | auto-tracked on the next `pgxf sync` |

---

## Execution Rules

1. `/pgxf build` — full scan of DESIGN/WORKPLAN files in `.pgf/` → generate INDEX
2. `/pgxf lookup NodeName` — O(1) search in the INDEX, fall back to MANIFEST search if not found
3. `/pgxf sync` — full rebuild followed by a diff report
4. `/pgxf status` — aggregated output based on INDEX/MANIFEST
5. `/pgxf prune` — remove orphan nodes not present in the source
6. When the project name is omitted → auto-detect from `.pgf/` in the current directory
7. When the `.pgxf/` directory does not exist → create it automatically

---

## Full INDEX-{Name}.json Schema

Detailed schema and per-field rules: `{SKILL_DIR}/references/pgxf-format.md`

> **Path convention**: `{SKILL_DIR}` is a runtime-neutral placeholder pointing to this skill's root directory (where SKILL.md resides). Each runtime substitutes it with the local install path. Do not hardcode absolute paths or runtime-dependent env vars (same rule as the PGF SKILL).

---

## Checklist

### Build Verification

- [ ] Were all DESIGN/WORKPLAN files scanned?
- [ ] Are there no duplicate node names?
- [ ] Do the split files of `(decomposed)` nodes exist?
- [ ] Were PPR def blocks mapped to the correct nodes?
- [ ] Are parent-children relationships bidirectionally consistent?

### Sync Verification

- [ ] Do the added/removed/modified counts match the actual changes?
- [ ] Does the summary aggregation match the nodes' statuses?
- [ ] Does the `decomposed_to` reference point to a valid file?

### Operational Rules

- [ ] The INDEX file is a derived artifact — whether to include it in git is a project policy (recommended: .gitignore)
- [ ] The MANIFEST is optional — unnecessary for a single project
- [ ] For 50+ node projects, always verify sync before lookup
