# SISAIImprove Design @v:1.4

> Source: `_workspace/intergrated_ref_report.md` (P0 set). Scope: P0-3 provenance quarantine,
> P0-1 adversarial red/blue verify, P0-2 held-out benchmark, P0-4 judge critique.
> History: @v:1.0 → round-1 (2C/8H) → @v:1.1 → round-2 (2C/3H) → @v:1.2 → @v:1.3 (cross-model roles,
> from cm_test) → **@v:1.4 (this): round-3 self-review fixes on CrossModelRoles (C1 grandfather,
> H1 mechanism-vs-label, H2 minimal-pair gate, H3 schema, H4 category map)**.
> See `REVIEW-SISAIImprove.md`; cm_test evidence: `_workspace/cm_test/battery/results/VERDICT-battery.md`
> + `DESIGN-v1.3-input.md` (operator-approved promotion).
>
> **Governing principle (inviolable):** cognition (fetch/match, variant-gen, hardening, critique)
> lives in the **AI meta-layer** and emits **schema-validated attestations**; deterministic `core/`
> only *gates* on them. No clock/RNG/network/AI in `core/`. defensive-only.
>
> **v1.2 keystone corrections (from round-2):**
> 1. **Holdout is structurally author-disjoint** — `split:holdout` is a *frozen, independently-sourced*
>    benchmark; the adversarial loop **physically cannot write it** (core enforces append only to
>    `tune|adversarial`). Independence is a mechanism, not a self-asserted `authored_by` label (R1).
> 2. **Holdout gate is per-suite & advisory-until-provisioned** — a suite without a sized frozen
>    holdout keeps its **legacy full-set gate authoritative**; `insufficient_holdout` is logged, not
>    `passed:False`. No fail-closed break of the 11 suites (R2).
> 3. **Authority is deterministically derived from the source URL host**, never from AI judgment (R5).
> 4. **`is_inert_indicator` is storage-shape hygiene, NOT a weapon detector**; the real defensive-only
>    guarantee is the deterministic boundary (core never executes collected text) (R4).
>
> **v1.3/v1.4 addition — cross-model role independence (lifts the v1.2 single-runtime residual):**
> **Two distinct independence properties (do not conflate — this was the v1.2 R1 point):**
> (i) **Structural freeze (binding, v1.2)** — the loop physically cannot write `split:holdout`; the holdout
> is frozen/committed/read-only. This is a *mechanism*, guaranteed regardless of which model curated it.
> (ii) **Cross-model authorship disjointness (added quality layer)** — the model whose cognition authored a
> detector should not also author that suite's benchmark or judge its own rule, to avoid *correlated blind
> spots*. This is enforced by `roles_disjoint` over a committed RoleRegistry. **It is label-based** (it
> trusts the registry's model-ids), so it is a *defense-in-depth quality layer on top of (i)*, never a
> replacement for the structural guarantee. (Residual: two ids for the same underlying model defeat (ii)
> but not (i).)
> 1. **Author = per-category routing, not one global model** — capability does NOT transfer across detector
>    categories (cm_test battery: every model's MIN gated_f1 = 0; each strong in a *different* category).
>    A fixed single Author is both weak (blind spots) and an independence bottleneck. Route per category.
> 2. **Holdout curator default = configurable (cm_test tentative Tier-1: grok-build)** — only cross-round-
>    stable curation signal, but single-fixture-per-category (tiering, not fine ranking), so it is a
>    *configurable default with fallback*, not a hardcoded constant. Bound by the binding pair Author≠Holdout.
> 3. **Red & Judge = commodity roles** — cm_test metrics saturate (all models clear the bar; no fine
>    ranking). Assign by cost/latency, subject only to the binding pair Judge ≠ Author-of-what-it-judges
>    (curator≠judge is NOT required — second-order). (Confident Judge ranking, if ever needed, requires a
>    separate Judge-only metric-hardening round — out of scope here.)
> 4. **Gate-neutrality lesson** — a model-gating check must refuse only genuinely unsafe inputs; cm_test's
>    coarse ReDoS heuristic falsely refused 33/93 legitimate negation patterns and masked capability. Use
>    the principled v3 check; the real defense is a regex execution-timeout sandbox (carried forward).

## Gantree

```
SISAIImprove // P0 self-verification hardening (designing) @v:1.4
    ProvenanceGate // P0-3: verified-or-quarantine ingest (designing)
        FetchIsolation // meta: isolated fetch sub-agent (no write tools/shared ctx) -> tuple only (designing)
        AuthorityFromUrl // core: derive authority from URL host vs DOMAIN_WHITELIST (NOT AI) (designing)
        IsProvVerified // core: gate(verified + host∈whitelist + 64hex sha256) (designing) @dep:AuthorityFromUrl
        StripIncomingProv // core: drop source-supplied provenance before gate (designing)
        QuarantineLifecycle // core: fp-dedup store + transient(retry) vs rejected + status count (designing) @dep:IsProvVerified
        IngestWire // core: extend ingest_threats (kw quarantine_path) verified->threats else->quarantine (designing) @dep:IsProvVerified,StripIncomingProv,QuarantineLifecycle
    AdversarialVerify // P0-1: red/blue loop (meta-layer; engines/) (designing)
        VariantGenMeta // meta: AI_generate_indicator_variants (designing)
        InertHygiene // core: is_inert_indicator = storage-shape check only (designing)
        BlueRun // core: pure detector.scan over variants -> misses (designing)
        AtomicAppendSamples // core: atomic append; MAY write split∈{tune,adversarial} ONLY (designing) @dep:InertHygiene,BlueRun
        DryLoop // meta(engines): bounded; harden; reject if holdout precision drops; caps->budget_exhausted (designing) @dep:VariantGenMeta,AtomicAppendSamples
    HeldoutBench // P0-2: honest generalization metric (designing)
        FrozenHoldout // data: independently-sourced, committed, read-only holdout rows (designing)
        SplitConvention // sample.split: tune|holdout|adversarial (split-less->tune) (designing)
        VerifyLib // core(sisai_verify.py): pure metrics/split helper (designing) @dep:SplitConvention
        PerSuiteGate // gate: legacy full-set authoritative until FrozenHoldout sized; then holdout-only; adversarial=train-only (designing) @dep:VerifyLib,FrozenHoldout
    CritiqueGate // P0-4: multi-lens judge before FIRST record (designing)
        CritiqueMeta // meta: AI_make_judge (correctness/evade/fp/scope) (designing)
        IsCritiqued // core: pure gate is_critiqued(defense) (designing)
        RecordWire // core: critique required only on first record; grandfather already-recorded (designing) @dep:IsCritiqued
    SchemaContracts // schema additions (walker-subset, anchored patterns) (designing)
        # threat.provenance += source_sha256(^[0-9a-f]{64}$) + authority enum ; defense.critique ; sample.split ; quarantine.schema
        # (v1.4) role_registry.schema (committed contract; author/holdout_curator/judge model-ids per suite) ; suite.category (taxonomy for AuthorRouting)
        # register in SCHEMA_NAMES/EXPECTED_FILES + validate_live + schema_features regression
    ModuleOwnership // assign new core primitives to modules (designing)
        # core/sisai_detect.py: is_inert_indicator, BlueRun ; core/sisai_verify.py: metrics+MIN_HOLDOUT ;
        # reuse core/sisai_io.atomic append ; AUTHORITY_FROM_URL+DOMAIN_WHITELIST in sisai_provenance ;
        # adversarial_verify (loop) in engines/ (NOT core/)
    DeterminismGuard // cross-cutting enforced test (needs-verify) @dep:ProvenanceGate,AdversarialVerify,HeldoutBench,CritiqueGate
        DeterminismTest // tests/test_determinism_boundary.py: AST scan over core/ AND engines/ (designing)
        # forbid imports {time,datetime,random,secrets,socket,urllib,requests,http,ftplib,subprocess,asyncio};
        # resolve import aliases; catch os.urandom/os.system/os.popen by attribute; no AI_ symbols in core/
    CrossModelRoles // v1.4: multi-runtime authorship-disjointness ON TOP OF the structural freeze (designing) @dep:HeldoutBench
        RoleRegistry // data: committed contract — per-suite {author_model, holdout_curator_model, judge_model} (designing)
        DisjointnessGate // core: pure gate; binding pairs author!=holdout & author!=judge; UNREGISTERED suite -> advisory (designing) @dep:RoleRegistry
        AuthorRouting // meta: AI_route_author_by_category over suite.category map (no single global author) (designing) @dep:RoleRegistry,SchemaContracts
        # grandfather: suite absent from RoleRegistry -> roles_unprovisioned (logged, NON-blocking) — mirrors PerSuiteGate/RecordWire.
        # default curator configurable (cm_test tentative grok-build); commodity Red/Judge by cost. Structural freeze (§i)
        # is the binding guarantee; this label-based layer (§ii) is defense-in-depth. cm_test = capability evidence ONLY (not corpus).
```

## PPR (round-2 hardened)

### ProvenanceGate — authority from URL, not from AI

```python
DOMAIN_AUTHORITY = {                                   # core (pure): deterministic origin trust
    "nvd.nist.gov": "NVD", "services.nvd.nist.gov": "NVD",
    "cve.org": "MITRE", "cve.mitre.org": "MITRE",
    "github.com": "GHSA", "arxiv.org": "arXiv", "export.arxiv.org": "arXiv"}

def authority_from_url(url: str) -> str | None:        # core — trust anchor is the host, not the page
    host = urlsplit_host(url)                           # stdlib urllib.parse is parsing-only... see note*
    return DOMAIN_AUTHORITY.get(host)
# *NOTE: url PARSING is pure string work; to keep core import-clean, parse host with a small regex in core
#  (no network). urllib is NOT imported in core (DeterminismTest forbids it) — use re-based host extract.

def is_provenance_verified(threat: dict) -> bool:     # core (pure) — in sisai_provenance.py
    p = threat.get("provenance") or {}
    return (bool(p.get("verified"))
            and authority_from_url(p.get("source_url","")) is not None         # host-derived, page can't self-claim
            and authority_from_url(p["source_url"]) == p.get("authority")       # AI-claimed authority must match host
            and bool(re.fullmatch(r"[0-9a-f]{64}", p.get("source_sha256",""))))
    # AI match verdict is ADVISORY input to 'verified'; the binding trust is host∈whitelist (deterministic).

# meta (isolated) sets provenance; ingest STRIPS any source-supplied provenance first (anti fail-open).
```

### AdversarialVerify — inert = hygiene; holdout unwritable by loop

```python
def is_inert_indicator(sample: dict) -> bool:          # core (sisai_detect.py) — STORAGE HYGIENE, not weapon-gate
    """Stored as inert single-line DATA of the same shape as existing labeled rows.
    The defensive-only guarantee comes from the deterministic boundary (core never executes
    collected text), NOT from this check. This only keeps the corpus well-formed."""
    t = sample.get("text", "")
    return (0 < len(t) <= 240 and "\n" not in t and sample.get("label") in ("malicious","benign"))

def atomic_append_samples(code, rows):                 # core (sisai_io) — STRUCTURAL author-disjointness
    assert all(r["split"] in ("tune","adversarial") for r in rows)   # loop can NEVER write split=holdout
    assert all(is_inert_indicator(r) for r in rows)
    atomic_write_jsonl(path_of(code), existing + rows)

def adversarial_verify(code, max_rounds=8, max_variants=200, dry_rounds=2):   # META (engines/, not core)
    rule, detector = load(code); seen=set(); dry=0; rounds=0
    base = verify_suite(code); base_prec = base["holdout"]["precision"] if base.get("holdout") else 1.0
    while dry < dry_rounds and rounds < max_rounds and len(seen) < max_variants:
        rounds += 1
        variants = [v for v in VariantGenMeta(rule, threat_of(code), seen) if is_inert_indicator(v)]
        seen |= {v["text"] for v in variants}
        misses = BlueRun(detector, variants)
        if not misses: dry += 1; continue
        cand = AI_harden_patterns(rule, misses); m = verify_suite_with(cand)
        hp = m["holdout"]["precision"] if m.get("holdout") else base_prec     # handle insufficient_holdout shape
        if hp < max(0.85, base_prec): continue                               # reject regressive harden
        dry=0; atomic_append_samples(code, misses); rule=cand; detector=recompile(rule)
    return {"status": "converged" if dry>=dry_rounds else "budget_exhausted", "rounds": rounds}
    # budget_exhausted => defense NOT recorded (fail-closed). Convergence is best-effort, not guaranteed.
```

### HeldoutBench — frozen holdout, per-suite advisory gate

```python
MIN_HOLDOUT = {"malicious": 5, "benign": 4}            # core (sisai_verify.py), module-level

def verify_suite(code: str) -> dict:                   # core; VerifyLib = pure metrics/split helper
    detector, samples = load_suite(code)               # suite keeps its OWN loader (no central coupling)
    sp = lambda s: [x for x in samples if x.get("split","tune") == s]   # split-less -> tune
    hold = sp("holdout")
    sized = (count(hold,"malicious") >= MIN_HOLDOUT["malicious"]
             and count(hold,"benign") >= MIN_HOLDOUT["benign"])
    if not sized:
        # PerSuiteGate: holdout not provisioned -> legacy FULL-SET gate stays authoritative (non-blocking)
        full = metrics(detector, samples)
        return {"holdout": None, "reason": "insufficient_holdout", "gate": "legacy-fullset",
                "passed": (full.recall == 1.0 and full.precision >= 0.85)}
    g = metrics(detector, hold)                         # provisioned -> gate on FROZEN holdout ONLY
    return {"holdout": g, "gate": "holdout", "tune": metrics(detector, sp("tune")),
            "passed": (g.recall == 1.0 and g.precision >= 0.85)}
    # FrozenHoldout rows are committed + read-only; adversarial_verify cannot author them (atomic_append asserts).
    # adversarial split is NEVER in the gate (train-only). 11 suites pass via legacy gate until expansion.
```

### CritiqueGate — first-record only (unchanged from v1.1; was RESOLVED)

```python
def is_critiqued(defense) -> bool: return bool((defense.get("critique") or {}).get("passed"))   # core
def record_defense(defense, ledger, corpus, now, threats=None):     # EXTENDS existing
    if not is_verified(defense): return reject("not verified")
    already = is_consumed(key(defense), ledger)["consumed"]
    if not already and not is_critiqued(defense): return reject("critique not passed")  # first-record only
    ... existing idempotent record/dedup/corpus/threat-mark/self-heal (grandfathers the 11) ...
```

### CrossModelRoles — authorship-disjointness ON TOP OF the structural freeze (v1.4, from cm_test)

```python
# ROLE_REGISTRY is a COMMITTED data contract (role_registry.schema), NOT an AI runtime attestation.
# It adds property (ii) cross-model authorship-disjointness; property (i) structural freeze (v1.2,
# atomic_append asserts split!=holdout) remains the BINDING guarantee. This layer is label-based
# (trusts model-ids) -> defense-in-depth, never a replacement for (i).
ROLE_REGISTRY = {                                      # committed; default curator configurable
    "<suite-code>": {"author_model": "<per-category>", "holdout_curator_model": "<default: grok-build>",
                     "judge_model": "<commodity>"}}

def roles_disjoint(suite: str, reg: dict = ROLE_REGISTRY) -> dict:    # core (pure) — no AI, no I/O
    """Advisory-until-provisioned, mirroring PerSuiteGate/RecordWire (do NOT regress the 11 suites)."""
    r = reg.get(suite)
    if not r:                                          # C1: unregistered -> grandfather, NON-blocking
        return {"ok": True, "gate": "roles_unprovisioned"}            # logged, not passed:False
    a, h, j = r.get("author_model"), r.get("holdout_curator_model"), r.get("judge_model")
    if not (a and h and j):
        return {"ok": False, "gate": "roles_incomplete"}             # registered but malformed -> fail-closed
    # H2: enforce ONLY the binding pairs — Author!=Holdout (uncorrelated benchmark) AND Author!=Judge
    # (no self-grading). curator!=judge is second-order and NOT required.
    return {"ok": a != h and a != j, "gate": "roles"}

# wire-in (RecordWire): first-record only, same shape as is_critiqued — grandfathers already-recorded.
#   v = roles_disjoint(suite_of(defense))
#   if v["gate"] != "roles_unprovisioned" and not v["ok"]: return reject("role overlap")

def AI_route_author_by_category(suite: str, category_map: dict) -> str:   # META (engines/) — not core
    """Pick the author model for suite.category (capability does not transfer -> per-category). Red/Judge
    are commodity (assign by cost) subject to roles_disjoint. cm_test informs the choice; NEVER recorded
    into ledger/corpus (capability evidence only)."""
```

## DeterminismGuard (enforced, expanded scope)

```python
# tests/test_determinism_boundary.py
FORBIDDEN_IMPORTS = {"time","datetime","random","secrets","socket","urllib","requests",
                     "http","ftplib","subprocess","asyncio"}
FORBIDDEN_ATTRS   = {("os","urandom"),("os","system"),("os","popen")}
def test_core_and_engines_are_deterministic():
    for f in glob("core/*.py") + glob("engines/*.py"):
        tree = ast.parse(read(f))
        assert not (import_names_with_aliases(tree) & FORBIDDEN_IMPORTS), f   # resolve `import x as y`
        assert not attribute_calls(tree) & FORBIDDEN_ATTRS, f                 # os.urandom/system/popen
        assert "AI_" not in symbols(tree), f                                  # no cognition in core/engines
```

## Acceptance criteria (v1.4)
- Holdout independence is **structural** (loop can't write holdout; holdout is frozen/committed), not a label.
- 11 suites keep passing (legacy full-set gate until each suite's frozen holdout is provisioned & sized).
- Authority is **host-derived** (deterministic); injected page text cannot set authority/verified past the gate.
- `is_inert_indicator` documented as storage hygiene; defensive-only rests on the deterministic boundary.
- core/ AND engines/ determinism enforced by committed AST test (imports+aliases+os.* attrs+no AI_).
- All fail-closed: unverified→quarantine, no-critique→reject, capped loop→budget_exhausted(no record), small holdout→legacy gate.
- **(v1.4)** Role-disjointness enforces only the binding pairs (Author≠Holdout, Author≠Judge); an unregistered
  suite is `roles_unprovisioned` (advisory, non-blocking — the 11 suites never regress); RoleRegistry + suite.category
  are committed schema contracts; author is routed per category. Model choice is a label-based defense-in-depth layer
  over the binding structural freeze, informed by cm_test evidence, never recorded into ledger/corpus.

## Review status
- Round 1 (@v1.0): REVISE (C2,H8). Round 2 (@v1.1): REVISE — Risk C 2 (R1 author-independence, R2 size/staging), H 3 (R3,R4,R5); Architecture PASS. **All resolved at @v1.2.**
- @v1.2 residual (single-runtime holdout independence is bounded) → **addressed at @v1.3**: cross-model
  role-disjointness (`CrossModelRoles`) makes Author/Holdout/Judge multi-runtime, backed by cm_test capability
  evidence (operator-approved promotion 2026-06-19). Structural freeze remains the binding guarantee; the model
  layer adds disjointness on top.
- Round-3 self-review (PGF 3-perspective on @v1.3) → **@v1.4**: fixed C1 (roles_disjoint would have fail-closed
  the 11 suites → grandfather advisory), H1 (split the two independence properties; model layer is label-based
  defense-in-depth, not the guarantee), H2 (gate only the binding pairs, not curator≠judge), H3 (RoleRegistry +
  suite.category as committed schema contracts), H4 (per-category routing keyed on suite.category), and M1/M3
  (configurable curator default; `AI_route_author_by_category` naming). **Verdict: PASS (Critical=0, High=0).**
- Residual (documented, accepted): (M2) cm_test evidence lives in the gitignored `_workspace/` sandbox — for a
  committed design, promote `VERDICT-battery.md` to a committed path or embed key numbers; (general) cm_test is
  single-fixture-per-category (tiering, not fine ranking) and does not test independence itself — independence
  stays a *mechanism* here, not a measured score; model-id disjointness (ii) is label-based by construction.
