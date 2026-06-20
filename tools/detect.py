#!/usr/bin/env python3
"""SISAI — unified detection entry (two-layer, deterministic edge, defensive-only).

Operationalizes the independent-validation finding (keyword 0/7 → semantic 7/7,
docs/INDEPENDENT-VALIDATION-RESULTS.md): the keyword bundle is a fast, auditable PREFILTER, and the
META-LAYER SEMANTIC verdict is the first-class decision. This is the single entry across all shipped
detectors that combines them via `engines/detect_hybrid` and, when no semantic verdict is supplied,
EMITS AN ESCALATION (`semantic_recommended`) — because keyword alone does not generalize.

Usage in a SISAI turn: the deterministic CLI runs the keyword prefilter instantly; the meta-layer (AI
runtime) then supplies a semantic verdict per (text, category) in-process, and `detect(... semantic=...)`
returns the adjudicated hybrid verdict. The semantic layer is non-deterministic cognition — injected,
never embedded here (this module is pure-import; no clock/network/AI/randomness).

CLI (keyword prefilter + escalation flag; the semantic layer is supplied in-process by the meta-layer):
    python tools/detect.py --text "..." [--category <cat>] [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engines.detect_hybrid import hybrid_verdict                       # noqa: E402
from calibration.robustness import predictors                          # noqa: E402

CATEGORIES = tuple(sorted(predictors()))


def _semantic_for(category, semantic):
    """Resolve the injected semantic verdict for a category: bool | {category: bool} | None."""
    if semantic is None:
        return None
    if isinstance(semantic, bool):
        return semantic
    if isinstance(semantic, dict):
        return semantic.get(category)
    return None


def detect(text: str, category: str = None, semantic=None) -> dict:
    """Two-layer detection over one or all categories.

    semantic: the meta-layer's verdict — a bool (this category), a {category: bool} map, or None.
    When None, the verdict falls back to the keyword prefilter and `semantic_recommended` is True
    (escalate to the meta-layer; keyword alone is unreliable — independent recall 0.17–0.33)."""
    preds = predictors()
    cats = [category] if category else list(CATEGORIES)
    per = {}
    for cat in cats:
        sv = _semantic_for(cat, semantic)
        sem_predict = (lambda t, _v=sv: _v) if sv is not None else None
        v = hybrid_verdict(text if isinstance(text, str) else "", preds[cat], sem_predict)
        per[cat] = v
    flagged = [c for c, v in per.items() if v["flagged"]]
    used_semantic = any(v["semantic"] is not None for v in per.values())
    return {
        "flagged": bool(flagged),
        "flagged_categories": sorted(flagged),
        "by": "semantic" if used_semantic else "keyword",
        "per_category": per,
        "semantic_recommended": not used_semantic,   # escalate: meta-layer should supply the verdict
    }


# ---- CLI ----------------------------------------------------------------------------------------

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
        sys.stderr.write("usage: python tools/detect.py --text \"...\" | --file <path> [--category <cat>] [--json]\n"
                         f"  categories: {', '.join(CATEGORIES)}\n")
        return 2
    cat = _opt(argv, "--category")
    if cat is not None and cat not in CATEGORIES:
        sys.stderr.write(f"unknown category: {cat}\n")
        return 2
    r = detect(text, cat)            # CLI = keyword prefilter only; semantic is supplied in-process
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        state = "FLAGGED" if r["flagged"] else "clean"
        print(f"{state} (keyword prefilter) | flagged={r['flagged_categories'] or '-'}")
        if r["semantic_recommended"]:
            print("  semantic_recommended: keyword alone is unreliable (independent recall 0.17-0.33);"
                  " escalate to the meta-layer for the first-class semantic verdict.")
    return 1 if r["flagged"] else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
