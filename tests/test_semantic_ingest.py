#!/usr/bin/env python3
"""Per-row semantic-judge ingestion + hybrid evaluation (machinery test).

Exercises Phase 2: an external semantic judge (distinct from author and curator) classifies the
independent holdout rows; the hybrid is graded against them. Uses a TEMP inbox + a synthetic judge
(oracle stand-in); never touches the real semantic inbox and claims no real-judge result.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json, atomic_write_json
from calibration import semantic_ingest as si
from calibration.independent_eval import load_independent_holdout

CAT = "config-tampering"          # curator grok-4.3; keyword recall 0.0 on it


def _judge_submission(judge_model, correct=True):
    rows = load_independent_holdout(CAT)["rows"]
    return {"category": CAT, "judge_model": judge_model, "blind": {"labels_hidden": True},
            "verdicts": [{"text": r["text"],
                          "verdict": (r["label"] if correct else "benign")} for r in rows]}


class TestValidation(unittest.TestCase):
    def test_valid_distinct_judge(self):
        self.assertEqual(si.validate_semantic(_judge_submission("kimi")), [])

    def test_judge_equals_curator_rejected(self):
        # grok-4.3 curated this holdout -> cannot also judge it (knows the labels)
        probs = si.validate_semantic(_judge_submission("grok-4.3"))
        self.assertTrue(any("3-way" in p for p in probs))

    def test_judge_equals_author_rejected(self):
        probs = si.validate_semantic(_judge_submission("meta-layer"))
        self.assertTrue(any("3-way" in p for p in probs))

    def test_incomplete_coverage_rejected(self):
        sub = _judge_submission("kimi")
        sub["verdicts"] = sub["verdicts"][:3]
        self.assertTrue(any("coverage" in p for p in si.validate_semantic(sub)))


class TestIngestAndHybrid(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = si.SEM_DIR
        si.SEM_DIR = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def tearDown(self):
        si.SEM_DIR = self._orig

    def _ingest(self, sub):
        p = os.path.join(self.tmp.name, "_sub.json")
        atomic_write_json(p, sub)
        return si.ingest(p)

    def test_hybrid_recovers_recall_with_distinct_judge(self):
        self.assertEqual(self._ingest(_judge_submission("kimi"))["status"], "ingested")
        v = si.verify_independence_hybrid(CAT)
        self.assertTrue(v["independent"], v)
        self.assertEqual(v["keyword"]["recall"], 0.0)      # keyword alone: total miss
        self.assertEqual(v["hybrid"]["recall"], 1.0)       # hybrid recovers via the judge
        self.assertEqual(v["hybrid"]["fp"], 0)

    def test_bad_judge_does_not_clear(self):
        self._ingest(_judge_submission("kimi", correct=False))   # judge calls everything benign
        v = si.verify_independence_hybrid(CAT)
        self.assertFalse(v["independent"])                 # hybrid can't clear with a useless judge

    def test_majority_vote_across_judges(self):
        self._ingest(_judge_submission("kimi", correct=True))
        self._ingest(_judge_submission("codex", correct=True))
        ev = si.evaluate(CAT)
        self.assertEqual(set(ev["judges"]), {"kimi", "codex"})
        self.assertEqual(ev["consensus"]["hybrid"]["recall"], 1.0)

    def test_ingest_rejects_curator_as_judge(self):
        self.assertEqual(self._ingest(_judge_submission("grok-4.3"))["status"], "rejected")


class TestSemanticBenchmark(unittest.TestCase):
    def test_seven_judges_all_hybrid_independent(self):
        # 7 external semantic judges (each 3-way distinct, blind) agreed with the curator labels 100%;
        # hybrid (keyword + semantic) clears all 7 where keyword alone scored 0.17-0.33.
        # (docs/INDEPENDENT-VALIDATION-RESULTS.md, Phase 2)
        rep = si.report()
        self.assertEqual(rep["judged_total"], 7)
        self.assertEqual(rep["independent_total"], 7)


class TestCli(unittest.TestCase):
    def test_usage(self):
        self.assertEqual(si._main(["semantic_ingest.py"]), 2)


if __name__ == "__main__":
    unittest.main()
