"""SISAI-Core — deterministic shared backbone (stdlib only).

Single source of truth for the security self-improvement machinery: identity
fingerprints, the self-expanding channel registry, the reuse ledger, attack-surface
coverage + triage, threat->defense provenance with corpus feedback, and the
three-strand loop driver.

Determinism boundary: everything here is pure, stdlib-only, free of
clock/network/AI/random. Time is injected (`now`). Collected external text can never
alter control flow here — that is the first line of prompt-injection defense.
No dependency on HELIX or any external project: SISAI is fully self-contained.
"""

from .sisai_fingerprint import (
    normalize_name, tokenize_name,
    channel_fingerprint, threat_fingerprint, defense_fingerprint,
)
from .sisai_io import atomic_write_json, read_json
from .sisai_schema import validate_against_schema, schema_features, schema_path
from .sisai_channels import (
    empty_registry, register_channel, active_channels, kind_coverage,
    should_discover_channels, missing_kinds, next_channels_to_scan, CHANNEL_KINDS,
)
from .sisai_ledger import (
    empty_ledger, is_consumed, append_entry, reindex_ledger,
)
from .sisai_triage import (
    triage_score, rank_threats, top_threat, measure_coverage, least_covered_category,
)
from .sisai_provenance import trace_defense, is_verified, defense_to_corpus_entry
from .sisai_loop import next_action, plan_defense, match_external_defense, VALID_ACTIONS

__all__ = [
    "normalize_name", "tokenize_name",
    "channel_fingerprint", "threat_fingerprint", "defense_fingerprint",
    "atomic_write_json", "read_json",
    "validate_against_schema", "schema_features", "schema_path",
    "empty_registry", "register_channel", "active_channels", "kind_coverage",
    "should_discover_channels", "missing_kinds", "next_channels_to_scan", "CHANNEL_KINDS",
    "empty_ledger", "is_consumed", "append_entry", "reindex_ledger",
    "triage_score", "rank_threats", "top_threat", "measure_coverage", "least_covered_category",
    "trace_defense", "is_verified", "defense_to_corpus_entry",
    "next_action", "plan_defense", "match_external_defense", "VALID_ACTIONS",
]
