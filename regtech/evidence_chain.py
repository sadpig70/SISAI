#!/usr/bin/env python3
"""SISAI B2-1 — RegTech evidence chain (EU AI Act, DRAFT; deterministic, defensive-only).

Maps regulatory requirements (Annex IV technical documentation) to the SISAI evidence actually present
in recorded state, and reports per-requirement coverage (covered / partial / gap) with provenance
enforced. Builds on the B1-2 audit evidence (`tools/audit_export.defense_evidence`) and stays a pure
function of (corpus, ledger, now): a tamper-evident `content_sha256` over the body makes the dossier
reproducible and time-independent.

IMPORTANT — this is a DRAFT skeleton, NOT a conformity assessment. The requirement registry and the
Annex IV mapping (`regtech/requirements.json`) require compliance/legal SME validation; the dossier
surfaces this in `review_status`. The deterministic engine is the contribution; regulatory
completeness is an explicit, gated SME task.

Provenance enforcement: a requirement is "covered" only when every required evidence kind is present
AND at least one satisfying evidence item is itself provenance-backed (lineage to source). Otherwise it
degrades to "partial" (some evidence) or "gap" (none).

CLI:
    python regtech/evidence_chain.py [--corpus .sisai/corpus.json] [--ledger .sisai/ledger.json]
        [--now YYYY-MM-DD] [--json]
"""

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from tools.audit_export import defense_evidence                       # noqa: E402

REQ_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.json")
REVIEW_STATUS = ("DRAFT — requires compliance/legal SME validation; this is NOT a conformity "
                 "assessment and makes no legal claim of EU AI Act compliance")
_PROVENANCE_LAYERS = ("channel", "external_source", "self_designed")


def load_requirements(path: str = None) -> list:
    return (read_json(path or REQ_PATH) or {}).get("requirements", [])


def evidence_index(corpus: list) -> dict:
    """Classify recorded defenses into regulatory evidence kinds -> sorted defense_ids. Deterministic."""
    idx = {}
    for d in corpus or []:
        ev = defense_evidence(d)
        did = ev.get("defense_id")
        if not did:
            continue
        if ev.get("artifact"):
            idx.setdefault("detection-rule", set()).add(did)
        if ev.get("has_verification"):
            idx.setdefault("verification-record", set()).add(did)
        if any((l or {}).get("layer") in _PROVENANCE_LAYERS for l in ev.get("lineage", [])):
            idx.setdefault("provenance-lineage", set()).add(did)
        if ev.get("covers_threat"):
            idx.setdefault("threat-coverage", set()).add(did)
    return {k: sorted(v) for k, v in idx.items()}


def map_requirement(req: dict, idx: dict) -> dict:
    """Decide a requirement's status against the evidence index, with provenance enforced."""
    required = req.get("required_evidence_kinds", []) or []
    missing = [k for k in required if not idx.get(k)]
    satisfied_by = sorted({did for k in required for did in idx.get(k, [])})
    prov_ids = set(idx.get("provenance-lineage", []))
    provenance_enforced = bool(set(satisfied_by) & prov_ids)
    if not missing and provenance_enforced:
        status = "covered"
    elif satisfied_by:
        status = "partial"
    else:
        status = "gap"
    return {"req_id": req.get("req_id"), "annex_iv_item": req.get("annex_iv_item"),
            "obligation": req.get("obligation"), "required_evidence_kinds": required,
            "status": status, "missing_kinds": missing, "satisfied_by": satisfied_by,
            "provenance_enforced": provenance_enforced, "retention_months": req.get("retention_months")}


def _content_hash(body) -> str:
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build_dossier(corpus: list, ledger: dict, now: str, requirements: list = None) -> dict:
    """Pure: recorded state -> deterministic, tamper-evident EU AI Act evidence dossier (DRAFT)."""
    reqs = requirements if requirements is not None else load_requirements()
    idx = evidence_index(corpus)
    mapped = sorted((map_requirement(r, idx) for r in reqs), key=lambda m: m.get("req_id") or "")
    cov = {"total": len(mapped),
           "covered": sum(1 for m in mapped if m["status"] == "covered"),
           "partial": sum(1 for m in mapped if m["status"] == "partial"),
           "gap": sum(1 for m in mapped if m["status"] == "gap")}
    cov["coverage_ratio"] = round(cov["covered"] / cov["total"], 4) if cov["total"] else 0.0
    body = {"framework": "EU-AI-Act", "requirements": mapped, "coverage": cov,
            "evidence_kinds_available": sorted(idx), "review_status": REVIEW_STATUS,
            "ledger_entries": len((ledger or {}).get("entries", []))}
    return {"report_kind": "sisai-regtech-dossier", "generated_at": now,
            "content_sha256": _content_hash(body), **body}


def render_md(dossier: dict) -> str:
    c = dossier["coverage"]
    lines = [f"# SISAI RegTech dossier — {dossier['framework']} ({dossier['generated_at']})", "",
             f"> {dossier['review_status']}", "",
             f"- content_sha256: `{dossier['content_sha256']}`",
             f"- coverage: {c['covered']}/{c['total']} covered "
             f"({c['partial']} partial, {c['gap']} gap)", "",
             "| req_id | Annex IV item | status | missing | provenance | retention(mo) |",
             "|---|---|---|---|---|---|"]
    for m in dossier["requirements"]:
        lines.append(f"| {m['req_id']} | {m['annex_iv_item']} | {m['status']} | "
                     f"{','.join(m['missing_kinds']) or '-'} | "
                     f"{'yes' if m['provenance_enforced'] else 'NO'} | {m['retention_months']} |")
    return "\n".join(lines) + "\n"


# ---- CLI ----------------------------------------------------------------------------------------

def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    corpus = read_json(_opt(argv, "--corpus") or os.path.join(ROOT, ".sisai", "corpus.json")) or []
    ledger = read_json(_opt(argv, "--ledger") or os.path.join(ROOT, ".sisai", "ledger.json")) or {}
    dossier = build_dossier(corpus, ledger, _opt(argv, "--now", "1970-01-01"))
    if "--json" in argv:
        print(json.dumps(dossier, ensure_ascii=False, indent=2))
    else:
        print(render_md(dossier))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
