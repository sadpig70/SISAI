#!/usr/bin/env python3
"""SISAI B1-1 — AI Gateway prompt-shield middleware (deterministic, defensive-only).

A reference middleware that sits in front of an LLM gateway. It scans inputs / retrieved documents /
tool outputs for prompt-injection, jailbreak, and policy-override directives, and applies the
provenance gate so unverified external sources are isolated. Its FIRST-LINE guarantee is the
deterministic boundary (docs/SELF-DEFENSE.md): collected external text is DATA — it is scanned, never
executed, and never elevated to an instruction. Every verdict therefore carries `treat_as: "data"`.

Detection is a NEGATION-AWARE injection bundle over the pure backbone primitives
(`core/sisai_detect.compile_rule` + `scan`): a shared guard (`^(?!...)` lookahead) vetoes DEFENSIVE
framing — third-person descriptions ("the attacker tried to make the model ignore..."), policy
statements ("never reveal the system prompt"), quoted detection examples — so a defensive citation is
not mistaken for an attack. Provenance is gated by `core/sisai_provenance` exactly as the ingest path:
source-claimed provenance is stripped, only host-derived authority + sha256 counts.

This file is the runtime edge (reads argv/files); the core it calls is pure.

CLI:
    python tools/prompt_shield.py --text "Ignore all previous instructions and ..." [--json]
    python tools/prompt_shield.py --file doc.txt --source-url https://github.com/o/r/... \
        --authority GHSA --sha256 <64hex> --verified [--json]
Exit code: 1 if the input is isolated (flagged or unverified provenance), else 0 (2 on usage error).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_detect import compile_rule, scan                       # noqa: E402
from core.sisai_provenance import is_provenance_verified              # noqa: E402

# Guard: veto defensive / third-person / policy / quoted-example framing before matching a directive.
_GUARD = (r"(?i)^(?!.*\b(?:never|cannot|can't|must\s*not|do\s*not|don't|should\s*not|prohibit\w*|"
          r"forbidden|attacker|tried|attempt\w*|detect\w*|policy|describe\w*|quot\w*)\b)")

INJECTION_BUNDLE = {
    "guard": _GUARD,
    "indicators": [
        {"id": "pi.override", "desc": "imperative override of prior instructions",
         "regex": r"\b(?:ignore|disregard|forget|override|set\s+aside|dismiss|pretend)\b.{0,30}\b(?:previous|prior|earlier|above|preceding)\b.{0,20}\b(?:instruction|prompt|rule|direction|message)s?\b"},
        {"id": "pi.override-all", "desc": "discard everything stated earlier",
         "regex": r"\b(?:forget|ignore|disregard)\b.{0,20}\b(?:everything|all)\b.{0,20}\b(?:earlier|above|before|said|told|stated)\b"},
        {"id": "pi.override-pretend", "desc": "pretend the prior rules do not apply",
         "regex": r"\bpretend\b.{0,20}\b(?:rules?|instructions?)\b.{0,15}\b(?:above|here|no\s+longer|don't\s+apply)\b"},
        {"id": "pi.role-hijack", "desc": "role / system-prompt override or jailbreak framing",
         "regex": r"\byou\s+are\s+now\b|\bact\s+as\b.{0,25}\b(?:unrestricted|no\s+restrictions?|dan|jailbroken)\b|\bdeveloper\s+mode\b|\bnew\s+(?:instructions?|system\s+prompt|persona)\s*:"},
        {"id": "pi.role-norestrict", "desc": "claim of no restrictions / jailbreak state",
         "regex": r"\b(?:from\s+now\s+on|you(?:\s+now)?\s+have)\b.{0,30}\bno\s+restrictions?\b"},
        {"id": "pi.prompt-exfil", "desc": "attempt to extract the system / hidden prompt",
         "regex": r"\b(?:reveal|print|show|output|repeat|dump|leak|disclose|spit\s+out)\b.{0,30}\b(?:system\s+prompt|your\s+(?:initial\s+)?(?:instructions|prompt|rules)|hidden\s+prompt|initial\s+(?:prompt|instructions?))\b"},
        {"id": "pi.embedded-exec", "desc": "directive to run embedded/attached code",
         "regex": r"\b(?:run|execute|eval|invoke)\b.{0,30}\b(?:the\s+following|this|below|attached|embedded)\b.{0,25}\b(?:command|code|script|payload)\b"},
        {"id": "pi.attached-exec", "desc": "directive to run an attached script",
         "regex": r"\b(?:run|execute|launch)\b.{0,20}\battached\b.{0,15}\bscript\b"},
        {"id": "pi.secret-exfil", "desc": "directive to send your own secrets to a sink",
         "regex": r"\b(?:send|upload|post|forward|exfiltrate|mail|email)\b.{0,20}\byour\b.{0,25}\b(?:api[\s_-]?key|token|secret|password|credential)s?\b"},
        {"id": "pi.hidden-marker", "desc": "directive concealed in an HTML comment or zero-width chars",
         "regex": r"<!--[^>]*?(?:ignore|system\s+prompt|exfiltrate|instruction|credential)[^>]*?-->|[​‌‍‎‏﻿]"},
    ],
}


def _patterns():
    g = INJECTION_BUNDLE["guard"]
    return [{"id": ind["id"], "desc": ind["desc"], "regex": g + r".*(?:" + ind["regex"] + r")"}
            for ind in INJECTION_BUNDLE["indicators"]]


def compile_shield():
    """Compile the injection bundle. Returns (compiled, skipped, patterns_meta). skipped=0 expected."""
    pats = _patterns()
    compiled, skipped = compile_rule({"patterns": pats})
    return compiled, skipped, pats


def predict():
    """Pure predictor text->bool (drives verify_suite on the llm-prompt-injection holdout)."""
    compiled, _, _ = compile_shield()
    return lambda text: scan(text, compiled)


def _scan_matches(text: str) -> list:
    out = []
    for ind in INJECTION_BUNDLE["indicators"]:
        compiled, _ = compile_rule({"patterns": [{"id": ind["id"],
                                    "regex": INJECTION_BUNDLE["guard"] + r".*(?:" + ind["regex"] + r")"}]})
        if compiled and scan(text, compiled):
            out.append({"id": ind["id"], "desc": ind["desc"]})
    return out


def shield(text: str, provenance: dict = None) -> dict:
    """Classify a piece of collected text for the gateway. Returns a VERDICT (data only):
        {flagged, matches, provenance, isolate, treat_as}

    Boundary invariant: `treat_as` is ALWAYS "data" — this function never returns the text as an
    instruction and never executes it (it only feeds it to regex). `isolate` is True when the text is
    flagged as an injection OR its provenance is not host-verified (quarantine before use)."""
    matches = _scan_matches(text if isinstance(text, str) else "")
    if provenance is None:
        prov = "absent"
    else:
        prov = "verified" if is_provenance_verified({"provenance": provenance}) else "unverified"
    return {"flagged": bool(matches), "matches": matches,
            "provenance": prov,
            "isolate": bool(matches) or prov != "verified",
            "treat_as": "data"}        # collected external text is DATA, never an instruction


# ---- CLI ----------------------------------------------------------------------------------------

USAGE = ("usage:\n"
         "  python tools/prompt_shield.py --text \"<text>\" [--json]\n"
         "  python tools/prompt_shield.py --file <path> [--source-url U --authority A --sha256 H --verified] [--json]\n")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    text = _opt(argv, "--text")
    path = _opt(argv, "--file")
    if path and text is None:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    if text is None:
        sys.stderr.write(USAGE)
        return 2
    prov = None
    if _opt(argv, "--source-url"):
        prov = {"source_url": _opt(argv, "--source-url"), "authority": _opt(argv, "--authority"),
                "source_sha256": _opt(argv, "--sha256", ""), "verified": "--verified" in argv}
    verdict = shield(text, prov)
    if "--json" in argv:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
    else:
        state = "ISOLATE" if verdict["isolate"] else "allow (as data)"
        print(f"{state} | flagged={verdict['flagged']} provenance={verdict['provenance']} "
              f"treat_as={verdict['treat_as']}")
        for m in verdict["matches"]:
            print(f"  {m['id']}: {m['desc']}")
    return 1 if verdict["isolate"] else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
