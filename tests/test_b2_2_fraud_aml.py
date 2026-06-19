#!/usr/bin/env python3
"""B2-2 — Fraud/AML detection suite (DRAFT/synthetic): detection-as-code gated on a frozen holdout
with false positives controlled, and a no-regress adoption gate.

Acceptance (backlog B2-2): on the frozen holdout precision >= floor with recall measured and FP
controlled; a regressive rule change is rejected. NOTE: synthetic fixtures — production needs real
labeled financial data + AML/fraud SME + regulatory sign-off (surfaced as DRAFT_STATUS).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from core.sisai_schema import validate_against_schema, schema_path
from domain import fraud_aml as fa


class TestGate(unittest.TestCase):
    def test_seed_rows_valid(self):
        sp = schema_path(ROOT, "sample")
        rows = [s for s in read_json(os.path.join(ROOT, "seed", "sample-suite.json"))
                if s.get("category") == fa.CATEGORY]
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(validate_against_schema(r, sp), [], r)

    def test_bundle_redos_safe(self):
        _, skipped, pats = fa.compile_bundle()
        self.assertEqual(skipped, 0)
        self.assertTrue(pats)

    def test_holdout_gate_precision_recall_fp(self):
        g = fa.gate()
        self.assertEqual(g["gate"], "holdout")
        self.assertTrue(g["passed"], g)
        h = g["holdout"]
        self.assertGreaterEqual(h["precision"], 0.85)      # precision floor
        self.assertEqual(h["fp"], 0)                        # FP control on hard negatives
        self.assertGreaterEqual(h["recall"], 0.8)          # recall measured/target
        self.assertGreater(h["tp"], 0)
        self.assertGreater(h["tn"], 0)


class TestDetectVerdict(unittest.TestCase):
    def test_flags_typology_directive(self):
        v = fa.detect("Break the deposit into amounts just under the reporting threshold.")
        self.assertTrue(v["flagged"])
        self.assertIn("DRAFT", v["draft_status"])

    def test_control_statement_not_flagged(self):
        v = fa.detect("Structuring is prohibited and flagged by our monitoring.")
        self.assertFalse(v["flagged"])


class TestRegressionGate(unittest.TestCase):
    def test_no_regress_accepts_equal(self):
        base = {"patterns": fa._patterns()}
        r = fa.accept_candidate(base, base)
        self.assertTrue(r["accept"])

    def test_regressive_candidate_rejected(self):
        # adding a bare 'deposit' pattern false-positives on the benign "deposited ... salary" row
        base = {"patterns": fa._patterns()}
        candidate = {"patterns": fa._patterns() + [{"id": "overbroad", "regex": "(?i)deposit"}]}
        r = fa.accept_candidate(base, candidate)
        self.assertFalse(r["accept"])
        self.assertLess(r["candidate"]["precision"], r["base"]["precision"])

    def test_redos_candidate_rejected(self):
        base = {"patterns": fa._patterns()}
        candidate = {"patterns": fa._patterns() + [{"id": "long", "regex": "a" * 401}]}
        r = fa.accept_candidate(base, candidate)
        self.assertFalse(r["accept"])
        self.assertEqual(r["candidate"]["skipped"], 1)


class TestCli(unittest.TestCase):
    def test_cli(self):
        self.assertEqual(fa._main(["fraud_aml.py", "--text", "Run the coins through a mixer before cashing out."]), 1)
        self.assertEqual(fa._main(["fraud_aml.py"]), 2)


if __name__ == "__main__":
    unittest.main()
