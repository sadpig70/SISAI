#!/usr/bin/env python3
"""B0-6 Education Lab — the lab reproduces the generalization lesson and auto-grades student rules.

Acceptance (backlog B0-6): reproduce what test_v14_seed_data showed — a naive rule FAILS the frozen
holdout (false positives on hard negatives + a miss), a negation-aware rule PASSES at precision 1.0 —
and the grader auto-scores arbitrary submitted rules (degenerate/ReDoS handling included). The shipped
B0-1 bundles, fed through the same grader, must PASS for all three categories.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from labs.defense_rule_lab import grade_rule as gr
from tools import detect_pr as dp

EX = os.path.join(ROOT, "labs", "defense_rule_lab", "examples")


class TestLabReproduction(unittest.TestCase):
    def test_step1_naive_rule_fails_holdout(self):
        rule = read_json(os.path.join(EX, "step1-naive-config-rule.json"))
        rep = gr.grade(rule, "config-tampering", reveal=True)
        self.assertFalse(rep["passed"], rep)
        h = rep["holdout"]
        # the lesson: a naive verb match BOTH false-positives on hard negatives AND misses verify_ssl
        self.assertGreater(h["fp"], 0, "naive rule should false-positive on hard negatives")
        self.assertGreater(h["fn"], 0, "naive rule should miss verify_ssl=false")
        fps = rep["feedback"]["holdout_false_positives"]
        self.assertTrue(any("Never disable" in t for t in fps), fps)

    def test_step3_negation_aware_rule_passes_holdout(self):
        rule = read_json(os.path.join(EX, "step3-negation-aware-config-rule.json"))
        rep = gr.grade(rule, "config-tampering")
        self.assertTrue(rep["passed"], rep)
        self.assertEqual(rep["gate"], "holdout")
        self.assertEqual(rep["holdout"]["recall"], 1.0)
        self.assertEqual(rep["holdout"]["precision"], 1.0)
        self.assertEqual(rep["skipped"], 0)


class TestGraderRobustness(unittest.TestCase):
    def test_match_everything_is_degenerate_fail(self):
        rep = gr.grade({"patterns": [{"id": "all", "regex": "(?i)."}]}, "config-tampering")
        self.assertFalse(rep["passed"])
        self.assertTrue(rep["degenerate"])              # tn == 0 (flags every benign too)

    def test_match_nothing_is_degenerate_fail(self):
        rep = gr.grade({"patterns": [{"id": "none", "regex": "zzz_no_such_token_zzz"}]}, "config-tampering")
        self.assertFalse(rep["passed"])
        self.assertTrue(rep["degenerate"])              # tp == 0 (flags nothing)

    def test_uncompilable_pattern_is_surfaced_as_skipped(self):
        rep = gr.grade({"patterns": [{"id": "bad", "regex": "([unclosed"}]}, "config-tampering")
        self.assertEqual(rep["skipped"], 1)             # surfaced, never executed blindly
        self.assertFalse(rep["passed"])

    def test_overlength_pattern_is_skipped(self):
        rep = gr.grade({"patterns": [{"id": "long", "regex": "a" * 401}]}, "config-tampering")
        self.assertEqual(rep["skipped"], 1)             # ReDoS length bound (MAX_PATTERN_LEN)


class TestShippedBundlesPassGrader(unittest.TestCase):
    def test_detect_pr_bundles_pass_for_all_categories(self):
        # ties B0-6 to B0-1: the shipped negation-aware bundles, scored by the lab grader, PASS
        for cat in gr.CATEGORIES:
            rule = dp._compose(dp.RULE_BUNDLES[cat])
            rep = gr.grade(rule, cat)
            self.assertEqual(rep["verdict"], "PASS", f"{cat}: {rep}")
            self.assertEqual(rep["holdout"]["fp"], 0, f"{cat}: false positives")


class TestGraderCli(unittest.TestCase):
    def test_cli_exit_codes(self):
        naive = os.path.join(EX, "step1-naive-config-rule.json")
        good = os.path.join(EX, "step3-negation-aware-config-rule.json")
        self.assertEqual(gr._main(["grade_rule.py", "--rule", good, "--category", "config-tampering"]), 0)
        self.assertEqual(gr._main(["grade_rule.py", "--rule", naive, "--category", "config-tampering"]), 1)
        self.assertEqual(gr._main(["grade_rule.py", "--category", "config-tampering"]), 2)   # usage
        self.assertEqual(gr._main(["grade_rule.py", "--rule", good, "--category", "nope"]), 2)


if __name__ == "__main__":
    unittest.main()
