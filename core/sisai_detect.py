#!/usr/bin/env python3
"""SISAI detection primitives — rule compile + pure scan + storage hygiene (stdlib, deterministic).

A detection rule is `{"patterns": [{"id","regex","desc"}, ...]}`. `scan` runs the compiled patterns
over a text (pure, no clock/AI/network). `is_inert_indicator` is STORAGE-SHAPE hygiene only — the
defensive-only guarantee is the deterministic boundary (core never executes collected text), not this
check (v1.4 R4). `blue_run` reports which malicious variants a detector fails to flag (loop input).

NOTE: regex from external authors is untrusted; `compile_rule` is exception-safe and length-bounds each
pattern. A full ReDoS execution-timeout sandbox remains the future hardening (re has no stdlib timeout).
"""

import re

from core.sisai_io import read_json, atomic_write_json

MAX_PATTERN_LEN = 400          # length sanity bound (a real timeout sandbox is the proper defense)
INERT_MAX_LEN = 240
LOOP_WRITABLE_SPLITS = ("tune", "adversarial")    # the loop may NEVER write split=holdout (frozen)


def is_inert_indicator(sample: dict) -> bool:
    """Storage hygiene: a stored sample is an inert, single-line, labeled DATA row of the corpus shape.
    NOT a weapon detector — defensive-only rests on the deterministic boundary, not on this check."""
    t = (sample or {}).get("text", "")
    return (isinstance(t, str) and 0 < len(t) <= INERT_MAX_LEN and "\n" not in t
            and (sample or {}).get("label") in ("malicious", "benign"))


def compile_rule(rule: dict):
    """Compile a rule's patterns to a list of compiled regexes. Returns (compiled, skipped):
    skipped counts patterns dropped as over-length or uncompilable (surfaced, never executed blindly)."""
    compiled, skipped = [], 0
    for p in (rule or {}).get("patterns", []) or []:
        src = (p or {}).get("regex")
        if not isinstance(src, str) or len(src) > MAX_PATTERN_LEN:
            skipped += 1
            continue
        try:
            compiled.append(re.compile(src))
        except re.error:
            skipped += 1
    return compiled, skipped


def scan(text: str, compiled) -> bool:
    """True if any compiled pattern matches the text. Pure; the text is DATA, never executed."""
    t = text if isinstance(text, str) else ""
    return any(rx.search(t) for rx in compiled)


def blue_run(compiled, variants) -> list:
    """Return the malicious-labeled variants the detector FAILS to flag (the misses the loop hardens on).
    Only inert, malicious-labeled rows are considered."""
    misses = []
    for v in variants or []:
        if v.get("label") == "malicious" and is_inert_indicator(v) and not scan(v.get("text", ""), compiled):
            misses.append(v)
    return misses


def atomic_append_samples(samples_path: str, rows: list) -> int:
    """STRUCTURAL author-disjointness (v1.2 binding guarantee): the adversarial loop MAY append only
    split in {tune, adversarial}; it can NEVER write split=holdout (the frozen, independently-sourced
    benchmark). Asserts split + inert hygiene, then atomic-merges. Returns rows appended.

    This is the mechanism that makes holdout independence structural rather than a label: there is simply
    no code path here that writes a holdout row. Raises ValueError on a violation (fail-closed)."""
    rows = list(rows or [])
    for r in rows:
        sp = r.get("split")
        if sp is not None and sp not in LOOP_WRITABLE_SPLITS:
            raise ValueError(f"atomic_append_samples: loop may not write split={sp!r} (holdout is frozen)")
        if not is_inert_indicator(r):
            raise ValueError("atomic_append_samples: non-inert sample row rejected")
    if not rows:
        return 0
    existing = read_json(samples_path) or []
    atomic_write_json(samples_path, existing + rows)
    return len(rows)
