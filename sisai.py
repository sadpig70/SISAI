#!/usr/bin/env python3
"""SISAI driver — wire the three strands to the backbone and report the next turn.

Reads the channel registry, collected threats and defense corpus (seed fixtures, or
live `.sisai/` artifacts), runs one deterministic turn: triage threats, measure
attack-surface coverage, decide external-first defense plans, and compute the next
loop action. Also the actuator for closing the loop (record a verified defense and
feed it back to the corpus).

Determinism: build_report is a pure function of inputs. Wall-clock is read ONLY at
the CLI edge (`--now` overrides). No network/AI here — collection/design is the AI
meta-layer (skills); this is the backbone control plane.

CLI:
    python sisai.py status
    python sisai.py plan
    python sisai.py discover-channel --channel ch.json --registry .sisai/channels.json
    python sisai.py record-defense --defense def.json --ledger .sisai/ledger.json --corpus .sisai/corpus.json
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.sisai_io import atomic_write_json, read_json                  # noqa: E402
from core.sisai_ledger import (                                          # noqa: E402
    empty_ledger, is_consumed, append_entry, reindex_ledger, normalize_name,
)
from core.sisai_channels import (                                        # noqa: E402
    register_channel, active_channels, kind_coverage, should_discover_channels,
    missing_kinds, next_channels_to_scan,
)
from core.sisai_triage import rank_threats, top_threat, measure_coverage  # noqa: E402
from core.sisai_provenance import defense_to_corpus_entry, is_verified   # noqa: E402
from core.sisai_loop import next_action, plan_defense                    # noqa: E402
from engines.adapters import (                                           # noqa: E402
    channels_seed_to_registry, threats_seed_to_list, defenses_seed_to_corpus,
)

SEED = os.path.join(ROOT, "seed")


def _load(root, live_name, seed_name):
    """Prefer a live .sisai/ artifact, else fall back to the shipped seed."""
    live = read_json(os.path.join(root, ".sisai", live_name))
    if live is not None:
        return live
    return read_json(os.path.join(SEED, seed_name))


def build_report(root=None, now="1970-01-01") -> dict:
    """One deterministic SISAI turn over the current channel/threat/defense state."""
    root = root or ROOT
    registry = _load(root, "channels.json", "channels.json")
    if isinstance(registry, list):  # seed format -> registry
        registry = channels_seed_to_registry(registry, now=now)
    threats = threats_seed_to_list(_load(root, "threats.json", "threats.json"))
    corpus = defenses_seed_to_corpus(_load(root, "defenses.json", "defenses.json"))
    ledger = read_json(os.path.join(root, ".sisai", "ledger.json")) or empty_ledger()
    reindex_ledger(ledger)

    # triage + coverage (blind-spot guard)
    ranked = rank_threats(threats, now)
    coverage = measure_coverage(threats)
    # untriaged = threats not yet defended (not in ledger)
    untriaged = [t for t in threats
                 if not is_consumed({"title": t["title"], "fingerprint": t["fingerprint"]}, ledger)["consumed"]]
    top = top_threat(untriaged, now)

    state = {
        "pending_verified_defense": False,
        "should_discover_channels": should_discover_channels(registry),
        "coverage": coverage,
        "untriaged_threats": len(untriaged),
        "active_channels": len(active_channels(registry)),
        "top_threat": top,
    }
    action = next_action(state)

    plan = plan_defense(top, corpus, ledger) if top else None
    return {
        "channels": {"active": len(active_channels(registry)),
                     "kinds": kind_coverage(registry), "missing_kinds": missing_kinds(registry),
                     "next_to_scan": [c.get("id") for c in next_channels_to_scan(registry)]},
        "threats": {"total": len(threats), "untriaged": len(untriaged)},
        "coverage": coverage,
        "top_threat": ({"threat_id": top["threat_id"], "title": top["title"],
                        "category": top["category"], "cvss": top.get("cvss"),
                        "score": ranked[0]["score"]} if top else None),
        "defense_plan": plan,
        "next_action": action,
    }


def _mark_threat_defended(ledger: dict, threat_id, threats, now: str):
    """Mark the covered threat as defended so it leaves the untriaged set (loop progression).

    The defense carries only the threat *id*, but `is_consumed` matches on the threat's
    title/fingerprint — so the actuator resolves the id against the provided threats list
    and appends a `kind:"threat"` entry (the mechanism asserted by test_skip_when_already_defended).
    Returns the threat_id if a new entry was appended, else None. Idempotent.
    """
    if not (threat_id and threats):
        return None
    threat = next((t for t in threats if t.get("threat_id") == threat_id), None)
    if not threat:
        return None
    key = {"title": threat.get("title", ""), "fingerprint": threat.get("fingerprint")}
    if is_consumed(key, ledger)["consumed"]:
        return None
    append_entry(ledger, {"entry_id": threat_id, "kind": "threat",
                          "title": threat.get("title", ""),
                          "fingerprint": threat.get("fingerprint")}, now=now)
    return threat_id


def record_defense(defense: dict, ledger_path: str, corpus_path: str, now: str,
                   threats=None) -> dict:
    """Actuator: record a VERIFIED defense to the ledger + feed it back to the corpus.

    Idempotent — re-running on an already-recorded defense is a no-op. Only verified
    + implemented defenses are accepted (defensive discipline). `now` injected. When
    `threats` is supplied, the defense's `covers_threat` is also marked defended so the
    threat leaves the untriaged set and `next_action` advances to the next threat.
    """
    if not is_verified(defense):
        return {"status": "rejected", "why": "defense not verified+implemented"}
    from core.sisai_fingerprint import defense_fingerprint
    fp = defense_fingerprint(defense)
    entry = {"entry_id": defense.get("defense_id") or f"DEF-{fp[:8]}", "kind": "defense",
             "title": defense.get("title", ""), "fingerprint": fp,
             "implementations": defense.get("implementations", [])}
    ledger = read_json(ledger_path) or empty_ledger()
    reindex_ledger(ledger)
    defense_already = is_consumed({"title": entry["title"], "fingerprint": fp}, ledger)["consumed"]
    if not defense_already:
        append_entry(ledger, entry, now=now)
    # Mark the covered threat defended even on re-run (self-heals ledgers written before
    # threat-marking existed); idempotent — a no-op once the threat is already recorded.
    threat_marked = _mark_threat_defended(ledger, defense.get("covers_threat"), threats, now)
    if not defense_already or threat_marked:
        atomic_write_json(ledger_path, ledger)
    if defense_already:
        return {"status": "already_recorded", "defense_id": entry["entry_id"],
                "threat_marked": threat_marked}
    corpus_entry = defense_to_corpus_entry(defense)
    corpus = read_json(corpus_path) or []
    if not any(c.get("defense_id") == corpus_entry["defense_id"] for c in corpus):
        corpus.append(corpus_entry)
        atomic_write_json(corpus_path, corpus)
    return {"status": "closed", "defense_id": entry["entry_id"],
            "threat_marked": threat_marked, "corpus_entry": corpus_entry}


def _threats_as_list(loaded):
    """Normalize a loaded threats artifact (seed dict or runtime list) to a list."""
    if isinstance(loaded, dict):
        return loaded.get("threats", [])
    if isinstance(loaded, list):
        return loaded
    return []


def ingest_threats(raw_threats: list, threats_path: str, ledger_path: str, now: str,
                   seed_threats=None) -> dict:
    """Actuator: ingest freshly-scanned threats into runtime state (the RUN_THREAT_INTEL
    output path). Collected text is DATA only — never control flow.

    Steps (deterministic): schema-validate each candidate, assign stable id+fingerprint,
    drop candidates already defended (ledger) or already present (runtime), then atomic
    merge into `threats_path`. `now` injected. Idempotent: re-ingesting the same batch
    accepts nothing.
    """
    from core.sisai_schema import validate_against_schema, schema_path
    existing = _threats_as_list(read_json(threats_path))
    if not existing and seed_threats is not None:
        existing = _threats_as_list(seed_threats)
    existing = threats_seed_to_list(existing)
    ledger = read_json(ledger_path) or empty_ledger()
    reindex_ledger(ledger)
    normalized = threats_seed_to_list(raw_threats or [])
    seen_fp = {t.get("fingerprint") for t in existing}
    # Title dedup too: fingerprint can shift when a defaulted field (e.g. category)
    # is absent in the raw input but present once stored, so title keeps re-ingest idempotent.
    seen_titles = {normalize_name(t.get("title", "")) for t in existing}
    accepted, skipped = [], []
    sp = schema_path(ROOT, "threat")
    for t in normalized:
        problems = validate_against_schema(t, sp)
        if problems:
            skipped.append({"threat_id": t.get("threat_id"), "why": "schema_invalid",
                            "detail": problems[:3]})
        elif is_consumed({"title": t["title"], "fingerprint": t["fingerprint"]}, ledger)["consumed"]:
            skipped.append({"threat_id": t["threat_id"], "why": "already_defended"})
        elif t["fingerprint"] in seen_fp or normalize_name(t["title"]) in seen_titles:
            skipped.append({"threat_id": t["threat_id"], "why": "duplicate_runtime_threat"})
        else:
            accepted.append(t)
            seen_fp.add(t["fingerprint"])
            seen_titles.add(normalize_name(t["title"]))
    merged = existing + accepted
    if accepted:
        atomic_write_json(threats_path, merged)
    return {"status": "ingested" if accepted else "noop",
            "accepted": [t["threat_id"] for t in accepted],
            "skipped": skipped,
            "total_threats": len(merged)}


def _print(r: dict) -> None:
    print("=== SISAI turn ===")
    c = r["channels"]
    print(f"  channels: {c['active']} active | kinds={c['kinds']} | missing={c['missing_kinds']}")
    t = r["threats"]
    cov = r["coverage"]
    print(f"  threats: {t['total']} total, {t['untriaged']} undefended | "
          f"coverage repair_required={cov['repair_required']} "
          f"(dominance={cov['category_dominance']}, categories={cov['distinct_categories']})")
    if r["top_threat"]:
        tt = r["top_threat"]
        print(f"  top threat (triage): {tt['threat_id']} \"{tt['title']}\" "
              f"[{tt['category']}] cvss={tt['cvss']} score={tt['score']}")
    if r["defense_plan"]:
        p = r["defense_plan"]
        print(f"  defense plan: {p['action']} ({p['why']})")
    a = r["next_action"]
    print(f"  NEXT ACTION: {a['action']}  ({a['why']})")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _now(argv):
    n = _opt(argv, "--now")
    if n:
        return n
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


USAGE = ("usage:\n"
         "  python sisai.py status [--root R] [--now YYYY-MM-DD] [--json]\n"
         "  python sisai.py plan [--now YYYY-MM-DD]\n"
         "  python sisai.py discover-channel --channel <ch.json> --registry <reg.json> [--now ...]\n"
         "  python sisai.py record-defense --defense <def.json> --ledger <l.json> --corpus <c.json> [--now ...]\n"
         "  python sisai.py ingest-threats --threats <new.json> --ledger <l.json> [--out .sisai/threats.json] [--now ...]\n")


def _main(argv) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"

    if cmd in ("status", "plan"):
        r = build_report(_opt(argv, "--root"), now=_now(argv))
        if cmd == "plan":
            plan = r.get("defense_plan")
            if plan is None:
                plan = {"action": "NO_PENDING_THREAT",
                        "why": f"all known threats defended; next_action={r['next_action']['action']}"}
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        elif "--json" in argv:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            _print(r)
        return 0

    if cmd == "discover-channel":
        chf, reg = _opt(argv, "--channel"), _opt(argv, "--registry")
        if not (chf and reg):
            sys.stderr.write(USAGE)
            return 2
        registry = read_json(reg) or {"channels": [], "by_fingerprint": {}}
        with open(chf, encoding="utf-8") as f:
            res = register_channel(registry, json.load(f), now=_now(argv))
        atomic_write_json(reg, registry)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if cmd == "record-defense":
        df, led, cor = _opt(argv, "--defense"), _opt(argv, "--ledger"), _opt(argv, "--corpus")
        if not (df and led and cor):
            sys.stderr.write(USAGE)
            return 2
        root = _opt(argv, "--root") or ROOT
        threats = threats_seed_to_list(_load(root, "threats.json", "threats.json"))
        with open(df, encoding="utf-8") as f:
            res = record_defense(json.load(f), led, cor, now=_now(argv), threats=threats)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["status"] in ("closed", "already_recorded") else 1

    if cmd == "ingest-threats":
        tf, led = _opt(argv, "--threats"), _opt(argv, "--ledger")
        if not (tf and led):
            sys.stderr.write(USAGE)
            return 2
        root = _opt(argv, "--root") or ROOT
        out = _opt(argv, "--out") or os.path.join(root, ".sisai", "threats.json")
        with open(tf, encoding="utf-8") as f:
            raw = json.load(f)
        raw_list = _threats_as_list(raw)
        seed = read_json(os.path.join(SEED, "threats.json"))
        res = ingest_threats(raw_list, out, led, now=_now(argv), seed_threats=seed)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["status"] in ("ingested", "noop") else 1

    sys.stderr.write(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
