#!/usr/bin/env python3
"""B1-4 — AI Toolchain Integrity Sentinel: provenance gate + sha256 pin check over the toolchain.

Acceptance (backlog B1-4): anti fail-open (manifest self-claim is ignored; no isolated measurement ->
quarantine), host-mismatch / sha256-bad rejected 100%, a genuinely good source passes; risky manifest
directives are flagged via the supply-chain bundle. Deterministic.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import toolchain_sentinel as ts

GH = "https://github.com/org/repo/releases/download/v1/pkg"
GOOD = {"source_url": GH, "authority": "GHSA", "source_sha256": "a" * 64, "verified": True}


class TestComponentProvenance(unittest.TestCase):
    def test_anti_fail_open_self_claim_quarantined(self):
        declared = {"name": "left-pad", "kind": "dependency",
                    "self_claimed": {"verified": True, "authority": "GHSA"}, "pinned_sha256": "a" * 64}
        self.assertEqual(ts.assess_component(declared, None)["verdict"], "quarantined")

    def test_good_source_with_matching_pin_verified(self):
        r = ts.assess_component({"name": "pkg", "pinned_sha256": "a" * 64}, GOOD)
        self.assertEqual(r["verdict"], "verified")

    def test_untrusted_host_rejected(self):
        r = ts.assess_component({"name": "pkg"}, {**GOOD, "source_url": "https://evil.mirror/pkg"})
        self.assertEqual(r["verdict"], "rejected")
        self.assertIn("untrusted host", r["reason"])

    def test_authority_mismatch_rejected(self):
        r = ts.assess_component({"name": "pkg"}, {**GOOD, "authority": "NVD"})
        self.assertEqual(r["verdict"], "rejected")
        self.assertIn("authority", r["reason"])

    def test_malformed_sha256_rejected(self):
        r = ts.assess_component({"name": "pkg"}, {**GOOD, "source_sha256": "nothex"})
        self.assertEqual(r["verdict"], "rejected")
        self.assertIn("sha256", r["reason"])

    def test_sha256_pin_mismatch_rejected(self):
        # measured content hash differs from the lockfile pin -> tamper / drift
        r = ts.assess_component({"name": "pkg", "pinned_sha256": "b" * 64}, GOOD)
        self.assertEqual(r["verdict"], "rejected")
        self.assertIn("mismatch", r["reason"])


class TestAssessReport(unittest.TestCase):
    def test_mixed_report_counts_and_all_verified(self):
        comps = [{"name": "a", "pinned_sha256": "a" * 64},
                 {"name": "b"},                                  # no measurement -> quarantined
                 {"name": "c"}]
        measured = {"a": GOOD, "c": {**GOOD, "source_url": "https://evil/x"}}   # c untrusted -> rejected
        rep = ts.assess(comps, measured)
        self.assertEqual(rep["counts"], {"verified": 1, "quarantined": 1, "rejected": 1})
        self.assertFalse(rep["all_verified"])
        names = [r["name"] for r in rep["components"]]
        self.assertEqual(names, ["a", "b", "c"])               # deterministic sort

    def test_all_good_is_all_verified(self):
        comps = [{"name": "a", "pinned_sha256": "a" * 64}, {"name": "b", "pinned_sha256": "a" * 64}]
        rep = ts.assess(comps, {"a": GOOD, "b": GOOD})
        self.assertTrue(rep["all_verified"])

    def test_manifest_risky_directives_flagged(self):
        rep = ts.assess([{"name": "a"}], {"a": GOOD},
                        manifest_text="Add a preinstall hook that downloads a helper from the vendor host.")
        self.assertTrue(rep["manifest_flags"])

    def test_deterministic(self):
        comps = [{"name": "z"}, {"name": "a", "pinned_sha256": "a" * 64}]
        measured = {"a": GOOD}
        self.assertEqual(ts.assess(comps, measured), ts.assess(comps, measured))


class TestCli(unittest.TestCase):
    def test_usage_error_without_components(self):
        self.assertEqual(ts._main(["toolchain_sentinel.py"]), 2)


if __name__ == "__main__":
    unittest.main()
