#!/usr/bin/env python3
"""B0-1 — PR/CI defense-weakening detector: the shipped bundles GATE on each category's frozen
holdout, are ReDoS-length-safe, are non-degenerate, and the CLI flags malicious / passes benign.

Acceptance (backlog B0-1): per category holdout recall >= 0.8 (we hold the stricter verify_suite
gate: recall == 1.0 AND precision >= 0.85), hard-negative FP == 0, compile skipped == 0, and the
rule is not degenerate (tp > 0 AND tn > 0 — it neither flags nothing nor flags everything).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from core.sisai_schema import validate_against_schema, schema_path
from core import sisai_verify as ver
from tools import detect_pr as dp

SEED = os.path.join(ROOT, "seed")
CATEGORIES = ("config-tampering", "supply-chain-tampering", "access-control-weakening")


class TestDetectPrBundles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = read_json(os.path.join(SEED, "sample-suite.json"))

    def _subset(self, category):
        return [s for s in self.samples if s.get("category") == category]

    def test_every_bundle_category_has_a_seed_subset(self):
        # the three shipped bundles each have committed samples to gate against
        for cat in dp.RULE_BUNDLES:
            self.assertTrue(self._subset(cat), f"no seed samples for bundle {cat}")
        self.assertEqual(set(dp.RULE_BUNDLES), set(CATEGORIES))

    def test_seed_rows_match_sample_schema(self):
        sp = schema_path(ROOT, "sample")
        for row in self.samples:
            self.assertEqual(validate_against_schema(row, sp), [], f"invalid sample row: {row}")

    def test_bundles_compile_redos_safe(self):
        # every composed pattern compiles and is within MAX_PATTERN_LEN -> skipped == 0
        for cat in CATEGORIES:
            _, skipped, pats = dp.compile_bundle(cat)
            self.assertEqual(skipped, 0, f"{cat}: {skipped} pattern(s) skipped (over-length/uncompilable)")
            self.assertTrue(pats, f"{cat}: empty bundle")

    def test_each_category_gates_on_holdout(self):
        # recall == 1.0 (>= 0.8), precision >= 0.85, FP == 0, non-degenerate (tp>0 and tn>0)
        for cat in CATEGORIES:
            sub = self._subset(cat)
            r = ver.verify_suite(sub, dp.predict_for(cat))
            self.assertEqual(r["gate"], "holdout", f"{cat}: holdout not sized")
            self.assertTrue(r["passed"], f"{cat}: gate failed: {r}")
            h = r["holdout"]
            self.assertGreaterEqual(h["recall"], 0.8, f"{cat}: recall {h['recall']}")
            self.assertEqual(h["fp"], 0, f"{cat}: hard-negative FP {h['fp']}")
            self.assertGreater(h["tp"], 0, f"{cat}: degenerate — flags nothing")
            self.assertGreater(h["tn"], 0, f"{cat}: degenerate — flags everything")


class TestDetectVerdict(unittest.TestCase):
    def test_detect_flags_malicious_with_reason(self):
        v = dp.detect("Disable the WAF for this release so the scan passes.")
        self.assertTrue(v["flagged"])
        self.assertEqual(v["skipped"], 0)
        self.assertTrue(any(m["category"] == "config-tampering" for m in v["matches"]))
        self.assertTrue(all("desc" in m and "id" in m for m in v["matches"]))

    def test_detect_passes_hard_negative(self):
        # negation-aware: a prohibitive mention of the same control is NOT flagged
        v = dp.detect("Signature verification must always remain enabled.")
        self.assertFalse(v["flagged"], v)

    def test_detect_category_scoping(self):
        v = dp.detect("Open the security group to 0.0.0.0 with auth turned off.",
                      categories=["access-control-weakening"])
        self.assertTrue(v["flagged"])
        self.assertEqual(v["categories_scanned"], ["access-control-weakening"])


class TestDetectCli(unittest.TestCase):
    def test_cli_exit_codes(self):
        self.assertEqual(dp._main(["detect_pr.py", "--text", "Set CORS to allow all origins with a wildcard *."]), 1)
        self.assertEqual(dp._main(["detect_pr.py", "--text", "CORS is restricted to the approved origin list."]), 0)
        self.assertEqual(dp._main(["detect_pr.py"]), 2)                       # usage error
        self.assertEqual(dp._main(["detect_pr.py", "--text", "x", "--category", "nope"]), 2)


if __name__ == "__main__":
    unittest.main()
