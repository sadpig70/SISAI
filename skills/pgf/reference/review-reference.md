# Review Mode — Iterative Review & Improvement Specification

> Closely review existing artifacts (documents, designs, skills, code) and iterate on fixes/improvements/additions.
> Different from `design --analyze` (code→DESIGN reverse engineering): review is the mode that **raises the quality of artifacts that already exist**.

---

## 1. Overview

### Purpose

- Systematically surface inconsistencies, omissions, ambiguities, and improvement points in existing artifacts
- Prioritize, fix, and verify the discovered issues
- Iterate until issues are exhausted (Convergence Loop)

### When to Use

| Situation | Example |
|-----------|---------|
| Improve document quality | Review PG/PGF skill documents |
| Verify a design | Check internal consistency of DESIGN.md |
| Strengthen a skill | Supplement missing features in an existing skill |
| Code review | Review the quality/security/performance of implementation code |
| Cross-verification | Check consistency across multiple documents |

---

## 2. Commands

| Command | Action |
|---------|--------|
| `/PGF review {target}` | Closely review the target file/directory |
| `/PGF review {target} --scope {files}` | Review only a specific file scope |
| `/PGF review {target} --max-cycles N` | Iterate up to N times (default: until issues are exhausted) |

---

## 3. Execution Flow

```python
def review_cycle(
    target: str,
    scope: list[str] = None,
    max_cycles: int = 10,
) -> ReviewResult:
    """close review → fix → re-verify, iterated"""

    cycle = 0
    all_fixes = []

    while cycle < max_cycles:
        cycle += 1

        # Phase 1: ANALYZE — multi-angle analysis
        issues = analyze(target, scope)

        if not issues:
            break  # issues exhausted → complete

        # Phase 2: PRIORITIZE — determine priority
        prioritized = prioritize_issues(issues)

        # Phase 3: IMPLEMENT — implement fixes
        fixes = implement_fixes(prioritized)
        all_fixes.extend(fixes)

        # Phase 4: VERIFY — verify fixes
        remaining = verify_fixes(target, fixes)

        report_cycle(cycle, len(issues), len(fixes), len(remaining))

        if not remaining:
            break  # all issues resolved

    return ReviewResult(
        cycles=cycle,
        total_issues=len(all_fixes),
        status="passed" if cycle < max_cycles else "max_cycles_reached",
    )
```

---

## 4. Analysis Framework

```python
def analyze(target: str, scope: list[str]) -> list[Issue]:
    """5-axis analysis"""
    content = read_all(target, scope)

    [parallel]
        consistency = AI_check_internal_consistency(content)
        # explanations that contradict each other within the same document

        completeness = AI_check_completeness(content)
        # are core concepts defined without omission

        clarity = AI_check_clarity(content)
        # ambiguous expressions, parts open to differing interpretation

        accuracy = AI_check_accuracy(content)
        # do examples match the explanations, are references valid

        improvements = AI_identify_improvements(content)
        # better wording, concepts to add, structural improvements

    # add cross-consistency when targeting multiple files
    if len(scope or [target]) > 1:
        cross = AI_check_cross_consistency(content)
        return merge_deduplicate(consistency, completeness, clarity, accuracy, improvements, cross)

    return merge_deduplicate(consistency, completeness, clarity, accuracy, improvements)
```

### Issue Format

```python
Issue = {
    "id": str,           # e.g. P1, F2, C3
    "location": str,     # file:section or file:line
    "type": str,         # "fix" | "improve" | "add"
    "impact": str,       # "high" | "medium" | "low"
    "description": str,  # issue description
    "suggestion": str,   # proposed fix
}
```

---

## 5. Prioritization

```python
def prioritize_issues(issues: list[Issue]) -> list[Issue]:
    """sort by impact × type"""
    priority_order = {
        ("high", "fix"): 1,
        ("high", "improve"): 2,
        ("medium", "fix"): 3,
        ("high", "add"): 4,
        ("medium", "improve"): 5,
        ("medium", "add"): 6,
        ("low", "fix"): 7,
        ("low", "improve"): 8,
        ("low", "add"): 9,
    }
    return sorted(issues, key=lambda i: priority_order.get((i.impact, i.type), 10))
```

---

## 6. Progress Report Format

```text
[PGF REVIEW] Cycle 1 | target: PG/SKILL.md
  Analyzed: 17 issues found (6 fix, 7 improve, 4 add)
  Implemented: 11 fixes
  Remaining: 1 (deferred)

[PGF REVIEW] Cycle 2 | re-verification
  Analyzed: 0 new issues
  Judgment: passed

[PGF REVIEW] === Complete ===
  Cycles: 2
  Total fixes: 11
  Files modified: 3
  Status: passed
```

---

## 7. Relationship with Other Modes

| Mode | Relationship |
|------|-------------|
| `design --analyze` | code→DESIGN reverse engineering. review improves the quality of existing artifacts |
| `verify` | post-implementation verification. review reviews artifacts regardless of before/after implementation |
| `design-review` (3-perspective) | pre-verification before the DESIGN→PLAN transition. review is general-purpose iterative review |
