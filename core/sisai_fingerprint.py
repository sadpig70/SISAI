#!/usr/bin/env python3
"""SISAI identity primitives — deterministic fingerprints for channels/threats/defenses.

Pure stdlib, no clock/network/AI. Fingerprints let the ledger and channel registry
decide "have we already seen this?" so channels, threats and defenses are recorded
once and reused — the reuse backbone the system is built on.
"""

import hashlib
import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_TOKEN = re.compile(r"[a-z0-9]+")


def normalize_name(s: str) -> str:
    """Lowercase, strip all non-alphanumerics. Deterministic."""
    return _NON_ALNUM.sub("", (s or "").lower())


def tokenize_name(s: str) -> list:
    """Lowercase alphanumeric tokens (deterministic order: as they appear)."""
    return _TOKEN.findall((s or "").lower())


def _digest(parts) -> str:
    """Stable short sha256 over sorted, normalized parts (order-independent)."""
    norm = sorted(normalize_name(p) for p in parts if p)
    if not norm:
        return ""
    return hashlib.sha256("|".join(norm).encode("utf-8")).hexdigest()[:16]


def channel_fingerprint(channel: dict) -> str:
    """Identity of an information source: normalized url + kind (dedup key)."""
    url = (channel.get("url") or "").lower().rstrip("/")
    return _digest([url, channel.get("kind", "")])


def threat_fingerprint(threat: dict) -> str:
    """Identity of a threat: title + category + cve (so re-collected threats dedup)."""
    return _digest([threat.get("title", ""), threat.get("category", ""),
                    threat.get("cve") or ""])


def defense_fingerprint(defense: dict) -> str:
    """Identity of a defense: title + sorted controls (so duplicate defenses fold)."""
    controls = defense.get("controls", []) or []
    return _digest([defense.get("title", "")] + list(controls))
