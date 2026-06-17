# WORKPLAN-I18n @v:1.0

> Goal: make the repository English-only. Translate all Korean prose in tracked files
> to natural English **without changing semantics, code, identifiers, PG notation, JSON
> structure, file paths, or behavior**. PNG files are excluded. The SISAI deterministic
> backbone (core/, sisai.py, engines/, tests/) already contains no Korean.

## POLICY
```yaml
scope: git-tracked files containing Hangul, except *.png
preserve: code, identifiers, PG notation (AI_/Gantree/status/→/[parallel]), paths, JSON keys & logic values, markdown structure
translate: prose, comments, docstrings, frontmatter descriptions/triggers, diagram text
semantics_unchanged: true            # translation must not alter meaning or behavior
person_reference: "정욱님" -> "the operator" in defenses/docs; KEPT as "정욱님" in AGENTS.md (proper name)
gate: 0 residual Hangul (except the documented intentional retentions) + all CI gates green
```

## Justified retentions (must stay non-English)
```text
AGENTS.md — addresses the user by proper name "정욱님" (native-language proper names are
  an accepted convention): the naming directive + the approval-gate reference.
.gitignore line `deepseek지침.md` — a literal filename pattern matching a real
  Hangul-named (gitignored, untracked) scratch file. Translating it would break the
  ignore. Kept by necessity; the file itself is out of repo scope (gitignored).
```

## Batches (parallel — independent files, no collisions)
```text
B1 skills/pg        skills/pg/SKILL.md + reference/{work-as-program,control-flow-cookbook}.md
B2 skills/pgxf      skills/pgxf/SKILL.md + references/pgxf-format.md
B3 skills/pgf core  skills/pgf/SKILL.md + reference/agent-protocol.md
B4 skills/pgf ref   skills/pgf/reference/{evolve,execution-discipline,integration-doctrine,large-work-playbook,review-reference,design-review-reference,cycle-reference}.md
B5 skills/pgf misc  discovery/personas.json + loop/stop-hook.py + agents/pgf-persona-p{1..14}.md
B6 root             README.md + AGENTS.md + RUNBOOK.md
B7 docs             docs/{INSTRUCTIONS-sisai-cycle,ARCHITECTURE,SELF-DEFENSE}.md
B8 .pgf             DESIGN-SISAI.md + DESIGN-DefenseSweep.md + WORKPLAN-DefenseSweep.md + WORKPLAN-SISAI.md
B9 small (self)     seed/*.json, .pgf/status-SISAI.json, defenses/{design-notes-MA,zero-trust-mapping-AS,incident-playbook-PI}.md, assets/sisai-strands.svg
```

## Verification gate
```text
- re-scan tracked files (excl *.png): 0 Hangul lines except the .gitignore retention
- skills/ changed -> regenerate skills/INTEGRITY.json (--write-integrity)
- python core/sisai_validate.py . --integrity --live  -> PASS
- python -m unittest discover -s tests -q             -> OK
- python defenses/verify_all.py                       -> 11/11 PASS
- build_report deterministic (2x identical) · status untriaged unchanged (0/15)
```
