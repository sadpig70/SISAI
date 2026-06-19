#!/usr/bin/env python3
"""SISAI B1-3 — SOC alert-clustering (deterministic, defensive-only).

Folds a stream of SOC alerts / tickets into the threats that actually RECUR: cluster by
`core/sisai_fingerprint.threat_fingerprint`, rank the clusters with `core/sisai_triage.rank_threats`
(severity x recency), and surface attack-surface blind spots with `core/sisai_triage.measure_coverage`
(category dominance / narrowness). Idempotent: an alert whose `alert_id` was already ingested is a
re-delivery and is ignored (no double count); a recurring DISTINCT occurrence increments its cluster.

The structured alert fields (title/category/cvss/recency) are assumed already extracted from raw text
by the meta-layer; this is the deterministic clustering/triage backbone (no clock/AI/network; `now`
injected). Output is a report (data); nothing is recorded into the live ledger/corpus.

An alert: {alert_id?, title, category?, cvss?, recency?, techniques?}.

CLI:
    python tools/soc_cluster.py --alerts alerts.json [--store .sisai/soc-store.json] [--now D] [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json, atomic_write_json                 # noqa: E402
from core.sisai_fingerprint import threat_fingerprint                 # noqa: E402
from core.sisai_triage import rank_threats, measure_coverage          # noqa: E402


def empty_store() -> dict:
    return {"clusters": {}, "seen_alert_ids": []}


def _max(a, b):
    """Deterministic max that tolerates None (treats None as smallest)."""
    if a is None:
        return b
    if b is None:
        return a
    return a if a >= b else b


def ingest_alerts(store: dict, alerts: list) -> tuple:
    """Fold alerts into the cluster store, idempotently. Returns (store, added).

    Re-delivery of an already-seen alert_id is ignored (idempotent). A new distinct occurrence either
    opens a cluster (by threat_fingerprint) or increments an existing one, keeping the worst CVSS and
    newest recency as the cluster representative (order-independent)."""
    store = store or empty_store()
    store.setdefault("clusters", {})
    seen = set(store.setdefault("seen_alert_ids", []))
    added = 0
    for a in alerts or []:
        aid = a.get("alert_id")
        if aid is not None and aid in seen:
            continue                                       # idempotent: re-delivered alert ignored
        if aid is not None:
            seen.add(aid)
        fp = threat_fingerprint(a)
        cl = store["clusters"].get(fp)
        if cl is None:
            store["clusters"][fp] = {
                "fingerprint": fp, "threat_id": f"THR-{fp[:8]}",
                "title": a.get("title", ""), "category": a.get("category", "uncategorized"),
                "cvss": a.get("cvss"), "recency": a.get("recency"),
                "techniques": sorted(set(a.get("techniques", []) or [])), "count": 1,
            }
        else:
            cl["count"] += 1
            cl["cvss"] = _max(cl.get("cvss"), a.get("cvss"))
            cl["recency"] = _max(cl.get("recency"), a.get("recency"))
            cl["techniques"] = sorted(set(cl["techniques"]) | set(a.get("techniques", []) or []))
        added += 1
    store["seen_alert_ids"] = sorted(seen)
    return store, added


def _cluster_threats(store: dict) -> list:
    """Distinct cluster representatives (deterministic order by fingerprint)."""
    return [store["clusters"][fp] for fp in sorted(store.get("clusters", {}))]


def triage_clusters(store: dict, now: str) -> list:
    """Clusters ranked by triage score (severity x recency); each carries its recurrence count."""
    ranked = rank_threats(_cluster_threats(store), now)
    return [{"threat_id": r["threat"]["threat_id"], "title": r["threat"]["title"],
             "category": r["threat"]["category"], "count": r["threat"]["count"],
             "score": r["score"]} for r in ranked]


def coverage(store: dict, thresholds: dict = None) -> dict:
    """Blind-spot signals over the DISTINCT clusters (threat types, not raw alert volume)."""
    return measure_coverage(_cluster_threats(store), thresholds)


def report(store: dict, now: str, thresholds: dict = None) -> dict:
    clusters = _cluster_threats(store)
    total_alerts = sum(c["count"] for c in clusters)
    return {
        "summary": {"total_alerts": total_alerts, "distinct_clusters": len(clusters),
                    "dedup_ratio": round(1 - len(clusters) / total_alerts, 4) if total_alerts else 0.0,
                    "ingested_alert_ids": len(store.get("seen_alert_ids", []))},
        "ranked": triage_clusters(store, now),
        "coverage": coverage(store, thresholds),
    }


def cluster_alerts(alerts: list) -> dict:
    """One-shot pure clustering (no persistence). Convenience over ingest_alerts(empty_store())."""
    store, _ = ingest_alerts(empty_store(), alerts)
    return store


# ---- CLI ----------------------------------------------------------------------------------------

def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    af = _opt(argv, "--alerts")
    if not af:
        sys.stderr.write("usage: python tools/soc_cluster.py --alerts <alerts.json> "
                         "[--store <store.json>] [--now YYYY-MM-DD] [--json]\n")
        return 2
    alerts = read_json(af) or []
    store_path = _opt(argv, "--store")
    store = (read_json(store_path) if store_path else None) or empty_store()
    store, added = ingest_alerts(store, alerts)
    if store_path:
        atomic_write_json(store_path, store)
    rep = report(store, _opt(argv, "--now", "1970-01-01"))
    rep["added_this_run"] = added
    if "--json" in argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        s = rep["summary"]
        print(f"alerts={s['total_alerts']} clusters={s['distinct_clusters']} "
              f"added={added} | coverage repair_required={rep['coverage']['repair_required']}")
        for c in rep["ranked"][:5]:
            print(f"  {c['score']:.4f} x{c['count']} [{c['category']}] {c['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
