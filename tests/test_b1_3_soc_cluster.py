#!/usr/bin/env python3
"""B1-3 — SOC alert-clustering: dedup is idempotent, triage is reproducible, blind-spot signals fire.

Acceptance (backlog B1-3): re-ingesting the same alert adds nothing (idempotent dedup); the cluster
ranking is deterministic; coverage emits dominance/narrow blind-spot signals.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import soc_cluster as sc

ALERTS = [
    {"alert_id": "a1", "title": "Brute force on SSH", "category": "credential-attack", "cvss": 7.0, "recency": "2026-06-19"},
    {"alert_id": "a2", "title": "Brute force on SSH", "category": "credential-attack", "cvss": 8.5, "recency": "2026-06-20"},
    {"alert_id": "a3", "title": "Prompt injection via README", "category": "llm-prompt-injection", "cvss": 6.0, "recency": "2026-06-18"},
]


class TestClustering(unittest.TestCase):
    def test_clusters_by_fingerprint_and_counts_recurrence(self):
        store = sc.cluster_alerts(ALERTS)
        self.assertEqual(len(store["clusters"]), 2)                  # the two SSH alerts fold into one
        ssh = next(c for c in store["clusters"].values() if c["title"] == "Brute force on SSH")
        self.assertEqual(ssh["count"], 2)
        self.assertEqual(ssh["cvss"], 8.5)                          # worst CVSS kept
        self.assertEqual(ssh["recency"], "2026-06-20")             # newest recency kept

    def test_reingest_same_alert_ids_is_idempotent(self):
        store, added = sc.ingest_alerts(sc.empty_store(), ALERTS)
        self.assertEqual(added, 3)
        store, added2 = sc.ingest_alerts(store, ALERTS)             # re-delivery
        self.assertEqual(added2, 0)                                 # nothing added
        self.assertEqual(len(store["clusters"]), 2)                # cluster set unchanged
        self.assertEqual(sum(c["count"] for c in store["clusters"].values()), 3)  # counts unchanged

    def test_new_distinct_occurrence_without_id_increments(self):
        store, _ = sc.ingest_alerts(sc.empty_store(), ALERTS)
        # an id-less recurrence of the SSH threat -> counted (genuine new occurrence)
        store, added = sc.ingest_alerts(store, [{"title": "Brute force on SSH", "category": "credential-attack"}])
        self.assertEqual(added, 1)
        ssh = next(c for c in store["clusters"].values() if c["title"] == "Brute force on SSH")
        self.assertEqual(ssh["count"], 3)


class TestTriageAndCoverage(unittest.TestCase):
    def test_ranking_is_deterministic_and_severity_ordered(self):
        store = sc.cluster_alerts(ALERTS)
        r1 = sc.triage_clusters(store, "2026-06-20")
        r2 = sc.triage_clusters(store, "2026-06-20")
        self.assertEqual(r1, r2)                                    # reproducible
        self.assertEqual(r1[0]["title"], "Brute force on SSH")     # higher severity+recency first

    def test_report_is_deterministic(self):
        store = sc.cluster_alerts(ALERTS)
        a = json.dumps(sc.report(store, "2026-06-20"), sort_keys=True)
        b = json.dumps(sc.report(store, "2026-06-20"), sort_keys=True)
        self.assertEqual(a, b)

    def test_coverage_narrow_signal(self):
        store = sc.cluster_alerts(ALERTS)                          # only 2 distinct categories
        cov = sc.coverage(store)
        self.assertTrue(cov["signals"]["narrow"])                  # < min_categories (3)
        self.assertEqual(cov["distinct_categories"], 2)

    def test_coverage_dominance_signal(self):
        skewed = [{"alert_id": f"x{i}", "title": f"cred attack {i}", "category": "credential-attack"}
                  for i in range(5)] + [{"alert_id": "y", "title": "one injection", "category": "llm-prompt-injection"}]
        cov = sc.coverage(sc.cluster_alerts(skewed))
        self.assertTrue(cov["signals"]["skewed"])                  # one category dominates
        self.assertGreaterEqual(cov["category_dominance"], 0.6)


class TestCli(unittest.TestCase):
    def test_usage_error_without_alerts(self):
        self.assertEqual(sc._main(["soc_cluster.py"]), 2)


if __name__ == "__main__":
    unittest.main()
