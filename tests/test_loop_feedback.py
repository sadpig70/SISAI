#!/usr/bin/env python3
"""Loop feedback — close the spiral honestly: only independently-verified (hybrid) detectors feed back
as defenses; findings become threats. Real .sisai is never touched (temp paths only)."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from core.sisai_provenance import is_verified
from sisai import record_defense
from tools import loop_feedback as lf


class TestDetectorDefense(unittest.TestCase):
    def test_independent_category_is_verified(self):
        d = lf.detector_defense("config-tampering")     # hybrid-independent (7/7 judges)
        self.assertTrue(d["verification"]["passed"])
        self.assertTrue(is_verified(d))
        self.assertIn("meta-layer-semantic", d["controls"])
        self.assertIn("prefilter", d["verification"]["method"])   # keyword honestly framed as prefilter

    def test_unverified_defense_is_rejected_by_record(self):
        with tempfile.TemporaryDirectory() as t:
            led, cor = os.path.join(t, "l.json"), os.path.join(t, "c.json")
            unverified = {**lf.detector_defense("config-tampering"),
                          "verification": {"method": "none", "passed": False}}
            self.assertEqual(record_defense(unverified, led, cor, now="2026-06-20")["status"], "rejected")


class TestFindingsToThreats(unittest.TestCase):
    def test_shape(self):
        ts = lf.findings_to_threats("config-tampering", ["Disable the WAF", "  "], now="2026-06-20")
        self.assertEqual(len(ts), 1)                    # blank dropped
        self.assertEqual(ts[0]["category"], "config-tampering")
        self.assertIn("detected", ts[0]["techniques"])


class TestPlanAndCommit(unittest.TestCase):
    def test_plan_all_verified(self):
        p = lf.feedback_plan()
        self.assertEqual(p["verified_total"], p["total"])   # all 7 hybrid-independent now
        self.assertEqual(p["total"], 7)

    def test_commit_records_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as t:
            led, cor = os.path.join(t, "l.json"), os.path.join(t, "c.json")
            r1 = lf.commit(led, cor, "2026-06-20")
            self.assertEqual(r1["recorded"], 7)
            self.assertEqual(len(read_json(cor)), 7)
            r2 = lf.commit(led, cor, "2026-06-20")          # idempotent
            self.assertEqual(len(read_json(cor)), 7)


class TestCli(unittest.TestCase):
    def test_usage(self):
        self.assertEqual(lf._main(["loop_feedback.py"]), 2)
        self.assertEqual(lf._main(["loop_feedback.py", "--plan"]), 0)


if __name__ == "__main__":
    unittest.main()
