#!/usr/bin/env python3
"""SISAI channel registry — information sources are first-class, self-expanding assets.

The system does not use a fixed channel list. The AI runtime (skills) DISCOVERS new
sources (advisories, CVE feeds, papers, OSS, exploit DBs, vendor intel); this
deterministic backbone RECORDS them (dedup by fingerprint) and decides which to scan
next so coverage stays broad — discover → record → reuse, with no desync.

Determinism: pure functions, stdlib only, `now` injected. Discovery itself (finding
a brand-new source) is the AI meta-layer; recording/dedup/selection is here.
"""

from .sisai_fingerprint import channel_fingerprint

CHANNEL_KINDS = ("cve", "advisory", "news", "paper", "oss", "exploit_db",
                 "vendor_intel", "standard")

DEFAULT_CHANNEL_POLICY = {
    "min_active_channels": 4,       # below this -> a discovery turn is needed
    "min_kinds_covered": 4,         # distinct source kinds we want represented
}


def empty_registry() -> dict:
    return {"channels": [], "by_fingerprint": {}}


def register_channel(registry: dict, channel: dict, now: str) -> dict:
    """Record a discovered channel. Idempotent by fingerprint (reuse guarantee).

    Returns {status: 'registered'|'exists', channel_id}. Preserves `discovered_from`
    (provenance of how the source was found). Mutates and returns nothing extra.
    """
    fp = channel_fingerprint(channel)
    if not fp:
        raise ValueError("register_channel: channel needs a url/kind to fingerprint")
    if fp in registry["by_fingerprint"]:
        return {"status": "exists", "channel_id": registry["by_fingerprint"][fp]}
    cid = channel.get("id") or f"CH-{fp[:8]}"
    record = dict(channel)
    record["id"] = cid
    record["fingerprint"] = fp
    record["status"] = channel.get("status", "active")
    record["registered_at"] = now
    record.setdefault("kind", "news")
    record.setdefault("orthogonality", 0.5)
    registry["channels"].append(record)
    registry["by_fingerprint"][fp] = cid
    return {"status": "registered", "channel_id": cid}


def active_channels(registry: dict) -> list:
    return [c for c in registry["channels"] if c.get("status") == "active"]


def kind_coverage(registry: dict) -> dict:
    """Count active channels per kind (blind-spot signal for source diversity)."""
    cov = {}
    for c in active_channels(registry):
        k = c.get("kind", "news")
        cov[k] = cov.get(k, 0) + 1
    return cov


def should_discover_channels(registry: dict, policy: dict = None) -> bool:
    """True when active channels are too few OR too few distinct kinds are covered."""
    P = dict(DEFAULT_CHANNEL_POLICY)
    if policy:
        P.update(policy)
    act = active_channels(registry)
    if len(act) < P["min_active_channels"]:
        return True
    return len(kind_coverage(registry)) < P["min_kinds_covered"]


def missing_kinds(registry: dict) -> list:
    """Channel kinds with zero active coverage (deterministic order)."""
    covered = set(kind_coverage(registry))
    return [k for k in CHANNEL_KINDS if k not in covered]


def next_channels_to_scan(registry: dict, k: int = 3) -> list:
    """Pick up to k active channels, preferring under-covered kinds, then by id.

    Deterministic: sort by (kind coverage count asc, channel id asc) so scanning
    spreads across source types instead of hammering one feed.
    """
    cov = kind_coverage(registry)
    act = active_channels(registry)
    act_sorted = sorted(act, key=lambda c: (cov.get(c.get("kind", "news"), 0), c.get("id", "")))
    return act_sorted[:k]
