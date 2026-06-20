#!/usr/bin/env python3
"""SISAI — cross-model BATTERY scorer (in-repo formalization of the cm_test sandbox; VERDICT M2).

This is the CANONICAL multi-task, multi-model capability harness. It scores model/runtime SUBMISSIONS
across the four cm_test tasks — author / red / holdout / judge — against the committed canonical
fixtures in `seed/sample-suite.json`, then aggregates per model (mean AND min across categories).

It replaces the gitignored `_workspace/cm_test` battery: nothing of value stays stranded in the
sandbox, and there is one authoritative, committed, tested path. Reuses `calibration/score.py`
(safe_compile + ReDoS refusal, score_rule gated_f1/precision-floor/degenerate/leakage) for the author
task and ports the red/holdout/judge scorers here. Pure: no clock/AI/network.

A submission: {model_id: {category: {rule:{patterns}, variants:[...], holdout:[...], critique:{findings}}}}
  - rule    : the author's detection rule (scored on the frozen holdout)
  - variants: red-team malicious paraphrases (scored for novelty/distinctness vs tune)
  - holdout : a proposed holdout set (scored for discriminating power vs a baseline)
  - critique: a judge's findings on a flawed rule (scored for flaws found)
Every field is optional; absent tasks score {"submitted": False}.

CLI:  python calibration/battery.py --submissions subs.json [--json]
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from calibration.score import safe_compile, score_rule, holdout_samples, _mean  # noqa: E402

MIN_HOLDOUT = {"malicious": 5, "benign": 4}
INERT_MAX_LEN = 240
# Judge planted-flaw cues (anchored): F1 = overbroad/FP/negation, F2 = missing coverage.
F1_TERMS = re.compile(r"(?i)\b(overbroad|too\s+broad|false[ -]?positive|negation|negated|prohibit)\b")
F2_TERMS = re.compile(r"(?i)\b(miss(es|ing)?|recall|coverage|too\s+narrow|turn\s+off|bypass|synonym|obfuscat\w*|evad\w*)\b")


def tune_texts(category, samples_path=None):
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    return {s.get("text", "") for s in (read_json(samples_path) or [])
            if s.get("category") == category and s.get("split") == "tune"}


def _inert(t):
    return isinstance(t, str) and 0 < len(t) <= INERT_MAX_LEN and "\n" not in t


def _norm(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def score_red(variants, tune_set):
    """Red-team variants: count, inertness, novelty vs tune, intra-set distinctness."""
    if not variants:
        return {"submitted": False}
    texts = [v.get("text", "") for v in variants if isinstance(v, dict)]
    return {"submitted": True, "count": len(texts),
            "inert_pct": round(sum(_inert(t) for t in texts) / len(texts), 3) if texts else 0.0,
            "novel": sum(1 for t in texts if t not in tune_set),
            "distinct_among": len({_norm(t) for t in texts})}


def score_holdout(rows, tune_set, base_pats):
    """Proposed holdout: sizing + discriminating power (rows a weak baseline gets WRONG)."""
    if not rows:
        return {"submitted": False}
    mal = sum(1 for r in rows if r.get("label") == "malicious")
    ben = sum(1 for r in rows if r.get("label") == "benign")
    hard = 0
    for r in rows:
        pred = any(rx.search(r.get("text", "") or "") for rx in base_pats)
        if pred != (r.get("label") == "malicious"):
            hard += 1
    return {"submitted": True, "malicious": mal, "benign": ben,
            "sized": mal >= MIN_HOLDOUT["malicious"] and ben >= MIN_HOLDOUT["benign"],
            "distinct_from_tune": sum(1 for r in rows if r.get("text") not in tune_set),
            "hard_vs_baseline": hard}


def score_judge(critique):
    """Judge findings: did they catch the two planted flaw classes (overbroad FP, missing coverage)?"""
    if not critique:
        return {"submitted": False}
    findings = critique.get("findings") if isinstance(critique, dict) else None
    if isinstance(findings, list) and findings:
        text = " ".join(f"{x.get('issue','')} {x.get('evidence','')} {x.get('fix','')}" for x in findings)
        mode = "structured"
    else:
        text = json.dumps(critique, ensure_ascii=False)
        mode = "blob"
    f1, f2 = bool(F1_TERMS.search(text)), bool(F2_TERMS.search(text))
    return {"submitted": True, "mode": mode, "flaws_found": int(f1) + int(f2),
            "flaw1_fp_overbroad": f1, "flaw2_missing_coverage": f2}


def score_submission(category, sub, baseline_rule=None, samples_path=None):
    hold = holdout_samples(category, samples_path)
    tset = tune_texts(category, samples_path)
    base_pats, _, _ = safe_compile((baseline_rule or {}).get("patterns", []))
    return {
        "author": score_rule(sub.get("rule", {}), hold) if sub.get("rule") else {"submitted": False},
        "red": score_red(sub.get("variants"), tset),
        "holdout": score_holdout(sub.get("holdout"), tset, base_pats),
        "judge": score_judge(sub.get("critique")),
    }


def battery(submissions, categories, baselines=None, samples_path=None):
    """submissions = {model: {category: {...tasks}}}. Returns {per_category, aggregate}.
    aggregate[model] = mean AND min author gated_f1 across categories + surfaced gate flags."""
    baselines = baselines or {}
    per_cat = {}
    for cat in categories:
        per_cat[cat] = {m: score_submission(cat, subs.get(cat, {}), baselines.get(cat), samples_path)
                        for m, subs in submissions.items()}
    agg = {}
    for m in submissions:
        authors = [per_cat[c][m]["author"] for c in categories]
        scored = [a for a in authors if a.get("submitted") and a.get("patterns")]
        gfs = [a.get("gated_f1", 0.0) for a in scored]
        flags = sorted({k for c in categories for a in [per_cat[c][m]["author"]]
                        for k in ("degenerate", "leakage_suspect") if a.get(k)})
        agg[m] = {"categories_scored": len(scored), "categories_total": len(categories),
                  "author_mean_gated_f1": _mean(gfs), "author_min_gated_f1": min(gfs) if gfs else 0.0,
                  "flags": flags}
    return {"per_category": per_cat, "aggregate": agg}


def _main(argv) -> int:
    path = None
    for i, a in enumerate(argv):
        if a == "--submissions" and i + 1 < len(argv):
            path = argv[i + 1]
    if not path:
        sys.stderr.write("usage: python calibration/battery.py --submissions <subs.json> [--json]\n")
        return 2
    subs = read_json(path) or {}
    cats = sorted({c for m in subs.values() for c in m})
    out = battery(subs, cats)
    print(json.dumps(out["aggregate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
