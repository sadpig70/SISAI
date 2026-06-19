#!/usr/bin/env python3
"""SISAI B0-4 — benchmark / holdout-generator harness (deterministic orchestration, defensive-only).

Drives the red/blue hardening loop to grow a detector's ADVERSARIAL training split, and routes any
proposed HOLDOUT samples to a separate human-curation queue — the frozen benchmark is never machine-
written. The cognition (variant generation, hardening, holdout proposals) is META-LAYER and injected
as callables; this harness is pure control flow (no clock/AI/network; `now` injected).

Composition:
  - engines.adversarial.adversarial_verify — the bounded loop. Misses are appended ONLY as
    split=adversarial (core.atomic_append_samples structurally refuses split=holdout).
  - calibration.score.score_rule — after the loop, flag leakage_suspect (recall==1.0 AND
    precision==1.0 on the frozen holdout: implausibly perfect, a possible holdout leak/overfit).
  - propose_holdout_candidates — proposed holdout rows go to a SEPARATE file as unsplit proposals
    marked needs_human_review; a row that pre-claims any split (especially holdout) is refused.

Fail-closed: when the loop returns budget_exhausted, `record_ok` is False — the caller MUST NOT
record the defense/rule (convergence is best-effort, never assumed).

This is benchmark tooling: nothing here writes the frozen holdout or records into ledger/corpus.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json, atomic_write_json                 # noqa: E402
from core.sisai_detect import is_inert_indicator                      # noqa: E402
from engines.adversarial import adversarial_verify                    # noqa: E402
from calibration.score import score_rule, holdout_samples             # noqa: E402


def propose_holdout_candidates(candidate_path: str, rows: list, now: str) -> int:
    """Append proposed holdout samples to a SEPARATE human-curation queue (never the benchmark).

    A candidate is an inert, labeled, UNSPLIT proposal. A row that pre-claims a split (above all
    'holdout') is refused (ValueError) — only a human curator may promote a proposal into the frozen
    holdout. fp-dedup by text. Returns rows appended."""
    rows = list(rows or [])
    for r in rows:
        if (r or {}).get("split") is not None:
            raise ValueError("holdout candidate must not pre-claim a split (human curation assigns it)")
        if not is_inert_indicator(r):
            raise ValueError("holdout candidate must be an inert, labeled sample row")
    store = read_json(candidate_path) or []
    seen = {r.get("text") for r in store}
    added = 0
    for r in rows:
        if r.get("text") in seen:
            continue
        store.append({"text": r["text"], "label": r["label"],
                      "proposed_at": now, "status": "needs_human_review"})
        seen.add(r["text"])
        added += 1
    if added:
        atomic_write_json(candidate_path, store)
    return added


def run_harness(rule: dict, threat: dict, category: str, samples_path: str, *,
                gen_variants, harden, verify,
                holdout_candidate_path: str = None, gen_holdout_candidates=None,
                now: str = "1970-01-01", samples_path_for_holdout: str = None, **loop_kw) -> dict:
    """Run the adversarial loop, flag leakage, route holdout proposals to curation, and decide
    record_ok (fail-closed on budget_exhausted). Returns the loop result enriched with
    {leakage_suspect, score, holdout_candidates_proposed, record_ok}."""
    res = adversarial_verify(rule, threat, samples_path,
                             gen_variants=gen_variants, harden=harden, verify=verify, **loop_kw)

    hold = holdout_samples(category, samples_path_for_holdout)
    score = score_rule(res["rule"], hold) if hold else {}

    n_candidates = 0
    if gen_holdout_candidates is not None and holdout_candidate_path:
        proposals = gen_holdout_candidates(res["rule"], threat) or []
        n_candidates = propose_holdout_candidates(holdout_candidate_path, proposals, now)

    return {**res,
            "leakage_suspect": bool(score.get("leakage_suspect")),
            "score": score,
            "holdout_candidates_proposed": n_candidates,
            "record_ok": res["status"] == "converged"}    # fail-closed


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    # The cognition (gen_variants/harden/verify/gen_holdout_candidates) is meta-layer and injected
    # programmatically; there is no pure-CLI run. Surface the curation queue for inspection instead.
    cand = _opt(argv, "--show-candidates")
    if cand:
        print(json.dumps(read_json(cand) or [], ensure_ascii=False, indent=2))
        return 0
    sys.stderr.write("usage: python tools/benchmark_harness.py --show-candidates <queue.json>\n"
                     "(the loop is driven programmatically with injected meta-layer cognition)\n")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
