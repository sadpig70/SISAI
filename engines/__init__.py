"""SISAI engine adapters — map native collected artifacts onto the backbone.

The AI runtime (skills) produces raw threat/defense/channel artifacts; these pure
stdlib adapters normalize them into the deterministic backbone shapes so the loop,
ledger, triage and provenance all read one canonical structure.
"""
