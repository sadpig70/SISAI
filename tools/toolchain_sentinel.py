#!/usr/bin/env python3
"""SISAI B1-4 — AI Toolchain Integrity Sentinel / AIBOM (deterministic, defensive-only).

Watches the toolchain — dependencies, registries, install hooks, build artifacts, prompt-templates —
under one integrity scheme. Two layers, both reusing the backbone:

  1. Component provenance gate (core/sisai_provenance): a component is trusted ONLY when an isolated
     check supplies host-derived authority + a well-formed sha256 that MATCHES the lockfile pin. The
     manifest's own self-claimed provenance is STRIPPED first (anti fail-open: a manifest cannot
     self-certify), exactly like the threat-ingest gate. No isolated measurement => quarantine.
  2. Manifest text scan (tools/detect_pr, supply-chain-tampering bundle): flags risky directives
     (untrusted mirror, unpinned ref, curl|bash, dropped lockfile, ...) in manifest/CI text.

Verdicts: verified | quarantined (no isolated measurement; fail-closed) | rejected (untrusted host /
authority mismatch / malformed or mismatched sha256). The host whitelist is core's DOMAIN_AUTHORITY.

This is the runtime edge; the core it calls is pure. Output is an integrity report (data) — nothing
is installed, executed, or recorded.

CLI:
    python tools/toolchain_sentinel.py --components comps.json [--measured measured.json]
        [--manifest manifest.txt] [--json]
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_io import read_json                                     # noqa: E402
from core.sisai_provenance import is_provenance_verified, authority_from_url  # noqa: E402
from core.sisai_provenance import _SHA256_RE                           # noqa: E402
from tools.detect_pr import detect                                     # noqa: E402


def _verdict(name, kind, verdict, reason):
    return {"name": name, "component_kind": kind, "verdict": verdict, "reason": reason}


def assess_component(declared: dict, measured: dict = None) -> dict:
    """Assess one toolchain component. `declared` is the manifest/lockfile entry (self-claimed
    provenance is ignored). `measured` is the isolated checker's ground truth (host-derived) — absent
    => quarantine (fail-closed)."""
    name = (declared or {}).get("name")
    kind = (declared or {}).get("kind", "dependency")

    if not measured:                                  # anti fail-open: manifest can't self-certify
        return _verdict(name, kind, "quarantined", "no isolated verification (manifest cannot self-certify)")

    prov = {"source_url": measured.get("source_url", ""), "authority": measured.get("authority"),
            "source_sha256": measured.get("source_sha256", ""), "verified": measured.get("verified")}

    if not is_provenance_verified({"provenance": prov}):
        if authority_from_url(prov["source_url"]) is None:
            reason = "untrusted host (not in authority whitelist)"
        elif authority_from_url(prov["source_url"]) != prov["authority"]:
            reason = "authority does not match host-derived authority"
        elif not _SHA256_RE.match(prov["source_sha256"] or ""):
            reason = "malformed sha256"
        else:
            reason = "provenance not verified"
        return _verdict(name, kind, "rejected", reason)

    pinned = (declared or {}).get("pinned_sha256")
    if pinned and pinned != prov["source_sha256"]:
        return _verdict(name, kind, "rejected", "sha256 mismatch (artifact tampered or pin drift)")

    return _verdict(name, kind, "verified", "host-derived authority + sha256 verified")


def scan_manifest(text: str) -> list:
    """Risky supply-chain directives in manifest/CI text (reuses the B0-1 supply-chain bundle)."""
    return detect(text or "", categories=["supply-chain-tampering"])["matches"]


def assess(components: list, measured_map: dict = None, manifest_text: str = None) -> dict:
    """Assess a set of components + (optional) manifest text. Deterministic; output sorted by name."""
    measured_map = measured_map or {}
    results = sorted((assess_component(c, measured_map.get(c.get("name"))) for c in (components or [])),
                     key=lambda r: r.get("name") or "")
    counts = {"verified": 0, "quarantined": 0, "rejected": 0}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"components": results, "counts": counts,
            "all_verified": counts["verified"] == len(results) and len(results) > 0,
            "manifest_flags": scan_manifest(manifest_text) if manifest_text else []}


# ---- CLI ----------------------------------------------------------------------------------------

USAGE = ("usage:\n"
         "  python tools/toolchain_sentinel.py --components comps.json [--measured measured.json]\n"
         "      [--manifest manifest.txt] [--json]\n")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    cf = _opt(argv, "--components")
    if not cf:
        sys.stderr.write(USAGE)
        return 2
    components = read_json(cf) or []
    measured = read_json(_opt(argv, "--measured")) or {} if _opt(argv, "--measured") else {}
    manifest = None
    if _opt(argv, "--manifest"):
        with open(_opt(argv, "--manifest"), encoding="utf-8") as f:
            manifest = f.read()
    report = assess(components, measured, manifest)
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"verified={report['counts']['verified']} quarantined={report['counts']['quarantined']} "
              f"rejected={report['counts']['rejected']} | manifest_flags={len(report['manifest_flags'])}")
        for r in report["components"]:
            if r["verdict"] != "verified":
                print(f"  [{r['verdict']}] {r['name']}: {r['reason']}")
    return 0 if report["all_verified"] and not report["manifest_flags"] else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
