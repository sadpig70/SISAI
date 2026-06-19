#!/usr/bin/env python3
"""SISAI B2-4 — PharmacoVigilance triage (deterministic, defensive-only, DRAFT — most conservative).

Triages adverse-event report narratives for SERIOUS safety signals (ICH E2A / CIOMS seriousness:
death, hospitalization, life-threatening, congenital anomaly, persistent disability, serious
unexpected) to PRIORITISE human review — never to make a clinical decision. Detection-as-code over the
pure backbone; the guard vetoes non-serious / resolved / negated / expected / historical phrasing so a
recovered, non-serious, or negated event is not escalated.

Two hard invariants beyond detection (the reason this tier is the most conservative):
  1. NO autonomous clinical decision — `triage` ALWAYS returns decision="human_review_required" with
     autonomous_clinical_decision=False. The tool escalates; a qualified human decides.
  2. No feedback before verification — `can_feedback` records a signal into downstream state ONLY when
     its verification has passed AND a human has approved it (verified + human-approval gate). An
     unverified or unapproved signal is never fed back (false-alarm suppression).
Provenance is enforced and every decision yields an audit record.

GATED DOMAIN TIER — DRAFT: synthetic, abstract AE fixtures (no real patient data); production requires
clinical SME, regulatory (drug-safety) sign-off, and the highest error-cost caution (DRAFT_STATUS).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_detect import compile_rule, scan                       # noqa: E402
from core.sisai_verify import verify_suite                             # noqa: E402
from core.sisai_provenance import is_provenance_verified              # noqa: E402

CATEGORY = "pharmacovigilance"
DRAFT_STATUS = ("DRAFT / synthetic fixtures — requires clinical SME, drug-safety regulatory sign-off, "
                "and the most conservative handling; NEVER an autonomous clinical decision")

# Guard vetoes non-serious / negated / resolved / expected / historical framing.
_GUARD = (r"(?i)^(?!.*\b(?:no|not|without|none|denied|resolved|mild|transient|non-serious|expected|"
          r"recovered|recovery|historical|per\s+the\s+label)\b)")

SIGNAL_BUNDLE = {
    "guard": _GUARD,
    "indicators": [
        {"id": "pv.death", "desc": "fatal outcome", "regex": r"\b(?:died|death|fatal|deceased)\b"},
        {"id": "pv.hospitalization", "desc": "hospitalization / prolonged hospitalization",
         "regex": r"\bhospitali[sz]ed\b|\bhospitali[sz]ation\b"},
        {"id": "pv.life-threatening", "desc": "life-threatening event",
         "regex": r"\blife-?threatening\b"},
        {"id": "pv.congenital", "desc": "congenital anomaly / birth defect",
         "regex": r"\bcongenital\s+anomal\w*|\bbirth\s+defect\b"},
        {"id": "pv.disability", "desc": "persistent / significant disability",
         "regex": r"\bpermanent\s+disabilit\w*|\bdisabling\b|\bincapacit\w*"},
        {"id": "pv.serious-unexpected", "desc": "serious unexpected reaction",
         "regex": r"\bunexpected\b.{0,15}\bserious\b|\bserious\b.{0,15}\bunexpected\b"},
    ],
}


def _patterns():
    g = SIGNAL_BUNDLE["guard"]
    return [{"id": ind["id"], "desc": ind["desc"], "regex": g + r".*(?:" + ind["regex"] + r")"}
            for ind in SIGNAL_BUNDLE["indicators"]]


def compile_bundle():
    pats = _patterns()
    compiled, skipped = compile_rule({"patterns": pats})
    return compiled, skipped, pats


def predict():
    compiled, _, _ = compile_bundle()
    return lambda text: scan(text, compiled)


def detect(text: str) -> dict:
    matches = []
    for ind in SIGNAL_BUNDLE["indicators"]:
        compiled, _ = compile_rule({"patterns": [{"id": ind["id"],
                                    "regex": SIGNAL_BUNDLE["guard"] + r".*(?:" + ind["regex"] + r")"}]})
        if compiled and scan(text, compiled):
            matches.append({"id": ind["id"], "desc": ind["desc"]})
    return {"serious_signal": bool(matches), "signals": matches}


def triage(report_text: str, provenance: dict = None) -> dict:
    """Triage one AE report. ALWAYS routes to a human — never an autonomous clinical decision."""
    sig = detect(report_text if isinstance(report_text, str) else "")
    if provenance is None:
        prov = "absent"
    else:
        prov = "verified" if is_provenance_verified({"provenance": provenance}) else "unverified"
    return {
        "serious_signal": sig["serious_signal"],
        "signals": sig["signals"],
        "provenance": prov,
        "escalate": sig["serious_signal"],                 # to a human reviewer
        "decision": "human_review_required",               # INVARIANT — never decides clinically
        "autonomous_clinical_decision": False,             # INVARIANT
        "audit": {"signal_ids": [m["id"] for m in sig["signals"]], "provenance": prov},
        "draft_status": DRAFT_STATUS,
    }


def can_feedback(signal_record: dict) -> bool:
    """No feedback before verification AND human approval. A signal is recorded downstream ONLY when its
    verification passed AND a human approved it — unverified/unapproved signals are never fed back."""
    rec = signal_record or {}
    verified = bool((rec.get("verification") or {}).get("passed"))
    return verified and bool(rec.get("human_approved"))


def _holdout(samples_path=None):
    samples_path = samples_path or os.path.join(ROOT, "seed", "sample-suite.json")
    return [s for s in (read_json(samples_path) or []) if s.get("category") == CATEGORY]


def gate(samples_path=None) -> dict:
    compiled, skipped, _ = compile_bundle()
    r = verify_suite(_holdout(samples_path), lambda t: scan(t, compiled))
    return {"gate": r.get("gate"), "skipped": skipped,
            "passed": bool(r.get("passed")) and skipped == 0, "holdout": r.get("holdout")}


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
        sys.stderr.write("usage: python domain/pharmacovigilance.py --text \"<AE report>\" | --gate\n")
        return 2
    print(json.dumps(triage(text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
