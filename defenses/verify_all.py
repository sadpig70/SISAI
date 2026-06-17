#!/usr/bin/env python3
"""Aggregate verifier — run every defenses/verify_*.py suite and summarize.

One command for the whole defense layer: per-suite precision/recall + FP/FN, plus
an overall pass. A suite passes its own gate (recall==1.0 & precision>=0.85) and
prints a JSON metrics object; this runner collects them into a regression summary.

    python defenses/verify_all.py            # human + JSON summary, exit 0 iff all pass

Pure stdlib (glob/subprocess/json). Deterministic given the suites + samples.
"""

import glob
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def discover_suites() -> list:
    """All verify_*.py under defenses/, excluding this aggregate runner. Sorted."""
    here = os.path.basename(__file__)
    return sorted(p for p in glob.glob(os.path.join(_HERE, "verify_*.py"))
                  if os.path.basename(p) != here)


def run_suite(path: str) -> dict:
    """Run one suite, parse its JSON metrics. Returns a normalized record."""
    name = os.path.basename(path)[len("verify_"):-len(".py")]
    proc = subprocess.run([sys.executable, path], capture_output=True, text=True)
    try:
        m = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"suite": name, "passed": False, "error": "unparseable output",
                "exit": proc.returncode, "stderr": (proc.stderr or "")[-300:]}
    return {
        "suite": name,
        "passed": bool(m.get("passed")) and proc.returncode == 0,
        "recall": m.get("recall"), "precision": m.get("precision"),
        "fp": m.get("fp"), "fn": m.get("fn"), "samples": m.get("samples"),
        "errors": m.get("errors", []),
        "exit": proc.returncode,
    }


def verify_all() -> dict:
    suites = [run_suite(p) for p in discover_suites()]
    precs = [s["precision"] for s in suites if isinstance(s.get("precision"), (int, float))]
    return {
        "passed": bool(suites) and all(s["passed"] for s in suites),
        "suite_count": len(suites),
        "min_precision": min(precs) if precs else None,
        "total_fp": sum(s.get("fp") or 0 for s in suites),
        "total_fn": sum(s.get("fn") or 0 for s in suites),
        "suites": suites,
    }


if __name__ == "__main__":
    summary = verify_all()
    for s in summary["suites"]:
        flag = "PASS" if s["passed"] else "FAIL"
        print(f"[{flag}] {s['suite']:20} recall={s.get('recall')} "
              f"precision={s.get('precision')} fp={s.get('fp')} fn={s.get('fn')}")
    print(f"\n{summary['suite_count']} suites | min_precision={summary['min_precision']} "
          f"| total_fp={summary['total_fp']} total_fn={summary['total_fn']} | "
          f"overall={'PASS' if summary['passed'] else 'FAIL'}")
    print(json.dumps(summary, ensure_ascii=False))
    sys.exit(0 if summary["passed"] else 1)
