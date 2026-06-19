#!/usr/bin/env python3
"""B0-5 — cross-model calibration package: DOGFOOD passes on a (new) category, every gate fires,
and the cross-model aggregate computes mean AND min gated_f1.

Acceptance (backlog B0-5): DOGFOOD PASS on a new category; all gates fire (degenerate -> gated_f1 0,
ReDoS -> refused, malformed -> surfaced, leakage flag fires, a normal rule passes); cross-model
aggregate yields mean + min across categories.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from calibration import score as cal
from tools import detect_pr as dp

NEW_CATS = ["supply-chain-tampering", "access-control-weakening"]   # added in B0-1, not in legacy cm_test


class TestDogfood(unittest.TestCase):
    def test_dogfood_passes_on_new_category(self):
        ok, report = cal.dogfood("access-control-weakening")
        self.assertTrue(ok, report["checks"])
        self.assertTrue(report["checks"]["sized"])

    def test_each_gate_fires(self):
        _, r = cal.dogfood("supply-chain-tampering")
        c = r["checks"]
        self.assertTrue(c["degenerate_gated"])     # catch-all -> gated_f1 0 + degenerate
        self.assertTrue(c["redos_refused"])        # (a+)+$ -> refused, 0 patterns, unsafe 1
        self.assertTrue(c["malformed_surfaced"])   # non-str regex -> errors, not silently dropped
        self.assertTrue(c["leakage_flag_fires"])   # perfect rule -> leakage_suspect
        self.assertTrue(c["winner_passes"])        # normal partial rule -> clean PASS


class TestScoreRuleGates(unittest.TestCase):
    def setUp(self):
        self.hold = cal.holdout_samples("config-tampering")

    def test_redos_nested_quantifier_refused(self):
        s = cal.score_rule({"patterns": [{"regex": "(a+)+$"}]}, self.hold)
        self.assertEqual(s["unsafe"], 1)
        self.assertEqual(s["patterns"], 0)

    def test_overlength_refused(self):
        s = cal.score_rule({"patterns": [{"regex": "a" * (cal.MAX_PATTERN_LEN + 1)}]}, self.hold)
        self.assertEqual(s["unsafe"], 1)

    def test_uncompilable_is_error_not_unsafe(self):
        s = cal.score_rule({"patterns": [{"regex": "([unclosed"}]}, self.hold)
        self.assertEqual(s["errors"], 1)
        self.assertEqual(s["unsafe"], 0)

    def test_degenerate_zeroes_gated_f1(self):
        s = cal.score_rule({"patterns": [{"regex": "(?i)."}]}, self.hold)
        self.assertTrue(s["degenerate"])
        self.assertEqual(s["gated_f1"], 0.0)

    def test_shipped_bundle_scores_clean_high(self):
        # the B0-1 bundle, scored by calibration, is a strong (perfect) rule -> gated_f1 == f1, leakage flag
        rule = dp._compose(dp.RULE_BUNDLES["config-tampering"])
        s = cal.score_rule(rule, self.hold)
        self.assertEqual(s["recall"], 1.0)
        self.assertEqual(s["precision"], 1.0)
        self.assertGreater(s["gated_f1"], 0.0)
        self.assertTrue(s["leakage_suspect"])      # 1.0/1.0 is implausibly perfect -> surfaced


class TestCrossModelAggregate(unittest.TestCase):
    def test_aggregate_mean_and_min(self):
        good = {c: dp._compose(dp.RULE_BUNDLES[c]) for c in NEW_CATS}     # passes both
        naive = {c: {"patterns": [{"regex": "(?i)."}]} for c in NEW_CATS}  # degenerate both
        submissions = {"model-good": good, "model-naive": naive}
        out = cal.aggregate(submissions, NEW_CATS)
        agg = out["aggregate"]
        self.assertIn("mean_gated_f1", agg["model-good"])
        self.assertIn("min_gated_f1", agg["model-good"])
        # min cannot exceed mean; naive is degenerate everywhere -> 0
        self.assertLessEqual(agg["model-good"]["min_gated_f1"], agg["model-good"]["mean_gated_f1"])
        self.assertEqual(agg["model-naive"]["mean_gated_f1"], 0.0)
        self.assertEqual(agg["model-naive"]["min_gated_f1"], 0.0)
        self.assertIn("degenerate", agg["model-naive"]["flags"])
        self.assertGreater(agg["model-good"]["min_gated_f1"], 0.0)


class TestCli(unittest.TestCase):
    def test_dogfood_cli_passes(self):
        self.assertEqual(cal._main(["score.py", "--dogfood"]), 0)
        self.assertEqual(cal._main(["score.py"]), 2)


if __name__ == "__main__":
    unittest.main()
