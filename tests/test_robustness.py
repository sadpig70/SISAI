#!/usr/bin/env python3
"""Adversarial robustness regression — every shipped detector must generalize beyond its frozen
holdout to the paraphrase/synonym/obfuscation variants in the split=adversarial rows, WITHOUT
regressing the frozen holdout gate.

This locks in the depth pass: baseline adversarial recall was 0.0 (rules over-fit to holdout
phrasing); after hardening it is 1.0 with no holdout regression and no ReDoS skips.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from core import sisai_verify as ver
from core.sisai_detect import compile_rule
from calibration import robustness as rb
from tools import detect_pr as dp, prompt_shield as ps
from domain import fraud_aml as fa, trust_safety as tsf, pharmacovigilance as pv

SAMPLES = os.path.join(ROOT, "seed", "sample-suite.json")


def _detectors():
    d = {c: (dp.predict_for(c),
             [{"id": i["id"], "regex": dp.RULE_BUNDLES[c]["guard"] + r".*(?:" + i["regex"] + r")"}
              for i in dp.RULE_BUNDLES[c]["indicators"]]) for c in dp.RULE_BUNDLES}
    d["llm-prompt-injection"] = (ps.predict(), ps._patterns())
    d["fraud-aml"] = (fa.predict(), fa._patterns())
    d["trust-safety"] = (tsf.predict(), tsf._patterns())
    d["pharmacovigilance"] = (pv.predict(), pv._patterns())
    return d


class TestAdversarialRobustness(unittest.TestCase):
    def test_every_category_has_adversarial_rows(self):
        for cat in _detectors():
            self.assertTrue(rb.adversarial_rows(cat), f"{cat}: no adversarial variants")

    def test_recall_and_fp(self):
        rep = rb.measure_all()
        for cat, r in rep["per_category"].items():
            self.assertGreaterEqual(r["recall"], 0.8, f"{cat}: adversarial recall {r['recall']} — misses {r['misses']}")
            self.assertEqual(r["false_positives"], 0, f"{cat}: FP on benign variants {r['fp_texts']}")
        self.assertEqual(rep["summary"]["false_positives_total"], 0)
        self.assertGreaterEqual(rep["summary"]["min_recall"], 0.8)


class TestNoHoldoutRegression(unittest.TestCase):
    def test_holdout_gates_still_pass_and_no_redos(self):
        samples = read_json(SAMPLES)
        for cat, (predict, pats) in _detectors().items():
            sub = [s for s in samples if s.get("category") == cat]
            r = ver.verify_suite(sub, predict)
            self.assertTrue(r["passed"], f"{cat}: holdout regressed: {r}")
            self.assertEqual(r["holdout"]["precision"], 1.0, cat)
            self.assertEqual(r["holdout"]["fp"], 0, cat)
            skipped = sum(compile_rule({"patterns": [p]})[1] for p in pats)
            self.assertEqual(skipped, 0, f"{cat}: {skipped} pattern(s) over-length/uncompilable")


if __name__ == "__main__":
    unittest.main()
