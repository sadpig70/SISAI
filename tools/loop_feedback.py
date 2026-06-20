#!/usr/bin/env python3
"""SISAI — loop feedback: close the self-improvement spiral (deterministic edge, defensive-only).

Connects detection back into the backbone: detection findings become THREATS, and the
INDEPENDENTLY-VERIFIED detector becomes a recorded DEFENSE in the corpus, so the next synthesis round
reuses it. Honest by construction:

  - The defense recorded is the TWO-LAYER detector (keyword prefilter + meta-layer semantic), whose
    verification is the INDEPENDENT hybrid result (distinct curator + judge), not the single-author
    holdout. A category whose hybrid is NOT independent yields `verification.passed = False`, so
    `record_defense` REJECTS it (no overstated defenses enter the corpus).
  - The keyword bundle alone is documented as a prefilter (independent recall 0.17–0.33), never sold as
    the verified control.

`--plan` is a dry run (no state change). `--commit` records the verified defenses to the ledger+corpus
(runtime state) — an explicit, idempotent closure step. Pure-import; `now` injected.

CLI:
    python tools/loop_feedback.py --plan [--json]
    python tools/loop_feedback.py --commit [--ledger .sisai/ledger.json --corpus .sisai/corpus.json] --now D
    python tools/loop_feedback.py --findings <flagged.json> --category C --now D   # findings -> threats (dry)
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_provenance import is_verified                          # noqa: E402
from sisai import record_defense                                       # noqa: E402
from calibration.robustness import predictors                          # noqa: E402
from calibration.semantic_ingest import verify_independence_hybrid      # noqa: E402

CATEGORIES = tuple(sorted(predictors()))


def detector_defense(category: str) -> dict:
    """Build a defense object for a category's two-layer detector, with HONEST verification:
    passed iff the hybrid is independently validated (distinct curator + judge)."""
    v = verify_independence_hybrid(category)
    h = v.get("hybrid") or {}
    passed = bool(v.get("independent"))
    method = (f"independent hybrid (distinct curator+judge): recall={h.get('recall')} "
              f"precision={h.get('precision')} fp={h.get('fp')}; keyword-only independent=0/7 (prefilter)")
    return {
        "defense_id": f"DEF-detect-{category}",
        "title": f"{category} two-layer detector (keyword prefilter + meta-layer semantic)",
        "kind": "designed", "origin": "pgf-sisai",
        "covers_category": category,
        "controls": ["keyword-prefilter", "meta-layer-semantic", "frozen-holdout-gate", "independent-validation"],
        "verification": {"method": method, "passed": passed},
        "implementations": [{"rule_id": f"detect/{category}", "artifact_path": "tools/detect.py"}],
        "source_channels": ["independent-curation", "semantic-judge"],
    }


def findings_to_threats(category: str, texts, now: str) -> list:
    """Flagged detection texts -> threat candidates (the RUN_THREAT_INTEL feed; data only)."""
    out = []
    for t in texts or []:
        if not isinstance(t, str) or not t.strip():
            continue
        out.append({"title": f"detected [{category}]: {t.strip()}", "category": category,
                    "techniques": ["detected"], "recency": now, "evidence": [t.strip()]})
    return out


def feedback_plan() -> dict:
    """Dry run: per category, the defense that WOULD feed back and whether it is verified to do so."""
    rows = []
    for cat in CATEGORIES:
        d = detector_defense(cat)
        rows.append({"category": cat, "verified": is_verified(d),
                     "passed": d["verification"]["passed"], "defense_id": d["defense_id"]})
    return {"categories": rows,
            "verified_total": sum(1 for r in rows if r["verified"]),
            "total": len(rows)}


def commit(ledger_path: str, corpus_path: str, now: str) -> dict:
    """Record every independently-verified detector defense (idempotent). Rejects unverified ones."""
    results = []
    for cat in CATEGORIES:
        d = detector_defense(cat)
        res = record_defense(d, ledger_path, corpus_path, now=now)
        results.append({"category": cat, "status": res.get("status"), "why": res.get("why")})
    return {"results": results,
            "recorded": sum(1 for r in results if r["status"] in ("closed", "already_recorded"))}


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    if "--findings" in argv:
        cat = _opt(argv, "--category")
        texts = read_json(_opt(argv, "--findings")) or []
        print(json.dumps(findings_to_threats(cat, texts, _opt(argv, "--now", "1970-01-01")),
                         ensure_ascii=False, indent=2))
        return 0
    if "--commit" in argv:
        led = _opt(argv, "--ledger") or os.path.join(ROOT, ".sisai", "ledger.json")
        cor = _opt(argv, "--corpus") or os.path.join(ROOT, ".sisai", "corpus.json")
        print(json.dumps(commit(led, cor, _opt(argv, "--now", "1970-01-01")), ensure_ascii=False, indent=2))
        return 0
    if "--plan" in argv:
        print(json.dumps(feedback_plan(), ensure_ascii=False, indent=2))
        return 0
    sys.stderr.write("usage: python tools/loop_feedback.py --plan | --commit [--ledger P --corpus P] "
                     "--now D | --findings <f.json> --category C\n")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
