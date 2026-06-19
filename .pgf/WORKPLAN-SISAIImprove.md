# WORKPLAN-SISAIImprove — execute DESIGN @v1.4 into the backbone

> Source: `.pgf/DESIGN-SISAIImprove.md` @v1.4. POLICY: surgical, stdlib-only in core/+engines/,
> every increment keeps `python -m unittest discover -s tests -q` GREEN and `sisai_validate.py` PASS.
> defensive-only. No commit unless asked.

## POLICY
- `max_verify_cycles: 2` · `determinism: core/+engines/ pure (enforced by DeterminismGuard test)`
- **No-regress rule**: all new gates are advisory-until-provisioned + grandfather (the 11 suites/seed
  have no provenance/critique/split/role entry → must NOT start failing).
- Increment boundary = a green test run. Wiring that changes live behavior comes AFTER its pure
  primitives + schemas + seed migration exist.

## Sequence (status: done / in-progress / designing / blocked)

```
ExecV14 // implement @v1.4 (in-progress)
    INC1_PureCore // pure primitives + schemas + determinism test + unit tests (done)
        SchemaContracts // threat.provenance(+source_sha256,authority enum); defense.critique; sample + role-registry schemas; registered (done)
        ProvenanceCore // sisai_provenance: DOMAIN_AUTHORITY, host_from_url(re), authority_from_url, is_provenance_verified, strip_incoming_provenance (done)
        CritiqueCore // sisai_provenance: is_critiqued(defense) pure gate (done)
        VerifyLib // core/sisai_verify.py: MIN_HOLDOUT, metrics, verify_suite (split-aware advisory gate) (done)
        DetectLib // core/sisai_detect.py: is_inert_indicator, compile_rule, scan, blue_run (done)
        RolesGate // sisai_verify: index_role_registry + roles_disjoint (advisory; binding pairs only) (done)
        DeterminismTest // tests/test_determinism_boundary.py: AST scan core/+engines/ (done)
        UnitTests // tests/test_v14_core.py: 17 cases, all green; full suite 67 OK; validate PASS (done)
    INC2_Wiring // live behavior — opt-in gates, grandfather (done)
        IngestWire // ingest_threats(+quarantine_path,+fetch_provenance): strip -> overlay fetcher prov -> gate -> verified|quarantine; legacy when path absent (done) @dep:ProvenanceCore,SchemaContracts
        RecordWire // record_defense(+require_critique): is_critiqued on FIRST record only; grandfather recorded; default off (done) @dep:CritiqueCore
        QuarantineLifecycle // _quarantine_append: fp-dedup store + reason/at; CLI --quarantine flag (done) @dep:ProvenanceCore
        CLIWireGates // sisai.py: --require-critique, --quarantine, --fetch-provenance flags (opt-in, default legacy) (done)
        SeedMigration // NOT NEEDED for INC2 — seed threats stay grandfathered (null-prov, no gate unless provisioned); holdout-split seeds deferred to when verify_suite is wired live (designing)
    INC3_Engines // engines/ adversarial loop + routing (done)
        AtomicAppendSamples // core/sisai_detect: append split in {tune,adversarial} ONLY (holdout unwritable); inert+split asserts (done)
        AdversarialVerify // engines/adversarial: bounded red/blue loop, injected cognition, no-regress harden, budget_exhausted=fail-closed (done) @dep:DetectLib,VerifyLib,AtomicAppendSamples
        AuthorRouting // engines/adversarial: route_author over category map (deterministic; pairs with roles_disjoint) (done) @dep:RolesGate
    CLIWire // sisai.py gate flags wired in INC2; adversarial loop is meta-layer-driven (injected cognition), not a deterministic CLI cmd (done) @dep:INC2_Wiring
```

## Verification criteria per node
- **SchemaContracts**: new/extended schemas stay in stdlib walker subset; `validate_schemas_in_subset` clean; `validate_layout` finds the new files.
- **ProvenanceCore/CritiqueCore/VerifyLib/DetectLib/RolesGate**: pure (no forbidden imports, no `AI_` symbol); unit-tested truth tables incl. fail-closed + grandfather paths.
- **DeterminismTest**: AST scan asserts core/ AND engines/ free of {time,datetime,random,secrets,socket,urllib,requests,http,ftplib,subprocess,asyncio} (+aliases), no os.urandom/system/popen, no `AI_` symbols in core/.
- **Each increment**: full unittest suite GREEN + `core/sisai_validate.py .` PASS.

## Current
- **INC1 DONE**: pure primitives + schemas + determinism test + unit tests.
- **INC2 DONE** (this session): ProvenanceGate wired into `ingest_threats` (opt-in `quarantine_path`;
  strip page-claimed prov → overlay fetcher ground-truth → host-derived gate → verified|quarantine);
  CritiqueGate wired into `record_defense` (opt-in `require_critique`, first-record only, grandfather);
  `_quarantine_append` fp-dedup; CLI flags `--quarantine`/`--fetch-provenance`/`--require-critique`.
  +8 wiring tests; **full suite 75 OK**; `sisai_validate.py .` PASS. Gates default OFF → 11 suites
  never regress; anti-fail-open proven (self-claimed provenance is stripped → quarantined).
- **INC3 DONE** (this session): `core/sisai_detect.atomic_append_samples` (structural holdout freeze —
  loop can only write tune/adversarial); `engines/adversarial.adversarial_verify` (bounded red/blue loop,
  injected cognition so engines/ stays pure, no-regress harden, `budget_exhausted`=fail-closed);
  `engines/adversarial.route_author` (per-category, deterministic). +9 tests; **full suite 84 OK**;
  determinism guard green over `engines/adversarial.py`; `sisai_validate.py .` PASS.
- **INC4 DONE** (this session): `seed/sample-suite.json` (sample.schema-valid; frozen-holdout sized so
  `verify_suite` gates on the holdout — negation-aware rule passes, naive rule fails on hard negatives) +
  `seed/role-registry.json` (role-registry.schema-valid EXAMPLE template; `roles_disjoint` passes;
  production assignment stays gated) + `docs/ARCHITECTURE.md` §5b note. +5 tests; **full suite 89 OK**.
- **@v1.4 backbone implementation COMPLETE** across INC1–INC4. Committed on `feat/sisaiimprove-v14`
  (INC1-3 = 388decc; INC4 follow-up). NOT pushed (separate gated decision). Adversarial cognition
  (gen_variants/harden) is supplied by the meta-layer (skills) at runtime, by design.
