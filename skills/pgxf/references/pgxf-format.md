# PGXF Index Format Specification

> Detailed schema and per-field rules for INDEX-{Name}.json and MANIFEST.json.

---

## 1. Full INDEX-{Name}.json Schema

```json
{
  "pgxf_version": "1.0",
  "project": "ProjectName",
  "files": [
    ".pgf/DESIGN-ProjectName.md",
    ".pgf/DESIGN-SubModule.md",
    ".pgf/WORKPLAN-ProjectName.md"
  ],
  "nodes": {
    "NodeName": {
      "node":           "NodeName",
      "status":         "in-progress",
      "file":           ".pgf/DESIGN-ProjectName.md",
      "line":           12,
      "depth":          1,
      "parent":         "RootNode",
      "children":       ["ChildA", "ChildB"],
      "deps":           ["OtherNode"],
      "has_ppr":        true,
      "ppr_file":       ".pgf/DESIGN-ProjectName.md",
      "ppr_line":       87,
      "decomposed_to":  null,
      "tags":           ["#core"]
    }
  },
  "summary": {
    "total":        24,
    "done":         12,
    "in-progress":  5,
    "designing":    4,
    "blocked":      2,
    "decomposed":   1,
    "needs-verify": 0,
    "delegated":    0,
    "awaiting-return": 0,
    "returned":     0
  },
  "decomposed_links": [
    {
      "source_node": "PaymentFlow",
      "source_file": ".pgf/DESIGN-OrderSystem.md",
      "target_file": ".pgf/DESIGN-PaymentFlow.md",
      "target_root": "PaymentFlow"
    }
  ],
  "built_at":   "2026-04-11T09:00:00",
  "updated_at": "2026-04-11T10:30:00"
}
```

---

## 2. Per-Field Rules

### Project Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pgxf_version` | str | ✅ | PGXF schema version ("1.0") |
| `project` | str | ✅ | CamelCase project name |
| `files` | list[str] | ✅ | list of scanned source files (relative paths) |
| `nodes` | dict[str, IndexEntry] | ✅ | node name → IndexEntry mapping |
| `summary` | dict[str, int] | ✅ | aggregation by status |
| `decomposed_links` | list[DecomposedLink] | ✅ | list of (decomposed) cross-references |
| `built_at` | str (ISO8601) | ✅ | initial build timestamp |
| `updated_at` | str (ISO8601) | ✅ | last update timestamp |

### IndexEntry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node` | str | ✅ | CamelCase node identifier (unique within the project) |
| `status` | str | ✅ | PG/PGF status code |
| `file` | str | ✅ | containing file relative path |
| `line` | int | ✅ | starting line within the file (1-based) |
| `depth` | int | ✅ | tree depth (root = 0) |
| `parent` | str \| null | ✅ | parent node name (null for root) |
| `children` | list[str] | ✅ | direct child node names (empty list allowed) |
| `deps` | list[str] | ✅ | @dep: dependency list (empty list allowed) |
| `has_ppr` | bool | ✅ | whether a PPR def block exists |
| `ppr_file` | str \| null | ❌ | file containing the PPR def (required when has_ppr=true) |
| `ppr_line` | int \| null | ❌ | PPR def starting line (required when has_ppr=true) |
| `decomposed_to` | str \| null | ❌ | split tree file path (required when status=decomposed) |
| `tags` | list[str] | ✅ | list of #tags (empty list allowed) |

### DecomposedLink Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_node` | str | ✅ | original node name marked (decomposed) |
| `source_file` | str | ✅ | original file path |
| `target_file` | str | ✅ | split tree file path |
| `target_root` | str | ✅ | root node name of the split tree |

---

## 3. Full MANIFEST.json Schema

```json
{
  "pgxf_version": "1.0",
  "workspace": "WorkspaceName",
  "projects": [
    {
      "name":           "ProjectName",
      "index":          ".pgxf/INDEX-ProjectName.json",
      "design":         ".pgf/DESIGN-ProjectName.md",
      "workplan":       ".pgf/WORKPLAN-ProjectName.md",
      "total_nodes":    24,
      "done":           12,
      "completion_pct": 50.0,
      "status_summary": {
        "done": 12, "in-progress": 5, "designing": 4,
        "blocked": 2, "decomposed": 1
      },
      "blocked_nodes":  ["PaymentGateway"],
      "decomposed_files": [".pgf/DESIGN-PaymentFlow.md"]
    }
  ],
  "global_summary": {
    "total_projects":  3,
    "total_nodes":     88,
    "done":            66,
    "completion_pct":  75.0,
    "status_summary": {
      "done": 66, "in-progress": 12, "designing": 7, "blocked": 3
    }
  },
  "updated_at": "2026-04-11T09:00:00"
}
```

### MANIFEST Project Entry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | ✅ | project name |
| `index` | str | ✅ | INDEX file path |
| `design` | str \| null | ✅ | DESIGN file path (null if absent) |
| `workplan` | str \| null | ❌ | WORKPLAN file path |
| `total_nodes` | int | ✅ | total number of nodes |
| `done` | int | ✅ | number of completed nodes |
| `completion_pct` | float | ✅ | completion rate (1 decimal place) |
| `status_summary` | dict[str, int] | ✅ | aggregation by status |
| `blocked_nodes` | list[str] | ❌ | list of blocked nodes (for quick reference) |
| `decomposed_files` | list[str] | ❌ | list of decomposed split files |

---

## 4. Node Name Uniqueness Rule

Within the project scope, node names must be unique.

### Handling Duplicates

```
[PGXF] ⚠ DUPLICATE NODE: "ValidateCard"
  → .pgf/DESIGN-OrderSystem.md:12
  → .pgf/DESIGN-PaymentFlow.md:4
  Action: adopt the first, mark the second with a warning
  Fix: recommend splitting node names into OrderValidateCard / PaymentValidateCard
```

### (decomposed) Exception

A `(decomposed)` node has the same name in both the original file and the split file. This is **not** a duplicate — PGXF links them via `decomposed_links` and uses the original's entry as the representative.

---

## 5. PPR Matching Rules

### CamelCase → snake_case Conversion

```
PaymentProcessor    → payment_processor
AI_ExtractKeywords  → ai_extract_keywords  (inline — matching not required)
ValidateCard        → validate_card
SeAAIHub           → se_aai_hub
```

### Matching Priority

1. **Exact match**: `def payment_processor(` ← `PaymentProcessor`
2. **Prefix match**: `def payment_processor_v2(` ← `PaymentProcessor` (emits a warning)
3. **Match failure**: `has_ppr = false`

### PPR Location Search Scope

1. The `## PPR` section of the same file (priority)
2. Other DESIGN files in the same project
3. The split `(decomposed)` file

---

## 6. status Value Mapping

PG's 6 base + PGF's 3 extensions = 9 statuses total:

| Status | Origin | summary key |
|--------|--------|------------|
| `done` | PG | `done` |
| `in-progress` | PG | `in-progress` |
| `designing` | PG | `designing` |
| `blocked` | PG | `blocked` |
| `decomposed` | PG | `decomposed` |
| `needs-verify` | PG | `needs-verify` |
| `delegated` | PGF | `delegated` |
| `awaiting-return` | PGF | `awaiting-return` |
| `returned` | PGF | `returned` |

In the summary aggregation, `decomposed` nodes are **included in total but excluded from the completion calculation** (aggregated separately in the split tree).

---

## 7. Sync Diff Output Format

```json
{
  "added": [
    {"node": "RefundFlow", "file": ".pgf/DESIGN-OrderSystem.md", "line": 22}
  ],
  "removed": [
    {"node": "LegacyGateway", "last_file": ".pgf/DESIGN-OrderSystem.md"}
  ],
  "modified": [
    {
      "node": "ChargeCard",
      "field": "status",
      "old": "designing",
      "new": "in-progress"
    },
    {
      "node": "SendReceipt",
      "field": "line",
      "old": 18,
      "new": 20
    }
  ]
}
```
