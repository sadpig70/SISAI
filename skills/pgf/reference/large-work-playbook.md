# large-work-playbook — large-scale / multi-file work playbook (execution guide)

> A procedure for finishing large work without mistakes: 30+ nodes / multi-file / migration·integration. Combines pgxf index + batches +
> safe replacement. Reference template: HELIX monorepo integration (`D:/HELIX`, vendoring 19 skills · 207 files).

---

## 1. When to Use This Playbook

- Nodes > 30, or `(decomposed)` splits, or changes that cut across multiple files/skills.
- Integrating two systems, mass vendoring, path normalization, bulk schema changes, etc.

## 2. pgxf Index (overview + node lookup)

Large-scale PG is not loaded entirely into context. Build an index with pgxf for lazy-load, O(1) node lookup, and status aggregation.
- On entry, load only the index and expand only the needed subtrees.
- `(decomposed)` split trees are connected by reference in the index.

## 3. Decompose → Persist WORKPLAN (batch = unit of subcontract)

```text
B0 Skeleton    directories/scaffold
B1..Bk         independent batches (each @dep + verification gate)
B(k+1) Normalize cross-cutting bulk change (path/schema) — once, after copies complete
B(last) Verify  full gate
```
Batch state in the status JSON → safe to interrupt/resume. Design **copies to be idempotent** (safe to overwrite).

## 4. Inventory First (a grounded plan)

No guessing. Measure the scale to ground the plan.
```bash
find <src> -type f | wc -l          # file count
diff -rq <treeA> <treeB>            # identify duplicates/divergence (dedup decision)
grep -rl "<old-path>" <tree> | wc -l   # normalization scope
```
> HELIX reference: inventory of IdeaFirst 121 files + recreate 52 files → discovered pg/pgf/pgxf duplication → dedup decision.

## 5. Safe Replacement (normalization batch)

Make cross-cutting bulk changes **atomic**: write the batch only when every anchor matches exactly once.

```python
# write only after all replacements are validated (so a partial failure doesn't corrupt files)
results, errors = {}, []
for f, edits in PLAN.items():
    txt = read(f)
    for old, new in edits:
        if txt.count(old) != 1: errors.append((f, old)); continue   # enforce single anchor match
        txt = txt.replace(old, new, 1)
    results[f] = txt
if errors: abort(errors)            # any failure → write nothing
for f, txt in results.items(): write(f, txt)
```

**Preservation rules** (things migration easily breaks — must be preserved):
- **Line endings**: preserve each file's original CRLF/LF (prevent whole-file diff in `autocrlf` environments). Normalize→edit→restore to the original line endings.
- **Generalizations/improvements**: if the target has *evolved independently*, do not overwrite it with the source (regression). Add only.
- **Cross-reference integrity**: after path changes, confirm `grep -rl "<old>"` = 0 and confirm link targets exist.

## 6. Verification (per batch + overall)

```text
- Batch gate: file count = source sum, dangling anchors = 0, py_compile OK
- Overall: unittest OK · validate PASS · no regression (maintain existing test count)
- Inventory matrix: prove in a table that every item (skill/module) maps to a destination (nothing missing)
```

## 7. Checklist

- [ ] Ground the plan with measured inventory (file count · duplication · normalization scope)
- [ ] WORKPLAN batches + status persistence (idempotent copies)
- [ ] Bulk replacement is atomic (single anchor match) + preserve line endings/improvements/cross-references
- [ ] Prove completeness with a coverage matrix
- [ ] Pass per-batch and overall gates (zero regression)

> Execution safety discipline (persistence · evidence verification · determinism) → [`execution-discipline.md`](./execution-discipline.md).
> Integration vs fusion decision → [`integration-doctrine.md`](./integration-doctrine.md).
