#!/usr/bin/env python3
"""SISAI B0-2 — Policy-to-Detection compiler (rule skeleton, deterministic, defensive-only).

Turns a security POLICY into a negation-aware detection rule and auto-gates it on a frozen holdout.

Boundary (honest about the gap): extracting the structured fields from a natural-language
requirement — "RBAC must be enforced" -> {control_terms:[rbac], violation_verbs:[disable,...],
intact_cues:[enforced]} — is META-LAYER COGNITION and lives OUTSIDE this file. What is deterministic,
and all this module does, is ASSEMBLE the regex skeleton from that structured spec and run it through
the backbone gate (`core/sisai_verify.verify_suite`). No NL understanding, no clock/AI/network here.

A policy spec:
    {
      "id": "POL-rbac",
      "requirement": "RBAC must be enforced",        # documentation only
      "category": "access-control-weakening",
      "control_terms":   ["rbac", "rbac check", "access control"],
      "violation_verbs": ["disable", "turn off", "bypass", "remove", "relax", "skip"],
      "bad_state_tokens":["0777"],                    # optional explicit violation tokens
      "intact_cues":     ["enforced", "required"]     # phrasing that means the policy is RESTATED, not violated
    }

compile_policy() emits, per control term, two negation-aware patterns ("verb near term" in each
order) plus one per bad-state token. Each composed pattern is `guard + .*(?:indicator)` where the
guard is a leading `(?!...)` lookahead over STANDARD_NEGATION + the policy's intact_cues, so a
restatement of the policy ("RBAC must be enforced") is NOT flagged as a violation. Patterns are
length-bounded so `compile_rule` reports skipped=0 (ReDoS length bound respected).

defensive-only: output is a detection rule + a gate report (data). Nothing is executed.

CLI:
    python tools/policy_compile.py --policy pol.json [--json]
    python tools/policy_compile.py --policy pol.json --gate [--category <cat>] [--json]
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_detect import compile_rule, scan                       # noqa: E402
from core.sisai_verify import verify_suite                             # noqa: E402

# Lean core guard set; the per-policy intact_cues carry the category-specific phrasing (keeps each
# composed pattern well under MAX_PATTERN_LEN so nothing is skipped).
STANDARD_NEGATION = ["never", "cannot", "must", "prohibited", "forbidden"]


def _lit(s: str) -> str:
    """Literal term -> regex with flexible internal whitespace (escaped; ReDoS-safe, no wildcards)."""
    words = str(s).split()
    return r"\s+".join(re.escape(w) for w in words) if words else re.escape(str(s))


def _guard(policy: dict) -> str:
    cues = STANDARD_NEGATION + list(policy.get("intact_cues", []) or [])
    body = "|".join(_lit(c) for c in cues)
    return r"(?i)^(?!.*\b(?:" + body + r")\b)"


def compile_policy(policy: dict) -> dict:
    """Deterministic: policy spec -> {policy_id, category, patterns:[{id,desc,regex}]}.
    Same spec -> byte-identical patterns (order is the spec's order)."""
    guard = _guard(policy)
    verb_alt = "|".join(_lit(v) for v in policy.get("violation_verbs", []) or [])
    pid = policy.get("id", "POL")
    patterns, n = [], 0
    for term in policy.get("control_terms", []) or []:
        t = _lit(term)
        if verb_alt:
            patterns.append({"id": f"{pid}.v{n}", "desc": f"violation verb acting on '{term}'",
                             "regex": guard + r".*(?:(?:" + verb_alt + r")\b.{0,20}\b" + t + r")"})
            n += 1
            patterns.append({"id": f"{pid}.v{n}", "desc": f"'{term}' targeted by a violation verb",
                             "regex": guard + r".*(?:" + t + r"\b.{0,20}\b(?:" + verb_alt + r"))"})
            n += 1
    for tok in policy.get("bad_state_tokens", []) or []:
        patterns.append({"id": f"{pid}.s{n}", "desc": f"explicit bad-state token '{tok}'",
                         "regex": guard + r".*(?:" + _lit(tok) + r")"})
        n += 1
    return {"policy_id": pid, "category": policy.get("category"), "patterns": patterns}


def compile_policy_set(policies: list) -> dict:
    """Merge several policies into one rule (patterns concatenated, ids stay unique by policy id)."""
    patterns = []
    cats = []
    for p in policies or []:
        r = compile_policy(p)
        patterns.extend(r["patterns"])
        if r["category"]:
            cats.append(r["category"])
    return {"category": cats[0] if len(set(cats)) == 1 else "mixed", "patterns": patterns}


def gate_policy(rule: dict, category: str, samples_path: str = None) -> dict:
    """Compile + gate a policy rule on a category's frozen holdout (reuses verify_suite). Pure."""
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    rows = [s for s in (read_json(samples_path) or []) if s.get("category") == category]
    compiled, skipped = compile_rule(rule)
    res = verify_suite(rows, lambda t: scan(t, compiled))
    return {"category": category, "gate": res.get("gate"), "skipped": skipped,
            "passed": bool(res.get("passed")) and skipped == 0, "holdout": res.get("holdout")}


# ---- Worked example policies --------------------------------------------------------------------
# A config-tampering policy set whose compiled rule PASSES that category's holdout (>=1 category
# gated pass). Plus the three card examples (compile + violation/restatement discrimination).

CONFIG_POLICY_SET = [
    {
        "id": "POL-config",
        "requirement": "Security build/CI controls must stay enabled and verified.",
        "category": "config-tampering",
        "control_terms": ["waf", "tls validation", "security gate", "certificate checks",
                          "signature verification", "vulnerability scan", "checksum validation"],
        "violation_verbs": ["disable", "turn off", "bypass", "skip", "comment out", "remove"],
        "bad_state_tokens": ["verify_ssl=false"],
        "intact_cues": ["always remain", "remain enabled", "enforced", "runs on"],
    },
]

CARD_POLICIES = {
    "rbac": {
        "id": "POL-rbac", "requirement": "RBAC must be enforced",
        "category": "access-control-weakening",
        "control_terms": ["rbac", "rbac check", "access control"],
        "violation_verbs": ["disable", "turn off", "bypass", "remove", "relax", "skip"],
        "intact_cues": ["enforced", "required"],
    },
    "lockfile": {
        "id": "POL-lockfile", "requirement": "The lockfile must never be deleted",
        "category": "supply-chain-tampering",
        "control_terms": ["lockfile", "lock file", "package-lock.json", "yarn.lock"],
        "violation_verbs": ["delete", "drop", "remove"],
        "intact_cues": ["committed", "required", "reproducible"],
    },
    "system-prompt": {
        "id": "POL-sysprompt", "requirement": "The system prompt must remain secret",
        "category": "llm-prompt-injection",
        "control_terms": ["system prompt", "hidden prompt", "initial prompt"],
        "violation_verbs": ["reveal", "print", "show", "leak", "disclose", "repeat", "dump", "exfiltrate"],
        "intact_cues": ["secret", "confidential", "remain"],
    },
}


# ---- CLI ----------------------------------------------------------------------------------------

USAGE = ("usage:\n"
         "  python tools/policy_compile.py --policy <pol.json> [--json]\n"
         "  python tools/policy_compile.py --policy <pol.json> --gate [--category <cat>] [--json]\n")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    pf = _opt(argv, "--policy")
    if not pf:
        sys.stderr.write(USAGE)
        return 2
    policy = read_json(pf)
    if not isinstance(policy, dict):
        sys.stderr.write("policy file must be a JSON object (policy spec)\n")
        return 2
    rule = compile_policy(policy)
    if "--gate" in argv:
        category = _opt(argv, "--category") or rule.get("category")
        report = gate_policy(rule, category)
        if "--json" in argv:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            h = report["holdout"] or {}
            print(f"[{category}] {'PASS' if report['passed'] else 'FAIL'} "
                  f"(gate={report['gate']}, skipped={report['skipped']}) "
                  f"recall={h.get('recall')} precision={h.get('precision')}")
        return 0 if report["passed"] else 1
    print(json.dumps(rule, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
