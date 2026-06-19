#!/usr/bin/env python3
"""SISAI provenance — threat->defense lineage + verified-defense->corpus feedback.

Two responsibilities (stdlib, deterministic, no clock/AI):
  1. trace_defense() — ordered lineage of a defense: the channel(s) the threat came
     from -> the threat -> external source or self-design -> verification. Auditable.
  2. defense_to_corpus_entry() — the feedback bond: a VERIFIED defense becomes a
     reusable corpus source, so the next synthesis round recombines proven defenses
     (the self-improvement spiral). Only verified+implemented defenses may enter.

v1.4 adds the deterministic ingest gates (host-derived authority, not AI-judged):
  3. is_provenance_verified() — gate on verified + host∈whitelist + 64-hex sha256.
  4. strip_incoming_provenance() — drop source-supplied provenance before the gate (anti fail-open).
  5. is_critiqued() — pure first-record critique gate (P0-4).
"""

import re

# DOMAIN_AUTHORITY: the trust anchor is the HOST, never the page text or an AI verdict (R5).
DOMAIN_AUTHORITY = {
    "nvd.nist.gov": "NVD", "services.nvd.nist.gov": "NVD",
    "cve.org": "MITRE", "cve.mitre.org": "MITRE",
    "github.com": "GHSA",
    "arxiv.org": "arXiv", "export.arxiv.org": "arXiv",
}

# Host extraction is pure string work; urllib is NOT imported in core (DeterminismGuard forbids it).
_HOST_RE = re.compile(r"^[a-z][a-z0-9+.\-]*://([^/?#@]*@)?([^/?#:]+)", re.IGNORECASE)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def host_from_url(url: str) -> str:
    """Lowercased host of an absolute URL (re-based, no network, no urllib). '' if unparseable."""
    if not isinstance(url, str):
        return ""
    m = _HOST_RE.match(url.strip())
    return m.group(2).lower() if m else ""


def authority_from_url(url: str):
    """Deterministic origin trust from the host alone (None if host not whitelisted)."""
    return DOMAIN_AUTHORITY.get(host_from_url(url))


def is_provenance_verified(threat: dict) -> bool:
    """Gate (pure): verified flag AND host∈whitelist AND AI-claimed authority matches the host-derived
    one AND a well-formed 64-hex sha256. The AI match verdict is advisory; the binding trust is the host."""
    p = (threat or {}).get("provenance") or {}
    derived = authority_from_url(p.get("source_url", ""))
    return (bool(p.get("verified"))
            and derived is not None
            and derived == p.get("authority")
            and bool(_SHA256_RE.match(p.get("source_sha256", "") or "")))


def strip_incoming_provenance(threat: dict) -> dict:
    """Return a copy with any source-supplied provenance removed (set to None). The isolated meta-layer
    fetch sub-agent re-attaches provenance; collected page text must never self-claim it past the gate."""
    out = dict(threat or {})
    out["provenance"] = None
    return out


def is_critiqued(defense: dict) -> bool:
    """Pure first-record gate (P0-4): a defense's multi-lens critique must have passed."""
    return bool(((defense or {}).get("critique") or {}).get("passed"))


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
