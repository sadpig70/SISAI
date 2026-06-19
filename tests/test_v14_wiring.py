#!/usr/bin/env python3
"""INC2 wiring tests — ProvenanceGate into ingest_threats + CritiqueGate into record_defense.

Verifies the gates ENFORCE when provisioned (quarantine_path / require_critique) and GRANDFATHER
(legacy behavior) when not — so the existing 11 suites / seeds never regress.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import sisai

HEX64 = "b" * 64
NVD_PROV = {"verified": True, "source_url": "https://nvd.nist.gov/vuln/CVE-1",
            "authority": "NVD", "source_sha256": HEX64}


def _tmp(d, name, obj):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def _readj(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


class TestIngestProvenanceGate(unittest.TestCase):
    def test_legacy_mode_no_gate(self):
        """Without quarantine_path, threats ingest regardless of provenance (grandfather)."""
        with tempfile.TemporaryDirectory() as d:
            tp = os.path.join(d, "threats.json"); lp = _tmp(d, "ledger.json", {})
            raw = [{"title": "New attack A", "category": "supply-chain"}]
            r = sisai.ingest_threats(raw, tp, lp, now="2026-06-19")
            self.assertEqual(r["status"], "ingested")
            self.assertEqual(r["quarantined_count"], 0)

    def test_gate_quarantines_unverified(self):
        with tempfile.TemporaryDirectory() as d:
            tp = os.path.join(d, "threats.json"); lp = _tmp(d, "ledger.json", {})
            qp = os.path.join(d, "quarantine.json")
            raw = [{"title": "Unverified attack", "category": "supply-chain"}]   # no provenance
            r = sisai.ingest_threats(raw, tp, lp, now="2026-06-19", quarantine_path=qp)
            self.assertEqual(r["accepted"], [])
            self.assertEqual(r["quarantined_count"], 1)
            self.assertEqual(_readj(qp)[0]["quarantine"]["reason"], "unverified_provenance")

    def test_gate_admits_verified_via_fetch_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            tp = os.path.join(d, "threats.json"); lp = _tmp(d, "ledger.json", {})
            qp = os.path.join(d, "quarantine.json")
            raw = [{"title": "Verified attack", "category": "cve"}]
            r = sisai.ingest_threats(raw, tp, lp, now="2026-06-19",
                                     quarantine_path=qp, fetch_provenance=[NVD_PROV])
            self.assertEqual(len(r["accepted"]), 1)
            self.assertEqual(r["quarantined_count"], 0)

    def test_page_claimed_provenance_is_stripped(self):
        """A page self-claiming verified NVD provenance is stripped -> quarantined unless the
        out-of-band fetcher supplies it."""
        with tempfile.TemporaryDirectory() as d:
            tp = os.path.join(d, "threats.json"); lp = _tmp(d, "ledger.json", {})
            qp = os.path.join(d, "quarantine.json")
            raw = [{"title": "Liar", "category": "cve", "provenance": NVD_PROV}]   # self-claimed
            r = sisai.ingest_threats(raw, tp, lp, now="2026-06-19", quarantine_path=qp)  # no fetch_provenance
            self.assertEqual(r["quarantined_count"], 1)
            self.assertEqual(r["accepted"], [])


class TestRecordCritiqueGate(unittest.TestCase):
    def _defense(self, critique=None):
        d = {"defense_id": "DEF-x1", "title": "Test defense", "kind": "designed",
             "covers_threat": "THR-x", "verification": {"method": "redteam", "passed": True},
             "implementations": [{"rule_id": "R1", "artifact_path": "rules/r1.json"}]}
        if critique is not None:
            d["critique"] = critique
        return d

    def test_legacy_no_critique_required(self):
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "l.json"); cor = os.path.join(d, "c.json")
            r = sisai.record_defense(self._defense(), led, cor, now="2026-06-19")  # require_critique default False
            self.assertEqual(r["status"], "closed")

    def test_required_rejects_uncritiqued_first_record(self):
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "l.json"); cor = os.path.join(d, "c.json")
            r = sisai.record_defense(self._defense(), led, cor, now="2026-06-19", require_critique=True)
            self.assertEqual(r["status"], "rejected")
            self.assertIn("critique", r["why"])

    def test_required_admits_critiqued(self):
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "l.json"); cor = os.path.join(d, "c.json")
            r = sisai.record_defense(self._defense({"passed": True}), led, cor,
                                     now="2026-06-19", require_critique=True)
            self.assertEqual(r["status"], "closed")

    def test_already_recorded_is_grandfathered(self):
        """A defense recorded once (no critique, legacy) re-records as no-op even under require_critique."""
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "l.json"); cor = os.path.join(d, "c.json")
            sisai.record_defense(self._defense(), led, cor, now="2026-06-19")            # first: legacy
            r = sisai.record_defense(self._defense(), led, cor, now="2026-06-20", require_critique=True)
            self.assertEqual(r["status"], "already_recorded")                            # grandfathered


if __name__ == "__main__":
    unittest.main()
