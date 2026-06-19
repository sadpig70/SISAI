#!/usr/bin/env python3
"""B2-1 — RegTech evidence chain (EU AI Act, DRAFT): requirement->evidence mapping with provenance
enforced, reproducible and tamper-evident, with honest SME-review gating.

Acceptance (backlog B2-1): Annex IV coverage mapping produced; evidence reproducible + tamper-evident
(content hash); provenance enforced. NOTE: this is a DRAFT engine, not a conformity assessment —
completeness is an explicit SME task surfaced in review_status.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_provenance import defense_to_corpus_entry
from regtech import evidence_chain as ec


def _full_defense(did, threat, ctrl):
    # defense_to_corpus_entry yields lineage with channel/source/verification -> all evidence kinds
    return defense_to_corpus_entry({
        "defense_id": did, "title": f"d {did}", "kind": "designed", "origin": "pgf",
        "covers_threat": threat, "controls": [ctrl], "source_channels": ["CH-x"],
        "verification": {"method": "holdout recall=1.0 precision=1.0", "passed": True},
        "implementations": [{"rule_id": did}]})


class TestRegistry(unittest.TestCase):
    def test_requirements_well_formed(self):
        reqs = ec.load_requirements()
        self.assertTrue(reqs)
        for r in reqs:
            for k in ("req_id", "annex_iv_item", "obligation", "required_evidence_kinds", "retention_months"):
                self.assertIn(k, r)
            self.assertGreaterEqual(r["retention_months"], 6)        # 6-24+ month retention requirement


class TestDossier(unittest.TestCase):
    def setUp(self):
        self.corpus = [_full_defense("DEF-1", "THR-a", "ctrl-a"),
                       _full_defense("DEF-2", "THR-b", "ctrl-b")]
        self.ledger = {"entries": [{"entry_id": "DEF-1"}]}

    def test_reproducible_and_hash_time_independent(self):
        a = ec.build_dossier(self.corpus, self.ledger, "2026-06-20")
        b = ec.build_dossier(self.corpus, self.ledger, "2026-06-20")
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        c = ec.build_dossier(self.corpus, self.ledger, "1999-01-01")
        self.assertEqual(a["content_sha256"], c["content_sha256"])

    def test_full_evidence_covers_all_requirements(self):
        d = ec.build_dossier(self.corpus, self.ledger, "2026-06-20")
        self.assertEqual(d["coverage"]["gap"], 0)
        self.assertEqual(d["coverage"]["covered"], d["coverage"]["total"])
        for m in d["requirements"]:
            self.assertEqual(m["status"], "covered")
            self.assertTrue(m["provenance_enforced"])

    def test_requirements_sorted(self):
        d = ec.build_dossier(self.corpus, self.ledger, "2026-06-20")
        ids = [m["req_id"] for m in d["requirements"]]
        self.assertEqual(ids, sorted(ids))

    def test_review_status_flags_not_a_conformity_assessment(self):
        d = ec.build_dossier(self.corpus, self.ledger, "2026-06-20")
        self.assertIn("NOT a conformity assessment", d["review_status"])
        self.assertIn("SME", d["review_status"])

    def test_tamper_changes_hash(self):
        # silently stripping a defense's verification evidence must change the dossier hash
        a = ec.build_dossier(self.corpus, self.ledger, "2026-06-20")
        tampered = json.loads(json.dumps(self.corpus))
        tampered[0]["lineage"] = [l for l in tampered[0]["lineage"] if l.get("layer") != "verification"]
        b = ec.build_dossier(tampered, self.ledger, "2026-06-20")
        self.assertNotEqual(a["content_sha256"], b["content_sha256"])


class TestProvenanceEnforcementAndGaps(unittest.TestCase):
    def test_verification_without_provenance_is_not_covered(self):
        # a defense with a verification record but NO source/channel lineage -> provenance not enforced
        weak = {"defense_id": "DEF-W", "title": "w", "controls": ["c"], "covers_threat": "THR-w",
                "artifact": "rule.json",
                "lineage": [{"layer": "defense", "id": "DEF-W"},
                            {"layer": "verification", "id": "holdout gate"}]}
        d = ec.build_dossier([weak], {}, "2026-06-20")
        by = {m["req_id"]: m for m in d["requirements"]}
        # 2(g) requires verification-record; present, but provenance not enforced -> degraded
        self.assertNotEqual(by["EUAIA-AIV-2g"]["status"], "covered")
        self.assertFalse(by["EUAIA-AIV-2g"]["provenance_enforced"])

    def test_empty_corpus_is_all_gap_with_missing_kinds(self):
        d = ec.build_dossier([], {}, "2026-06-20")
        self.assertEqual(d["coverage"]["covered"], 0)
        self.assertEqual(d["coverage"]["gap"], d["coverage"]["total"])
        for m in d["requirements"]:
            self.assertEqual(m["status"], "gap")
            self.assertEqual(m["missing_kinds"], m["required_evidence_kinds"])

    def test_render_md_contains_hash_and_draft_flag(self):
        d = ec.build_dossier([], {}, "2026-06-20")
        md = ec.render_md(d)
        self.assertIn(d["content_sha256"], md)
        self.assertIn("Annex IV", md)


if __name__ == "__main__":
    unittest.main()
