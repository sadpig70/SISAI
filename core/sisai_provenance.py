#!/usr/bin/env python3
"""SISAI provenance — threat->defense lineage + verified-defense->corpus feedback.

Two responsibilities (stdlib, deterministic, no clock/AI):
  1. trace_defense() — ordered lineage of a defense: the channel(s) the threat came
     from -> the threat -> external source or self-design -> verification. Auditable.
  2. defense_to_corpus_entry() — the feedback bond: a VERIFIED defense becomes a
     reusable corpus source, so the next synthesis round recombines proven defenses
     (the self-improvement spiral). Only verified+implemented defenses may enter.
"""


def trace_defense(defense: dict) -> list:
    """Ordered lineage [{layer, id}] for a defense (deterministic, engine-neutral)."""
    lineage = []
    if defense.get("defense_id"):
        lineage.append({"layer": "defense", "id": defense["defense_id"]})
    if defense.get("covers_threat"):
        lineage.append({"layer": "threat", "id": defense["covers_threat"]})
    for ch in sorted(set(defense.get("source_channels", []) or [])):
        lineage.append({"layer": "channel", "id": ch})
    kind = defense.get("kind")
    if kind == "external" and defense.get("origin"):
        lineage.append({"layer": "external_source", "id": defense["origin"]})
    elif kind == "designed":
        lineage.append({"layer": "self_designed", "id": defense.get("origin", "pgf")})
    ver = defense.get("verification") or {}
    if ver.get("method"):
        lineage.append({"layer": "verification", "id": ver["method"]})
    return lineage


def is_verified(defense: dict) -> bool:
    """A defense is verified when its verification block passed and it is implemented."""
    ver = defense.get("verification") or {}
    return bool(ver.get("passed")) and bool(defense.get("implementations"))


def defense_to_corpus_entry(defense: dict) -> dict:
    """Convert a VERIFIED defense into a reusable corpus source (feedback bond).

    Raises ValueError unless the defense is verified+implemented (only proven
    defenses feed the corpus, so synthesis recombines real assets, not drafts).
    """
    if not is_verified(defense):
        raise ValueError("defense_to_corpus_entry: defense not verified+implemented "
                         "(only proven defenses may seed the corpus)")
    impl = (defense.get("implementations") or [{}])[0]
    return {
        "defense_id": defense.get("defense_id"),
        "title": defense.get("title"),
        "controls": defense.get("controls", []) or [],
        "covers_threat": defense.get("covers_threat"),
        "kind": defense.get("kind"),
        "artifact": impl.get("artifact_path") or impl.get("rule_id"),
        "lineage": trace_defense(defense),
        "reuse_policy": "recombine_for_related_threats",
    }
