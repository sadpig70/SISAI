#!/usr/bin/env python3
"""SISAI B0-3 — Control-Drift Monitor (CLI, deterministic, defensive-only).

Detects security controls being WEAKENED over time in config/IaC diffs (WAF off, TLS off, scan
bypass, public exposure, RBAC relaxed, lockfile dropped, ...) and accumulates a deterministic
drift trend — WITHOUT ever trusting the diff to self-certify.

Pipeline (composition, no new trust logic):
  1. diff_to_drift_threats() — run the B0-1 detector (`tools/detect_pr`) over the ADDED lines of a
     diff; each weakening directive becomes a drift threat candidate (marked `control-drift`).
     The candidate carries SELF-CLAIMED provenance on purpose — to prove it can't pass the gate.
  2. monitor_drift() — route candidates through `sisai.ingest_threats(..., quarantine_path=...)`:
     the gate STRIPS source-claimed provenance (anti fail-open), overlays the isolated fetcher's
     ground truth (injected via --fetch-provenance, host-derived authority + sha256), and routes
     verified->threats, unverified->quarantine. No fetcher truth => everything quarantines (0 pass).
     fp-dedup means re-ingesting the same drift accepts/quarantines it only once.
  3. drift_trend() — a pure, deterministic time-series count of ACCEPTED drift events.

defensive-only: output is detection/quarantine/trend data. The diff text is DATA — it is scanned,
never executed, and never elevated to an instruction.

CLI:
    python tools/control_drift.py --diff change.patch --source-url https://github.com/o/r/commit/x \
        [--fetch-provenance prov.json] [--threats .sisai/drift-threats.json] \
        [--quarantine .sisai/drift-quarantine.json] [--ledger .sisai/drift-ledger.json] [--now D] [--json]
    python tools/control_drift.py --trend --threats .sisai/drift-threats.json [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from sisai import ingest_threats, _threats_as_list                     # noqa: E402
from tools.detect_pr import detect                                     # noqa: E402

DRIFT_MARKER = "control-drift"
# self-claimed provenance the diff/page asserts about itself — schema-valid but the gate strips it
_SELF_CLAIM = {"authority": "GHSA", "source_sha256": "a" * 64, "verified": True}


def _added_lines(diff_text: str) -> list:
    """The lines that a diff INTRODUCES. If the text looks like a unified diff, take '+' adds only
    (skip the '+++' header); otherwise treat every non-empty line as introduced. Pure."""
    text = diff_text if isinstance(diff_text, str) else ""
    lines = text.splitlines()
    looks_diff = any(ln.startswith(("@@", "+++", "---", "diff --git")) for ln in lines)
    out = []
    for ln in lines:
        if looks_diff:
            if ln.startswith("+") and not ln.startswith("+++"):
                cand = ln[1:].strip()
            else:
                continue
        else:
            cand = ln.strip()
        if cand:
            out.append(cand)
    return out


def diff_to_drift_threats(diff_text: str, now: str, source_url: str = None) -> list:
    """Each weakening directive in the diff's added lines -> one drift threat candidate per
    (line, category). Deterministic order. Provenance is SELF-CLAIMED (gate will strip it)."""
    claim = dict(_SELF_CLAIM)
    if source_url:
        claim["source_url"] = source_url
    claim["verified_on"] = now
    out = []
    for line in _added_lines(diff_text):
        verdict = detect(line)
        if not verdict["flagged"]:
            continue
        by_cat = {}
        for m in verdict["matches"]:
            by_cat.setdefault(m["category"], []).append(m["id"])
        for cat in sorted(by_cat):
            out.append({
                "title": f"control drift [{cat}]: {line}",
                "category": cat,
                "techniques": [DRIFT_MARKER] + sorted(by_cat[cat]),
                "recency": now,
                "evidence": [line],
                "provenance": dict(claim),
            })
    return out


def monitor_drift(diff_text: str, threats_path: str, ledger_path: str, quarantine_path: str,
                  now: str, source_url: str = None, fetch_provenance=None) -> dict:
    """Detect drift in a diff and route it through the provenance gate. seed_threats=None so no
    seed bleed; quarantine_path set so the gate is active (unverified -> quarantine)."""
    candidates = diff_to_drift_threats(diff_text, now, source_url=source_url)
    res = ingest_threats(candidates, threats_path, ledger_path, now, seed_threats=None,
                         quarantine_path=quarantine_path, fetch_provenance=fetch_provenance)
    res["detected"] = len(candidates)
    return res


def is_drift(threat: dict) -> bool:
    return DRIFT_MARKER in (threat or {}).get("techniques", [])


def drift_trend(threats_path: str) -> dict:
    """Deterministic time-series of ACCEPTED drift events: totals by category and by date.
    Pure function of the stored threats (same input -> byte-identical output)."""
    threats = [t for t in _threats_as_list(read_json(threats_path)) if is_drift(t)]
    by_category, by_date = {}, {}
    for t in threats:
        by_category[t.get("category", "uncategorized")] = by_category.get(t.get("category", "uncategorized"), 0) + 1
        d = t.get("recency") or "unknown"
        by_date[d] = by_date.get(d, 0) + 1
    return {"total": len(threats),
            "by_category": dict(sorted(by_category.items())),
            "by_date": dict(sorted(by_date.items()))}


# ---- CLI ----------------------------------------------------------------------------------------

USAGE = ("usage:\n"
         "  python tools/control_drift.py --diff <file> [--source-url URL] [--fetch-provenance F]\n"
         "      [--threats P] [--quarantine P] [--ledger P] [--now YYYY-MM-DD] [--json]\n"
         "  python tools/control_drift.py --trend --threats P [--json]\n")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _now(argv):
    n = _opt(argv, "--now")
    if n:
        return n
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def _main(argv) -> int:
    threats_path = _opt(argv, "--threats") or os.path.join(ROOT, ".sisai", "drift-threats.json")

    if "--trend" in argv:
        out = drift_trend(threats_path)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    diff_file = _opt(argv, "--diff")
    if not diff_file:
        sys.stderr.write(USAGE)
        return 2
    with open(diff_file, encoding="utf-8") as f:
        diff_text = f.read()
    ledger_path = _opt(argv, "--ledger") or os.path.join(ROOT, ".sisai", "drift-ledger.json")
    quarantine_path = _opt(argv, "--quarantine") or os.path.join(ROOT, ".sisai", "drift-quarantine.json")
    fp_file = _opt(argv, "--fetch-provenance")
    fetch_prov = _threats_as_list(read_json(fp_file)) if fp_file else None
    res = monitor_drift(diff_text, threats_path, ledger_path, quarantine_path, _now(argv),
                        source_url=_opt(argv, "--source-url"), fetch_provenance=fetch_prov)
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"detected={res['detected']} accepted={len(res['accepted'])} "
              f"quarantined={res['quarantined_count']} total_threats={res['total_threats']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
