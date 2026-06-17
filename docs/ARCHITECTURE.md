# ARCHITECTURE — SISAI 3 strands ↔ implementation mapping

> Design source of truth: `.pgf/DESIGN-SISAI.md`. Operational directive: `docs/INSTRUCTIONS-sisai-cycle.md`.

## 1. Thesis

A single deterministic backbone (`core/`) binds the three strands into one source of truth, `next_action`
decides which strand to run each turn, and **verified defenses feed back into the corpus** to form a spiral
that compounds without converging. Channels themselves are first-class assets that are discovered, recorded, and reused.

## 2. Strands ↔ modules

| Strand | Role | AI meta layer (skills) | Deterministic backbone (core/) |
|---|---|---|---|
| **A. ThreatIntel** | Channel scan → threat collection/classification | Actual scanning/extraction | `channels` (scan candidates), `ledger` (dedup), `triage` (prioritization), `diversity` (blind spots) |
| **B. DefenseSynth** | External search for solutions → in-house design when none exists | External search, **pgf full-cycle design** | `loop.plan_defense` (external-first decision), `provenance` (lineage) |
| **C. DetectOps** | Operate detection rules/reports → feed performance back | Rule application/evaluation | `provenance.defense_to_corpus_entry` (feedback after verification), `ledger` (records) |
| **Channel self-expansion** | Discover/register new sources | New-source discovery | `channels.register_channel` (record/dedup), `should_discover_channels` |

## 3. next_action priority (deterministic)

```
RECORD_DEFENSE   (verified defense → ledger+corpus feedback; highest priority, close the loop)
→ DISCOVER_CHANNELS (insufficient active channels/coverage → expand sources)
→ REFRESH_COVERAGE  (attack-surface skew → steer toward uncovered categories)
→ RUN_THREAT_INTEL  (0 untriaged threats & channels present → collect fresh threats)
→ SOLVE_OR_DESIGN   (handle top threat: external-first → pgf design when none exists)
```

## 4. Material flow (one line)

```
discover channels → scan channels → collect threats (triage) → [search external defense ─ adopt if present]
                                            └ if none, pgf in-house design → verify → record in ledger
                                                                       └ corpus feedback (base pairs) ┐
   ▲ every turn measure blind spots (diversity) · block reuse (ledger) · prioritize (triage) ──────────┘
```

## 5. Deterministic boundary (governing constraint)

```
core/ (excluding the sisai.py CLI edge)  → pure determinism (stdlib; now injected). Ingested text leaves control flow unchanged.
AI meta layer (skills)                   → channel discovery, threat understanding, defense design (nondeterminism allowed; output is schema-validated)
defensive-only                           → detection/prevention/reports only. Weaponized output is out of scope.
wall-clock                               → only at the sisai.py CLI edge (--now injection takes precedence)
```

## 6. Extension point — N strands

The invariant is the backbone, not the number of strands. To add a new strand (e.g., ComplianceMap, RedTeamSim),
add only an adapter (`engines/`) and a `next_action` branch. The backbone and the deterministic boundary are invariant.

## 7. Relationship to HELIX

It inherits the design *pattern* (explore⊕exploit + backbone spiral, ledger/diversity/provenance/atomic-io/schema-walker)
but has **0 code dependency**. SISAI is independently implemented with security-domain-specific concepts (channel
self-expansion, triage, external-first in-house design, self-defense) and runs from the SISAI folder alone.
