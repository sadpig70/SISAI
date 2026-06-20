#!/usr/bin/env python3
"""SISAI — holdout independence protocol (deterministic, defensive-only, honest).

Closes the loop on the single-author gap: a passing holdout gate proves internal consistency and
paraphrase robustness, but NOT independent validation if the same party authored both the rule and the
holdout. This module MEASURES and GATES independence honestly — it never fabricates it.

Independence has two layers, both required for an "independent" verdict:
  1. FACTUAL (binding): the recorded curator of the category's holdout differs from the rule author
     (`calibration/curation-provenance.json` — the honest ground truth, not placeholders).
  2. LABEL (defense-in-depth): the committed role registry makes the suite's roles disjoint
     (`core/sisai_verify.roles_disjoint` over `seed/role-registry.json`).

Verdicts: independent | single_author | roles_conflict | unprovisioned. The current real categories
are all single_author (the meta-layer authored both) — surfaced, not hidden. `require_independent`
is the gate a future workflow uses to accept ONLY independently-validated categories.

Pure: no clock/AI/network.

CLI:  python calibration/independence.py [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_verify import index_role_registry, roles_disjoint      # noqa: E402

CURATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curation-provenance.json")
ROLE_REGISTRY_PATH = os.path.join(ROOT, "seed", "role-registry.json")


def _curation_index(path=None):
    data = read_json(path or CURATION_PATH) or {}
    return {e["category"]: e for e in data.get("entries", []) if e.get("category")}


def assess_category(category, curation_idx=None, role_idx=None) -> dict:
    """Independence verdict for one category. FACTUAL attribution is binding; roles are defense-in-depth."""
    curation_idx = _curation_index() if curation_idx is None else curation_idx
    if role_idx is None:
        role_idx = index_role_registry(read_json(ROLE_REGISTRY_PATH) or {})
    cur = curation_idx.get(category)
    if not cur:
        return {"category": category, "verdict": "unprovisioned", "independent": False,
                "reason": "no curation-provenance record"}
    factual = cur.get("rule_author") and cur.get("holdout_curator") and \
        cur.get("rule_author") != cur.get("holdout_curator") and bool(cur.get("independent"))
    rd = roles_disjoint(category, role_idx)
    if not factual:
        verdict, reason = "single_author", "holdout curated by the rule author (not independent)"
    elif not rd["ok"]:
        verdict, reason = "roles_conflict", "role registry roles not disjoint"
    else:
        verdict, reason = "independent", "distinct curator + disjoint roles"
    return {"category": category, "verdict": verdict, "independent": verdict == "independent",
            "reason": reason, "rule_author": cur.get("rule_author"),
            "holdout_curator": cur.get("holdout_curator"), "roles_gate": rd["gate"]}


def require_independent(category, curation_idx=None, role_idx=None) -> bool:
    """Gate: True ONLY when the category is independently validated. Use to accept independent evidence."""
    return assess_category(category, curation_idx, role_idx)["independent"]


def report(categories=None) -> dict:
    """Fleet independence report. Defaults to every category in the curation provenance record."""
    cur_idx = _curation_index()
    role_idx = index_role_registry(read_json(ROLE_REGISTRY_PATH) or {})
    cats = categories if categories is not None else sorted(cur_idx)
    rows = [assess_category(c, cur_idx, role_idx) for c in cats]
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"categories": rows, "counts": counts,
            "independent_total": sum(1 for r in rows if r["independent"]),
            "note": "single_author is the honest current state for the shipped detectors; the "
                    "protocol/gate is ready for real independent curation."}


def _main(argv) -> int:
    rep = report()
    if "--json" in argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"independence: {rep['independent_total']}/{len(rep['categories'])} independent | "
              f"counts={rep['counts']}")
        for r in rep["categories"]:
            print(f"  {r['category']:26s} {r['verdict']:14s} ({r['rule_author']} / {r['holdout_curator']})")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
