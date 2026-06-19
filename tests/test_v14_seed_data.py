#!/usr/bin/env python3
"""INC4 — the shipped example data validates against the v1.4 schemas and flows through the gates.

Closes the loop from "functions exist + unit-tested" to "real committed data passes the contracts":
  - seed/sample-suite.json   -> sample.schema; drives verify_suite onto the FROZEN holdout gate.
  - seed/role-registry.json  -> role-registry.schema; drives roles_disjoint (binding pairs).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from core.sisai_schema import validate_against_schema, schema_path
from core import sisai_detect as det
from core import sisai_verify as ver

SEED = os.path.join(ROOT, "seed")


class TestSampleSuite(unittest.TestCase):
    def setUp(self):
        self.samples = read_json(os.path.join(SEED, "sample-suite.json"))

    def test_each_row_matches_sample_schema(self):
        sp = schema_path(ROOT, "sample")
        for row in self.samples:
            self.assertEqual(validate_against_schema(row, sp), [], f"invalid sample row: {row}")

    def test_holdout_is_sized_and_gate_runs(self):
        # a NEGATION-AWARE rule: flags the directive verbs but not negated/prohibitive mentions
        # (the holdout's hard negatives -- "never disable", "bypassing ... prohibited" -- are the precision test)
        rule = {"patterns": [{"id": "p1", "regex":
                 "(?i)^(?!.*\\b(never|cannot|must|prohibited|always remain|remain enabled)\\b)"
                 ".*(disable|turn off|bypass|verify_ssl\\s*=\\s*false|comment out)"}]}
        compiled, skipped = det.compile_rule(rule)
        self.assertEqual(skipped, 0)                    # the lookahead compiles fine in core (no false ReDoS refusal)
        r = ver.verify_suite(self.samples, lambda t: det.scan(t, compiled))
        self.assertEqual(r["gate"], "holdout")          # frozen holdout is sized -> gates on it
        self.assertTrue(r["passed"])                    # recall 1.0, precision >= 0.85 on the holdout
        self.assertEqual(r["holdout"]["precision"], 1.0)

    def test_loop_cannot_write_holdout_rows(self):
        # the structural freeze: feeding holdout-split rows to the loop's writer is refused
        with self.assertRaises(ValueError):
            det.atomic_append_samples(os.path.join(SEED, "_never.json"),
                                      [{**self.samples[4], "split": "holdout"}])


class TestRoleRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = read_json(os.path.join(SEED, "role-registry.json"))

    def test_matches_role_registry_schema(self):
        sp = schema_path(ROOT, "role-registry")
        self.assertEqual(validate_against_schema(self.reg, sp), [])

    def test_example_entry_is_disjoint(self):
        idx = ver.index_role_registry(self.reg)
        self.assertTrue(ver.roles_disjoint("EXAMPLE-config-tampering", idx)["ok"])


if __name__ == "__main__":
    unittest.main()
