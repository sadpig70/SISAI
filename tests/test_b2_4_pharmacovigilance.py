#!/usr/bin/env python3
"""B2-4 — PharmacoVigilance triage (DRAFT/synthetic, most conservative): serious-signal detection that
NEVER decides clinically and never feeds back before verification + human approval.

Acceptance (backlog B2-4): no feedback before verification (false-alarm suppression), provenance,
full audit trail, and NO autonomous clinical decision (human approval mandatory). NOTE: synthetic
fixtures — production needs clinical SME + drug-safety regulatory sign-off (surfaced as DRAFT_STATUS).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from core.sisai_schema import validate_against_schema, schema_path
from domain import pharmacovigilance as pv


class TestGate(unittest.TestCase):
    def test_seed_rows_valid(self):
        sp = schema_path(ROOT, "sample")
        rows = [s for s in read_json(os.path.join(ROOT, "seed", "sample-suite.json"))
                if s.get("category") == pv.CATEGORY]
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(validate_against_schema(r, sp), [], r)

    def test_bundle_redos_safe(self):
        _, skipped, pats = pv.compile_bundle()
        self.assertEqual(skipped, 0)
        self.assertTrue(pats)

    def test_holdout_gate(self):
        g = pv.gate()
        self.assertEqual(g["gate"], "holdout")
        self.assertTrue(g["passed"], g)
        h = g["holdout"]
        self.assertGreaterEqual(h["precision"], 0.85)
        self.assertEqual(h["fp"], 0)                        # resolved/negated/non-serious not escalated
        self.assertGreaterEqual(h["recall"], 0.8)


class TestNoAutonomousDecision(unittest.TestCase):
    def test_triage_always_routes_to_human(self):
        for txt in ["The patient died shortly after administration.",        # serious
                    "The patient reported a mild rash that resolved."]:       # non-serious
            t = pv.triage(txt)
            self.assertEqual(t["decision"], "human_review_required")
            self.assertFalse(t["autonomous_clinical_decision"])

    def test_serious_signal_escalates_nonserious_does_not(self):
        self.assertTrue(pv.triage("The patient was hospitalized after the second dose.")["escalate"])
        self.assertFalse(pv.triage("No adverse events were observed during the study.")["escalate"])

    def test_audit_trail_present(self):
        t = pv.triage("The event caused permanent disability.")
        self.assertIn("audit", t)
        self.assertTrue(t["audit"]["signal_ids"])


class TestNoFeedbackBeforeVerification(unittest.TestCase):
    def test_unverified_signal_not_fed_back(self):
        self.assertFalse(pv.can_feedback({"verification": {"passed": False}, "human_approved": True}))

    def test_verified_but_unapproved_not_fed_back(self):
        self.assertFalse(pv.can_feedback({"verification": {"passed": True}}))      # no human approval

    def test_verified_and_human_approved_can_feed_back(self):
        self.assertTrue(pv.can_feedback({"verification": {"passed": True}, "human_approved": True}))


class TestProvenance(unittest.TestCase):
    GOOD = {"source_url": "https://github.com/org/repo/x", "authority": "GHSA",
            "source_sha256": "a" * 64, "verified": True}

    def test_provenance_states(self):
        self.assertEqual(pv.triage("x", None)["provenance"], "absent")
        self.assertEqual(pv.triage("x", {"verified": True})["provenance"], "unverified")
        self.assertEqual(pv.triage("x", self.GOOD)["provenance"], "verified")


class TestCli(unittest.TestCase):
    def test_cli(self):
        self.assertEqual(pv._main(["pharmacovigilance.py", "--text", "The patient died after the dose."]), 0)
        self.assertEqual(pv._main(["pharmacovigilance.py"]), 2)


if __name__ == "__main__":
    unittest.main()
