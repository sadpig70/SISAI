#!/usr/bin/env python3
"""Independent-validation round freshness — re-validation must use a FRESH holdout, never the frozen
one already stored (no teach-to-the-benchmark). Pure freshness helpers + the ingest stale-guard.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import atomic_write_json
from calibration import rounds
from calibration import independent_eval as ie


def _holdout(curator, texts_mal, texts_ben):
    return {"category": "config-tampering", "curator_model": curator,
            "rows": [{"label": "malicious", "text": t} for t in texts_mal]
                    + [{"label": "benign", "text": t} for t in texts_ben]}


class TestFreshnessHelpers(unittest.TestCase):
    def test_identical_is_stale(self):
        self.assertTrue(rounds.is_stale({"a", "b"}, {"b", "a"}))

    def test_no_prev_is_not_stale(self):
        self.assertFalse(rounds.is_stale({"a"}, set()))

    def test_assess_overlap(self):
        a = rounds.assess([{"text": "a"}, {"text": "b"}], [{"text": "a"}, {"text": "c"}])
        self.assertFalse(a["identical"])
        self.assertEqual(a["overlap"], 1)
        self.assertEqual(a["fresh"], 1)


class TestIngestStaleGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = ie.INDEP_DIR
        ie.INDEP_DIR = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.mal = [f"disable control number {i} in CI" for i in range(5)]
        self.ben = [f"control {i} is enforced by policy" for i in range(4)]

    def tearDown(self):
        ie.INDEP_DIR = self._orig

    def _ingest(self, sub):
        p = os.path.join(self.tmp.name, "_sub.json")
        atomic_write_json(p, sub)
        return ie.ingest(p)

    def test_first_round_ingests(self):
        self.assertEqual(self._ingest(_holdout("grok", self.mal, self.ben))["status"], "ingested")

    def test_identical_resubmission_rejected_as_stale(self):
        self._ingest(_holdout("grok", self.mal, self.ben))
        res = self._ingest(_holdout("grok", self.mal, self.ben))   # same rows again
        self.assertEqual(res["status"], "rejected")
        self.assertTrue(any("stale" in p for p in res["problems"]))

    def test_fresh_round_with_new_rows_ingests(self):
        self._ingest(_holdout("grok", self.mal, self.ben))
        fresh_mal = [f"bypass gate variant {i}" for i in range(5)]    # different rows -> new round
        res = self._ingest(_holdout("grok", fresh_mal, self.ben + ["one more benign note"]))
        self.assertEqual(res["status"], "ingested")


class TestCli(unittest.TestCase):
    def test_usage(self):
        self.assertEqual(rounds._main(["rounds.py"]), 2)


if __name__ == "__main__":
    unittest.main()
