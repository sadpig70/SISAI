#!/usr/bin/env python3
"""SISAI structure & contract validator (stdlib only).

Checks that the self-contained layout is intact, the vendored engine skills are
present, and the seed artifacts satisfy the shipped JSON Schemas — without pulling
in any third-party dependency. Run in CI and before any loop turn.

CLI:
    python core/sisai_validate.py            # validate repo at cwd
    python core/sisai_validate.py <root>
"""

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
    root = argv[1] if len(argv) > 1 else "."
    print(f"=== SISAI validation (root: {os.path.abspath(root)}) ===")
    print(f"  - vendored skills: {', '.join(EXPECTED_SKILLS)}")
    print(f"  - schemas: {', '.join(SCHEMA_NAMES)}")
    problems = validate_project(root)
    if problems:
        print("\nFAIL — problems:")
        for p in problems:
            print(f"  * {p}")
        return 1
    print("\nPASS — SISAI structure + seed artifacts + contracts consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
