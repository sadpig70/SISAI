#!/usr/bin/env python3
"""SISAI — per-row semantic-verdict ingestion & hybrid evaluation (deterministic, defensive-only).

The next step after independent holdouts (0/7 keyword). An external runtime acts as a SEMANTIC JUDGE:
blind to the labels and the rules, it classifies each holdout row by MEANING. We inject that as the
semantic layer of `engines/detect_hybrid` and measure keyword-vs-hybrid quantitatively — with three
parties kept distinct so no one grades their own work:

    author  = the rule author (meta-layer)            — from calibration/curation-provenance.json
    curator = who curated the holdout (+ labels)       — from seed/independent-holdouts/<cat>.json
    judge   = who gave the per-row semantic verdicts   — from the submission

Binding gate (STRICTER than core.roles_disjoint, which leaves curator≠judge optional): all THREE must
be distinct. The curator knows the labels, so the judge must never be the curator (leakage), nor the
author (self-enhancement). Multiple judges → majority vote (single-judge bias control).

Submission: {category, judge_model, blind:{labels_hidden,rules_hidden}, verdicts:[{text, verdict}]}.
Pure: no clock/AI/network; the judge's verdicts are DATA (never executed).

CLI:
    python calibration/semantic_ingest.py --ingest <submission.json>
    python calibration/semantic_ingest.py --verify [--category C] [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json, atomic_write_json                 # noqa: E402
from core.sisai_verify import index_role_registry, roles_disjoint      # noqa: E402
from engines.detect_hybrid import evaluate as hybrid_evaluate          # noqa: E402
from calibration.independent_eval import (                             # noqa: E402
    load_independent_holdout, _rule_author, ROLE_REGISTRY_PATH)
from calibration.robustness import predictors                          # noqa: E402

SEM_DIR = os.path.join(ROOT, "seed", "independent-holdouts", "semantic")
RECALL_FLOOR, PRECISION_FLOOR = 0.8, 0.85


def roles_three_way(category, judge_model, role_idx=None) -> dict:
    """All three parties distinct (binding). Registry roles_disjoint is advisory on top."""
    author = _rule_author(category)
    curator = (load_independent_holdout(category) or {}).get("curator_model")
    parties = [author, curator, judge_model]
    ok = all(parties) and len(set(parties)) == 3
    if role_idx is None:
        role_idx = index_role_registry(read_json(ROLE_REGISTRY_PATH) or {})
    rd = roles_disjoint(category, role_idx)
    return {"ok": ok, "author": author, "curator": curator, "judge": judge_model,
            "registry_gate": rd["gate"], "registry_ok": rd["ok"]}


def validate_semantic(sub: dict) -> list:
    """Structural + independence problems with a semantic submission (empty == valid)."""
    if not isinstance(sub, dict):
        return ["submission is not an object"]
    problems = []
    cat, judge = sub.get("category"), sub.get("judge_model")
    if not cat:
        problems.append("missing category")
    if not judge:
        problems.append("missing judge_model")
    holdout = load_independent_holdout(cat) if cat else None
    if not holdout:
        return problems + [f"no independent holdout ingested for category {cat!r}"]
    verdicts = sub.get("verdicts")
    if not isinstance(verdicts, list) or not verdicts:
        return problems + ["missing/empty verdicts"]
    seen = {}
    for v in verdicts:
        if not isinstance(v, dict) or v.get("verdict") not in ("malicious", "benign") or not v.get("text"):
            problems.append(f"bad verdict row: {v}")
        else:
            seen[v["text"]] = v["verdict"]
    hold_texts = {r["text"] for r in holdout["rows"]}
    missing = hold_texts - set(seen)
    if missing:
        problems.append(f"{len(missing)} holdout row(s) not judged (coverage incomplete)")
    if judge:
        tw = roles_three_way(cat, judge)
        if not tw["ok"]:
            problems.append(f"roles not 3-way distinct (author={tw['author']}, curator={tw['curator']}, judge={judge})")
    return problems


def ingest(path: str) -> dict:
    sub = read_json(path)
    problems = validate_semantic(sub)
    if problems:
        return {"status": "rejected", "problems": problems[:6]}
    d = os.path.join(SEM_DIR, sub["category"])
    os.makedirs(d, exist_ok=True)
    atomic_write_json(os.path.join(d, f"{sub['judge_model']}.json"), sub)
    return {"status": "ingested", "category": sub["category"], "judge_model": sub["judge_model"],
            "verdicts": len(sub["verdicts"])}


def load_verdicts(category) -> dict:
    """{judge_model: {text: is_malicious(bool)}} for every ingested judge of a category."""
    d = os.path.join(SEM_DIR, category)
    out = {}
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            sub = read_json(os.path.join(d, fn)) or {}
            out[sub.get("judge_model", fn[:-5])] = {v["text"]: v["verdict"] == "malicious"
                                                    for v in sub.get("verdicts", []) if v.get("text")}
    return out


def semantic_predict(category, judge=None):
    """text->bool. A single judge, or majority vote across all judges (ties -> malicious, fail-safe)."""
    verds = load_verdicts(category)
    if judge is not None:
        m = verds.get(judge, {})
        return lambda t: bool(m.get(t, False))

    def majority(t):
        votes = [j.get(t, False) for j in verds.values()]
        if not votes:
            return False
        return sum(votes) * 2 >= len(votes)            # tie -> malicious (fail-safe for detection)
    return majority


def evaluate(category) -> dict:
    """keyword vs hybrid (per judge + majority consensus) on the independent holdout."""
    holdout = load_independent_holdout(category)
    if not holdout:
        return {"category": category, "error": "no holdout"}
    rows = holdout["rows"]
    kw = predictors().get(category)
    verds = load_verdicts(category)
    per_judge = {j: hybrid_evaluate(rows, kw, semantic_predict(category, j)) for j in verds}
    consensus = hybrid_evaluate(rows, kw, semantic_predict(category)) if verds else None
    return {"category": category, "judges": sorted(verds), "per_judge": per_judge, "consensus": consensus}


def verify_independence_hybrid(category) -> dict:
    """Data-driven: independent iff >=1 valid 3-way-distinct judge AND the (consensus) hybrid clears the
    holdout (recall>=0.8, precision>=0.85, FP=0)."""
    verds = load_verdicts(category)
    if not verds:
        return {"category": category, "independent": False, "reason": "no semantic judge ingested"}
    for j in verds:
        if not roles_three_way(category, j)["ok"]:
            return {"category": category, "independent": False, "reason": f"judge {j} not 3-way distinct"}
    ev = evaluate(category)["consensus"] or {}
    h = ev.get("hybrid", {})
    ok = h.get("recall", 0) >= RECALL_FLOOR and h.get("precision", 0) >= PRECISION_FLOOR and h.get("fp", 1) == 0
    return {"category": category, "independent": ok, "judges": sorted(verds),
            "keyword": ev.get("keyword"), "hybrid": h,
            "reason": "hybrid clears the independent holdout with distinct judge(s)" if ok
                      else "hybrid did not clear the independent holdout"}


def report() -> dict:
    cats = sorted(c for c in predictors() if load_verdicts(c))
    rows = [verify_independence_hybrid(c) for c in cats]
    return {"categories": rows, "judged_total": len(cats),
            "independent_total": sum(1 for r in rows if r["independent"])}


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
        out = verify_independence_hybrid(cat) if cat else report()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    sys.stderr.write("usage: python calibration/semantic_ingest.py --ingest <sub.json> | --verify [--category C]\n")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
