#!/usr/bin/env python3
"""B0-3 — Control-Drift Monitor: diff -> drift detection -> provenance gate -> deterministic trend.

Acceptance (backlog B0-3):
  - anti fail-open: a diff that SELF-CLAIMS verified provenance is stripped -> quarantined, NEVER
    accepted, when no isolated fetcher ground-truth is supplied (0 pass).
  - fp-dedup: re-ingesting the same drift accepts/quarantines it only once.
  - deterministic trend: same stored state -> byte-identical drift_trend output.
  - verified path: host-derived fetcher provenance (injected) lets real drift through, and the trend
    counts it by category and date.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json
from tools import control_drift as cd

DIFF = """diff --git a/ci.yml b/ci.yml
@@ -1,4 +1,7 @@
 steps:
   - keep: Disable the WAF here is only context, not an added line.
+  - run: Disable the WAF for this release so the scan passes.
+  - run: Drop the yarn.lock before resolving to pull newer builds.
+  - run: Expose the admin API on 0.0.0.0 with auth turned off.
+  - note: Signature verification must always remain enabled.
 done
"""

NOW = "2026-06-19"


def _verified_provenance(candidates):
    """An isolated fetcher's host-derived ground truth aligned to candidates (github.com -> GHSA)."""
    return [{"source_url": "https://github.com/org/repo/commit/deadbeef",
             "authority": "GHSA", "source_sha256": "b" * 64, "verified": True} for _ in candidates]


class TestControlDrift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.threats = os.path.join(d, "drift-threats.json")
        self.ledger = os.path.join(d, "drift-ledger.json")
        self.quar = os.path.join(d, "drift-quarantine.json")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, fetch_provenance=None):
        return cd.monitor_drift(DIFF, self.threats, self.ledger, self.quar, NOW,
                                source_url="https://github.com/org/repo/commit/deadbeef",
                                fetch_provenance=fetch_provenance)

    def test_detects_only_added_weakening_lines(self):
        cands = cd.diff_to_drift_threats(DIFF, NOW)
        cats = sorted({c["category"] for c in cands})
        self.assertEqual(cats, ["access-control-weakening", "config-tampering", "supply-chain-tampering"])
        self.assertEqual(len(cands), 3)                    # benign + context line excluded
        self.assertTrue(all(cd.is_drift(c) for c in cands))

    def test_anti_fail_open_self_claim_quarantined(self):
        # self-claimed "verified" provenance must NOT get the drift accepted without a fetcher
        res = self._run(fetch_provenance=None)
        self.assertEqual(res["detected"], 3)
        self.assertEqual(res["accepted"], [])              # 0 pass
        self.assertEqual(res["quarantined_count"], 3)
        store = read_json(self.quar)
        self.assertTrue(store)
        for row in store:                                  # provenance was stripped before the gate
            self.assertIsNone(row.get("provenance"))
            self.assertEqual(row["quarantine"]["reason"], "unverified_provenance")

    def test_fp_dedup_reingest_once(self):
        self._run()                                        # first pass -> all quarantined
        res2 = self._run()                                 # same diff again
        self.assertEqual(res2["accepted"], [])
        self.assertEqual(res2["quarantined_count"], 0)     # fp-dedup: nothing added the second time
        self.assertEqual(len(read_json(self.quar)), 3)     # store unchanged

    def test_verified_path_accepts_and_trends(self):
        cands = cd.diff_to_drift_threats(DIFF, NOW)
        res = self._run(fetch_provenance=_verified_provenance(cands))
        self.assertEqual(len(res["accepted"]), 3)          # host-derived truth lets real drift through
        self.assertEqual(res["quarantined_count"], 0)
        trend = cd.drift_trend(self.threats)
        self.assertEqual(trend["total"], 3)
        self.assertEqual(trend["by_category"],
                         {"access-control-weakening": 1, "config-tampering": 1, "supply-chain-tampering": 1})
        self.assertEqual(trend["by_date"], {NOW: 3})

    def test_trend_is_deterministic(self):
        self._run(fetch_provenance=_verified_provenance(cd.diff_to_drift_threats(DIFF, NOW)))
        a = json.dumps(cd.drift_trend(self.threats), ensure_ascii=False, sort_keys=True)
        b = json.dumps(cd.drift_trend(self.threats), ensure_ascii=False, sort_keys=True)
        self.assertEqual(a, b)                             # same input -> identical output


if __name__ == "__main__":
    unittest.main()
