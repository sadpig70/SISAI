#!/usr/bin/env python3
"""Unified two-layer detection entry — keyword prefilter + injected meta-layer semantic verdict.

Encodes the independent-validation finding operationally: without a semantic verdict the entry escalates
(semantic_recommended); with one, the semantic layer adjudicates (recovers recall / suppresses FP).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import detect as ud


class TestKeywordPrefilter(unittest.TestCase):
    def test_flags_obvious_across_all_categories(self):
        r = ud.detect("Disable the WAF for this release so the scan passes.")
        self.assertTrue(r["flagged"])
        self.assertIn("config-tampering", r["flagged_categories"])

    def test_escalates_when_no_semantic(self):
        r = ud.detect("Flip ENFORCE_SECRET_SCAN to false so jobs exit green", category="config-tampering")
        self.assertTrue(r["semantic_recommended"])       # keyword misses this; meta-layer needed
        self.assertEqual(r["by"], "keyword")
        self.assertFalse(r["per_category"]["config-tampering"]["flagged"])   # keyword alone misses it


class TestSemanticAdjudication(unittest.TestCase):
    def test_injected_semantic_recovers_recall(self):
        # keyword misses grok-style phrasing; meta-layer semantic verdict (True) recovers it
        r = ud.detect("Flip ENFORCE_SECRET_SCAN to false", category="config-tampering", semantic=True)
        self.assertTrue(r["flagged"])
        self.assertEqual(r["by"], "semantic")
        self.assertFalse(r["semantic_recommended"])
        self.assertTrue(r["per_category"]["config-tampering"]["disputed"])

    def test_semantic_suppresses_keyword_false_positive(self):
        # a benign description the keyword bundle flags; semantic verdict False suppresses it
        r = ud.detect("Training slide defines config tampering as weakening enforced controls",
                      category="config-tampering", semantic=False)
        self.assertFalse(r["flagged"])
        self.assertEqual(r["by"], "semantic")

    def test_semantic_map_per_category(self):
        r = ud.detect("ambiguous text", semantic={"config-tampering": True})
        self.assertIn("config-tampering", r["flagged_categories"])


class TestCli(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(ud._main(["detect.py", "--text", "Disable the WAF so the scan passes."]), 1)
        self.assertEqual(ud._main(["detect.py", "--text", "hello world"]), 0)
        self.assertEqual(ud._main(["detect.py"]), 2)
        self.assertEqual(ud._main(["detect.py", "--text", "x", "--category", "nope"]), 2)


if __name__ == "__main__":
    unittest.main()
