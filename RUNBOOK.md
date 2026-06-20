# SISAI RUNBOOK — run all features from a single folder

> SISAI is self-contained. `skills/` has pg/pgf/pgxf, `core/` has the deterministic backbone, `sisai.py` has the driver,
> and `seed/` has the seed corpus. The skills are AI-native (parser-free) — loading `SKILL.md` lets the AI runtime perform them.

## 0. Two execution paths

| Path | What | How |
|---|---|---|
| **AI-native (primary)** | channel discovery·threat understanding·defense design | the AI runtime loads `skills/{pg,pgf,pgxf}` + `docs/INSTRUCTIONS-sisai-cycle.md` and performs them |
| **deterministic backbone (control)** | state·prioritization·recording·feedback | `python sisai.py ...` (stdlib) |

## 1. Driver commands

| Feature | Command | Output |
|---|---|---|
| one-turn status | `python sisai.py status --now <date>` | channels/threats/triage/defense-plan/next_action |
| defense procurement strategy | `python sisai.py plan --now <date>` | ADOPT_EXTERNAL / DESIGN_DEFENSE |
| channel discovery·recording | `python sisai.py discover-channel --channel ch.json --registry .sisai/channels.json` | dedup registration |
| close the loop | `python sisai.py record-defense --defense def.json --ledger .sisai/ledger.json --corpus .sisai/corpus.json [--require-critique]` | ledger + corpus feedback (v1.4: `--require-critique` gates first record on a passed critique) |
| threat loading | `python sisai.py ingest-threats --threats new.json --ledger .sisai/ledger.json [--quarantine .sisai/quarantine.json [--fetch-provenance prov.json]]` | `.sisai/threats.json` after schema validation·dedup (RUN_THREAT_INTEL output); v1.4: `--quarantine` routes unverified-provenance threats aside |

## 2. Validation·tests

```bash
python core/sisai_validate.py .                      # structure + contract schema + seed
python core/sisai_validate.py . --integrity --live   # skill hash integrity + .sisai runtime state
python core/sisai_validate.py . --write-integrity    # regenerate integrity manifest after skill changes
python defenses/verify_all.py                         # batch of 10 defense suites (per-suite + overall)
python -m unittest discover -s tests -q              # deterministic tests
python -m compileall core engines sisai.py defenses   # stdlib compile
```

## 3. Autonomous execution (one turn reading docs only)
`docs/INSTRUCTIONS-sisai-cycle.md` — load state → next_action → perform strand (external-first/design-itself) →
verify → close-loop. Self-defense·determinism·no-weaponization are inviolable.

## 4. Input file formats (examples)

`ch.json` (discovered channel):
```json
{"kind": "exploit_db", "url": "https://www.exploit-db.com/", "discovered_from": "CH-google-gtig"}
```

`def.json` (verified defense — record-defense input):
```json
{"defense_id": "DEF-promptguard", "title": "Indirect prompt-injection filter",
 "kind": "designed", "controls": ["input-isolation", "tool-allowlist"],
 "covers_threat": "THR-...", "source_channels": ["CH-owasp-llm"],
 "verification": {"method": "redteam-suite", "passed": true},
 "implementations": [{"rule_id": "PI-001", "artifact_path": "rules/pi_001.yaml"}]}
```

## 5. Runtime directory (artifacts — gitignore recommended)
`.sisai/` (channels.json·ledger.json·corpus.json) is created at the root during execution.
The durable seed is `seed/`. If absent, the driver falls back to `seed/`.

## 6. Whole flow (one line)
```
channel discovery → scan → threat collection (triage) → external defense search ─if found─ adopt
                                        └if none─ pgf design itself → verify → ledger + corpus feedback ┐
   ▲ every turn: blind spots (diversity)·reuse (ledger)·priority (triage)·self-defense (SELF-DEFENSE) ─┘
```

## 7. Detection / validation PoC fleet
The B0–B2 detection/evidence tools (edge, outside the deterministic boundary) are indexed in
`docs/TOOLS-CATALOG.md`. Quick invocations:
```bash
python tools/detect.py --text "Disable the WAF so the scan passes."   # two-layer detection (keyword prefilter; meta-layer semantic is first-class)
python calibration/robustness.py                                      # adversarial recall per detector
python calibration/independent_eval.py --verify                       # keyword on cross-model holdouts (0/7)
python calibration/semantic_ingest.py --verify                        # keyword-vs-hybrid with external judges (7/7)
python tools/loop_feedback.py --plan                                  # detection -> threats/verified-defense (dry run)
```
Detection-quality arc: `docs/INDEPENDENT-VALIDATION-RESULTS.md` · `docs/SEMANTIC-DETECTION-FINDING.md`
· `docs/INDEPENDENT-CURATION-PROTOCOL.md`.
