#!/usr/bin/env python3
"""SISAI loop driver — sequence the three strands (stdlib only, deterministic).

Decides the next turn over: ThreatIntel (collect), DefenseSynthesis (solve/design),
DetectOps (operate+feedback), plus channel self-expansion. Priorities make it a
self-improving spiral: close the loop (record verified defense) first, keep sources
broad (discover channels), sense fresh threats, then address the highest-priority
threat. The "external first, else self-design" rule lives in plan_defense().

Determinism: pure function of `state`; identical state -> identical action.
"""

from .sisai_ledger import is_consumed
from .sisai_fingerprint import threat_fingerprint

DEFAULT_LOOP_POLICY = {
    "min_active_channels": 4,
}

VALID_ACTIONS = ("RECORD_DEFENSE", "DISCOVER_CHANNELS", "REFRESH_COVERAGE",
                 "RUN_THREAT_INTEL", "SOLVE_OR_DESIGN")


def next_action(state: dict, policy: dict = None) -> dict:
    """Decide the next loop action from current state (deterministic).

    Expected state keys (all optional):
        pending_verified_defense: bool   (a verified defense awaiting record)
        should_discover_channels: bool   (channel coverage low)
        coverage: {"repair_required": bool}
        untriaged_threats: int
        active_channels: int
        top_threat: dict|None            (triage-selected highest priority)
    Returns {action, why, [target]}.
    """
    P = dict(DEFAULT_LOOP_POLICY)
    if policy:
        P.update(policy)

    # 1) Close the loop: a verified defense must be recorded + fed back to corpus.
    if state.get("pending_verified_defense"):
        return {"action": "RECORD_DEFENSE",
                "why": "verified defense -> ledger + corpus feedback (close loop)"}

    # 2) Keep sources broad: expand channels before they run dry / go narrow.
    if state.get("should_discover_channels"):
        return {"action": "DISCOVER_CHANNELS",
                "why": "channel coverage low -> expand information sources"}

    # 3) Repair blind spots before sensing more of the same.
    if (state.get("coverage") or {}).get("repair_required"):
        return {"action": "REFRESH_COVERAGE",
                "why": "attack-surface skew -> steer toward under-covered categories"}

    # 4) Sense fresh threats if none are pending triage and we have sources.
    if int(state.get("untriaged_threats", 0)) == 0 and int(state.get("active_channels", 0)) > 0:
        return {"action": "RUN_THREAT_INTEL",
                "why": "scan channels for fresh threats"}

    # 5) Address the highest-priority known threat.
    top = state.get("top_threat")
    if top:
        return {"action": "SOLVE_OR_DESIGN",
                "why": "address highest-priority threat (external first, else design)",
                "target": top.get("threat_id") if isinstance(top, dict) else top}

    # 6) Default: keep sensing.
    return {"action": "RUN_THREAT_INTEL", "why": "balance -> keep sensing the world"}


def plan_defense(threat: dict, defense_corpus: list, ledger: dict) -> dict:
    """External-first defense procurement strategy (deterministic).

    The actual external search / pgf design is the AI meta-layer; this decides WHICH
    path to take and guarantees external solutions are preferred over self-design,
    and already-defended threats are skipped (reuse).
    """
    cand = {"title": threat.get("title", ""), "fingerprint": threat_fingerprint(threat)}
    if is_consumed(cand, ledger)["consumed"]:
        return {"action": "SKIP", "why": "threat already defended (reuse)"}

    hit = match_external_defense(threat, defense_corpus)
    if hit:
        return {"action": "ADOPT_EXTERNAL", "defense": hit,
                "why": "external solution found -> adopt + adapt"}
    return {"action": "DESIGN_DEFENSE",
            "why": "no external solution -> design via pgf (self-improvement)",
            "threat_id": threat.get("threat_id")}


def match_external_defense(threat: dict, defense_corpus: list):
    """Deterministically find an existing defense applicable to a threat.

    Match when a corpus defense shares the threat's category or any technique. Picks
    the best overlap (then defense_id) for stability. Returns the defense or None.
    """
    t_cat = threat.get("category")
    t_tech = set(threat.get("techniques", []) or [])
    best = None
    best_key = (-1, "")
    for d in defense_corpus or []:
        d_cat = d.get("covers_category") or d.get("category")
        d_tech = set(d.get("covers_techniques", []) or d.get("techniques", []) or [])
        overlap = len(t_tech & d_tech) + (1 if t_cat and t_cat == d_cat else 0)
        if overlap <= 0:
            continue
        key = (overlap, d.get("defense_id", ""))
        if key > best_key:
            best_key = key
            best = d
    return best
