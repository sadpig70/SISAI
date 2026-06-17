#!/usr/bin/env python3
"""SISAI reuse ledger — "have we already handled this?" gate (stdlib only).

Records threats we have defended and defenses we have built, so the system never
re-does work it already completed. Matching is by fingerprint OR normalized title
(audit-friendly). A defense is only recorded once it is concrete (verified +
implemented) — mirrors the discipline of recording only real assets.

Determinism: pure functions; `now` injected, never read from a clock.
"""

from .sisai_fingerprint import normalize_name

SCHEMA_VERSION = "0.1"


def empty_ledger() -> dict:
    return {"schema_version": SCHEMA_VERSION, "entries": [],
            "by_fingerprint": {}, "blocked_titles": []}


def is_consumed(candidate: dict, ledger: dict) -> dict:
    """Decide whether a candidate (threat/defense) is already in the ledger.

    Returns {consumed: bool, match: {entry_id, on}|None}. `on` records which key
    matched (fingerprint|title) for the audit trail. Deterministic.
    """
    fp = candidate.get("fingerprint")
    if fp and fp in ledger.get("by_fingerprint", {}):
        return {"consumed": True, "match": {"entry_id": ledger["by_fingerprint"][fp], "on": "fingerprint"}}
    nt = normalize_name(candidate.get("title", ""))
    if nt:
        blocked = {normalize_name(t) for t in ledger.get("blocked_titles", [])}
        if nt in blocked:
            for e in ledger.get("entries", []):
                if normalize_name(e.get("title", "")) == nt:
                    return {"consumed": True, "match": {"entry_id": e.get("entry_id"), "on": "title"}}
            return {"consumed": True, "match": {"entry_id": None, "on": "title"}}
    return {"consumed": False, "match": None}


def append_entry(ledger: dict, entry: dict, now: str) -> dict:
    """Append a ledger entry. Defenses must be concrete (verified+implementations).

    Threats can be recorded as 'defended' once a defense exists. Raises ValueError on
    a defense without implementations (record only real assets). Mutates + returns.
    """
    kind = entry.get("kind")
    if kind == "defense" and not entry.get("implementations"):
        raise ValueError("append_entry: defense refused — no implementations "
                         "(record only verified/built defenses)")
    record = dict(entry)
    record.setdefault("entry_id", entry.get("entry_id") or entry.get("fingerprint"))
    record.setdefault("kind", kind or "unknown")
    record["recorded_at"] = now
    ledger.setdefault("entries", []).append(record)
    fp = record.get("fingerprint")
    if fp:
        ledger.setdefault("by_fingerprint", {})[fp] = record.get("entry_id")
    nt = normalize_name(record.get("title", ""))
    blocked = ledger.setdefault("blocked_titles", [])
    if nt and nt not in {normalize_name(t) for t in blocked}:
        blocked.append(record.get("title", ""))
    return ledger


def reindex_ledger(ledger: dict) -> dict:
    """Rebuild by_fingerprint / blocked_titles from entries[] (single source of truth)."""
    by_fp, blocked, seen = {}, [], set()
    for e in ledger.get("entries", []):
        fp = e.get("fingerprint")
        if fp:
            by_fp[fp] = e.get("entry_id")
        nt = normalize_name(e.get("title", ""))
        if nt and nt not in seen:
            seen.add(nt)
            blocked.append(e.get("title", ""))
    ledger["by_fingerprint"] = by_fp
    ledger["blocked_titles"] = blocked
    ledger.setdefault("schema_version", SCHEMA_VERSION)
    ledger.setdefault("entries", [])
    return ledger
