#!/usr/bin/env python3
"""Fleet integration — every catalogued PoC module imports, exposes a CLI entry, and (for detectors)
passes its frozen-holdout gate. A single regression entrypoint guarding the whole tool fleet against
drift, cross-checked with docs/TOOLS-CATALOG.md.
"""
import importlib
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# every shipped module that exposes a CLI _main
CLI_MODULES = [
    "tools.detect", "tools.detect_pr", "tools.policy_compile", "tools.control_drift", "tools.benchmark_harness",
    "tools.prompt_shield", "tools.audit_export", "tools.soc_cluster", "tools.toolchain_sentinel",
    "calibration.score", "calibration.robustness", "calibration.battery", "calibration.independence",
    "calibration.independent_eval", "calibration.semantic_ingest", "labs.defense_rule_lab.grade_rule",
    "regtech.evidence_chain", "domain.fraud_aml", "domain.trust_safety", "domain.pharmacovigilance",
]

# detectors that expose a gate() over a frozen holdout (prompt_shield is graded via verify_suite in
# its own test, not a gate() method)
GATED = ["domain.fraud_aml", "domain.trust_safety", "domain.pharmacovigilance"]


class TestFleetImportsAndCli(unittest.TestCase):
    def test_all_modules_import_and_expose_main(self):
        for name in CLI_MODULES:
            mod = importlib.import_module(name)
            self.assertTrue(hasattr(mod, "_main"), f"{name} missing CLI _main")
            rc = mod._main([name])                          # runs without crashing (usage error or default)
            self.assertIsInstance(rc, int, f"{name} _main must return an int exit code")


class TestDetectorGates(unittest.TestCase):
    def test_detect_pr_bundles_all_gate(self):
        from tools import detect_pr as dp
        from core.sisai_io import read_json
        from core import sisai_verify as ver
        samples = read_json(os.path.join(ROOT, "seed", "sample-suite.json"))
        for cat in dp.RULE_BUNDLES:
            sub = [s for s in samples if s.get("category") == cat]
            self.assertTrue(ver.verify_suite(sub, dp.predict_for(cat))["passed"], cat)

    def test_gated_detectors_pass(self):
        for name in GATED:
            mod = importlib.import_module(name)
            self.assertTrue(mod.gate()["passed"], f"{name} holdout gate failed")


class TestCatalogDocCoversFleet(unittest.TestCase):
    def test_catalog_lists_every_module(self):
        with open(os.path.join(ROOT, "docs", "TOOLS-CATALOG.md"), encoding="utf-8") as f:
            doc = f.read()
        for name in CLI_MODULES:
            # the catalog references each module by its file path (e.g. tools/detect_pr.py or labs/defense_rule_lab/)
            path_hint = name.rsplit(".", 1)[0].replace(".", "/") if name.startswith("labs.") else name.replace(".", "/")
            self.assertIn(path_hint, doc, f"{name} ({path_hint}) not documented in TOOLS-CATALOG.md")


if __name__ == "__main__":
    unittest.main()
