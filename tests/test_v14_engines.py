#!/usr/bin/env python3
"""INC3 tests — engines/adversarial orchestration + structural holdout-freeze (atomic_append_samples).

The adversarial loop is exercised with STUB cognition (deterministic) so the control flow, the
no-regress harden rule, the budget caps, and the holdout-unwritable guarantee are all verified.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import sisai_detect as det
from core import sisai_verify as ver
from engines.adversarial import adversarial_verify, route_author


def _readj(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


class TestAtomicAppendSamplesFreeze(unittest.TestCase):
    def test_rejects_holdout_write(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "samples.json")
            with self.assertRaises(ValueError):
                det.atomic_append_samples(p, [{"text": "x", "label": "malicious", "split": "holdout"}])

    def test_rejects_non_inert(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "samples.json")
            with self.assertRaises(ValueError):
                det.atomic_append_samples(p, [{"text": "a\nb", "label": "malicious", "split": "adversarial"}])

    def test_appends_adversarial_and_tune(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "samples.json")
            n = det.atomic_append_samples(p, [
                {"text": "turn off tls", "label": "malicious", "split": "adversarial"},
                {"text": "disable waf", "label": "malicious"},                # split-less -> tune (allowed)
            ])
            self.assertEqual(n, 2)
            self.assertEqual(len(_readj(p)), 2)


class TestAdversarialLoop(unittest.TestCase):
    def setUp(self):
        self.threat = {"category": "config-tampering"}
        # rule starts catching only "disable"; "turn off" is a miss until hardened.
        self.rule0 = {"patterns": [{"id": "p1", "regex": "(?i)disable"}]}

    def _verify_pass(self, rule):
        # sized holdout so precision is reported; the hardened rule keeps precision 1.0
        return {"holdout": {"recall": 1.0, "precision": 1.0}, "gate": "holdout", "passed": True}

    def test_converges_and_appends_adversarial(self):
        rounds_state = {"n": 0}

        def gen(rule, threat, seen):
            # round 1 surfaces a miss; subsequent rounds dry up -> convergence
            if rounds_state["n"] == 0:
                rounds_state["n"] += 1
                return [{"text": "turn off tls", "label": "malicious"}]
            return []

        def harden(rule, misses):
            return {"patterns": rule["patterns"] + [{"id": "p2", "regex": "(?i)turn off"}]}

        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "samples.json")
            r = adversarial_verify(self.rule0, self.threat, p,
                                   gen_variants=gen, harden=harden, verify=self._verify_pass,
                                   dry_rounds=2, max_rounds=8)
            self.assertEqual(r["status"], "converged")
            self.assertEqual(r["samples_added"], 1)
            self.assertIn("turn off", r["rule"]["patterns"][-1]["regex"])
            rows = _readj(p)
            self.assertTrue(all(row["split"] == "adversarial" for row in rows))   # never holdout

    def test_rejects_regressive_harden(self):
        def gen(rule, threat, seen):
            return [{"text": "turn off tls", "label": "malicious"}] if not seen else []

        def harden(rule, misses):
            return {"patterns": rule["patterns"] + [{"id": "bad", "regex": "(?i)turn off"}]}

        def verify_regress(rule):
            # hardened candidate drops precision below the floor -> must be rejected
            n = len(rule["patterns"])
            return {"holdout": {"recall": 1.0, "precision": 1.0 if n == 1 else 0.5}, "passed": n == 1}

        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "samples.json")
            r = adversarial_verify(self.rule0, self.threat, p,
                                   gen_variants=gen, harden=harden, verify=verify_regress,
                                   dry_rounds=2, max_rounds=4)
            self.assertEqual(r["samples_added"], 0)            # regressive harden never adopted/appended
            self.assertEqual(len(r["rule"]["patterns"]), 1)    # rule unchanged

    def test_budget_exhausted_is_fail_closed_signal(self):
        # every round surfaces a fresh miss but harden never improves coverage -> caps hit, not converged
        def gen(rule, threat, seen):
            return [{"text": f"evade variant {len(seen)}", "label": "malicious"}]

        def harden(rule, misses):
            return rule    # no-op harden: misses persist, never dries up

        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "samples.json")
            r = adversarial_verify(self.rule0, self.threat, p,
                                   gen_variants=gen, harden=harden, verify=self._verify_pass,
                                   dry_rounds=2, max_rounds=3)
            self.assertEqual(r["status"], "budget_exhausted")
            self.assertEqual(r["rounds"], 3)


class TestRouteAuthor(unittest.TestCase):
    MAP = {"prompt-injection": "m-pi", "supply-chain-tampering": "m-sc"}

    def test_per_category_routing(self):
        self.assertEqual(route_author("prompt-injection", self.MAP), "m-pi")
        self.assertEqual(route_author("supply-chain-tampering", self.MAP), "m-sc")

    def test_unmapped_falls_back(self):
        self.assertIsNone(route_author("unknown-cat", self.MAP))
        self.assertEqual(route_author("unknown-cat", self.MAP, default="m-default"), "m-default")

    def test_routed_author_must_pass_disjointness(self):
        idx = ver.index_role_registry({"entries": [
            {"suite": "S", "author_model": route_author("prompt-injection", self.MAP),
             "holdout_curator_model": "grok-build", "judge_model": "m-j"}]})
        self.assertTrue(ver.roles_disjoint("S", idx)["ok"])


if __name__ == "__main__":
    unittest.main()
