#!/usr/bin/env python3
"""SISAI structure & contract validator (stdlib only).

Checks that the self-contained layout is intact, the vendored engine skills are
present, and the seed artifacts satisfy the shipped JSON Schemas — without pulling
in any third-party dependency. Run in CI and before any loop turn.

CLI:
    python core/sisai_validate.py            # validate repo at cwd
    python core/sisai_validate.py <root>
"""

import hashlib
import json
import os
import sys

try:
    from .sisai_schema import validate_against_schema, schema_features, schema_path
    from .sisai_loop import next_action, VALID_ACTIONS
    from .sisai_triage import measure_coverage
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.sisai_schema import validate_against_schema, schema_features, schema_path
    from core.sisai_loop import next_action, VALID_ACTIONS
    from core.sisai_triage import measure_coverage

EXPECTED_FILES = [
    "core/sisai_fingerprint.py", "core/sisai_io.py", "core/sisai_schema.py",
    "core/sisai_channels.py", "core/sisai_ledger.py", "core/sisai_triage.py",
    "core/sisai_provenance.py", "core/sisai_loop.py", "core/sisai_validate.py",
    "engines/adapters.py", "sisai.py",
    "schemas/channel.schema.json", "schemas/threat.schema.json",
    "schemas/defense.schema.json", "schemas/ledger.schema.json",
    "schemas/loop-state.schema.json",
    "seed/channels.json", "seed/threats.json", "seed/defenses.json",
    "docs/ARCHITECTURE.md", "docs/SELF-DEFENSE.md", "README.md",
]

# vendored engine skills (self-contained; AI runtime is the execution engine)
EXPECTED_SKILLS = ["pg", "pgf", "pgxf"]

SCHEMA_NAMES = ("channel", "threat", "defense", "ledger", "loop-state")


def validate_layout(root: str) -> list:
    problems = []
    for rel in EXPECTED_FILES:
        if not os.path.exists(os.path.join(root, rel)):
            problems.append(f"missing file: {rel}")
    for name in EXPECTED_SKILLS:
        if not os.path.exists(os.path.join(root, "skills", name, "SKILL.md")):
            problems.append(f"missing vendored skill: skills/{name}/SKILL.md")
    return problems


def validate_schemas_in_subset(root: str) -> list:
    """Each shipped schema must stay within the stdlib walker subset (or jsonschema)."""
    try:
        import jsonschema  # noqa: F401
        return []
    except ImportError:
        pass
    problems = []
    for name in SCHEMA_NAMES:
        sp = schema_path(root, name)
        if not os.path.exists(sp):
            continue
        with open(sp, encoding="utf-8") as f:
            feats = schema_features(json.load(f))
        if not feats["in_subset"]:
            problems.append(f"{name}.schema unsupported keywords {feats['unsupported']} "
                            f"(jsonschema not installed)")
    return problems


def validate_seeds(root: str) -> list:
    """Seed channels/threats/defenses must satisfy their schemas."""
    problems = []
    chs = json.load(open(os.path.join(root, "seed", "channels.json"), encoding="utf-8"))
    for i, ch in enumerate(chs):
        problems += [f"seed channel[{i}]: {p}"
                     for p in validate_against_schema(ch, schema_path(root, "channel"))]
    threats = json.load(open(os.path.join(root, "seed", "threats.json"), encoding="utf-8"))["threats"]
    for i, t in enumerate(threats):
        # seed threats omit the generated threat_id/fingerprint; validate the human fields
        probe = dict(t)
        probe.setdefault("threat_id", f"SEED-{i}")
        problems += [f"seed threat[{i}]: {p}"
                     for p in validate_against_schema(probe, schema_path(root, "threat"))]
    defenses = json.load(open(os.path.join(root, "seed", "defenses.json"), encoding="utf-8"))["defenses"]
    for i, d in enumerate(defenses):
        probe = dict(d)
        probe.setdefault("defense_id", f"SEED-{i}")
        problems += [f"seed defense[{i}]: {p}"
                     for p in validate_against_schema(probe, schema_path(root, "defense"))]
    return problems


SKILL_MANIFEST = os.path.join("skills", "INTEGRITY.json")


def _skill_files(root: str) -> list:
    """All vendored skill files (sorted rel paths), excluding caches + the manifest."""
    base = os.path.join(root, "skills")
    out = []
    for dirpath, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc") or f == "INTEGRITY.json":
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, base).replace("\\", "/")
            out.append((rel, full))
    return sorted(out)


def compute_skill_manifest(root: str) -> dict:
    """sha256 of every vendored skill file — tamper-evidence for pg/pgf/pgxf.

    Line endings are normalized to LF before hashing so the manifest is stable across
    git autocrlf checkouts (an EOL flip is not tampering; a content change is).
    """
    man = {}
    for rel, full in _skill_files(root):
        with open(full, "rb") as fh:
            data = fh.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        man[rel] = hashlib.sha256(data).hexdigest()
    return man


def write_skill_manifest(root: str) -> tuple:
    """(Re)generate skills/INTEGRITY.json from current skill files. Git is the trust anchor."""
    man = compute_skill_manifest(root)
    path = os.path.join(root, SKILL_MANIFEST)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"algo": "sha256", "files": man}, f, ensure_ascii=False,
                  indent=1, sort_keys=True)
    os.replace(tmp, path)
    return path, len(man)


def validate_integrity(root: str) -> list:
    """Compare current skill files against the recorded manifest (tamper detection)."""
    path = os.path.join(root, SKILL_MANIFEST)
    if not os.path.exists(path):
        return [f"skill integrity: {SKILL_MANIFEST} missing (run --write-integrity)"]
    recorded = json.load(open(path, encoding="utf-8")).get("files", {})
    current = compute_skill_manifest(root)
    problems = []
    for rel, h in recorded.items():
        if rel not in current:
            problems.append(f"skill integrity: missing file skills/{rel}")
        elif current[rel] != h:
            problems.append(f"skill integrity: changed file skills/{rel}")
    for rel in current:
        if rel not in recorded:
            problems.append(f"skill integrity: untracked new file skills/{rel}")
    return problems


def _read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_live(root: str) -> list:
    """Validate runtime .sisai/ state (channels/ledger/corpus) — schema + semantic invariants.

    No-op (returns []) when .sisai/ is absent; the driver falls back to seed then.
    """
    problems = []
    sd = os.path.join(root, ".sisai")
    if not os.path.isdir(sd):
        return problems
    # channels registry: each channel item must satisfy channel.schema
    reg = _read_json(os.path.join(sd, "channels.json"))
    if isinstance(reg, dict):
        for i, ch in enumerate(reg.get("channels", [])):
            problems += [f"live channel[{i}]: {p}"
                         for p in validate_against_schema(ch, schema_path(root, "channel"))]
    # ledger: schema + every defense entry carries implementations (real assets only)
    led = _read_json(os.path.join(sd, "ledger.json"))
    if led is not None:
        problems += [f"live ledger: {p}"
                     for p in validate_against_schema(led, schema_path(root, "ledger"))]
        ledger_defense_ids = set()
        for e in led.get("entries", []):
            if e.get("kind") == "defense":
                ledger_defense_ids.add(e.get("entry_id"))
                if not e.get("implementations"):
                    problems.append(f"live ledger: defense {e.get('entry_id')} has no implementations")
        # corpus: each entry verified-only + must trace back to a recorded ledger defense
        cor = _read_json(os.path.join(sd, "corpus.json"))
        if isinstance(cor, list):
            for i, c in enumerate(cor):
                if not c.get("defense_id") or not c.get("title"):
                    problems.append(f"live corpus[{i}]: missing defense_id/title")
                elif c.get("defense_id") not in ledger_defense_ids:
                    problems.append(f"live corpus[{i}]: {c.get('defense_id')} not in ledger")
    return problems


def validate_project(root: str) -> list:
    problems = []
    problems += validate_layout(root)
    problems += validate_schemas_in_subset(root)
    problems += validate_seeds(root)
    # loop smoke (deterministic)
    a = next_action({"active_channels": 1, "untriaged_threats": 0})
    if a.get("action") not in VALID_ACTIONS:
        problems.append(f"loop smoke: invalid action {a.get('action')}")
    # coverage smoke
    rep = measure_coverage([{"category": "x"}, {"category": "y"}, {"category": "z"}])
    if "repair_required" not in rep:
        problems.append("coverage smoke: missing repair_required")
    return problems


def _main(argv) -> int:
    args = argv[1:]
    flags = [a for a in args if a.startswith("--")]
    positional = [a for a in args if not a.startswith("--")]
    root = positional[0] if positional else "."
    if "--write-integrity" in flags:
        path, n = write_skill_manifest(root)
        print(f"wrote {os.path.relpath(path, root)} ({n} skill files hashed)")
        return 0
    print(f"=== SISAI validation (root: {os.path.abspath(root)}) ===")
    print(f"  - vendored skills: {', '.join(EXPECTED_SKILLS)}")
    print(f"  - schemas: {', '.join(SCHEMA_NAMES)}")
    extra = [f for f in ("--integrity", "--live") if f in flags]
    if extra:
        print(f"  - extra checks: {', '.join(extra)}")
    problems = validate_project(root)
    if "--integrity" in flags:
        problems += validate_integrity(root)
    if "--live" in flags:
        problems += validate_live(root)
    if problems:
        print("\nFAIL — problems:")
        for p in problems:
            print(f"  * {p}")
        return 1
    print("\nPASS — SISAI structure + seed artifacts + contracts consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
