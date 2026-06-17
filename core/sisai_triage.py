#!/usr/bin/env python3
"""SISAI triage + coverage — what to defend FIRST, and where the blind spots are.

Two deterministic signals that steer the loop:
  * triage  : severity (CVSS) x recency -> rank threats so the worst/newest go first.
  * coverage: distribution over attack categories/techniques -> flag mode-collapse
              (the system fixating on one attack class while others go unwatched).

Determinism: pure functions, stdlib only; `now` is injected (an ISO date string).
Recency uses simple lexicographic/keyed date math on injected strings — no clock.
"""

from collections import Counter

DEFAULT_TRIAGE_WEIGHTS = (0.6, 0.4)         # (severity, recency)
DEFAULT_COVERAGE_THRESHOLDS = {
    "category_dominance": 0.60,             # one category >= 60% of threats -> skewed
    "min_categories": 3,                    # fewer distinct categories than this -> narrow
}


def _date_ordinal(d: str) -> int:
    """Map an ISO-ish date 'YYYY-MM-DD...' to an integer day count (deterministic).

    Tolerant: returns 0 if unpar. Pure arithmetic on injected strings, no clock.
    """
    if not d or len(d) < 10:
        return 0
    try:
        y, m, day = int(d[0:4]), int(d[5:7]), int(d[8:10])
    except ValueError:
        return 0
    return y * 372 + m * 31 + day           # monotonic enough for ordering/decay


def recency_decay(recency: str, now: str, horizon_days: int = 372) -> float:
    """1.0 for 'today', decaying linearly to 0.0 at `horizon_days` old. Clamped [0,1]."""
    age = _date_ordinal(now) - _date_ordinal(recency)
    if age <= 0:
        return 1.0
    if age >= horizon_days:
        return 0.0
    return 1.0 - age / horizon_days


def triage_score(threat: dict, now: str, weights=DEFAULT_TRIAGE_WEIGHTS) -> float:
    """severity(CVSS/10) x recency, weighted. Deterministic given (threat, now)."""
    sev = (threat.get("cvss") or 0.0) / 10.0
    rec = recency_decay(threat.get("recency", ""), now)
    return weights[0] * sev + weights[1] * rec


def rank_threats(threats: list, now: str, weights=DEFAULT_TRIAGE_WEIGHTS) -> list:
    """Threats sorted by triage score desc; ties broken by threat_id asc (deterministic)."""
    scored = [(triage_score(t, now, weights), t.get("threat_id", ""), t) for t in threats]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{"threat": t, "score": round(s, 4)} for s, _, t in scored]


def top_threat(threats: list, now: str) -> dict:
    ranked = rank_threats(threats, now)
    return ranked[0]["threat"] if ranked else None


def measure_coverage(threats: list, thresholds: dict = None) -> dict:
    """Attack-surface coverage report. repair_required=True when threats cluster on
    one category (blind spots forming). Deterministic counts."""
    P = dict(DEFAULT_COVERAGE_THRESHOLDS)
    if thresholds:
        P.update(thresholds)
    n = len(threats)
    cats = Counter(t.get("category", "uncategorized") for t in threats)
    techniques = Counter()
    for t in threats:
        techniques.update(t.get("techniques", []) or [])
    dominance = (max(cats.values()) / n) if n else 0.0
    skewed = n > 0 and dominance >= P["category_dominance"]
    narrow = 0 < len(cats) < P["min_categories"]
    repair_required = skewed or narrow
    return {
        "n": n,
        "repair_required": repair_required,
        "category_dominance": round(dominance, 4),
        "categories": dict(cats),
        "distinct_categories": len(cats),
        "distinct_techniques": len(techniques),
        "signals": {"skewed": skewed, "narrow": narrow},
        "thresholds": P,
    }


def least_covered_category(threats: list) -> str:
    """The category with the fewest threats (steering target). '' if none."""
    cats = Counter(t.get("category", "uncategorized") for t in threats)
    if not cats:
        return ""
    return sorted(cats.items(), key=lambda kv: (kv[1], kv[0]))[0][0]
