#!/usr/bin/env python3
"""DeterminismGuard (v1.4) — the deterministic boundary is the first line of injection defense.

core/ AND engines/ must be pure: no clock/RNG/network/subprocess imports (incl. `import x as y`
aliases), no os.urandom/os.system/os.popen attribute calls, and no `AI_` cognition symbols in core/.
Enforced by AST scan over the real source — collected text can never become control flow here.
"""
import ast
import glob
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_IMPORTS = {"time", "datetime", "random", "secrets", "socket", "urllib",
                     "requests", "http", "ftplib", "subprocess", "asyncio"}
FORBIDDEN_ATTRS = {("os", "urandom"), ("os", "system"), ("os", "popen")}


def _top(name: str) -> str:
    return (name or "").split(".")[0]


def _imported_top_modules(tree):
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(_top(a.name))          # resolves `import x as y` (uses real module, not alias)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mods.add(_top(node.module))
    return mods


def _attr_calls(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            found.add((node.value.id, node.attr))
    return found


def _symbols(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


class TestDeterminismBoundary(unittest.TestCase):
    def _files(self):
        fs = glob.glob(os.path.join(ROOT, "core", "*.py")) + glob.glob(os.path.join(ROOT, "engines", "*.py"))
        self.assertTrue(fs, "no core/engines source found")
        return fs

    def test_no_forbidden_imports(self):
        for f in self._files():
            with open(f, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            bad = _imported_top_modules(tree) & FORBIDDEN_IMPORTS
            self.assertFalse(bad, f"{os.path.relpath(f, ROOT)} imports forbidden {sorted(bad)}")

    def test_no_forbidden_attr_calls(self):
        for f in self._files():
            with open(f, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            bad = _attr_calls(tree) & FORBIDDEN_ATTRS
            self.assertFalse(bad, f"{os.path.relpath(f, ROOT)} calls forbidden {sorted(bad)}")

    def test_no_ai_symbols_in_core(self):
        for f in glob.glob(os.path.join(ROOT, "core", "*.py")):
            with open(f, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            ai = {s for s in _symbols(tree) if s.startswith("AI_")}
            self.assertFalse(ai, f"{os.path.relpath(f, ROOT)} has cognition symbols {sorted(ai)} in core/")


if __name__ == "__main__":
    unittest.main()
