#!/usr/bin/env python3
"""B1-2 — GRC/audit evidence exporter: reproducible, tamper-evident, fully-traced evidence.

Acceptance (backlog B1-2): same state -> byte-identical report (100% reproducibility); every defense
carries lineage + fingerprint + verification basis; an EU AI Act Annex IV mapping table is included
(draft, SME-review flagged). A missing verification is surfaced, not hidden.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_provenance import defense_to_corpus_entry
from tools import audit_export as ax


def _verified_defense(did, threat, ctrl):
    return {"defense_id": did, "title": f"defense {did}", "kind": "designed", "origin": "pgf",
            "covers_threat": threat, "controls": [ctrl], "source_channels": ["CH-x"],
            "verification": {"method": "holdout-gate recall=1.0 precision=1.0", "passed": True},
            "implementations": [{"rule_id": did}]}


class TestAuditExport(unittest.TestCase):
    def setUp(self):
        self.corpus = [defense_to_corpus_entry(_verified_defense("DEF-2", "THR-b", "ctrl-b")),
                       defense_to_corpus_entry(_verified_defense("DEF-1", "THR-a", "ctrl-a"))]
        self.ledger = {"entries": [{"entry_id": "DEF-1"}, {"entry_id": "DEF-2"}]}

    def test_report_is_reproducible(self):
        a = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        b = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_content_hash_is_time_independent(self):
        a = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        b = ax.build_report(self.corpus, self.ledger, "1999-01-01")
        self.assertEqual(a["content_sha256"], b["content_sha256"])   # state, not time, drives the hash
        self.assertNotEqual(a["generated_at"], b["generated_at"])

    def test_defenses_sorted_and_fully_evidenced(self):
        r = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        ids = [d["defense_id"] for d in r["defenses"]]
        self.assertEqual(ids, ["DEF-1", "DEF-2"])                    # deterministic order
        c = r["completeness"]
        self.assertEqual(c["total_defenses"], 2)
        self.assertEqual(c["fully_evidenced"], 2)                    # lineage + fingerprint + verification
        for d in r["defenses"]:
            self.assertTrue(d["has_lineage"] and d["has_fingerprint"] and d["has_verification"])

    def test_missing_verification_is_surfaced(self):
        # a corpus entry whose lineage lacks a verification layer must be reported, not hidden
        weak = {"defense_id": "DEF-3", "title": "weak", "controls": ["c"], "covers_threat": "THR-c",
                "lineage": [{"layer": "defense", "id": "DEF-3"}, {"layer": "threat", "id": "THR-c"}]}
        r = ax.build_report([weak], {}, "2026-06-20")
        self.assertFalse(r["defenses"][0]["has_verification"])
        self.assertEqual(r["completeness"]["fully_evidenced"], 0)

    def test_annex_iv_mapping_present_and_flagged(self):
        r = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        self.assertTrue(r["annex_iv_mapping"])
        self.assertIn("SME", r["annex_iv_mapping_status"])           # honest gap flagged
        for m in r["annex_iv_mapping"]:
            self.assertIn("annex_iv_item", m)
            self.assertIn("sisai_evidence", m)

    def test_tamper_changes_hash(self):
        a = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        tampered = json.loads(json.dumps(self.corpus))
        tampered[0]["controls"] = ["ctrl-b", "ADDED-BACKDOOR"]
        b = ax.build_report(tampered, self.ledger, "2026-06-20")
        self.assertNotEqual(a["content_sha256"], b["content_sha256"])

    def test_render_md_contains_hash(self):
        r = ax.build_report(self.corpus, self.ledger, "2026-06-20")
        md = ax.render_md(r)
        self.assertIn(r["content_sha256"], md)
        self.assertIn("Annex IV", md)


if __name__ == "__main__":
    unittest.main()
