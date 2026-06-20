#!/usr/bin/env python3
"""SISAI — independent-curation ingestion & evaluation (deterministic, defensive-only).

Turns the holdout-independence gap from "measured" into "executed". An EXTERNAL runtime (a curator
DISTINCT from the rule author) curates a frozen holdout for a category WITHOUT seeing the detector
rules; this module ingests that submission, stores it apart from the single-author sample-suite, and
re-grades the shipped detector on it. Only then can a category be called INDEPENDENTLY validated —
driven by data + role disjointness, never by a manual flag.

Submission format (one JSON file per category):
    {
      "category": "config-tampering",
      "curator_model": "grok-...",                 # MUST differ from the rule author
      "provenance": {"note": "...", "blind_to_rules": true},
      "rows": [{"label": "malicious", "text": "..."}, ...]   # sized: >=5 malicious, >=4 benign
    }

A category is INDEPENDENT iff: an ingested holdout exists, is sized + schema-valid + inert, the curator
differs from the rule author, the role registry is disjoint (`roles_disjoint`), AND the shipped
detector clears it (recall >= 0.8, precision >= 0.85, FP == 0). Pure: no clock/AI/network.

CLI:
    python calibration/independent_eval.py --ingest <submission.json>
    python calibration/independent_eval.py --verify [--category C] [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json, atomic_write_json                 # noqa: E402
from core.sisai_schema import validate_against_schema, schema_path      # noqa: E402
from core.sisai_detect import is_inert_indicator                       # noqa: E402
from core.sisai_verify import metrics, index_role_registry, roles_disjoint  # noqa: E402
from calibration.independence import _curation_index                   # noqa: E402
from calibration.robustness import predictors                          # noqa: E402

INDEP_DIR = os.path.join(ROOT, "seed", "independent-holdouts")
ROLE_REGISTRY_PATH = os.path.join(ROOT, "seed", "role-registry.json")
MIN = {"malicious": 5, "benign": 4}
RECALL_FLOOR, PRECISION_FLOOR = 0.8, 0.85


def _rule_author(category):
    """The recorded rule author for a category (defaults to 'meta-layer')."""
    return (_curation_index().get(category) or {}).get("rule_author", "meta-layer")


def validate_submission(sub: dict, root=ROOT) -> list:
    """Structural problems with a curation submission (empty list == valid)."""
    problems = []
    if not isinstance(sub, dict):
        return ["submission is not an object"]
    if not sub.get("category"):
        problems.append("missing category")
    if not sub.get("curator_model"):
        problems.append("missing curator_model")
    rows = sub.get("rows")
    if not isinstance(rows, list) or not rows:
        return problems + ["missing/empty rows"]
    sp = schema_path(root, "sample")
    mal = ben = 0
    for r in rows:
        if validate_against_schema(r, sp):
            problems.append(f"row fails sample schema: {r}")
        elif not is_inert_indicator(r):
            problems.append(f"row not inert/labeled: {r}")
        else:
            mal += r.get("label") == "malicious"
            ben += r.get("label") == "benign"
    if mal < MIN["malicious"] or ben < MIN["benign"]:
        problems.append(f"holdout not sized (have {mal} mal / {ben} ben; need {MIN['malicious']}/{MIN['benign']})")
    cur, auth = sub.get("curator_model"), _rule_author(sub.get("category", ""))
    if cur and cur == auth:
        problems.append(f"curator '{cur}' == rule author (not independent)")
    return problems


def ingest(path: str) -> dict:
    """Validate a submission and store it under seed/independent-holdouts/<category>.json. Returns result."""
    sub = read_json(path)
    problems = validate_submission(sub)
    if problems:
        return {"status": "rejected", "problems": problems[:6]}
    from calibration.rounds import is_stale                              # freshness: no teach-to-benchmark
    prev = load_independent_holdout(sub["category"])
    if prev and is_stale({r.get("text") for r in sub["rows"]}, {r.get("text") for r in prev["rows"]}):
        return {"status": "rejected", "problems": ["stale: identical to the stored frozen holdout — "
                "a new round needs fresh rows (no teach-to-the-benchmark)"]}
    os.makedirs(INDEP_DIR, exist_ok=True)
    dest = os.path.join(INDEP_DIR, f"{sub['category']}.json")
    atomic_write_json(dest, sub)
    return {"status": "ingested", "category": sub["category"], "curator_model": sub["curator_model"],
            "rows": len(sub["rows"]), "path": dest}


def load_independent_holdout(category):
    p = os.path.join(INDEP_DIR, f"{category}.json")
    return read_json(p)


def evaluate(category, predict=None) -> dict:
    """Grade the shipped detector on the ingested independent holdout. None if none ingested."""
    sub = load_independent_holdout(category)
    if not sub:
        return {"submitted": False}
    if predict is None:
        predict = predictors().get(category)
    if predict is None:
        return {"submitted": True, "error": f"no predictor for {category}"}
    m = metrics(predict, sub["rows"])
    return {"submitted": True, "curator_model": sub.get("curator_model"),
            "recall": m["recall"], "precision": m["precision"], "fp": m["fp"],
            "tp": m["tp"], "tn": m["tn"], "fn": m["fn"]}


def verify_independence(category, predict=None, role_idx=None) -> dict:
    """Binding, data-driven independence verdict for a category."""
    sub = load_independent_holdout(category)
    if not sub:
        return {"category": category, "independent": False, "reason": "no independent holdout ingested"}
    problems = validate_submission(sub)
    if problems:
        return {"category": category, "independent": False, "reason": "submission invalid", "problems": problems[:4]}
    if role_idx is None:
        role_idx = index_role_registry(read_json(ROLE_REGISTRY_PATH) or {})
    rd = roles_disjoint(category, role_idx)
    if not rd["ok"]:
        return {"category": category, "independent": False, "reason": "role registry roles not disjoint"}
    ev = evaluate(category, predict)
    passed = (ev.get("recall", 0) >= RECALL_FLOOR and ev.get("precision", 0) >= PRECISION_FLOOR
              and ev.get("fp", 1) == 0)
    return {"category": category, "independent": passed, "curator_model": sub.get("curator_model"),
            "eval": ev, "roles_gate": rd["gate"],
            "reason": "independent: distinct curator + disjoint roles + detector clears the holdout"
                      if passed else "detector did not clear the independent holdout"}


def report() -> dict:
    """Fleet view of which categories have a passing independent holdout ingested."""
    cats = sorted(c for c in predictors())
    rows = [verify_independence(c) for c in cats]
    return {"categories": rows,
            "independent_total": sum(1 for r in rows if r["independent"]),
            "ingested_total": sum(1 for r in rows if load_independent_holdout(r["category"]))}


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    if "--ingest" in argv:
        res = ingest(_opt(argv, "--ingest"))
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["status"] == "ingested" else 1
    if "--verify" in argv:
        cat = _opt(argv, "--category")
        out = verify_independence(cat) if cat else report()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    sys.stderr.write("usage: python calibration/independent_eval.py --ingest <sub.json> | --verify [--category C]\n")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
