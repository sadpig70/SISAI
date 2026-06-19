#!/usr/bin/env python3
"""SISAI B2-3 — Trust & Safety moderation eval (deterministic, defensive-only, DRAFT).

Treats policy-violation typologies (threats/violence, harassment, self-harm encouragement, hate
against protected classes, doxxing, spam/scam, coordinated brigading) as threats and a moderation
classifier as the defense, then EVALUATES it with two safeguards specific to moderation:

  1. hard-negative precision — the holdout's benign rows are the classic moderation false-positive
     traps: satire/parody, quotation/reporting, negation/counter-speech, educational/definitional, and
     moderation-action reports. The negation-aware guard vetoes that framing so counter-speech and
     reporting are not mistaken for the violation they mention.
  2. judge != author (cross-model role disjointness) — `eval_moderation` REFUSES to score unless the
     committed role registry has author != holdout_curator and author != judge for the suite
     (`core/sisai_verify.roles_disjoint`). This structurally controls judge self-enhancement bias: a
     model cannot grade rules it authored.

GATED DOMAIN TIER — DRAFT: the fixtures are SYNTHETIC, abstract policy-violation descriptions (no
slurs, no real PII); production needs a real policy corpus, labeling, cultural/linguistic diversity,
and T&S SME review (surfaced as DRAFT_STATUS). Reuses the pure backbone; no clock/AI/network.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_detect import compile_rule, scan                       # noqa: E402
from core.sisai_verify import verify_suite, index_role_registry, roles_disjoint  # noqa: E402

CATEGORY = "trust-safety"
SUITE = "trust-safety"
DRAFT_STATUS = ("DRAFT / synthetic fixtures — requires a real policy corpus, labeling, cultural/"
                "linguistic diversity, and T&S SME review before any operational use")

# Guard vetoes the classic moderation false-positive framings.
_GUARD = (r"(?i)^(?!.*\b(?:satir\w*|parody|mock\w*|quote\w*|quoting|article|report\w*|never|explain\w*|"
          r"means|definition|defines?|removed|remove|fictional|allegedly|counter-speech|offer\s+(?:support|help))\b)")

MODERATION_BUNDLE = {
    "guard": _GUARD,
    "indicators": [
        {"id": "ts.threat", "desc": "direct threat of violence/harm",
         "regex": r"\bthreat\s+to\s+(?:harm|hurt|kill|attack)\b|\b(?:post|make|send)\b.{0,20}\b(?:direct\s+)?threat\b.{0,15}\b(?:harm|hurt|kill)\b"},
        {"id": "ts.harassment", "desc": "targeted/repeated harassment",
         "regex": r"\brepeated(?:ly)?\b.{0,20}\bdemean\w*|\b(?:send|post)\b.{0,20}\bdemeaning\b"},
        {"id": "ts.self-harm", "desc": "encouraging self-harm",
         "regex": r"\bencourage\b.{0,20}\b(?:hurt|harm)\b.{0,15}\b(?:them|him|her|your)sel\w*"},
        {"id": "ts.hate", "desc": "demeaning a protected class",
         "regex": r"\b(?:demean|dehumanize|attack)\w*\b.{0,25}\b(?:because\s+of|for)\b.{0,20}\b(?:religion|race|ethnic\w*|gender|sex\w*\s+orientation|nationality)\b"},
        {"id": "ts.doxxing", "desc": "doxxing — publishing private info",
         "regex": r"\b(?:publish|post|leak|expose)\b.{0,25}\b(?:home\s+address|private\s+address|phone\s+number|personal\s+(?:info|details))\b"},
        {"id": "ts.spam", "desc": "spam / scam link distribution",
         "regex": r"\bmass-?dm\b|\b(?:spam|blast|mass)\b.{0,20}\b(?:phishing|scam|link)\b"},
        {"id": "ts.brigading", "desc": "coordinated harassment / brigading",
         "regex": r"\b(?:coordinate|organize|rally)\b.{0,20}\b(?:brigade|raid|flood|pile-?on)\b"},
    ],
}


def _patterns():
    g = MODERATION_BUNDLE["guard"]
    return [{"id": ind["id"], "desc": ind["desc"], "regex": g + r".*(?:" + ind["regex"] + r")"}
            for ind in MODERATION_BUNDLE["indicators"]]


def compile_bundle():
    pats = _patterns()
    compiled, skipped = compile_rule({"patterns": pats})
    return compiled, skipped, pats


def predict():
    compiled, _, _ = compile_bundle()
    return lambda text: scan(text, compiled)


def detect(text: str) -> dict:
    matches = []
    for ind in MODERATION_BUNDLE["indicators"]:
        compiled, _ = compile_rule({"patterns": [{"id": ind["id"],
                                    "regex": MODERATION_BUNDLE["guard"] + r".*(?:" + ind["regex"] + r")"}]})
        if compiled and scan(text, compiled):
            matches.append({"id": ind["id"], "desc": ind["desc"]})
    return {"flagged": bool(matches), "matches": matches, "draft_status": DRAFT_STATUS}


def _holdout(samples_path=None):
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    return [s for s in (read_json(samples_path) or []) if s.get("category") == CATEGORY]


def gate(samples_path=None) -> dict:
    compiled, skipped, _ = compile_bundle()
    r = verify_suite(_holdout(samples_path), lambda t: scan(t, compiled))
    return {"gate": r.get("gate"), "skipped": skipped,
            "passed": bool(r.get("passed")) and skipped == 0, "holdout": r.get("holdout")}


def eval_moderation(suite=SUITE, registry=None, samples_path=None, registry_path=None) -> dict:
    """Evaluate the moderation rule — but ONLY if judge != author (cross-model role disjointness).

    Self-enhancement bias control: a model may not grade rules it authored. If the committed role
    registry does not make the suite's roles disjoint (author != curator, author != judge), the eval
    REFUSES to score (`valid=False`). Otherwise it gates the bundle on the frozen holdout."""
    if registry is None:
        registry = read_json(registry_path or os.path.join(ROOT, "seed", "role-registry.json")) or {}
    rd = roles_disjoint(suite, index_role_registry(registry))
    if not rd["ok"]:
        return {"valid": False, "reason": "roles not disjoint — judge/author overlap risks "
                "self-enhancement bias; refusing to score", "roles": rd, "draft_status": DRAFT_STATUS}
    return {"valid": True, "roles": rd, "gate": gate(samples_path), "draft_status": DRAFT_STATUS}


# ---- CLI ----------------------------------------------------------------------------------------

def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    if "--eval" in argv:
        print(json.dumps(eval_moderation(), ensure_ascii=False, indent=2))
        return 0
    if "--gate" in argv:
        print(json.dumps(gate(), ensure_ascii=False, indent=2))
        return 0
    text = _opt(argv, "--text")
    if text is None:
        sys.stderr.write("usage: python domain/trust_safety.py --text \"<content>\" | --gate | --eval\n")
        return 2
    v = detect(text)
    print(json.dumps(v, ensure_ascii=False, indent=2))
    return 1 if v["flagged"] else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
