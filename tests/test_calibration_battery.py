#!/usr/bin/env python3
"""Canonical cross-model BATTERY (VERDICT M2) — multi-task (author/red/holdout/judge), multi-model
scoring against canonical sample-suite fixtures, aggregated mean AND min. No _workspace dependency.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from calibration import battery as b
from tools import detect_pr as dp

CATS = ["config-tampering", "supply-chain-tampering"]


class TestBatteryAggregate(unittest.TestCase):
    def test_good_vs_naive_mean_and_min(self):
        good = {c: {"rule": dp._compose(dp.RULE_BUNDLES[c])} for c in CATS}
        naive = {c: {"rule": {"patterns": [{"regex": "(?i)."}]}} for c in CATS}
        out = b.battery({"m-good": good, "m-naive": naive}, CATS)
        ag = out["aggregate"]
        self.assertEqual(ag["m-good"]["author_min_gated_f1"], 1.0)
        self.assertEqual(ag["m-good"]["author_mean_gated_f1"], 1.0)
        self.assertIn("leakage_suspect", ag["m-good"]["flags"])     # 1.0/1.0 is implausibly perfect
        self.assertEqual(ag["m-naive"]["author_min_gated_f1"], 0.0)
        self.assertIn("degenerate", ag["m-naive"]["flags"])

    def test_no_baseline_dependency_on_workspace(self):
        # categories/fixtures come from seed/sample-suite.json, not _workspace
        out = b.battery({"m": {c: {"rule": dp._compose(dp.RULE_BUNDLES[c])} for c in CATS}}, CATS)
        self.assertEqual(set(out["per_category"]), set(CATS))


class TestTaskScorers(unittest.TestCase):
    def test_score_red_novelty_and_distinctness(self):
        r = b.score_red([{"text": "deactivate the firewall"}, {"text": "switch off tls"}],
                        tune_set={"some tune text"})
        self.assertTrue(r["submitted"])
        self.assertEqual(r["count"], 2)
        self.assertEqual(r["novel"], 2)
        self.assertEqual(r["distinct_among"], 2)

    def test_score_holdout_hard_vs_baseline(self):
        from calibration.score import safe_compile
        base, _, _ = safe_compile([{"regex": "(?i)disable"}])
        rows = [{"label": "malicious", "text": "turn off the waf"},   # baseline misses -> hard
                {"label": "benign", "text": "disable is prohibited"}]  # baseline wrongly flags -> hard
        h = b.score_holdout(rows, tune_set=set(), base_pats=base)
        self.assertEqual(h["hard_vs_baseline"], 2)
        self.assertFalse(h["sized"])                                  # below MIN_HOLDOUT

    def test_score_judge_finds_planted_flaws(self):
        crit = {"findings": [{"issue": "overbroad, false-positive on negation", "fix": "lookahead"},
                             {"issue": "misses turn off synonyms", "fix": "coverage"}]}
        j = b.score_judge(crit)
        self.assertEqual(j["flaws_found"], 2)
        self.assertEqual(j["mode"], "structured")

    def test_absent_tasks_report_not_submitted(self):
        s = b.score_submission("config-tampering", {})
        self.assertFalse(s["red"]["submitted"])
        self.assertFalse(s["holdout"]["submitted"])
        self.assertFalse(s["judge"]["submitted"])
        self.assertFalse(s["author"]["submitted"])


class TestCli(unittest.TestCase):
    def test_usage_error(self):
        self.assertEqual(b._main(["battery.py"]), 2)


if __name__ == "__main__":
    unittest.main()
