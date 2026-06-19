#!/usr/bin/env python3
"""SISAI verification library — honest generalization metric + cross-model role gate (stdlib, pure).

P0-2 HeldoutBench: a detector is graded on a FROZEN holdout split when one is provisioned; until then
the legacy full-set gate stays authoritative (advisory, non-blocking — no fail-closed break of existing
suites). The adversarial split is train-only and NEVER in the gate.

v1.4 CrossModelRoles: `roles_disjoint` enforces ONLY the binding pairs (author!=holdout, author!=judge)
over a committed role registry, and is advisory-until-provisioned (an unregistered suite is grandfathered,
not blocked). It is a label-based defense-in-depth layer ON TOP OF the structural holdout freeze, which
remains the binding independence guarantee. Pure: no clock/AI/network/random.
"""

MIN_HOLDOUT = {"malicious": 5, "benign": 4}
PRECISION_FLOOR = 0.85


def _count(samples, label):
    return sum(1 for s in samples if s.get("label") == label)


def metrics(predict, samples) -> dict:
    """Confusion metrics for a predictor (text->bool malicious) over labeled samples. Pure."""
    tp = fp = tn = fn = 0
    for s in samples:
        pred = bool(predict(s.get("text", "")))
        mal = s.get("label") == "malicious"
        tp += int(pred and mal); fp += int(pred and not mal)
        tn += int((not pred) and not mal); fn += int((not pred) and mal)
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    return {"recall": round(rec, 3), "precision": round(prec, 3),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def split_of(sample) -> str:
    """A sample's split; split-less rows default to 'tune'."""
    return (sample or {}).get("split", "tune") or "tune"


def verify_suite(samples, predict) -> dict:
    """Grade a detector. If a sized FROZEN holdout exists -> gate on the holdout ONLY; else the legacy
    full-set gate stays authoritative (advisory). Adversarial split is train-only (never gated)."""
    hold = [s for s in samples if split_of(s) == "holdout"]
    sized = (_count(hold, "malicious") >= MIN_HOLDOUT["malicious"]
             and _count(hold, "benign") >= MIN_HOLDOUT["benign"])
    if not sized:
        full = metrics(predict, samples)
        return {"holdout": None, "reason": "insufficient_holdout", "gate": "legacy-fullset",
                "passed": full["recall"] == 1.0 and full["precision"] >= PRECISION_FLOOR}
    g = metrics(predict, hold)
    tune = [s for s in samples if split_of(s) == "tune"]
    return {"holdout": g, "gate": "holdout", "tune": metrics(predict, tune),
            "passed": g["recall"] == 1.0 and g["precision"] >= PRECISION_FLOOR}


# ---- CrossModelRoles (v1.4) ---------------------------------------------------------------------

def index_role_registry(registry: dict) -> dict:
    """Committed registry is a list of entries (schema-valid); index it by suite for O(1) lookup."""
    return {e["suite"]: e for e in (registry or {}).get("entries", []) if e.get("suite")}


def roles_disjoint(suite: str, index: dict) -> dict:
    """Advisory-until-provisioned (mirrors verify_suite / first-record critique — never regress the
    existing suites). Enforces only the binding pairs: author != holdout_curator AND author != judge.
    curator != judge is second-order and NOT required. Returns {ok, gate}."""
    r = (index or {}).get(suite)
    if not r:
        return {"ok": True, "gate": "roles_unprovisioned"}        # grandfather: logged, non-blocking
    a = r.get("author_model"); h = r.get("holdout_curator_model"); j = r.get("judge_model")
    if not (a and h and j):
        return {"ok": False, "gate": "roles_incomplete"}          # registered but malformed -> fail-closed
    return {"ok": a != h and a != j, "gate": "roles"}
