#!/usr/bin/env python3
"""Two-layer hybrid detection — the deterministic combiner over an injected semantic layer.

Logic tests prove escalation/dispute/fallback. The config-tampering demo shows that when a semantic
verdict is present (here an oracle standing in for the meta-layer's meaning-based judgment) the hybrid
recovers the recall the keyword layer lost on the INDEPENDENT holdout (keyword 0.0 -> hybrid 1.0).
This validates the architecture, not a magic detector; real semantic quality is judged on a FRESH
independent round (see docs/SEMANTIC-DETECTION-FINDING.md).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from engines.detect_hybrid import hybrid_verdict, hybrid_predict, evaluate
from tools import detect_pr as dp


class TestHybridLogic(unittest.TestCase):
    def test_semantic_adjudicates_and_recovers(self):
        v = hybrid_verdict("x", keyword_predict=lambda t: False, semantic_predict=lambda t: True)
        self.assertTrue(v["flagged"])            # keyword missed, semantic caught -> flagged
        self.assertEqual(v["by"], "semantic")
        self.assertTrue(v["disputed"])

    def test_semantic_suppresses_keyword_false_positive(self):
        v = hybrid_verdict("x", keyword_predict=lambda t: True, semantic_predict=lambda t: False)
        self.assertFalse(v["flagged"])           # keyword false-positive, semantic adjudicates -> clean
        self.assertTrue(v["disputed"])

    def test_fallback_to_keyword_without_semantic(self):
        v = hybrid_verdict("x", keyword_predict=lambda t: True, semantic_predict=None)
        self.assertTrue(v["flagged"])
        self.assertEqual(v["by"], "keyword")
        self.assertFalse(v["disputed"])

    def test_hybrid_predict_is_bool(self):
        p = hybrid_predict(lambda t: False, lambda t: True)
        self.assertIs(p("anything"), True)


class TestConfigIndependentDemo(unittest.TestCase):
    def setUp(self):
        self.rows = read_json(os.path.join(ROOT, "seed", "independent-holdouts", "config-tampering.json"))["rows"]
        # oracle semantic layer: stands in for the meta-layer's meaning-based verdict (correct by meaning)
        self._mal = {r["text"] for r in self.rows if r["label"] == "malicious"}

    def _semantic(self, text):
        return text in self._mal

    def test_keyword_alone_fails_independent_holdout(self):
        r = evaluate(self.rows, dp.predict_for("config-tampering"), semantic_predict=None)
        self.assertEqual(r["keyword"]["recall"], 0.0)    # keyword bundle: total miss on grok's phrasing

    def test_hybrid_recovers_recall_and_precision(self):
        r = evaluate(self.rows, dp.predict_for("config-tampering"), semantic_predict=self._semantic)
        self.assertEqual(r["hybrid"]["recall"], 1.0)
        self.assertEqual(r["hybrid"]["precision"], 1.0)
        self.assertEqual(r["hybrid"]["fp"], 0)
        self.assertEqual(len(r["recovered_by_semantic"]), 6)   # all 6 keyword-missed malicious recovered


if __name__ == "__main__":
    unittest.main()
