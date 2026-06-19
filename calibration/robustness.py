#!/usr/bin/env python3
"""SISAI — adversarial robustness measurement (deterministic, defensive-only).

Measures how well each shipped detector generalizes BEYOND its frozen holdout, against paraphrase /
synonym / obfuscation variants the meta-layer authored into the `split=adversarial` rows of
seed/sample-suite.json. This exposes single-fixture over-fitting honestly: a detector that aces its
holdout can still miss "deactivate the WAF" if it only learned "disable".

For each category it reports adversarial recall (malicious variants caught) + false positives on
benign paraphrases. The adversarial split is TRAIN-ONLY (never gated); this is a diagnostic, and the
frozen holdout remains the binding gate elsewhere.

Pure: predictors are the shipped, pure detection bundles; no clock/AI/network.

CLI:  python calibration/robustness.py [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from tools import detect_pr as dp                                      # noqa: E402
from tools import prompt_shield as ps                                  # noqa: E402
from domain import fraud_aml as fa                                     # noqa: E402
from domain import trust_safety as ts                                  # noqa: E402
from domain import pharmacovigilance as pv                             # noqa: E402


def predictors() -> dict:
    """category -> pure predictor text->bool, for every shipped detector."""
    d = {c: dp.predict_for(c) for c in dp.RULE_BUNDLES}
    d["llm-prompt-injection"] = ps.predict()
    d["fraud-aml"] = fa.predict()
    d["trust-safety"] = ts.predict()
    d["pharmacovigilance"] = pv.predict()
    return d


def adversarial_rows(category, samples_path=None):
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    return [s for s in (read_json(samples_path) or [])
            if s.get("category") == category and s.get("split") == "adversarial"]


def measure_category(category, predict, samples_path=None) -> dict:
    rows = adversarial_rows(category, samples_path)
    mal = [r for r in rows if r.get("label") == "malicious"]
    ben = [r for r in rows if r.get("label") == "benign"]
    caught = [r["text"] for r in mal if predict(r.get("text", ""))]
    misses = [r["text"] for r in mal if not predict(r.get("text", ""))]
    fps = [r["text"] for r in ben if predict(r.get("text", ""))]
    return {"category": category, "n_malicious": len(mal), "n_benign": len(ben),
            "recall": round(len(caught) / len(mal), 4) if mal else None,
            "false_positives": len(fps), "misses": misses, "fp_texts": fps}


def measure_all(samples_path=None) -> dict:
    preds = predictors()
    report = {c: measure_category(c, preds[c], samples_path) for c in sorted(preds)}
    recalls = [r["recall"] for r in report.values() if r["recall"] is not None]
    fp_total = sum(r["false_positives"] for r in report.values())
    return {"per_category": report,
            "summary": {"categories": len(report),
                        "min_recall": min(recalls) if recalls else None,
                        "mean_recall": round(sum(recalls) / len(recalls), 4) if recalls else None,
                        "false_positives_total": fp_total}}


def _main(argv) -> int:
    rep = measure_all()
    if "--json" in argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    s = rep["summary"]
    print(f"adversarial robustness: min_recall={s['min_recall']} mean_recall={s['mean_recall']} "
          f"fp_total={s['false_positives_total']}")
    for c, r in rep["per_category"].items():
        flag = "" if (r["recall"] == 1.0 and r["false_positives"] == 0) else "  <-- gap"
        print(f"  {c:26s} recall={r['recall']} fp={r['false_positives']}{flag}")
        for m in r["misses"]:
            print(f"      MISS: {m}")
        for f in r["fp_texts"]:
            print(f"      FP:   {f}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
