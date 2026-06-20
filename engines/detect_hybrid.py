#!/usr/bin/env python3
"""SISAI — two-layer hybrid detection (engines/ — pure control flow over injected cognition).

The independent-validation result (0/7; `docs/INDEPENDENT-VALIDATION-RESULTS.md`) showed deterministic
KEYWORD bundles do not generalize to blind cross-model phrasing (recall 0.17–0.33). SISAI's design
answer is layered, and this is the deterministic combiner for it:

  layer 1 — KEYWORD prefilter: the pure, fast, auditable `core` rule (`compile_rule`/`scan`). Cheap and
            explainable, but brittle to paraphrase.
  layer 2 — SEMANTIC classifier: the META-LAYER (AI) judging meaning, injected as a callable so engines/
            stays pure (no clock/network/AI/randomness — mirrors `engines/adversarial.py`).

Decision: when a semantic verdict is available it ADJUDICATES (it generalizes); the keyword verdict is
kept for audit + a `disputed` flag where they disagree. With no semantic layer, the keyword verdict is
the fallback. This recovers the recall the keyword layer loses while keeping every decision explainable.

The semantic layer is non-deterministic cognition and lives at the edge (the AI runtime supplies it per
call); this module never embeds it. `now`-free, import-pure.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.sisai_verify import metrics                                   # noqa: E402


def hybrid_verdict(text, keyword_predict, semantic_predict=None) -> dict:
    """Combine the keyword prefilter with an (optional) injected semantic classifier.

    Returns {flagged, by, keyword, semantic, disputed}. Semantic adjudicates when present; the keyword
    result is retained for audit and `disputed` marks disagreement."""
    kw = bool(keyword_predict(text))
    if semantic_predict is None:
        return {"flagged": kw, "by": "keyword", "keyword": kw, "semantic": None, "disputed": False}
    sem = bool(semantic_predict(text))
    return {"flagged": sem, "by": "semantic", "keyword": kw, "semantic": sem, "disputed": kw != sem}


def hybrid_predict(keyword_predict, semantic_predict=None):
    """A plain text->bool predictor for the hybrid verdict (drives verify_suite / metrics)."""
    return lambda text: hybrid_verdict(text, keyword_predict, semantic_predict)["flagged"]


def evaluate(rows, keyword_predict, semantic_predict=None) -> dict:
    """Grade keyword-only vs hybrid over labeled rows, and report the recall the semantic layer recovers."""
    kw = metrics(lambda t: bool(keyword_predict(t)), rows)
    hy = metrics(hybrid_predict(keyword_predict, semantic_predict), rows)
    recovered = [r.get("text") for r in rows
                 if r.get("label") == "malicious"
                 and not keyword_predict(r.get("text", ""))
                 and hybrid_predict(keyword_predict, semantic_predict)(r.get("text", ""))]
    return {"keyword": {"recall": kw["recall"], "precision": kw["precision"], "fp": kw["fp"]},
            "hybrid": {"recall": hy["recall"], "precision": hy["precision"], "fp": hy["fp"]},
            "recovered_by_semantic": recovered}
