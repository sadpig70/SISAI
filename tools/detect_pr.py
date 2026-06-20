#!/usr/bin/env python3
"""SISAI B0-1 — PR/CI defense-weakening detector (CLI, deterministic, defensive-only).

Scans PR text / diffs / manifests for directives that WEAKEN security controls in three
families:
  - config-tampering        (disable WAF/TLS, bypass gate, skip scan/signature, ...)
  - supply-chain-tampering  (unpin/drop lockfile, pre/postinstall hook, untrusted mirror, ...)
  - access-control-weakening(public bucket, 0777, GRANT ALL, sudoers, open 0.0.0.0, RBAC off, ...)

Each family is a NEGATION-AWARE rule bundle: a shared `guard` (a `^(?!...)` lookahead over
prohibitive/negated phrasing — "never disable", "forbidden", "must remain", ...) is composed
in front of every malicious `indicator`, so defensive prose that merely *mentions* a control
is not flagged. Detection reuses the pure backbone primitives `core/sisai_detect.compile_rule`
+ `scan`; this file is the CLI edge (it reads argv/files) and lives OUTSIDE the deterministic
boundary on purpose.

defensive-only: the output is a VERDICT (data) — a list of which patterns matched and why.
Matched text is never elevated to an instruction; the tool only flags and explains. It emits
no remediation that disables controls and runs no collected text.

One indicator -> one composed pattern (kept well under MAX_PATTERN_LEN) so `compile_rule`
reports skipped=0 for the shipped bundles (ReDoS length-bound respected).

CLI:
    python tools/detect_pr.py --text "Disable the WAF for this release."
    python tools/detect_pr.py --file pr_body.txt [--category supply-chain-tampering] [--json]
Exit code: 1 if any pattern flags the input, else 0 (2 on usage error).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.sisai_detect import compile_rule, scan                       # noqa: E402

# ---- Negation-aware rule bundles ----------------------------------------------------------------
# A bundle = {guard, indicators[]}. The composed pattern for each indicator is:
#     guard + r".*(?:" + indicator.regex + r")"
# so the negation lookahead applies to EVERY alternative (alternation is always grouped).

RULE_BUNDLES = {
    "config-tampering": {
        "guard": r"(?i)^(?!.*\b(?:never|cannot|must|prohibited|forbidden|only|always\s+remain|remain\s+enabled)\b)",
        "indicators": [
            {"id": "ct.disable", "desc": "imperative to disable/turn-off/bypass/weaken a control",
             "regex": r"\b(?:disable|deactivate|turn\s+off|switch\s+off|bypass|comment\s+out|neutralize|loosen|weaken)\b"},
            {"id": "ct.verify-ssl-off", "desc": "set verify_ssl=false (skip certificate checks)",
             "regex": r"verify_ssl\s*=\s*false"},
            {"id": "ct.skip-check", "desc": "skip/remove/drop a scan, checksum, validation or signature step",
             "regex": r"\b(?:skip|remove|drop)\b.{0,30}\b(?:scan|checksum|validation|verification|signature)\b"},
        ],
    },
    "supply-chain-tampering": {
        "guard": r"(?i)^(?!.*\b(?:never|must|forbidden|prohibited|blocked|block|immutable|only|reviewed|verified|audited|denied|rejected|require|requires|committed)\b)",
        "indicators": [
            {"id": "sc.pastebin", "desc": "fetch code from a pastebin/gist/paste service",
             "regex": r"\b(?:pastebin|gist|paste\s+service)\b"},
            {"id": "sc.fetch-exec", "desc": "fetch/run/pull/grab an unvetted script or binary at build time",
             "regex": r"\b(?:fetch|run|execute|download|sideload|pull|grab)\w*\b.{0,40}\b(?:script|installer|helper|setup\.sh|binary|blob|wheel|bootstrap)\b"},
            {"id": "sc.unpin", "desc": "use a moving/mutable/latest ref or unpin instead of a pin",
             "regex": r"\b(?:moving\s+main|mutable\s+tag|latest\s+tag)\b|\bunpin\w*\b|\bfloat\b.{0,20}\b(?:newest|latest)\b"},
            {"id": "sc.swap-pin", "desc": "swap/replace a pinned commit for a moving reference",
             "regex": r"\b(?:swap|replace)\b.{0,30}\bpinned\b"},
            {"id": "sc.drop-lock", "desc": "drop/delete/remove/wipe a lockfile",
             "regex": r"\b(?:drop|delete|remove|wipe)\b.{0,30}lock"},
            {"id": "sc.install-hook", "desc": "wire a pre/postinstall hook",
             "regex": r"\b(?:pre|post)install\s+hook\b"},
            {"id": "sc.unsafe-flag", "desc": "install flag that weakens integrity (index-url/trusted-host/no-audit/...)",
             "regex": r"--index-url\b|--trusted-host\b|--allow-unauthenticated\b|--no-audit\b|--no-package-lock\b"},
            {"id": "sc.untrusted-mirror", "desc": "pull from an unverified/unofficial mirror",
             "regex": r"\b(?:unverified|unofficial)\s+mirror\b"},
            {"id": "sc.skip-integrity", "desc": "skip/turn-off/disable a checksum/audit/integrity/verification step",
             "regex": r"\b(?:skip|turn\s+off|disable)\b.{0,30}\b(?:checksum|audit|integrity|verification)\b"},
            {"id": "sc.goflags", "desc": "GOFLAGS used to bypass the module checksum database",
             "regex": r"\bgoflags\b"},
            {"id": "sc.typosquat", "desc": "source a typosquatted package name",
             "regex": r"\b(?:typosquat|typosquatted)\b"},
            {"id": "sc.curl-bash", "desc": "curl piped to a shell",
             "regex": r"curl\s+\S+\s*\|\s*(?:ba)?sh\b"},
        ],
    },
    "access-control-weakening": {
        "guard": r"(?i)^(?!.*\b(?:never|must|denied|deny|rejected|forbidden|prohibited|enforced|pinned|blocked|restricted|only|private|require|requires|limited|reviewed|approval|approved|least)\b)",
        "indicators": [
            {"id": "ac.public", "desc": "make a resource public / publicly readable / anyone can read",
             "regex": r"\bvisibility\s+to\s+public\b|\bpublic-read\b|\bpublicly\s+readable\b|\bmake\b.{0,30}\bpublic\b|\bloosen\b.{0,30}\bacl\b|\banyone\s+can\s+read\b"},
            {"id": "ac.world-perms", "desc": "world-writable file mode (0777 / chmod 777)",
             "regex": r"\b0777\b|\bchmod\s+777\b|\bworld-?writable\b"},
            {"id": "ac.broad-grant", "desc": "grant admin/superuser to all / elevate everyone / cluster-admin",
             "regex": r"\bsuperuser\b.{0,30}\b(?:all|every|everyone)\b|\badmin\w*\b.{0,30}\b(?:all|every|everyone)\b|\belevate\b.{0,25}\b(?:everyone|all)\b|\beveryone\s+to\s+admin\w*|\bcluster-admin\b"},
            {"id": "ac.cors-wildcard", "desc": "allow/permit any/all origins / CORS wildcard",
             "regex": r"\b(?:allow|permit)\s+(?:any|all)\s+origins?\b|allow-origin:\s*\*|\bcors\b.{0,30}\*|\bwildcard\b"},
            {"id": "ac.sudoers", "desc": "append to sudoers / NOPASSWD",
             "regex": r"\bsudoers\b|\bnopasswd\b"},
            {"id": "ac.grant-all", "desc": "GRANT ALL privileges",
             "regex": r"\bgrant\s+all\b"},
            {"id": "ac.rbac-off", "desc": "disable the RBAC check",
             "regex": r"\bdisable\b.{0,20}\brbac\b|\brbac\s+check\b"},
            {"id": "ac.open-expose", "desc": "expose on 0.0.0.0 / all interfaces / turn auth off / no auth",
             "regex": r"\b0\.0\.0\.0\b|\ball\s+interfaces\b|\bauth\s+(?:turned\s+off|off)\b|\bno\s+auth(?:entication)?\b|without\s+(?:any\s+)?auth(?:entication)?\b"},
        ],
    },
}


def _compose(bundle: dict) -> dict:
    """Build a sisai_detect rule {patterns:[...]} from a bundle: guard + grouped indicator."""
    guard = bundle.get("guard", "")
    patterns = []
    for ind in bundle.get("indicators", []):
        patterns.append({"id": ind["id"], "desc": ind.get("desc", ""),
                         "regex": guard + r".*(?:" + ind["regex"] + r")"})
    return {"patterns": patterns}


def compile_bundle(category: str):
    """Compile a category's bundle. Returns (compiled, skipped, patterns_meta).
    skipped should be 0 for the shipped bundles (length-bounded, valid regex)."""
    bundle = RULE_BUNDLES[category]
    rule = _compose(bundle)
    compiled, skipped = compile_rule(rule)
    return compiled, skipped, rule["patterns"]


def predict_for(category: str):
    """Return a pure predictor text->bool for one category (drives verify_suite)."""
    compiled, _, _ = compile_bundle(category)
    return lambda text: scan(text, compiled)


def detect(text: str, categories=None) -> dict:
    """Scan `text` for defense-weakening directives. Returns a VERDICT (data only):
        {flagged: bool, matches: [{category, id, desc}], categories_scanned: [...], skipped: int}
    Matched text is reported, never executed or promoted to an instruction (defensive-only)."""
    cats = list(categories) if categories else list(RULE_BUNDLES.keys())
    matches, total_skipped = [], 0
    for cat in cats:
        bundle = RULE_BUNDLES[cat]
        for ind in bundle.get("indicators", []):
            compiled, skipped = compile_rule(
                {"patterns": [{"id": ind["id"],
                               "regex": bundle["guard"] + r".*(?:" + ind["regex"] + r")"}]})
            total_skipped += skipped
            if compiled and scan(text, compiled):
                matches.append({"category": cat, "id": ind["id"], "desc": ind.get("desc", "")})
    return {"flagged": bool(matches), "matches": matches,
            "categories_scanned": cats, "skipped": total_skipped}


# ---- CLI ----------------------------------------------------------------------------------------

USAGE = ("usage:\n"
         "  python tools/detect_pr.py --text \"<pr text>\" [--category <cat>] [--json]\n"
         "  python tools/detect_pr.py --file <path>      [--category <cat>] [--json]\n"
         f"  categories: {', '.join(RULE_BUNDLES.keys())} (default: all)\n")


def _opt(argv, name, default=None):
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
    return default


def _main(argv) -> int:
    text = _opt(argv, "--text")
    path = _opt(argv, "--file")
    if path and text is None:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    if text is None:
        sys.stderr.write(USAGE)
        return 2
    cat = _opt(argv, "--category")
    if cat is not None and cat not in RULE_BUNDLES:
        sys.stderr.write(f"unknown category: {cat}\n{USAGE}")
        return 2
    verdict = detect(text, [cat] if cat else None)
    if "--json" in argv:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
    else:
        if verdict["flagged"]:
            print("FLAGGED — defense-weakening directive(s) detected:")
            for m in verdict["matches"]:
                print(f"  [{m['category']}] {m['id']}: {m['desc']}")
        else:
            print("clean — no defense-weakening directive matched.")
    return 1 if verdict["flagged"] else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
