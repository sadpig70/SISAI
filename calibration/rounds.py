#!/usr/bin/env python3
"""SISAI — independent-validation round freshness (deterministic, pure).

Each detector improvement must be re-validated on a FRESH independent holdout, never the frozen one
already on disk — re-submitting the same set is teaching-to-the-benchmark. These pure helpers detect
that, and `calibration/independent_eval.ingest` rejects a stale (identical) holdout re-submission.
A genuinely new round (different rows) is allowed; git history preserves the prior round.

Pure: set math over row texts; no clock/network/AI.

CLI:  python calibration/rounds.py --check <new_holdout.json> --against <existing_holdout.json>
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402


def _texts(rows):
    return {r.get("text", "") for r in (rows or []) if r.get("text")}


def is_stale(new_texts: set, prev_texts: set) -> bool:
    """True iff a prior set exists and the new set is identical to it (frozen-set re-submission)."""
    return bool(prev_texts) and set(new_texts) == set(prev_texts)


def assess(new_rows, prev_rows) -> dict:
    """Freshness of new rows vs the previously-stored round (by row text)."""
    new_t, prev_t = _texts(new_rows), _texts(prev_rows)
    overlap = new_t & prev_t
    return {
        "prev_exists": bool(prev_t),
        "identical": is_stale(new_t, prev_t),
        "overlap": len(overlap),
        "fresh": len(new_t - prev_t),
        "total_new": len(new_t),
        "overlap_pct": round(len(overlap) / len(new_t), 3) if new_t else 0.0,
    }


def _main(argv) -> int:
    new_p = prev_p = None
    for i, a in enumerate(argv):
        if a == "--check" and i + 1 < len(argv):
            new_p = argv[i + 1]
        if a == "--against" and i + 1 < len(argv):
            prev_p = argv[i + 1]
    if not (new_p and prev_p):
        sys.stderr.write("usage: python calibration/rounds.py --check <new.json> --against <existing.json>\n")
        return 2
    new = read_json(new_p) or {}
    prev = read_json(prev_p) or {}
    rep = assess(new.get("rows"), prev.get("rows"))
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 1 if rep["identical"] else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
