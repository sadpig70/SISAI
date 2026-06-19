# SISAI — Technical Guide

> **Read this first.** A single, self-contained technical reference to SISAI: what it is, how it is built,
> how it runs, and how to extend it. A first-time AI runtime or engineer should be able to understand the
> whole system and operate it from this document alone. For the authoritative design see `.pgf/DESIGN-SISAI.md`
> and `.pgf/DESIGN-SISAIImprove.md`; for one-turn operation see `docs/INSTRUCTIONS-sisai-cycle.md`; for the
> self-defense rationale see `docs/SELF-DEFENSE.md`; for command recipes see `RUNBOOK.md`.

---

## 1. What SISAI is

**SISAI (Self-improvement Security AI)** is a **defensive-only** security AI that runs from a single folder
(`D:\SISAI`) and is **fully self-contained** (zero dependency on external paths, HELIX, or global settings).

Its job, each turn:
1. **Discover and expand** its own security information **channels** (CVE feeds, advisories, papers, OSS, …).
2. **Scan** those channels to **collect and classify threats** (attack techniques and real-world cases).
3. **Search externally first** for an existing defense; **if none exists, design one itself** with the
   vendored `pgf` skill (full-cycle).
4. **Verify** the defense, then **record** it and **feed it back** into a reusable corpus.

Over time, verified defenses compound into a richer corpus, so each round synthesizes better defenses — a
**self-improvement spiral that does not converge**.

**Defensive-only is a hard boundary.** Outputs are detection rules, prevention controls, and reports.
Weaponizing working exploits, automating targeted attacks, or generating detection-evasion tooling is **out
of scope and refused**. Detection/prevention/CTF/research framing only.

---

## 2. The mental model (read this twice)

```
            ┌──────────────────────── AI meta-layer (you, the runtime + skills) ─────────────────────────┐
            │  non-deterministic cognition: discover channels · understand threats · search/design        │
            │  defenses · critique · generate red-team variants. Output = schema-validated attestations.    │
            └───────────────▲───────────────────────────────────────────────────────────┬─────────────────┘
                            │ attestations (validated)                                    │ reads state
                            │                                                             ▼
┌───────────────────────────┴─────────────────────────────────────────────────────────────────────────────┐
│  Deterministic backbone (core/ + sisai.py edge)                                                            │
│  pure stdlib · no clock/network/AI/RNG · `now` injected · collected text is DATA, never control flow       │
│  control · recording · prioritization · gating · feedback                                                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Two layers, one rule that separates them:

- **AI meta-layer** — this is *you* (the AI runtime) plus the vendored `skills/{pg,pgf,pgxf}`. All
  non-deterministic, knowledge-bearing work happens here: scanning channels, understanding/extracting
  threats, searching for or **designing** defenses, judging/critiquing, generating adversarial variants.
- **Deterministic backbone** — `core/` Python modules (pure stdlib) plus the thin `sisai.py` CLI edge. It
  does control flow, recording, deduplication, prioritization, **gating**, and corpus feedback. It never
  calls the network, a clock, an RNG, or an AI; time is passed in as `now`.

**The deterministic boundary is the governing invariant** (see §6). Everything the meta-layer produces is
**data** that the backbone validates against a schema and gates on — collected text can never change the
backbone's control flow. This is SISAI's first line of prompt-injection defense.

---

## 3. The three strands + channel self-expansion

SISAI's work is organized into **three strands** bound by one backbone, plus channel self-expansion as a
first-class activity.

| Strand | What it does | Meta-layer (cognition) | Backbone (deterministic) |
|---|---|---|---|
| **A. ThreatIntel** | scan channels → collect/classify threats | actual scanning & extraction | `sisai_channels` (scan candidates), `sisai_ledger` (dedup), `sisai_triage` (priority + blind spots) |
| **B. DefenseSynth** | external-first search → in-house `pgf` design if none | external search, **pgf full-cycle** design | `sisai_loop.plan_defense` (external-first decision), `sisai_provenance` (lineage) |
| **C. DetectOps** | run detection rules/reports → feed performance back | rule application/evaluation | `sisai_provenance.defense_to_corpus_entry` (feedback after verification), `sisai_ledger` (records) |
| **Channel self-expansion** | discover/register new sources | new-source discovery | `sisai_channels.register_channel` / `should_discover_channels` |

A **channel** is a first-class asset (an information source), not a transient input: it is discovered →
recorded in a registry (dedup by fingerprint) → reused.

---

## 4. Repository layout

```
SISAI/
├── sisai.py                  # DRIVER / CLI edge: status · plan · discover-channel · record-defense · ingest-threats
├── core/                     # ★ deterministic backbone (pure stdlib; no clock/net/AI/RNG)
│   ├── sisai_fingerprint.py  #   stable identity (channel/threat/defense fingerprints) for dedup
│   ├── sisai_channels.py     #   self-expanding channel registry (register/dedup, coverage, next-to-scan)
│   ├── sisai_ledger.py       #   reuse gate: has this threat been defended / this defense built?
│   ├── sisai_triage.py       #   severity×recency scoring + coverage/blind-spot measurement
│   ├── sisai_provenance.py   #   lineage + verified→corpus feedback + v1.4 gates (provenance/critique)
│   ├── sisai_loop.py         #   next_action (which strand to run) + plan_defense (external-first)
│   ├── sisai_io.py           #   atomic crash-safe JSON writes (temp + os.replace, .bak self-heal)
│   ├── sisai_schema.py       #   JSON-Schema (draft-07) validator: jsonschema if present, else stdlib walker
│   ├── sisai_validate.py     #   repo layout + schema-subset + seed + integrity + live validation
│   ├── sisai_detect.py       #   v1.4: inert hygiene, rule compile/scan, blue_run, atomic_append_samples
│   └── sisai_verify.py       #   v1.4: verify_suite (frozen-holdout gate) + roles_disjoint (cross-model)
├── engines/
│   ├── adapters.py           #   pure transforms: native artifacts → backbone shapes (seed → list/registry/corpus)
│   └── adversarial.py        #   v1.4: bounded red/blue hardening loop (injected cognition) + author routing
├── schemas/                  # 7 JSON-Schema contracts (see §8)
├── seed/                     # shipped seed corpus + v1.4 example data (fallback when .sisai/ is absent)
├── defenses/                 # operational defense artifacts: detectors/, rules/, tests/, verify_all.py, design-notes
├── skills/{pg,pgf,pgxf}/     # vendored AI-runtime "driving engines" (parser-free notation/frameworks)
├── docs/                     # ARCHITECTURE · SELF-DEFENSE · INSTRUCTIONS-sisai-cycle · TECHNICAL-GUIDE (this)
├── .pgf/                     # design/workplan/status (sources of truth for design)
├── examples/                 # sample inputs (e.g. sample_defense.json)
├── tests/                    # deterministic unittest suite
└── .sisai/                   # RUNTIME artifacts (gitignored): channels/threats/corpus/ledger — falls back to seed/
```

---

## 5. The autonomous loop

Each turn the backbone computes **one** next action from the current state. The decision is deterministic
and prioritized (`core/sisai_loop.py:next_action`):

```
1. RECORD_DEFENSE     a verified defense is pending → record it to the ledger + feed corpus (close the loop)
2. DISCOVER_CHANNELS  channel coverage is low/narrow → expand information sources
3. REFRESH_COVERAGE   attack-surface is skewed → steer collection toward under-covered categories
4. RUN_THREAT_INTEL   no untriaged threats and channels exist → scan channels for fresh threats
5. SOLVE_OR_DESIGN    a top threat exists → procure a defense (external-first, else pgf design)
6. (default)          RUN_THREAT_INTEL — keep sensing
```

Material flow over many turns:

```
discover channels → scan channels → collect threats (triage) → [search external defense ─ adopt if present]
                                          └ if none, pgf in-house design → verify → record in ledger
                                                                     └ corpus feedback (base pairs) ┐
 ▲ every turn: measure blind spots · block reuse (ledger) · prioritize (triage) ────────────────────┘
```

`plan_defense(threat, defense_corpus, ledger)` is **external-first**: it tries `match_external_defense`
(category/technique overlap with the corpus) and only falls back to in-house `pgf` design when nothing
applies. This keeps SISAI from reinventing defenses that already exist.

---

## 6. The deterministic boundary (governing invariant)

This is the single most important constraint. Internalize it before changing any code.

```
core/ (excluding the sisai.py CLI edge) → pure determinism: stdlib only; no clock, network, AI, or RNG.
                                          `now` is injected. Ingested text NEVER alters control flow.
AI meta-layer (skills)                  → all nondeterministic cognition; its output is schema-validated
                                          before the backbone acts on it.
defensive-only                          → detection/prevention/reports only; weaponized output is refused.
wall-clock                              → read ONLY at the sisai.py CLI edge (`--now` injection wins).
```

Why it matters: many threats SISAI collects (prompt injection, data poisoning, supply-chain, skill-ecosystem
poisoning) **target AI systems like SISAI itself**. Because `core/` cannot be steered by collected text, a
malicious page/CVE/README cannot hijack SISAI by being ingested — it is just data in a field.

**Enforced in CI** by `tests/test_determinism_boundary.py` (the *DeterminismGuard*): an AST scan over
`core/` **and** `engines/` that forbids importing `{time, datetime, random, secrets, socket, urllib,
requests, http, ftplib, subprocess, asyncio}` (resolving `import x as y` aliases), forbids
`os.urandom/os.system/os.popen`, and forbids any `AI_` cognition symbol inside `core/`.

---

## 7. Core module reference

All functions are pure unless noted; `now` is an injected ISO date string (`YYYY-MM-DD`).

- **sisai_fingerprint** — `channel_fingerprint`, `threat_fingerprint`, `defense_fingerprint`: deterministic
  identity (sha256-derived) used for dedup and idempotency. `normalize_name`, `tokenize_name` helpers.
- **sisai_io** — `atomic_write_json(path, obj)` (temp file + `os.replace`, keeps a `.bak`); `read_json(path,
  default)` (self-heals from `.bak` on corruption). The only write primitive — uncorruptible across crashes.
- **sisai_schema** — `validate_against_schema(doc, schema)` → list of problems (empty = valid); uses
  `jsonschema` if installed, else a deterministic stdlib subset walker (type/required/properties/items/enum/
  minimum/maximum/pattern). `schema_path(root, name)`, `schema_features(schema)`.
- **sisai_channels** — `register_channel`, `active_channels`, `kind_coverage`, `should_discover_channels`,
  `missing_kinds`, `next_channels_to_scan`. The self-expanding source registry (dedup by fingerprint,
  spread scanning across kinds).
- **sisai_ledger** — `is_consumed(candidate, ledger)`, `append_entry`, `reindex_ledger`. The reuse gate
  (match by fingerprint, then normalized title) that makes ingest/record idempotent.
- **sisai_triage** — `triage_score`, `rank_threats`, `top_threat`, `measure_coverage` (blind-spot signals:
  category dominance ≥ 0.6 or < 3 distinct categories), `recency_decay`.
- **sisai_provenance** — `trace_defense` (audit lineage), `is_verified` (verification.passed AND
  implementations present), `defense_to_corpus_entry` (raises unless verified — the feedback bond). **v1.4
  gates:** `host_from_url`, `authority_from_url` (host-derived trust), `is_provenance_verified`,
  `strip_incoming_provenance`, `is_critiqued`.
- **sisai_loop** — `next_action(state, policy)` (§5), `plan_defense`, `match_external_defense`.
- **sisai_detect** (v1.4) — `is_inert_indicator` (storage hygiene: single-line ≤240 char labeled row),
  `compile_rule` (length-bounded, exception-safe), `scan(text, compiled)`, `blue_run` (misses a detector
  fails to flag), `atomic_append_samples` (the **structural holdout freeze**: appends only
  `split ∈ {tune, adversarial}`; refuses `holdout`).
- **sisai_verify** (v1.4) — `MIN_HOLDOUT`, `metrics(predict, samples)`, `verify_suite` (gates on a sized
  frozen holdout, else legacy full-set), `index_role_registry`, `roles_disjoint` (cross-model role gate).
- **sisai_validate** — `validate_project` and parts (`validate_layout`, `validate_schemas_in_subset`,
  `validate_seeds`, `validate_integrity`, `validate_live`). Run: `python core/sisai_validate.py .` → PASS.

`engines/adapters.py` projects raw seed artifacts into backbone shapes (`channels_seed_to_registry`,
`threats_seed_to_list`, `defenses_seed_to_corpus`). `engines/adversarial.py` holds the v1.4 red/blue
orchestration (`adversarial_verify`) and `route_author`; cognition is injected so `engines/` stays pure.

---

## 8. Data contracts (schemas/)

Seven JSON-Schema (draft-07) files, registered in `sisai_validate.SCHEMA_NAMES`:

| Schema | Required | Notable fields |
|---|---|---|
| `channel` | id, kind, url | kind ∈ {cve, advisory, news, paper, oss, exploit_db, vendor_intel, standard}; orthogonality, status, fingerprint |
| `threat` | threat_id, title, category | techniques[], cve, cvss[0–10], recency (`YYYY-MM[-DD]`), source_channels[], evidence[], **provenance** {source_url, authority∈{NVD,MITRE,GHSA,arXiv,null}, **source_sha256** (`^[0-9a-f]{64}$`), verified, verified_on} |
| `defense` | defense_id, title, kind | kind ∈ {external, designed}; controls[], covers_threat/category/techniques, verification {method, passed}, implementations [{rule_id, artifact_path}], **critique** {passed, findings[{lens∈{correctness,evadability,fp_risk,scope}, issue, evidence, fix}]} |
| `ledger` | schema_version, entries[], … | entries: {entry_id, kind, title, fingerprint, recorded_at, implementations[]} |
| `loop-state` | (none) | pending_verified_defense, should_discover_channels, coverage{repair_required}, untriaged_threats, active_channels, top_threat |
| `sample` (v1.4) | label, text | label ∈ {malicious, benign}; **split** ∈ {tune, holdout, adversarial}; category |
| `role-registry` (v1.4) | entries[] | entries: {suite, category, author_model, holdout_curator_model, judge_model} |

Bold fields are v1.4 additions. The provenance `authority` is **host-derived**, never AI-asserted.

---

## 9. Runtime state and seed fallback

- **Live state** lives in `.sisai/` (gitignored): `channels.json`, `threats.json`, `corpus.json`,
  `ledger.json`, optionally `quarantine.json`. These accumulate as the loop runs.
- If a live artifact is absent, the driver **falls back to `seed/`** (shipped templates:
  `channels.json`, `threats.json`, `defenses.json`, plus v1.4 examples `sample-suite.json`,
  `role-registry.json`). So a fresh checkout runs against the seed immediately.
- `defenses/` holds the **operational defense artifacts** that have been designed/adopted: detection
  `rules/`, `detectors/`, `tests/`, per-defense `design-notes-*.md`, compliance mappings, and
  `verify_all.py` which batch-verifies the defense detector suites.

---

## 10. CLI reference (`sisai.py`)

`python` is invoked without a path (it is on PATH); UTF-8. Time is injected with `--now YYYY-MM-DD`.

| Command | Purpose |
|---|---|
| `python sisai.py status [--now D] [--json] [--root R]` | one deterministic turn report: channels/threats/coverage/top_threat/defense_plan/**next_action** |
| `python sisai.py plan [--now D]` | the defense procurement plan for the top threat (ADOPT_EXTERNAL / DESIGN_DEFENSE) |
| `python sisai.py discover-channel --channel ch.json --registry .sisai/channels.json [--now D]` | register a discovered channel (idempotent, dedup) |
| `python sisai.py record-defense --defense def.json --ledger .sisai/ledger.json --corpus .sisai/corpus.json [--now D] [--require-critique]` | close the loop: record a **verified** defense + corpus feedback |
| `python sisai.py ingest-threats --threats new.json --ledger .sisai/ledger.json [--out .sisai/threats.json] [--quarantine .sisai/quarantine.json [--fetch-provenance prov.json]] [--now D]` | load scanned threats (schema-validate + dedup) |

**v1.4 opt-in flags** (default OFF → existing suites never regress):
- `--require-critique` (record-defense): require a passed multi-lens critique before a defense's first record.
- `--quarantine PATH` (ingest-threats): enforce the ProvenanceGate — strip page-claimed provenance, overlay
  the fetcher's ground-truth (`--fetch-provenance`, a list aligned with `--threats`), then route
  host-verified threats to state and unverified ones to the quarantine store.

---

## 11. The v1.4 self-verification gates

Five deterministic gates (`DESIGN-SISAIImprove @v1.4`). All are **opt-in + grandfather** — off by default so
the existing defense suites/seeds never start failing; provisioning (a flag, a registry entry, a sized
holdout) turns enforcement on per scope.

1. **ProvenanceGate** (`sisai_provenance`, in `ingest_threats --quarantine`). Trust is **host-derived**:
   `authority_from_url` maps a URL host to an authority (NVD/MITRE/GHSA/arXiv); the gate requires
   `verified` + host∈whitelist + the AI-claimed `authority` matching the host + a 64-hex `source_sha256`.
   Page-claimed provenance is **stripped first** (anti fail-open: a collected page cannot self-assert
   verification); only the isolated fetcher's out-of-band provenance counts. Unverified → quarantine.
2. **HeldoutBench** (`sisai_verify.verify_suite`). Grades a detector on a **frozen holdout** split when one
   is sized (≥5 malicious / ≥4 benign); otherwise the legacy full-set gate stays authoritative (advisory).
   The `adversarial` split is train-only and never gated.
3. **AdversarialVerify** (`engines/adversarial.adversarial_verify`). A bounded red/blue hardening loop:
   generate variants → find misses (`blue_run`) → harden → re-verify, rejecting any regressive harden, until
   it converges or hits a budget cap. **Cognition is injected** (`gen_variants`, `harden`, `verify`) so
   `engines/` stays pure. `budget_exhausted` means the defense is **not** recorded (fail-closed).
4. **CritiqueGate** (`sisai_provenance.is_critiqued`, in `record_defense --require-critique`). A multi-lens
   critique (correctness/evadability/fp_risk/scope) must pass before a defense's **first** record.
5. **CrossModelRoles** (`sisai_verify.roles_disjoint`). A committed `role-registry` enforces the binding
   pairs **Author ≠ Holdout** and **Author ≠ Judge** per suite — a label-based cross-model layer on top of
   the structural freeze. `route_author` picks the author per detector category (capability does not transfer
   across categories, so there is no single global author). Unregistered suites are grandfathered.

**Independence is structural, not a label.** The binding guarantee is that the loop physically cannot write a
holdout row: `atomic_append_samples` refuses `split=holdout`. The cross-model role layer is defense-in-depth
on top of that freeze.

---

## 12. Self-defense model

SISAI is both a tool that protects others and a target that must protect itself. Mapping (see
`docs/SELF-DEFENSE.md` for the full table):

| Threat | Backbone defense |
|---|---|
| Prompt injection | deterministic boundary — ingested text cannot change `core/` control flow |
| Data poisoning | fingerprint dedup + provenance gate; only **verified** defenses feed the corpus |
| Supply chain | external-first but **verification-gated** adoption |
| Skill-ecosystem poisoning | vendored skills (no dynamic loading) + integrity manifest in `validate` |

Code-enforced invariants: data ≠ instructions; feedback only after verification
(`defense_to_corpus_entry` raises otherwise); fingerprint reuse gate (idempotent); atomic writes;
defensive-only output. The v1.4 gates (§11) strengthen each of these.

---

## 13. How to operate it (a worked turn)

```bash
# 0. (AI runtime) load the driving skills first
#    skills/pg, skills/pgf  (+ skills/pgxf for very large designs)

# 1. read state and the next action (deterministic)
python sisai.py status --json --now 2026-06-19
#    → inspect next_action.action and .why

# 2. act on next_action:
#    DISCOVER_CHANNELS → (meta) find a source filling a missing kind, then:
python sisai.py discover-channel --channel ch.json --registry .sisai/channels.json --now 2026-06-19
#    RUN_THREAT_INTEL  → (meta) scan channels, extract threats into new.json, then:
python sisai.py ingest-threats --threats new.json --ledger .sisai/ledger.json --now 2026-06-19
#    SOLVE_OR_DESIGN   → (meta) external-first; if none, design a defense via pgf full-cycle, verify it
#    RECORD_DEFENSE    → close the loop (only verified defenses are accepted):
python sisai.py record-defense --defense def.json --ledger .sisai/ledger.json --corpus .sisai/corpus.json --now 2026-06-19

# 3. gates (must hold every turn)
python core/sisai_validate.py .            # → PASS
python -m unittest discover -s tests -q    # → OK
python defenses/verify_all.py              # batch-verify the defense detector suites
```

A defense is only recordable when **verified**: `verification.passed == true` AND `implementations`
(rule_id/artifact) present; otherwise `record-defense` returns `rejected`. Re-running any actuator is
idempotent (`already_recorded` / `noop`). Enable `--require-critique` / `--quarantine` to turn on the v1.4
gates for a hardened turn.

---

## 14. How to extend

- **Add a strand** — add an adapter in `engines/` and a `next_action` branch in `sisai_loop.py`. The backbone
  and the deterministic boundary are invariant; the number of strands is not.
- **Add/extend a schema** — edit/create `schemas/<name>.schema.json` using only the stdlib-walker subset
  (type, required, properties, items, enum, minimum, maximum, pattern — avoid `additionalProperties`/
  `patternProperties` unless `jsonschema` is guaranteed), then register it in `EXPECTED_FILES` and
  `SCHEMA_NAMES` in `core/sisai_validate.py`, and add a unit test.
- **Add a deterministic gate** — put pure logic in `core/`, keep it **advisory-until-provisioned + grandfather**
  (opt-in; never regress existing suites), wire it at the `sisai.py` actuator edge behind a flag, and test
  both the enforce path and the grandfather path.
- **Never** import a forbidden module or add an `AI_` symbol in `core/` — the DeterminismGuard test will fail.
  Cognitive steps belong in the meta-layer and are passed into `engines/` as injected callables.

---

## 15. Invariants checklist (must hold every turn / every change)

- [ ] `core/` + `engines/` are pure stdlib (no clock/network/AI/RNG; `now` injected) — DeterminismGuard green.
- [ ] Collected external text is **data only**; it never alters `core/` control flow.
- [ ] Output is **defensive-only** (detection/prevention/reports); no weaponized output enters corpus/ledger.
- [ ] Defenses feed back **only after verification** (`is_verified`); unverified → rejected.
- [ ] Channel/threat/defense records are **idempotent** (fingerprint reuse gate).
- [ ] Writes are atomic (`atomic_write_json`); state is never half-written.
- [ ] Holdout is **structurally frozen** (loop writes tune/adversarial only); cross-model roles disjoint.
- [ ] `python core/sisai_validate.py .` → PASS and `python -m unittest discover -s tests` → OK.
- [ ] Hard-to-reverse external actions (push/publish/deploy) only after gates **and operator approval**.

---

## 16. Glossary

- **Backbone** — the deterministic `core/` (+ `sisai.py` edge); control/recording/gating, no cognition.
- **Meta-layer** — the AI runtime + `skills/`; all cognition; output is schema-validated data.
- **Channel** — a first-class, reusable information source (CVE feed, advisory, paper, OSS, …).
- **Strand** — one of A. ThreatIntel / B. DefenseSynth / C. DetectOps (plus channel self-expansion).
- **Ledger** — the reuse gate recording which threats/defenses are already handled (idempotency).
- **Corpus** — the reusable store of **verified** defenses fed back to compound future synthesis.
- **Provenance** — host-derived source trust for ingested threats (authority + sha256 + verified).
- **Holdout** — the frozen, independently-sourced benchmark split a detector is graded on; structurally
  unwritable by the loop.
- **Spiral** — verified defense → corpus feedback → better next-round synthesis (compounds, never converges).
- **pgf** — the vendored PPR/Gantree Framework skill used to design defenses (full-cycle) when no external
  solution exists.

---

*This guide reflects the backbone through DESIGN-SISAIImprove @v1.4. When code and this guide diverge, the
code (`core/`, `engines/`, `sisai.py`, `schemas/`) and `.pgf/DESIGN-*.md` are authoritative; update this file.*
