#!/usr/bin/env python3
"""B0-4 — benchmark/holdout harness: grows the adversarial split, routes holdout proposals to a
SEPARATE human-curation queue, flags leakage, and is fail-closed on budget exhaustion.

Acceptance (backlog B0-4): the loop NEVER writes the frozen holdout (structurally enforced);
regressive hardening is never adopted; on budget_exhausted nothing is recorded (record_ok False);
leakage_suspect is surfaced. Proposed holdout samples land only in the curation queue, unsplit and
marked needs_human_review.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import benchmark_harness as bh
from tools import detect_pr as dp

THREAT = {"category": "config-tampering"}


def _passing_verify(rule):
    return {"holdout": {"recall": 1.0, "precision": 1.0}, "gate": "holdout", "passed": True}


def _readj(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


class TestCurationQueue(unittest.TestCase):
    def test_proposals_go_to_separate_queue_unsplit(self):
        with tempfile.TemporaryDirectory() as d:
            q = os.path.join(d, "candidates.json")
            n = bh.propose_holdout_candidates(q, [
                {"text": "novel evasion phrasing", "label": "malicious"},
                {"text": "a defensive citation hard negative", "label": "benign"},
            ], now="2026-06-19")
            self.assertEqual(n, 2)
            rows = _readj(q)
            for r in rows:
                self.assertNotIn("split", r)                       # unsplit proposal
                self.assertEqual(r["status"], "needs_human_review")
                self.assertEqual(r["proposed_at"], "2026-06-19")

    def test_preclaimed_split_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            q = os.path.join(d, "candidates.json")
            with self.assertRaises(ValueError):
                bh.propose_holdout_candidates(q, [
                    {"text": "x", "label": "malicious", "split": "holdout"}], now="2026-06-19")

    def test_fp_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            q = os.path.join(d, "candidates.json")
            bh.propose_holdout_candidates(q, [{"text": "dup", "label": "malicious"}], now="2026-06-19")
            again = bh.propose_holdout_candidates(q, [{"text": "dup", "label": "malicious"}], now="2026-06-19")
            self.assertEqual(again, 0)
            self.assertEqual(len(_readj(q)), 1)


class TestHarnessRun(unittest.TestCase):
    def setUp(self):
        # a rule that misses "turn off" until hardened
        self.rule0 = {"patterns": [{"id": "p1", "regex": "(?i)disable"}]}

    def test_converged_records_and_appends_adversarial_only(self):
        state = {"n": 0}

        def gen(rule, threat, seen):
            if state["n"] == 0:
                state["n"] += 1
                return [{"text": "turn off tls", "label": "malicious"}]
            return []

        def harden(rule, misses):
            return {"patterns": rule["patterns"] + [{"id": "p2", "regex": "(?i)turn off"}]}

        with tempfile.TemporaryDirectory() as d:
            samples = os.path.join(d, "samples.json")
            res = bh.run_harness(self.rule0, THREAT, "config-tampering", samples,
                                 gen_variants=gen, harden=harden, verify=_passing_verify,
                                 dry_rounds=2, max_rounds=8)
            self.assertEqual(res["status"], "converged")
            self.assertTrue(res["record_ok"])                      # converged -> recordable
            rows = _readj(samples)
            self.assertTrue(rows and all(r["split"] == "adversarial" for r in rows))   # never holdout

    def test_budget_exhausted_is_fail_closed(self):
        def gen(rule, threat, seen):
            return [{"text": f"evade {len(seen)}", "label": "malicious"}]   # endless fresh misses

        def harden(rule, misses):
            return rule                                            # no-op -> never converges

        with tempfile.TemporaryDirectory() as d:
            samples = os.path.join(d, "samples.json")
            res = bh.run_harness(self.rule0, THREAT, "config-tampering", samples,
                                 gen_variants=gen, harden=harden, verify=_passing_verify,
                                 dry_rounds=2, max_rounds=3)
            self.assertEqual(res["status"], "budget_exhausted")
            self.assertFalse(res["record_ok"])                     # fail-closed: do NOT record

    def test_leakage_flag_and_candidate_routing(self):
        # final rule is the perfect B0-1 bundle (1.0/1.0 on the real holdout) -> leakage flag fires
        perfect = dp._compose(dp.RULE_BUNDLES["config-tampering"])

        def gen(rule, threat, seen):
            return []                                              # no misses -> immediate convergence

        def harden(rule, misses):
            return rule

        def propose(rule, threat):
            return [{"text": "curator-only proposed evasion", "label": "malicious"}]

        with tempfile.TemporaryDirectory() as d:
            samples = os.path.join(d, "samples.json")
            queue = os.path.join(d, "candidates.json")
            res = bh.run_harness(perfect, THREAT, "config-tampering", samples,
                                 gen_variants=gen, harden=harden, verify=_passing_verify,
                                 holdout_candidate_path=queue, gen_holdout_candidates=propose,
                                 now="2026-06-19", dry_rounds=2, max_rounds=4)
            self.assertTrue(res["leakage_suspect"])                # 1.0/1.0 surfaced
            self.assertEqual(res["holdout_candidates_proposed"], 1)
            self.assertTrue(os.path.exists(queue))                 # proposal in the SEPARATE queue
            self.assertFalse(os.path.exists(samples))              # loop appended nothing to the benchmark


if __name__ == "__main__":
    unittest.main()
