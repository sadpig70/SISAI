#!/usr/bin/env python3
"""SISAI B0-5 — cross-model rule-quality calibration (deterministic, defensive-only).

An in-repo formalization of the cm_test battery scorer (VERDICT M2: the sandbox lived in
`_workspace/`, gitignored — this is the committed, self-contained version). It quantifies how well a
detection rule, authored by some model/runtime, GENERALIZES — graded on a category's frozen holdout
with the same gates the SISAI loop trusts, then aggregated across categories per model (mean AND min,
so a model strong on one category cannot hide behind the mean).

Reuses SISAI's own primitives: `core/sisai_verify.metrics` for the confusion matrix and the
`MAX_PATTERN_LEN` length bound. Adds, at this edge (NOT in core), a heuristic nested-quantifier ReDoS
refusal — core only length-bounds; here an untrusted author rule with catastrophic backtracking
(`(a+)+`, `(\\w+)*`) is refused outright. Pure: no clock/AI/network.

Gates (all surfaced, never silently averaged away):
  - unsafe   : pattern refused (over-length or nested-quantifier ReDoS) -> not run
  - errors   : pattern uncompilable -> surfaced
  - precision floor (0.85) + degenerate (flags >=80% of benign) -> gate gated_f1 to 0.0
  - leakage_suspect : recall==1.0 AND precision==1.0 (implausibly perfect; flag, do not zero)

Category data: any category in seed/sample-suite.json with a sized frozen holdout.

CLI:
    python calibration/score.py --dogfood [--category <cat>]   # self-test the gates
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_detect import MAX_PATTERN_LEN                          # noqa: E402
from core.sisai_verify import metrics as _metrics                      # noqa: E402

PRECISION_FLOOR = 0.85
# Catastrophic-backtracking heuristic: an unbounded quantifier (* / +) on a group whose body ALSO
# holds an unbounded quantifier, e.g. (a+)+ , (a*)* , (\w+)* . Bounded {0,n}, (?!...), single
# quantifiers and alternations are intentionally NOT refused (the hard-negative rules need them).
_DANGEROUS = re.compile(r"\([^()]*[*+][^()]*\)\s*[*+]")


def safe_compile(patterns):
    """Compile rule patterns with a ReDoS guard. Returns (compiled, unsafe, errors)."""
    compiled, unsafe, errors = [], 0, 0
    for p in patterns or []:
        src = (p or {}).get("regex")
        if not isinstance(src, str):
            errors += 1
            continue
        if len(src) > MAX_PATTERN_LEN or _DANGEROUS.search(src):
            unsafe += 1
            continue
        try:
            compiled.append(re.compile(src))
        except re.error:
            errors += 1
    return compiled, unsafe, errors


def holdout_samples(category, samples_path=None):
    """The frozen holdout rows for a category (the grade set)."""
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    return [s for s in (read_json(samples_path) or [])
            if s.get("category") == category and s.get("split") == "holdout"]


def score_rule(rule, samples):
    """Author-style score of one rule on a holdout. gated_f1 is the headline; gates are surfaced."""
    pats, unsafe, errors = safe_compile((rule or {}).get("patterns", []))
    n_ben = sum(1 for s in samples if s.get("label") == "benign")
    if not pats:
        return {"submitted": True, "patterns": 0, "unsafe": unsafe, "errors": errors,
                "recall": 0.0, "precision": 0.0, "f1": 0.0, "gated_f1": 0.0, "degenerate": False}
    m = _metrics(lambda t: any(rx.search(t or "") for rx in pats), samples)
    rec, prec = m["recall"], m["precision"]
    f1 = round(2 * prec * rec / (prec + rec), 3) if (prec + rec) else 0.0
    benign_match_rate = round(m["fp"] / n_ben, 3) if n_ben else 0.0
    degenerate = benign_match_rate >= 0.8
    precision_gate = prec >= PRECISION_FLOOR
    return {"submitted": True, "patterns": len(pats), "unsafe": unsafe, "errors": errors,
            "recall": rec, "precision": prec, "f1": f1, "tp": m["tp"], "fp": m["fp"],
            "tn": m["tn"], "fn": m["fn"], "precision_gate": precision_gate, "degenerate": degenerate,
            "leakage_suspect": rec == 1.0 and prec == 1.0,
            "gated_f1": f1 if (precision_gate and not degenerate) else 0.0}


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else 0.0


def aggregate(submissions, categories, samples_path=None):
    """submissions = {model_id: {category: rule}}. Returns {per_category, aggregate}.
    aggregate[model] reports mean AND min gated_f1 across categories + surfaced gate flags."""
    per_cat = {}
    for cat in categories:
        hold = holdout_samples(cat, samples_path)
        per_cat[cat] = {m: score_rule(subs.get(cat, {}), hold) for m, subs in submissions.items()}
    agg = {}
    for m in submissions:
        scored = [per_cat[c][m] for c in categories if per_cat[c][m].get("patterns")]
        gfs = [s["gated_f1"] for s in scored]
        flags = sorted({k for c in categories for s in [per_cat[c][m]]
                        for k in ("degenerate", "leakage_suspect") if s.get(k)})
        agg[m] = {
            "categories_scored": len(scored),
            "categories_total": len(categories),
            "mean_gated_f1": _mean(gfs),
            "min_gated_f1": min(gfs) if gfs else 0.0,
            "unsafe_total": sum(per_cat[c][m].get("unsafe", 0) for c in categories),
            "errors_total": sum(per_cat[c][m].get("errors", 0) for c in categories),
            "flags": flags,
        }
    return {"per_category": per_cat, "aggregate": agg}


# ---- dogfood: prove every gate fires on a (possibly new) category ------------------------------

def dogfood(category="access-control-weakening", samples_path=None):
    """Self-test the gates on a category's holdout. Returns (ok, report)."""
    hold = holdout_samples(category, samples_path)
    n_mal = sum(s["label"] == "malicious" for s in hold)
    n_ben = sum(s["label"] == "benign" for s in hold)

    mal_texts = [s.get("text", "") for s in hold if s.get("label") == "malicious"]

    catch_all = score_rule({"patterns": [{"regex": "(?i)."}]}, hold)
    redos = score_rule({"patterns": [{"regex": "(a+)+$"}]}, hold)
    malformed = score_rule({"patterns": [{"regex": 12345}]}, hold)
    # category-agnostic, derived from the holdout itself:
    # perfect -> a rule that MEMORIZES every holdout malicious line (one literal pattern each) ->
    #            recall==1.0 AND precision==1.0 -> leakage_suspect fires (genuine overfit/leak signal).
    perfect = score_rule({"patterns": [{"regex": "(?i)" + re.escape(t)} for t in mal_texts]}, hold)
    # winner -> a normal partial rule (memorizes all but the last two) -> recall<1.0, precision 1.0,
    #           gated_f1>0, NOT leakage -> clean PASS.
    winner = score_rule({"patterns": [{"regex": "(?i)" + re.escape(t)} for t in mal_texts[:-2]]}, hold)

    checks = {
        "sized": n_mal >= 5 and n_ben >= 4,
        "degenerate_gated": catch_all["gated_f1"] == 0.0 and catch_all["degenerate"],
        "redos_refused": redos["patterns"] == 0 and redos["unsafe"] == 1,
        "malformed_surfaced": malformed["errors"] == 1 and malformed["patterns"] == 0,
        "leakage_flag_fires": perfect["leakage_suspect"] is True,
        "winner_passes": winner["gated_f1"] > 0 and winner["precision"] >= PRECISION_FLOOR
                         and not winner["leakage_suspect"],
    }
    report = {"category": category, "holdout": {"malicious": n_mal, "benign": n_ben},
              "catch_all": catch_all, "redos": redos, "malformed": malformed,
              "perfect": perfect, "winner": winner, "checks": checks}
    return all(checks.values()), report


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    if "--dogfood" in argv:
        ok, report = dogfood(_opt(argv, "--category", "access-control-weakening"))
        print(json.dumps(report["checks"], ensure_ascii=False, indent=2))
        print("DOGFOOD:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    sys.stderr.write("usage: python calibration/score.py --dogfood [--category <cat>]\n")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
