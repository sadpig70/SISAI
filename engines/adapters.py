#!/usr/bin/env python3
"""SISAI strand adapters — native artifacts -> backbone shapes (pure, stdlib).

Deterministic transforms over already-parsed dicts (loading lives in the driver).
No clock/network/AI here. `now` is injected where an identity/timestamp is needed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sisai_channels import empty_registry, register_channel        # noqa: E402
from core.sisai_fingerprint import threat_fingerprint, defense_fingerprint  # noqa: E402


def channels_seed_to_registry(seed, now: str) -> dict:
    """List of raw channels -> deduped channel registry (reuse backbone)."""
    reg = empty_registry()
    for ch in seed or []:
        register_channel(reg, ch, now=now)
    return reg


def threats_seed_to_list(seed) -> list:
    """Raw threats -> normalized threat list with stable ids + fingerprints."""
    out = []
    for t in (seed or {}).get("threats", []) if isinstance(seed, dict) else (seed or []):
        rec = dict(t)
        rec["threat_id"] = t.get("threat_id") or f"THR-{threat_fingerprint(t)[:8]}"
        rec["fingerprint"] = threat_fingerprint(t)
        rec.setdefault("category", "uncategorized")
        rec.setdefault("techniques", [])
        out.append(rec)
    return out


def defenses_seed_to_corpus(seed) -> list:
    """Raw defenses -> defense corpus with stable ids + fingerprints (for matching)."""
    out = []
    for d in (seed or {}).get("defenses", []) if isinstance(seed, dict) else (seed or []):
        rec = dict(d)
        rec["defense_id"] = d.get("defense_id") or f"DEF-{defense_fingerprint(d)[:8]}"
        rec["fingerprint"] = defense_fingerprint(d)
        out.append(rec)
    return out
