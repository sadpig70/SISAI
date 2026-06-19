# SELF-DEFENSE — how SISAI defends itself

> SISAI is a security AI built on *the pg/pgf/pgxf skills + an AI runtime*. Yet many of the threats SISAI
> collects and analyzes (prompt injection, data poisoning, supply chain, skill-ecosystem poisoning) **target
> exactly AI systems like SISAI itself**. Thus SISAI is both a "tool that protects others" and a "target that
> must protect itself." This document specifies that self-defense design. (Basis: the workspace analysis of AI-abuse hacking methods, cases, and solutions §3, §5, §6, §8)

## Threat → SISAI exposure → backbone defense

| Threat (summary) | Risk to SISAI | Backbone defense |
|---|---|---|
| **Prompt injection** (OWASP #1) | Malicious instructions hidden in collected threat docs, READMEs, CVE descriptions | **Deterministic boundary** — ingested text cannot change the control flow of `core/` (data ≠ instructions). core has no stdlib/AI dependency on outside input |
| **Data poisoning** (5 docs → 90%) | Manipulated samples infiltrate the threat/defense corpus | **ledger fingerprint + provenance tracking** — `fingerprint` identifies identical/similar entries, `provenance` verifies the source. Unverified defenses cannot feed back into the corpus |
| **Supply chain** (LiteLLM, 40k in 40 min) | Referenced open source/packages become a contamination source | **External-first but verification-gated** — an external defense is recorded only with `verification.passed` + an implementation. AIBOM perspective |
| **Skill-ecosystem poisoning** (314 malicious) | Tampering with vendored pg/pgf/pgxf or MCP | **Self-contained + integrity** — skills are vendored inside the project (0 external dynamic loading), and `validate` confirms skill presence. Channel/corpus fingerprints are pinned |

## Invariants (enforced in code)

1. **Data ≠ instructions**: `core/` is pure determinism (stdlib). No collected string triggers branching/execution.
   AI judgment (understanding/design) happens only in the meta layer (skills), and its output is used only after
   validation against the backbone contract (schema).
2. **Feedback only after verification**: `defense_to_corpus_entry` raises `ValueError` unless `is_verified`
   (passed + implementations). An unverified defense cannot poison the corpus.
3. **Reuse fingerprint gate**: channels, threats, and defenses are recorded exactly once via `fingerprint`
   (idempotent). This blocks duplicate-injection amplification.
4. **Atomic writes**: ledger/corpus/registry use `atomic_write_json` (temp + os.replace) — uncorruptible even
   during a crash.
5. **defensive-only**: output is detection/prevention/reports. Weaponized output (working exploits, automated
   targeted attacks) is out of design scope and is not eligible for loading into the corpus/ledger.

## v1.4 self-verification gates (strengthen the invariants above)

The SISAIImprove @v1.4 backbone adds deterministic gates that harden self-defense (all opt-in +
grandfather, so existing suites never regress — see `docs/ARCHITECTURE.md` §5b):

- **ProvenanceGate** (`core/sisai_provenance`) strengthens *Prompt injection* + *Data poisoning* defense:
  source-supplied provenance is **stripped** before the gate (anti fail-open — a collected page cannot
  self-assert `verified`), trust is **host-derived** (`authority_from_url`, never AI-judged), and unverified
  threats are **quarantined** rather than ingested (`ingest-threats --quarantine`).
- **CritiqueGate** (`is_critiqued`, wired in `record-defense --require-critique`) extends invariant #2: a
  multi-lens critique must pass before a defense's first record.
- **AdversarialVerify + HeldoutBench** (`engines/adversarial`, `core/sisai_verify`): defenses are hardened
  against red-team variants and graded on a **structurally frozen holdout** — the loop writes only
  `split in {tune, adversarial}` (`atomic_append_samples` refuses `holdout`), so the benchmark cannot be
  gamed. Holdout independence is a *mechanism*, not a label.
- **CrossModelRoles** (`roles_disjoint`): Author != Holdout != Judge (binding pairs) per suite — a
  cross-model layer on top of the structural freeze, so no single runtime authors, benchmarks, and judges
  the same suite.
- **DeterminismGuard** (`tests/test_determinism_boundary.py`): an AST test enforcing invariant #1 in CI —
  `core/`+`engines/` carry no clock/RNG/network/subprocess imports and no `AI_` symbols in `core/`.

## Operational recommendations (meta layer — AI runtime)

- Process ingested input **in isolation** (separate context / minimized tool permissions). Never promote external text to system instructions.
- Record new channel/corpus entries together with a **source signature/hash** (provenance) before adoption.
- Vendored skills/MCP follow a **whitelist + version pinning**; re-verify (`validate`) on any change.
- Autonomous external actions (blocking/distribution) only for **what passed the gates**; hard-to-reverse actions require human approval.
