#!/usr/bin/env python3
"""SISAI adversarial-verify orchestration + author routing (engines/ — pure, stdlib, deterministic).

The red/blue hardening loop (P0-1) is a META-layer activity, but its CONTROL FLOW is deterministic and
lives here; the COGNITION is injected as callables so engines/ stays pure (no clock/AI/network/random —
the DeterminismGuard scans this file). The meta-layer (AI runtime) supplies:
  - gen_variants(rule, threat, seen) -> list[sample]   (red: paraphrase/obfuscate the directive)
  - harden(rule, misses) -> rule                       (blue: tighten patterns to catch the misses)
  - verify(rule) -> verify_suite-shaped dict           (grade on the frozen holdout; never regress)
The loop only ever appends split=adversarial via core.atomic_append_samples — it CANNOT write holdout.
budget_exhausted => the caller must NOT record the defense (fail-closed; convergence is best-effort).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sisai_detect import is_inert_indicator, compile_rule, blue_run, atomic_append_samples  # noqa: E402
from core.sisai_verify import PRECISION_FLOOR                                                     # noqa: E402


def _precision(verify_result: dict, fallback: float) -> float:
    """Precision from a verify_suite result; when no sized holdout exists, keep the prior value
    (no regression check is possible without a holdout) — mirrors the design PPR."""
    h = (verify_result or {}).get("holdout")
    return h["precision"] if h else fallback


def adversarial_verify(rule: dict, threat: dict, samples_path: str, *,
                       gen_variants, harden, verify,
                       max_rounds: int = 8, max_variants: int = 200, dry_rounds: int = 2) -> dict:
    """Bounded red/blue loop. Pure control flow over injected cognition. Returns
    {status: converged|budget_exhausted, rounds, rule, samples_added, variants_seen}."""
    seen = set()
    dry = rounds = added = 0
    base_prec = _precision(verify(rule), 1.0)
    while dry < dry_rounds and rounds < max_rounds and len(seen) < max_variants:
        rounds += 1
        variants = [v for v in (gen_variants(rule, threat, seen) or [])
                    if is_inert_indicator(v) and v.get("label") == "malicious" and v.get("text") not in seen]
        for v in variants:
            seen.add(v.get("text"))
        compiled, _ = compile_rule(rule)
        misses = blue_run(compiled, variants)
        if not misses:
            dry += 1
            continue
        cand = harden(rule, misses)
        if _precision(verify(cand), base_prec) < max(PRECISION_FLOOR, base_prec):
            continue                                              # reject a regressive harden
        dry = 0
        added += atomic_append_samples(samples_path, [{**m, "split": "adversarial"} for m in misses])
        rule = cand                                              # adopt the hardened rule
    return {"status": "converged" if dry >= dry_rounds else "budget_exhausted",
            "rounds": rounds, "rule": rule, "samples_added": added, "variants_seen": len(seen)}


def route_author(category: str, category_author_map: dict, default=None):
    """AuthorRouting (deterministic, DESIGN v1.4): pick the author model for a detector CATEGORY from the
    committed cm_test-evidence map — capability does not transfer, so there is no single global author.
    Unmapped categories fall back to `default` (the meta-layer chooses). The chosen assignment must still
    pass core.sisai_verify.roles_disjoint (Author!=Holdout, Author!=Judge)."""
    return (category_author_map or {}).get(category, default)
