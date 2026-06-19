#!/usr/bin/env python3
"""B0-6 Education Lab — grade a student detection rule against a FROZEN holdout (deterministic).

The lesson: a rule that scores well on samples you can see (the OPEN `tune` split) often breaks on
the hard negatives you can't (the FROZEN `holdout` split) — "Never disable TLS" must NOT be flagged
even though it contains "disable". Students iterate on tune; the grade is the holdout.

Reuses the backbone verbatim — `core/sisai_detect.compile_rule` + `core/sisai_verify.verify_suite` —
so a passing student rule is graded by the exact same gate the SISAI loop uses. No new detection
logic, no execution of any input: rules are regex patterns over text (data), defensive-only.

A rule file is the same shape the backbone consumes: {"patterns": [{"id","regex","desc"?}, ...]}.

CLI:
    python labs/defense_rule_lab/grade_rule.py --rule my_rule.json --category config-tampering
    python labs/defense_rule_lab/grade_rule.py --rule my_rule.json --category config-tampering --reveal --json
Exit code: 0 if the rule PASSES the holdout gate, else 1 (2 on usage error).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_detect import compile_rule, scan                       # noqa: E402
from core.sisai_verify import verify_suite, metrics, split_of          # noqa: E402

SEED = os.path.join(ROOT, "seed")
CATEGORIES = ("config-tampering", "supply-chain-tampering", "access-control-weakening")


def load_samples(category: str) -> list:
    """The committed lab corpus for a category (tune is open feedback; holdout is the frozen grade)."""
    rows = read_json(os.path.join(SEED, "sample-suite.json")) or []
    return [s for s in rows if s.get("category") == category]


def _wrong(samples, predict, split, want_flagged: bool) -> list:
    """Texts in `split` whose prediction != expectation (misses if want_flagged, else false positives)."""
    out = []
    for s in samples:
        if split_of(s) != split:
            continue
        is_mal = s.get("label") == "malicious"
        if is_mal != want_flagged:
            continue
        if bool(predict(s.get("text", ""))) != want_flagged:
            out.append(s.get("text", ""))
    return out


def grade(rule: dict, category: str, reveal: bool = False) -> dict:
    """Compile + grade a student rule on a category's frozen holdout. Pure (no clock/AI/network).

    Returns a report: ReDoS-skip count, open tune metrics, the holdout grade, a degenerate flag,
    the gate verdict, and human-readable reasons. With `reveal`, includes the offending holdout
    texts (default: counts only, to respect the frozen benchmark)."""
    compiled, skipped = compile_rule(rule)
    samples = load_samples(category)
    predict = lambda t: scan(t, compiled)
    res = verify_suite(samples, predict)
    hold = [s for s in samples if split_of(s) == "holdout"]
    hm = metrics(predict, hold) if hold else {}
    degenerate = bool(hm) and (hm["tp"] == 0 or hm["tn"] == 0)   # flags nothing, or flags everything

    reasons = []
    if skipped:
        reasons.append(f"{skipped} pattern(s) refused (over-length / uncompilable — ReDoS length bound)")
    if hm:
        if hm["recall"] < 1.0:
            reasons.append(f"recall {hm['recall']} < 1.0 — missed {hm['fn']} malicious directive(s)")
        if hm["precision"] < 0.85:
            reasons.append(f"precision {hm['precision']} < 0.85 — {hm['fp']} false positive(s) on hard negatives")
        if degenerate:
            reasons.append("degenerate — flags nothing" if hm["tp"] == 0 else "degenerate — flags everything")

    passed = bool(res.get("passed")) and skipped == 0 and not degenerate
    report = {
        "category": category,
        "verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "gate": res.get("gate"),
        "skipped": skipped,
        "degenerate": degenerate,
        "tune": metrics(predict, [s for s in samples if split_of(s) == "tune"]),
        "holdout": hm,
        "reasons": reasons or (["meets the gate: recall 1.0, precision >= 0.85, no skips"] if passed else []),
        "feedback": {
            "tune_false_positives": _wrong(samples, predict, "tune", False),
            "tune_misses": _wrong(samples, predict, "tune", True),
        },
    }
    if reveal:
        report["feedback"]["holdout_false_positives"] = _wrong(samples, predict, "holdout", False)
        report["feedback"]["holdout_misses"] = _wrong(samples, predict, "holdout", True)
    else:
        report["feedback"]["holdout_false_positives_count"] = hm.get("fp", 0) if hm else 0
        report["feedback"]["holdout_misses_count"] = hm.get("fn", 0) if hm else 0
    return report


# ---- CLI ----------------------------------------------------------------------------------------

USAGE = ("usage:\n"
         "  python labs/defense_rule_lab/grade_rule.py --rule <rule.json> --category <cat> [--reveal] [--json]\n"
         f"  categories: {', '.join(CATEGORIES)}\n")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    rule_path, cat = _opt(argv, "--rule"), _opt(argv, "--category")
    if not (rule_path and cat):
        sys.stderr.write(USAGE)
        return 2
    if cat not in CATEGORIES:
        sys.stderr.write(f"unknown category: {cat}\n{USAGE}")
        return 2
    rule = read_json(rule_path)
    if not isinstance(rule, dict) or "patterns" not in rule:
        sys.stderr.write("rule file must be a JSON object with a 'patterns' list\n")
        return 2
    report = grade(rule, cat, reveal="--reveal" in argv)
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"[{report['category']}] {report['verdict']}  (gate={report['gate']})")
        h = report["holdout"]
        if h:
            print(f"  holdout: recall={h['recall']} precision={h['precision']} "
                  f"tp={h['tp']} fp={h['fp']} tn={h['tn']} fn={h['fn']}")
        for r in report["reasons"]:
            print(f"  - {r}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
