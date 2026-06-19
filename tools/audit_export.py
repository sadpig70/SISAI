#!/usr/bin/env python3
"""SISAI B1-2 — GRC / audit evidence exporter (deterministic, tamper-evident, defensive-only).

Turns recorded SISAI state (defense corpus + reuse ledger) into an auditable evidence report: for
every recorded defense, its threat->defense->source->verification lineage, its fingerprint
(defense_id), and the verification basis that let it into the corpus. Reuses
`core/sisai_provenance.trace_defense` for lineage and `core/sisai_io` for atomic, deterministic I/O.

Reproducible: `build_report` is a pure function of (corpus, ledger, now) — the same state yields a
byte-identical report. A `content_sha256` is computed over the EVIDENCE BODY ONLY (excluding the
generation timestamp), so the hash is tamper-evident AND independent of WHEN the report was produced:
re-exporting unchanged state always yields the same content hash.

The EU AI Act Annex IV mapping is a DRAFT: it maps SISAI evidence types to technical-documentation
items, but coverage completeness requires compliance-SME review (an honest gap, surfaced in the report).

CLI:
    python tools/audit_export.py [--corpus .sisai/corpus.json] [--ledger .sisai/ledger.json]
        [--now YYYY-MM-DD] [--json] [--md out.md]
"""

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                    # noqa: E402
from core.sisai_provenance import trace_defense                       # noqa: E402

# EU AI Act Annex IV (technical documentation) — DRAFT mapping to SISAI evidence. Completeness is
# NOT claimed; each item still needs compliance-SME confirmation (recorded as mapping_status).
ANNEX_IV_MAPPING = [
    {"annex_iv_item": "2(b) design specifications & logic",
     "sisai_evidence": "defense rules + lineage (threat->defense->source)"},
    {"annex_iv_item": "2(g) validation & testing procedures",
     "sisai_evidence": "verification gate (recall/precision on frozen holdout)"},
    {"annex_iv_item": "3 monitoring, functioning & control",
     "sisai_evidence": "control-drift monitor + reuse ledger"},
    {"annex_iv_item": "4 risk management system",
     "sisai_evidence": "threat triage + coverage signals"},
    {"annex_iv_item": "5 post-market changes through lifecycle",
     "sisai_evidence": "ledger recorded_at history + defense corpus versions"},
    {"annex_iv_item": "6 provenance & data governance",
     "sisai_evidence": "provenance gate (host-derived authority + sha256)"},
]
MAPPING_STATUS = "draft — requires compliance-SME review for Annex IV completeness"


def defense_evidence(defense: dict) -> dict:
    """One auditable evidence record for a corpus defense (deterministic; keys sorted on dump)."""
    lineage = defense.get("lineage") or trace_defense(defense)
    verification = [l.get("id") for l in lineage if l.get("layer") == "verification"]
    return {
        "defense_id": defense.get("defense_id"),
        "fingerprint": defense.get("fingerprint") or defense.get("defense_id"),
        "title": defense.get("title"),
        "kind": defense.get("kind"),
        "covers_threat": defense.get("covers_threat"),
        "controls": sorted(defense.get("controls", []) or []),
        "artifact": defense.get("artifact"),
        "lineage": lineage,
        "verification": verification,
        "has_lineage": bool(lineage),
        "has_fingerprint": bool(defense.get("defense_id") or defense.get("fingerprint")),
        "has_verification": bool(verification),
    }


def _content_hash(body) -> str:
    """sha256 over the evidence body with sorted keys (stable, timestamp-independent)."""
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build_report(corpus: list, ledger: dict, now: str) -> dict:
    """Pure: recorded state -> deterministic, tamper-evident audit evidence report."""
    defenses = sorted((defense_evidence(d) for d in (corpus or [])),
                      key=lambda e: (e.get("defense_id") or "", e.get("title") or ""))
    completeness = {
        "total_defenses": len(defenses),
        "with_lineage": sum(1 for d in defenses if d["has_lineage"]),
        "with_fingerprint": sum(1 for d in defenses if d["has_fingerprint"]),
        "with_verification": sum(1 for d in defenses if d["has_verification"]),
        "fully_evidenced": sum(1 for d in defenses
                               if d["has_lineage"] and d["has_fingerprint"] and d["has_verification"]),
        "ledger_entries": len((ledger or {}).get("entries", [])),
    }
    body = {"defenses": defenses, "completeness": completeness,
            "annex_iv_mapping": ANNEX_IV_MAPPING, "annex_iv_mapping_status": MAPPING_STATUS}
    return {"report_kind": "sisai-audit-evidence", "generated_at": now,
            "content_sha256": _content_hash(body), **body}


def render_md(report: dict) -> str:
    lines = [f"# SISAI audit evidence ({report['generated_at']})", "",
             f"- content_sha256: `{report['content_sha256']}`",
             f"- defenses: {report['completeness']['fully_evidenced']}/"
             f"{report['completeness']['total_defenses']} fully evidenced "
             f"(lineage + fingerprint + verification)",
             f"- ledger entries: {report['completeness']['ledger_entries']}", "",
             "## Defenses", "",
             "| defense_id | title | covers_threat | lineage | verification |",
             "|---|---|---|---|---|"]
    for d in report["defenses"]:
        lines.append(f"| {d['defense_id']} | {d['title']} | {d['covers_threat']} | "
                     f"{len(d['lineage'])} layers | {'yes' if d['has_verification'] else 'MISSING'} |")
    lines += ["", "## EU AI Act Annex IV mapping (draft)", "",
              f"> {report['annex_iv_mapping_status']}", "",
              "| Annex IV item | SISAI evidence |", "|---|---|"]
    for m in report["annex_iv_mapping"]:
        lines.append(f"| {m['annex_iv_item']} | {m['sisai_evidence']} |")
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
    report = build_report(corpus, ledger, _opt(argv, "--now", "1970-01-01"))
    md_out = _opt(argv, "--md")
    if md_out:
        with open(md_out, "w", encoding="utf-8") as f:
            f.write(render_md(report))
    if "--json" in argv or not md_out:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_md(report))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
