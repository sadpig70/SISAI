#!/usr/bin/env python3
"""Holdout independence protocol — measures/gates independence honestly (never fabricates it).

The shipped detectors are all single_author today (the meta-layer authored both rule and holdout);
the protocol surfaces that and gates on real independence. The EXAMPLE-independent entry demonstrates
the independent path (distinct curator + disjoint roles).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from calibration import independence as ind

SHIPPED = ["config-tampering", "supply-chain-tampering", "access-control-weakening",
           "llm-prompt-injection", "fraud-aml", "trust-safety", "pharmacovigilance"]


class TestHonestCurrentState(unittest.TestCase):
    def test_all_shipped_categories_are_single_author(self):
        # the honest invariant: no shipped detector falsely claims independent validation
        for cat in SHIPPED:
            a = ind.assess_category(cat)
            self.assertEqual(a["verdict"], "single_author", cat)
            self.assertFalse(a["independent"], cat)

    def test_report_counts(self):
        rep = ind.report()
        self.assertEqual(rep["counts"].get("single_author"), len(SHIPPED))
        self.assertEqual(rep["independent_total"], 1)      # only the EXAMPLE demo


class TestIndependentPath(unittest.TestCase):
    def test_example_independent_passes_both_layers(self):
        a = ind.assess_category("EXAMPLE-independent")
        self.assertEqual(a["verdict"], "independent")
        self.assertTrue(a["independent"])
        self.assertNotEqual(a["rule_author"], a["holdout_curator"])

    def test_require_independent_gate(self):
        self.assertFalse(ind.require_independent("config-tampering"))   # single author -> rejected
        self.assertTrue(ind.require_independent("EXAMPLE-independent"))  # independent -> accepted


class TestVerdictLogic(unittest.TestCase):
    def test_unprovisioned_category(self):
        a = ind.assess_category("no-such-category")
        self.assertEqual(a["verdict"], "unprovisioned")
        self.assertFalse(a["independent"])

    def test_factual_independent_but_roles_conflict(self):
        # distinct curator (factual) but role registry roles overlap -> roles_conflict, not independent
        cur_idx = {"X": {"category": "X", "rule_author": "A", "holdout_curator": "B", "independent": True}}
        role_idx = {"X": {"suite": "X", "author_model": "A", "holdout_curator_model": "Z", "judge_model": "A"}}
        a = ind.assess_category("X", curation_idx=cur_idx, role_idx=role_idx)
        self.assertEqual(a["verdict"], "roles_conflict")
        self.assertFalse(a["independent"])

    def test_claimed_independent_flag_required(self):
        # rule_author != holdout_curator but independent flag false -> still single_author (not claimed)
        cur_idx = {"Y": {"category": "Y", "rule_author": "A", "holdout_curator": "B", "independent": False}}
        a = ind.assess_category("Y", curation_idx=cur_idx, role_idx={})
        self.assertEqual(a["verdict"], "single_author")


class TestCli(unittest.TestCase):
    def test_cli_runs(self):
        self.assertEqual(ind._main(["independence.py"]), 0)


if __name__ == "__main__":
    unittest.main()
