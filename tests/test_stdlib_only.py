"""Dependency guard: code that runs on the board imports only the Python standard library.

The UNO Q has no pip. Everything outside laptop/, dev/ and tests/ must import stdlib
modules (sqlite3 included) or our own packages. The App Lab app under app/ may also use
what App Lab's Python provides: arduino.* and numpy.
"""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAPTOP_ONLY = {"laptop", "dev", "tests", ".venv", ".git", "__pycache__", "node_modules"}
OURS = {"copilot", "explorer", "app"}
APP_LAB_PROVIDES = {"arduino", "numpy"}
# The one place outside app/ that may touch App Lab: the LED HAL's board backend, inside try/except
EXCEPTIONS = {os.path.join("copilot", "hal", "led.py"): {"arduino"}}


def board_files():
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in LAPTOP_ONLY and not d.startswith(".")]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(folder, name)


def imported_modules(path):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0], node.lineno
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0], node.lineno


class StdlibOnlyTest(unittest.TestCase):
    def test_board_code_imports_only_the_standard_library(self):
        self.assertTrue(hasattr(sys, "stdlib_module_names"), "needs Python 3.10+")
        offenders = []
        for path in board_files():
            rel = os.path.relpath(path, ROOT)
            allowed = set(sys.stdlib_module_names) | OURS
            if rel.split(os.sep)[0] == "app":
                allowed |= APP_LAB_PROVIDES
            allowed |= EXCEPTIONS.get(rel, set())
            for module, line in imported_modules(path):
                if module not in allowed:
                    offenders.append(f"{rel}:{line}: import {module}")
        self.assertEqual(offenders, [], "\nNot available on the board (no pip):\n  " + "\n  ".join(offenders))

    def test_guard_sees_the_copilot_package(self):
        files = [os.path.relpath(p, ROOT) for p in board_files()]
        self.assertIn(os.path.join("copilot", "pipeline.py"), files)
        self.assertIn("predict.py", files)
        self.assertNotIn(os.path.join("laptop", "prepare_m3kang.py"), files)


if __name__ == "__main__":
    unittest.main()
