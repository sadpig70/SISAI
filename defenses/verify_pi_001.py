#!/usr/bin/env python3
"""Evidence-based verification for PI-001 (defensive detection accuracy).

Runs the PI-001 detector over a labeled benign/malicious suite and measures
true/false positives. This is the `verification.method` referenced by the
defense record: a defense may only be recorded when this gate passes
(docs/INSTRUCTIONS-sisai-cycle.md §3, core/sisai_provenance.is_verified).

Pass criteria (defensive posture — never miss an attack, keep FPs low):
    recall    == 1.0     (every malicious sample flagged)
    precision >= 0.85    (few benign samples mis-flagged)

Exit code 0 on pass, 1 on fail. Pure stdlib, deterministic.
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
from defenses.detectors.pi_detector import load_rule, scan  # noqa: E402

_SAMPLES = os.path.join(_HERE, "tests", "pi_samples.jsonl")
RECALL_MIN = 1.0
PRECISION_MIN = 0.85


def load_samples(path: str = _SAMPLES) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run() -> dict:
    rule = load_rule()
    samples = load_samples()
    tp = fp = tn = fn = 0
    errors = []
    for s in samples:
        pred = scan(s["text"], rule)["malicious"]
        actual = s["label"] == "malicious"
        if pred and actual:
            tp += 1
        elif pred and not actual:
            fp += 1
            errors.append(("false_positive", s["id"], s.get("note", "")))
        elif not pred and not actual:
            tn += 1
        else:
            fn += 1
            errors.append(("false_negative", s["id"], s.get("note", "")))
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    passed = recall >= RECALL_MIN and precision >= PRECISION_MIN
    return {
        "method": "pi-detection-suite",
        "samples": len(samples),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "recall": round(recall, 4), "precision": round(precision, 4),
        "thresholds": {"recall_min": RECALL_MIN, "precision_min": PRECISION_MIN},
        "errors": errors,
        "passed": passed,
    }


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r["passed"] else 1)
