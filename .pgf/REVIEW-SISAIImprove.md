# REVIEW-SISAIImprove

## Scope
- Target: `.pgf/DESIGN-SISAIImprove.md` @v:1.0 (P0 self-verification hardening — P0-3/P0-1/P0-2/P0-4)
- Date: 2026-06-18
- Mode: design-review (PGF 3-perspective: P5 Feasibility · P7 Risk · P8 Architecture)

## Summary
All 3 reviewers returned **CONCERN**. Gate (`Critical=0 AND High≤2`) → **FAIL → REVISE**.
Tally: **Critical 2, High 8, Medium 7, Low 3**. The review caught two design-level flaws that
would have been expensive post-implementation: (C2) a closed self-grading loop that yields
invisible false confidence, and (C1) a migration/edge gap that would fail-closed all 11 existing
suites. Design revised to **@v:1.1** addressing every Critical + High (see Resolutions).

## Findings (Critical / High — gate-blocking)

### [Critical][risk] C2 — Closed self-grading loop (red = blue = judge = one runtime)
- Evidence: `VariantGenMeta` + `AI_harden_patterns` + `CritiqueMeta` all run in the single AI meta-layer; the `adversarial` split is authored by the same runtime that hardens against it, then counted in the gate.
- Impact: loop converges when the generator runs out of *its own* ideas, not when the detector is robust; `final_misses:0` reads green while measuring nothing. Inflates the exact self-verification SISAI exists to harden.
- Resolution (v1.1): adversarial split = **training signal only, excluded from the pass gate**; gate strictly on a **`holdout` authored by a distinct source/turn**; every sample row records `authored_by` so auditors confirm holdout-author ≠ pattern-author.

### [Critical][feasibility] C1 — VerifyLib/split migration silently breaks 11 suites; empty-holdout div-by-zero
- Evidence: 11 self-contained `verify_*.py` + 11 `*_samples.jsonl` (~18 rows, **no `split` field**). `by("holdout")` on split-less rows → empty → `recall 0/0` → every legacy suite fails the new gate.
- Resolution (v1.1): rows lacking `split` default to `tune`; **VerifyLib is a pure metrics/split helper only** (each suite keeps its own loader + JSON contract + subprocess isolation); empty/under-size holdout → explicit `insufficient_holdout` (fail-closed, surfaced by `validate --live`), not a false green; **SampleExpansion sequenced before** the holdout gate flips.

### [High] (8) — resolved in v1.1
- H1 precision never measured in adversarial loop → **recompute `verify_suite` each round; reject hardening if holdout precision drops; terminate on (0 new miss) AND (precision preserved)**.
- H2 held-out statistically meaningless at ~11 samples → **minimum-holdout-size guard** + SampleExpansion first.
- H3 "inert variant" asserted not enforced → new deterministic core predicate **`is_inert_indicator(sample)`**; `append_samples` must pass it; failing variants dropped (gated attestation, not a comment).
- H4 WebFetch ingests attacker text into the hardening/judge context → **isolated fetch sub-agent (no write tools, no shared context); only `{verified,url,authority,sha256}` crosses back; authority-domain whitelist at the core gate**.
- H5 `adversarial_verify` termination not guaranteed → **hard `max_rounds`/`max_variants` caps → `status: budget_exhausted` (fail-closed)**; atomic sample writes.
- H6 `adversarial_verify` homeless / straddles boundary → **loop lives in meta-layer**; core exposes only pure `BlueRun` + `is_inert_indicator` + atomic append.
- H7 DeterminismGuard unenforced (cited grep does not exist) → **new committed test `tests/test_determinism_boundary.py`** (AST import-scan over `core/` for forbidden imports) wired into the gate.
- H8 empty-holdout gate ambiguous → covered by C1 resolution (`insufficient_holdout`, explicit).

## Medium (resolved/scoped in v1.1)
- Provenance fail-open on self-asserted fields → **strip incoming `provenance` from raw; only `ProvVerifyMeta` may set it; gate requires `authority ∈ WHITELIST` + 64-hex `source_sha256`**.
- Critique gate retroactively rejects 11 recorded defenses → **gate only on first record (`defense_already=False`); already-recorded keep idempotent self-heal (grandfather)**.
- Quarantine lifecycle → **fingerprint dedup; transient(retry) vs rejected(contradiction) distinction; `requarantine` actuator; quarantine count in `status`; `quarantine.schema` + `validate --live` coverage**.
- `ingest_threats` signature break → **`quarantine_path` as trailing optional kwarg (default `.sisai/quarantine.json`); keep `seed_threats`; preserve schema-validate/dedup/title-dedup/seed-fallback; add `--quarantine` CLI**.
- New schemas must stay in stdlib walker subset → **use `enum`/`pattern` only; add to `SCHEMA_NAMES`/`EXPECTED_FILES` + `schema_features` regression**.
- `is_provenance_verified` placement → **`core/sisai_provenance.py`** beside `is_verified`.

## Accepted deferrals
- P1/P2 (case memory, detector lifecycle, tiered autonomy, relationship graph) remain out of this design.
- SampleExpansion (needed for a statistically meaningful holdout) is added as a P0-2 prerequisite node, not a separate project.

## Round 2 (@v:1.1) — verdict: REVISE
3-perspective re-review. **Architecture: PASS** (all 6 round-1 arch findings RESOLVED).
**Feasibility: CONCERN** (High 2). **Risk: CONCERN** (Critical 2, High 3). Gate `Critical=0 AND High≤2` → **NOT met**.

Valid blockers (arbitrated, all accepted):
- [Critical] **R1** holdout author-independence is unverifiable under one runtime — `authored_by` is a self-asserted label (provenance theater).
- [Critical] **R2** `MIN_HOLDOUT` blocks all 11 current suites (`insufficient_holdout`→fail) — "11 suites pass" is false until expansion; gate must stage.
- [High] **R4** `is_inert_indicator` gates *form* not *capability* — bypassable + over-rejects; wrong frame.
- [High] **R5** fetch isolation contains tools but the `verified`/`authority` verdict is AI-judged on attacker text (authority self-declarable).
- [High] **R3** SampleExpansion authorship unstated — if loop-authored, it re-poisons the holdout.
- [Med] F3/F4 (threat.schema lacks source_sha256/authority-enum; anchor patterns), P8 module ownership + determinism-scan scope (engines/, os.urandom attr, aliases).

Resolutions → @v:1.2:
- R1/R3 → **holdout is frozen, independently-sourced, committed, read-only; the loop physically cannot write `split:holdout`** (atomic_append asserts split∈{tune,adversarial}). Independence = mechanism, not label.
- R2 → **per-suite advisory gate**: legacy full-set gate authoritative until a suite's frozen holdout is sized; `insufficient_holdout` non-blocking. 11 suites keep passing.
- R5 → **authority derived from URL host** (DOMAIN_AUTHORITY), AI match advisory only; gate binds to host∈whitelist.
- R4 → `is_inert_indicator` reframed as **storage hygiene**; defensive-only rests on the deterministic boundary.
- F3/F4 + P8 → schema fields/anchors, module ownership (sisai_detect/sisai_verify, engines/ loop), determinism test scans core/+engines/ with alias + os.* attr handling.

## Status
Default review iterations (N=1) exceeded after 2 rounds → **needs_user_ack** (per loop contract — not a hard block).

## Next actions
1. (done) @v:1.0 → @v:1.1 → **@v:1.2** addressing round-1 and round-2 blockers.
2. **Decision (operator):** (a) round-3 confirmation review on @v:1.2, or (b) accept @v:1.2 with documented residual (single-runtime holdout independence is bounded; mitigated by frozen/committed/read-only independently-sourced holdout), or (c) adjust scope.
3. Then `plan` → `execute` order: P0-3 → P0-1 → P0-2 (+ frozen-holdout provisioning) → P0-4.
