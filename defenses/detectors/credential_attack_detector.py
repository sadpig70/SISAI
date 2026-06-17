#!/usr/bin/env python3
"""CA-001 detector — flag credential-attack INDICATORS in ingested auth logs/text.

Pure stdlib, deterministic (no clock / network / AI / randomness). It SCANS
ingested external text (auth logs, advisories, reports) and returns a verdict
OBJECT describing whether credential-attack indicators are present. It never
executes or obeys the matched text, and it is NOT a password cracker, GAN
generator, or stuffing tool — matched content stays data, reinforcing the
deterministic boundary in docs/SELF-DEFENSE.md (data != instruction).

Usage (programmatic):
    from defenses.detectors.credential_attack_detector import load_rule, scan
    rule = load_rule()
    verdict = scan(text, rule)   # {"malicious": bool, "matched": [...], "severity": str}
"""

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_RULE = os.path.join(os.path.dirname(_HERE), "rules", "CA-001-credential-attack.json")
_SEV_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def load_rule(path: str = _DEFAULT_RULE) -> dict:
    """Load the CA-001 rule JSON and pre-compile its patterns (deterministic)."""
    with open(path, "r", encoding="utf-8") as f:
        rule = json.load(f)
    rule["_compiled"] = [(p["id"], p.get("severity", "medium"), re.compile(p["regex"]))
                         for p in rule.get("patterns", [])]
    return rule


def scan(text: str, rule: dict) -> dict:
    """Return a verdict for one piece of ingested text (advisory data, not control)."""
    matched = []
    top = None
    for pid, sev, rx in rule.get("_compiled", []):
        if rx.search(text or ""):
            matched.append({"pattern_id": pid, "severity": sev})
            if top is None or _SEV_ORDER.get(sev, 0) > _SEV_ORDER.get(top, 0):
                top = sev
    return {
        "rule_id": rule.get("rule_id", "CA-001"),
        "malicious": bool(matched),
        "matched": matched,
        "severity": top,
        "action": rule.get("action_on_match", []) if matched else [],
    }


if __name__ == "__main__":  # pragma: no cover - manual smoke use
    import sys
    r = load_rule()
    blob = sys.stdin.read() if not sys.stdin.isatty() else " ".join(sys.argv[1:])
    print(json.dumps(scan(blob, r), ensure_ascii=False, indent=2))
