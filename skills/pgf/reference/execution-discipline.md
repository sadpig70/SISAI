# execution-discipline — execution discipline for finishing without mistakes (execution guide)

> The discipline for completing large work *without mistakes* in PGF. *What* the modes (design/plan/execute/verify) do is
> defined by other references; this document provides **how to execute safely** (decomposition, persistence, evidence verification, determinism boundary).
> Reference templates: HELIX (`D:/HELIX/.pgf/`), recreate.

---

## 1. Decompose → Persist → Batch Gate → Resume (core cycle)

Large work is not done in one shot. Decompose it, save it, and execute it in batches.

```text
1) Decompose   decompose into batches (B0..Bn) with Gantree, each batch has an independent verification gate
2) Persist     save to .pgf/{DESIGN,WORKPLAN,status}-{Name}.* (the plan goes into files)
3) Execute     in batch order, proceed to the next only after each batch passes its gate
4) Checkpoint  record batch state in the status JSON ("done"/"blocked")
5) Resume      on interruption, read status and start from the first non-done batch (copies idempotent)
```

Minimal form of `status-{Name}.json`:
```jsonc
{"phase":"execute","summary":{"done":5,"total":8},
 "batches":{"B0":"done","B1":"done","B5":"pending"},
 "resume_rule":"read batches; start at first non-done; copies idempotent"}
```
> Effect: even if a turn doesn't finish, the next turn reads status and resumes exactly where it left off. Lossless against context breaks.

## 2. Evidence-Based Verification (★ never trust self-reporting)

Before writing `passed` into `status`, **run the actual command and leave its output** as evidence.

```text
- python -m unittest discover -s tests   → OK (no pass if FAILED)
- python -m py_compile <mods>            → syntax/path integrity
- <app> sample / run examples/*.json     → confirm expected output
- run identical input twice → outputs match (confirm determinism)
```

**GATE-EVIDENCE** — structured record of measured gate results (do not proceed/publish unless everything is `passed:true`):
```jsonc
{"command":"python -m unittest discover -s tests","cwd":".","exit_code":0,
 "stdout_excerpt":"Ran 83 tests ... OK","passed":true,"artifact_checked":"tests/"}
```
> Lesson: do not write "passed" by guess or self-report — judge solely on the basis of exit_code.

## 3. 3-Perspective verify (verify mode)

- **Acceptance**: re-verify the DESIGN's acceptance_criteria.
- **Quality**: reuse/duplication/efficiency of the changed code (`/simplify`-style).
- **Architecture**: DESIGN Gantree ↔ actual structure match.
- Verdict: `passed` / `rework` (roll back and re-execute only the target subtree) / `blocked` (report). Within `max_verify_cycles`.

## 4. Determinism Boundary (enforced as a design constraint)

```text
deterministic core  → stdlib only, no clock/network/AI. time is injected via now, similarity via sim
meta layer (AI_)    → non-determinism allowed in judgment/creation steps (engine/design assets)
artifact verdict    → deterministic invariant (identical input → identical output)
wall-clock          → only at the CLI edge (prefer --now injection)
```
Check: `grep -rnE "datetime\.now|time\.time|random\.|utcnow" core/` must be 0 (core only).
> Reference: HELIX-Core is pure stdlib; the clock is only at the `helix.py` CLI edge.

## 5. Safety Rules (hard-to-reverse work)

- **Original immutable**: do not modify the canonical version, past artifacts, or existing entries. Add only new runs/new entries (only status transitions of one's own entry are allowed).
- **Idempotency pre-check**: before external creation (repo/file), check existence → if present, do not recreate (reconcile only). No delete/force.
- **Zero leakage**: zero foreign-runtime identifiers, undisclosed internal names, or PII in code/docs/commits.
- **Fail-safe**: do not commit corrupted artifacts; isolate/discard them. When in doubt, stop and report.

## 6. Checklist

- [ ] `.pgf/{DESIGN,WORKPLAN,status}` persisted + per-batch gates
- [ ] Is every "passed" grounded in measured GATE-EVIDENCE (exit_code)
- [ ] 3-perspective verify verdict recorded (rework only the target subtree)
- [ ] Core determinism confirmed (zero clock/randomness/external dependency)
- [ ] Original immutable · idempotency pre-check · zero leakage

> Large-scale (>30 nodes) / multi-file migration → [`large-work-playbook.md`](./large-work-playbook.md).
> Integration/fusion decision · meta closed loop → [`integration-doctrine.md`](./integration-doctrine.md).
