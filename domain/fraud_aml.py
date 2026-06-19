#!/usr/bin/env python3
"""SISAI B2-2 — Fraud / AML detection suite (detection-as-code, deterministic, defensive-only, DRAFT).

Treats well-known fraud/AML typologies (structuring, layering via shells, money mules, APP "safe
account" fraud, trade-based ML over-invoicing, crypto mixing, chargeback fraud) as threats, and ships a
NEGATION-AWARE detection bundle as the defense, graded on a frozen holdout with false-positives
controlled. Reuses the pure backbone (`core/sisai_detect.compile_rule` + `scan`,
`core/sisai_verify.verify_suite`) — same gate the loop trusts.

GATED DOMAIN TIER — DRAFT: the fixtures in seed/sample-suite.json are SYNTHETIC typology descriptions
(published FATF/FinCEN-level red flags), NOT real transactions. Production requires real labeled
financial data (PII/regulated), AML/fraud SME review, and operational integration. `DRAFT_STATUS`
surfaces this; no claim of production accuracy is made.

The guard vetoes legitimate-activity and AML-control phrasing ("reported as required", "prohibited and
flagged", "blocked by ... compliance policy") so a control statement is not mistaken for wrongdoing.

`accept_candidate` is the regression gate: a changed rule is adopted only if it does not lose recall
or drop precision below the floor / the baseline (no-regress, mirroring the adversarial loop).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_detect import compile_rule, scan                       # noqa: E402
from core.sisai_verify import verify_suite, metrics, PRECISION_FLOOR   # noqa: E402

CATEGORY = "fraud-aml"
DRAFT_STATUS = ("DRAFT / synthetic fixtures — requires real labeled financial data, AML/fraud SME "
                "review, and regulatory sign-off before any operational use")

_GUARD = (r"(?i)^(?!.*\b(?:required|reported|prohibited|flagged|monitoring|matches|blocked|compliance|"
          r"policy|legitimate|verified|never|approved|reconciled)\b)")

FRAUD_AML_BUNDLE = {
    "guard": _GUARD,
    "indicators": [
        {"id": "aml.structuring", "desc": "structuring/smurfing below the reporting threshold",
         "regex": r"\b(?:break|split|structure)\b.{0,30}\b(?:deposit|amount|transaction)s?\b.{0,30}\b(?:under|below|beneath)\b.{0,20}\b(?:threshold|reporting|10[,.]?000)\b"},
        {"id": "aml.layering", "desc": "layering through shell companies / nominees",
         "regex": r"\b(?:route|funnel|move|layer)\b.{0,30}\b(?:shell\s+compan\w+|nominee\w*)\b"},
        {"id": "aml.mule", "desc": "money mules — accounts in other people's names",
         "regex": r"\b(?:open|use)\b.{0,30}\baccounts?\b.{0,30}\b(?:other\s+people|someone\s+else|other'?s)\b|\bmoney\s+mule\b"},
        {"id": "aml.app-safe-account", "desc": "APP fraud — transfer to a controlled 'safe account'",
         "regex": r"\btransfer\b.{0,30}\bsafe\s+account\b"},
        {"id": "aml.tbml", "desc": "trade-based ML — mis-invoicing",
         "regex": r"\bover-?invoic\w*|\bunder-?invoic\w*"},
        {"id": "aml.mixing", "desc": "crypto mixing / tumbling",
         "regex": r"\b(?:run|pass|send)\b.{0,20}\bmixer\b|\b(?:through|via)\s+(?:a\s+)?mixer\b|\b(?:tumbler|coin\s+mixer)\b"},
        {"id": "aml.chargeback", "desc": "first-party / friendly chargeback fraud",
         "regex": r"\bfalse\s+chargeback\w*|\bfraudulent\s+chargeback\w*"},
    ],
}


def _patterns():
    g = FRAUD_AML_BUNDLE["guard"]
    return [{"id": ind["id"], "desc": ind["desc"], "regex": g + r".*(?:" + ind["regex"] + r")"}
            for ind in FRAUD_AML_BUNDLE["indicators"]]


def compile_bundle():
    """Compile the fraud/AML bundle. Returns (compiled, skipped, patterns_meta). skipped=0 expected."""
    pats = _patterns()
    compiled, skipped = compile_rule({"patterns": pats})
    return compiled, skipped, pats


def predict():
    compiled, _, _ = compile_bundle()
    return lambda text: scan(text, compiled)


def detect(text: str) -> dict:
    """Verdict (data only) for one transaction narrative / memo / customer message."""
    matches = []
    for ind in FRAUD_AML_BUNDLE["indicators"]:
        compiled, _ = compile_rule({"patterns": [{"id": ind["id"],
                                    "regex": FRAUD_AML_BUNDLE["guard"] + r".*(?:" + ind["regex"] + r")"}]})
        if compiled and scan(text, compiled):
            matches.append({"id": ind["id"], "desc": ind["desc"]})
    return {"flagged": bool(matches), "matches": matches, "draft_status": DRAFT_STATUS}


def _holdout(samples_path=None):
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    return [s for s in (read_json(samples_path) or []) if s.get("category") == CATEGORY]


def gate(samples_path=None) -> dict:
    """Grade the shipped bundle on the frozen fraud-aml holdout (verify_suite)."""
    compiled, skipped, _ = compile_bundle()
    r = verify_suite(_holdout(samples_path), lambda t: scan(t, compiled))
    return {"gate": r.get("gate"), "skipped": skipped,
            "passed": bool(r.get("passed")) and skipped == 0, "holdout": r.get("holdout")}


def accept_candidate(base_rule: dict, candidate_rule: dict, samples_path=None) -> dict:
    """Regression gate: adopt `candidate` over `base` only if it keeps recall and holds precision at
    >= max(floor, base precision), with no ReDoS skips. Pure."""
    hold = _holdout(samples_path)
    bc, _ = compile_rule(base_rule)
    cc, cskip = compile_rule(candidate_rule)
    bm = metrics(lambda t: scan(t, bc), hold)
    cm = metrics(lambda t: scan(t, cc), hold)
    floor = max(PRECISION_FLOOR, bm["precision"])
    accept = cskip == 0 and cm["recall"] >= bm["recall"] and cm["precision"] >= floor
    reason = ("ok" if accept else
              "ReDoS skip" if cskip else
              "recall regressed" if cm["recall"] < bm["recall"] else
              "precision below floor/baseline")
    return {"accept": accept, "reason": reason,
            "base": {"recall": bm["recall"], "precision": bm["precision"]},
            "candidate": {"recall": cm["recall"], "precision": cm["precision"], "skipped": cskip}}


# ---- CLI ----------------------------------------------------------------------------------------

def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    if "--gate" in argv:
        print(json.dumps(gate(), ensure_ascii=False, indent=2))
        return 0
    text = _opt(argv, "--text")
    if text is None:
        sys.stderr.write("usage: python domain/fraud_aml.py --text \"<narrative>\" | --gate\n")
        return 2
    print(json.dumps(detect(text), ensure_ascii=False, indent=2))
    return 1 if detect(text)["flagged"] else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
