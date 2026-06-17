"""SISAI backbone tests: fingerprint, io, schema, channels, ledger, triage, provenance."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest import mock

import tests._path  # noqa: F401
from core.sisai_fingerprint import (
    normalize_name, channel_fingerprint, threat_fingerprint, defense_fingerprint,
)
from core.sisai_io import atomic_write_json, read_json
from core.sisai_schema import validate_against_schema, schema_features, schema_path
from core.sisai_channels import (
    empty_registry, register_channel, should_discover_channels, kind_coverage,
    next_channels_to_scan, missing_kinds,
)
from core.sisai_ledger import empty_ledger, is_consumed, append_entry, reindex_ledger
from core.sisai_triage import (
    triage_score, rank_threats, top_threat, measure_coverage, recency_decay,
)
from core.sisai_provenance import trace_defense, is_verified, defense_to_corpus_entry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestFingerprint(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_name("Agent PACT!"), "agentpact")

    def test_channel_fp_idempotent_by_url_kind(self):
        a = channel_fingerprint({"url": "https://x.io/", "kind": "cve"})
        b = channel_fingerprint({"url": "https://x.io", "kind": "cve"})
        self.assertEqual(a, b)  # trailing slash normalized
        self.assertNotEqual(a, channel_fingerprint({"url": "https://y.io", "kind": "cve"}))

    def test_threat_defense_fp_deterministic(self):
        t = {"title": "Prompt injection", "category": "llm", "cve": "CVE-1"}
        self.assertEqual(threat_fingerprint(t), threat_fingerprint(dict(t)))
        d = {"title": "Filter", "controls": ["b", "a"]}
        self.assertEqual(defense_fingerprint(d), defense_fingerprint({"title": "Filter", "controls": ["a", "b"]}))


class TestIo(unittest.TestCase):
    def test_roundtrip_and_default(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            atomic_write_json(p, {"a": 1})
            self.assertEqual(read_json(p), {"a": 1})
            self.assertEqual(read_json(os.path.join(d, "no.json"), default=[]), [])

    def test_atomic_failure_keeps_original(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            atomic_write_json(p, {"v": 1})
            with mock.patch("core.sisai_io.os.replace", side_effect=OSError("boom")):
                with self.assertRaises(OSError):
                    atomic_write_json(p, {"v": 2})
            self.assertEqual(read_json(p), {"v": 1})
            self.assertEqual([n for n in os.listdir(d) if n.endswith(".tmp")], [])

    def test_read_json_self_heals_from_bak(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.json")
            atomic_write_json(p, {"v": 1})
            atomic_write_json(p, {"v": 2})            # .bak now snapshots {"v": 1}
            with open(p, "w", encoding="utf-8") as f:
                f.write("{ broken json ")             # corrupt the live file
            with io.StringIO() as buf, redirect_stderr(buf):
                self.assertEqual(read_json(p), {"v": 1})  # recovered from .bak


class TestSchema(unittest.TestCase):
    def test_walker_required_and_enum(self):
        s = {"type": "object", "required": ["k"], "properties": {"k": {"enum": ["a", "b"]}}}
        self.assertEqual(validate_against_schema({"k": "a"}, s), [])
        self.assertTrue(validate_against_schema({}, s))
        self.assertTrue(validate_against_schema({"k": "z"}, s))

    def test_threat_schema_accepts_provenance(self):
        sp = schema_path(".", "threat")
        import json as _json
        with open(sp, encoding="utf-8") as f:
            self.assertTrue(schema_features(_json.load(f))["in_subset"])  # provenance keeps subset
        t = {"threat_id": "T", "title": "t", "category": "c",
             "recency": "2026-03-02",
             "provenance": {"source_url": "https://nvd.nist.gov/vuln/detail/CVE-2026-31854",
                            "authority": "NVD", "verified": True, "verified_on": "2026-06-17"}}
        self.assertEqual(validate_against_schema(t, sp), [])
        bad = dict(t, provenance=dict(t["provenance"], verified_on="June 2026"))
        self.assertTrue(validate_against_schema(bad, sp))  # bad date rejected

    def test_walker_pattern(self):
        s = {"type": "object", "properties":
             {"recency": {"type": ["string", "null"], "pattern": "^[0-9]{4}-[0-9]{2}(-[0-9]{2})?$"}}}
        self.assertEqual(validate_against_schema({"recency": "2025-07"}, s), [])
        self.assertEqual(validate_against_schema({"recency": "2026-06-17"}, s), [])
        self.assertEqual(validate_against_schema({"recency": None}, s), [])   # null skips pattern
        self.assertTrue(validate_against_schema({"recency": "July 2025"}, s))
        self.assertTrue(schema_features(s)["in_subset"])   # pattern stays in walker subset

    def test_shipped_schemas_in_subset(self):
        for name in ("channel", "threat", "defense", "ledger", "loop-state"):
            with open(schema_path(ROOT, name), encoding="utf-8") as f:
                self.assertTrue(schema_features(json.load(f))["in_subset"], name)


class TestChannels(unittest.TestCase):
    def test_register_idempotent(self):
        reg = empty_registry()
        ch = {"url": "https://nvd.nist.gov", "kind": "cve"}
        r1 = register_channel(reg, ch, now="2026-06-17")
        r2 = register_channel(reg, dict(ch), now="2026-06-18")
        self.assertEqual(r1["status"], "registered")
        self.assertEqual(r2["status"], "exists")
        self.assertEqual(len(reg["channels"]), 1)  # reuse, not duplicate

    def test_should_discover_when_few(self):
        reg = empty_registry()
        register_channel(reg, {"url": "a", "kind": "cve"}, now="2026-06-17")
        self.assertTrue(should_discover_channels(reg))  # < min_active

    def test_scan_prefers_undercovered_kind(self):
        reg = empty_registry()
        register_channel(reg, {"id": "C1", "url": "a", "kind": "cve"}, now="n")
        register_channel(reg, {"id": "C2", "url": "b", "kind": "cve"}, now="n")
        register_channel(reg, {"id": "C3", "url": "c", "kind": "paper"}, now="n")
        first = next_channels_to_scan(reg, k=1)[0]
        self.assertEqual(first["kind"], "paper")  # least covered kind first
        self.assertIn("news", missing_kinds(reg))


class TestLedger(unittest.TestCase):
    def test_is_consumed_by_fingerprint_and_title(self):
        led = empty_ledger()
        append_entry(led, {"entry_id": "E1", "kind": "threat", "title": "Prompt Injection",
                           "fingerprint": "fp1"}, now="2026-06-17")
        self.assertTrue(is_consumed({"fingerprint": "fp1"}, led)["consumed"])
        self.assertTrue(is_consumed({"title": "prompt injection"}, led)["consumed"])
        self.assertFalse(is_consumed({"title": "novel threat", "fingerprint": "z"}, led)["consumed"])

    def test_defense_requires_implementations(self):
        led = empty_ledger()
        with self.assertRaises(ValueError):
            append_entry(led, {"entry_id": "D1", "kind": "defense", "title": "X"}, now="n")
        append_entry(led, {"entry_id": "D1", "kind": "defense", "title": "X",
                           "implementations": [{"rule_id": "R1"}]}, now="n")
        self.assertEqual(len(led["entries"]), 1)

    def test_reindex(self):
        led = {"entries": [{"entry_id": "E1", "title": "T", "fingerprint": "fp"}]}
        reindex_ledger(led)
        self.assertEqual(led["by_fingerprint"], {"fp": "E1"})


class TestTriage(unittest.TestCase):
    def test_recency_decay_bounds(self):
        self.assertEqual(recency_decay("2026-06-17", "2026-06-17"), 1.0)
        self.assertEqual(recency_decay("2000-01-01", "2026-06-17"), 0.0)

    def test_recency_month_only_contributes(self):
        # seed corpus uses 'YYYY-MM'; it must decay between 0 and 1 (not dead at 0)
        d = recency_decay("2026-01", "2026-06-17")
        self.assertTrue(0.0 < d < 1.0)
        # newer month decays less than older month
        self.assertGreater(recency_decay("2026-05", "2026-06-17"),
                           recency_decay("2025-01", "2026-06-17"))

    def test_high_cvss_recent_ranks_first(self):
        threats = [
            {"threat_id": "T1", "cvss": 9.8, "recency": "2026-06-01"},
            {"threat_id": "T2", "cvss": 2.0, "recency": "2020-01-01"},
        ]
        self.assertEqual(top_threat(threats, "2026-06-17")["threat_id"], "T1")

    def test_rank_deterministic_tiebreak(self):
        threats = [{"threat_id": "B", "cvss": 5, "recency": "2026-06-17"},
                   {"threat_id": "A", "cvss": 5, "recency": "2026-06-17"}]
        r = rank_threats(threats, "2026-06-17")
        self.assertEqual(r[0]["threat"]["threat_id"], "A")  # tie -> id asc

    def test_coverage_repair_when_skewed(self):
        threats = [{"category": "x"}] * 8 + [{"category": "y"}, {"category": "z"}]
        rep = measure_coverage(threats)
        self.assertTrue(rep["repair_required"])  # dominance 0.8

    def test_coverage_healthy_when_spread(self):
        threats = [{"category": c} for c in ("a", "b", "c", "d", "e")]
        self.assertFalse(measure_coverage(threats)["repair_required"])


class TestProvenance(unittest.TestCase):
    def _verified(self):
        return {"defense_id": "D1", "title": "Filter", "kind": "designed",
                "covers_threat": "T1", "source_channels": ["CH-1"],
                "verification": {"method": "redteam", "passed": True},
                "implementations": [{"rule_id": "R1"}]}

    def test_trace_lineage_order(self):
        layers = [s["layer"] for s in trace_defense(self._verified())]
        self.assertEqual(layers[0], "defense")
        self.assertIn("threat", layers)
        self.assertIn("self_designed", layers)
        self.assertIn("verification", layers)

    def test_corpus_entry_requires_verified(self):
        with self.assertRaises(ValueError):
            defense_to_corpus_entry({"defense_id": "D", "title": "x",
                                     "verification": {"passed": False}})
        entry = defense_to_corpus_entry(self._verified())
        self.assertEqual(entry["defense_id"], "D1")
        self.assertIn("lineage", entry)

    def test_is_verified(self):
        self.assertFalse(is_verified({"verification": {"passed": True}}))  # no impl
        self.assertTrue(is_verified(self._verified()))


if __name__ == "__main__":
    unittest.main()
