#!/usr/bin/env python3
"""Unit tests for DESIGN-SISAIImprove @v1.4 pure-core primitives (INC1).

Covers: ProvenanceGate (host authority, verified gate, strip), CritiqueGate, DetectLib (inert hygiene,
compile/scan/blue_run), VerifyLib (split-aware advisory gate), CrossModelRoles (advisory + binding pairs).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import sisai_provenance as prov
from core import sisai_detect as det
from core import sisai_verify as ver

HEX64 = "a" * 64


class TestProvenanceGate(unittest.TestCase):
    def test_host_from_url(self):
        self.assertEqual(prov.host_from_url("https://nvd.nist.gov/vuln/x"), "nvd.nist.gov")
        self.assertEqual(prov.host_from_url("HTTPS://GitHub.com/a/b"), "github.com")
        self.assertEqual(prov.host_from_url("https://user@arxiv.org/abs/1"), "arxiv.org")
        self.assertEqual(prov.host_from_url("not a url"), "")

    def test_authority_from_host_not_page(self):
        self.assertEqual(prov.authority_from_url("https://cve.mitre.org/x"), "MITRE")
        self.assertIsNone(prov.authority_from_url("https://evil.example.com/x"))

    def test_verified_gate(self):
        good = {"provenance": {"verified": True, "source_url": "https://nvd.nist.gov/v",
                               "authority": "NVD", "source_sha256": HEX64}}
        self.assertTrue(prov.is_provenance_verified(good))

    def test_gate_fails_closed(self):
        base = {"verified": True, "source_url": "https://nvd.nist.gov/v", "authority": "NVD", "source_sha256": HEX64}
        # authority must match host-derived
        self.assertFalse(prov.is_provenance_verified({"provenance": {**base, "authority": "MITRE"}}))
        # host must be whitelisted
        self.assertFalse(prov.is_provenance_verified({"provenance": {**base, "source_url": "https://evil.com/x"}}))
        # sha256 must be 64-hex
        self.assertFalse(prov.is_provenance_verified({"provenance": {**base, "source_sha256": "short"}}))
        # verified flag required
        self.assertFalse(prov.is_provenance_verified({"provenance": {**base, "verified": False}}))
        # null provenance (the existing seed shape) is not verified, but does not raise
        self.assertFalse(prov.is_provenance_verified({"provenance": None}))

    def test_strip_incoming_provenance(self):
        t = {"title": "x", "provenance": {"verified": True, "authority": "NVD"}}
        stripped = prov.strip_incoming_provenance(t)
        self.assertIsNone(stripped["provenance"])
        self.assertEqual(t["provenance"]["verified"], True)   # original untouched (copy)


class TestCritiqueGate(unittest.TestCase):
    def test_is_critiqued(self):
        self.assertTrue(prov.is_critiqued({"critique": {"passed": True}}))
        self.assertFalse(prov.is_critiqued({"critique": {"passed": False}}))
        self.assertFalse(prov.is_critiqued({}))                # grandfathered at the wire, not here
        self.assertFalse(prov.is_critiqued({"critique": None}))


class TestDetectLib(unittest.TestCase):
    def test_inert_hygiene(self):
        self.assertTrue(det.is_inert_indicator({"text": "disable tls", "label": "malicious"}))
        self.assertFalse(det.is_inert_indicator({"text": "a\nb", "label": "malicious"}))   # multiline
        self.assertFalse(det.is_inert_indicator({"text": "x" * 241, "label": "benign"}))   # too long
        self.assertFalse(det.is_inert_indicator({"text": "", "label": "malicious"}))       # empty
        self.assertFalse(det.is_inert_indicator({"text": "x", "label": "other"}))          # bad label

    def test_compile_skips_bad(self):
        compiled, skipped = det.compile_rule({"patterns": [
            {"regex": "(?i)disable"}, {"regex": "("}, {"regex": "x" * 401}]})
        self.assertEqual(len(compiled), 1)
        self.assertEqual(skipped, 2)

    def test_scan_and_blue_run(self):
        compiled, _ = det.compile_rule({"patterns": [{"regex": "(?i)disable"}]})
        self.assertTrue(det.scan("please Disable the WAF", compiled))
        self.assertFalse(det.scan("enable the WAF", compiled))
        variants = [{"text": "turn off the WAF", "label": "malicious"},      # missed
                    {"text": "disable the scan", "label": "malicious"},      # caught
                    {"text": "benign note", "label": "benign"}]              # ignored (not malicious)
        misses = det.blue_run(compiled, variants)
        self.assertEqual([m["text"] for m in misses], ["turn off the WAF"])


class TestVerifyLib(unittest.TestCase):
    def _predict(self, compiled):
        return lambda t: det.scan(t, compiled)

    def test_legacy_gate_when_holdout_unsized(self):
        compiled, _ = det.compile_rule({"patterns": [{"regex": "(?i)disable"}]})
        samples = [{"text": "disable tls", "label": "malicious"},
                   {"text": "keep tls on", "label": "benign"}]   # no holdout split -> legacy full-set
        r = ver.verify_suite(samples, self._predict(compiled))
        self.assertEqual(r["gate"], "legacy-fullset")
        self.assertIsNone(r["holdout"])
        self.assertTrue(r["passed"])                              # recall 1.0, precision 1.0

    def test_holdout_gate_when_sized(self):
        compiled, _ = det.compile_rule({"patterns": [{"regex": "(?i)(disable|turn off|bypass|skip|remove)"}]})
        mal = [{"text": f"disable control {i}", "label": "malicious", "split": "holdout"} for i in range(5)]
        ben = [{"text": f"keep control {i} on", "label": "benign", "split": "holdout"} for i in range(4)]
        r = ver.verify_suite(mal + ben, self._predict(compiled))
        self.assertEqual(r["gate"], "holdout")
        self.assertTrue(r["passed"])

    def test_adversarial_split_not_gated(self):
        compiled, _ = det.compile_rule({"patterns": [{"regex": "(?i)disable"}]})
        # adversarial rows present but holdout unsized -> still legacy; adversarial never forces the gate
        samples = [{"text": "disable x", "label": "malicious"},
                   {"text": "noise", "label": "malicious", "split": "adversarial"},
                   {"text": "fine", "label": "benign"}]
        r = ver.verify_suite(samples, self._predict(compiled))
        self.assertEqual(r["gate"], "legacy-fullset")


class TestCrossModelRoles(unittest.TestCase):
    REG = {"entries": [
        {"suite": "S1", "author_model": "m-a", "holdout_curator_model": "grok-build", "judge_model": "m-j"},
        {"suite": "S2", "author_model": "m-x", "holdout_curator_model": "m-x", "judge_model": "m-j"},   # author==curator
        {"suite": "S3", "author_model": "m-a", "holdout_curator_model": "grok-build"},                  # incomplete
    ]}

    def setUp(self):
        self.idx = ver.index_role_registry(self.REG)

    def test_disjoint_ok(self):
        self.assertEqual(ver.roles_disjoint("S1", self.idx), {"ok": True, "gate": "roles"})

    def test_binding_pair_violation(self):
        self.assertEqual(ver.roles_disjoint("S2", self.idx)["ok"], False)   # author == curator

    def test_curator_eq_judge_is_allowed(self):
        idx = ver.index_role_registry({"entries": [
            {"suite": "S", "author_model": "a", "holdout_curator_model": "c", "judge_model": "c"}]})
        self.assertTrue(ver.roles_disjoint("S", idx)["ok"])                  # curator==judge NOT a violation

    def test_incomplete_fails_closed(self):
        self.assertEqual(ver.roles_disjoint("S3", self.idx)["gate"], "roles_incomplete")
        self.assertFalse(ver.roles_disjoint("S3", self.idx)["ok"])

    def test_unregistered_grandfathered(self):
        r = ver.roles_disjoint("UNKNOWN", self.idx)
        self.assertEqual(r["gate"], "roles_unprovisioned")
        self.assertTrue(r["ok"])                                            # advisory, never blocks the 11 suites


if __name__ == "__main__":
    unittest.main()
