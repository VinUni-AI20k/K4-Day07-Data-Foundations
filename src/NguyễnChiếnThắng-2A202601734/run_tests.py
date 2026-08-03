"""Run the shared test suite against this student's personal package."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path


PERSONAL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PERSONAL_DIR.parents[1]
PACKAGE_NAME = "personal_solution"


def load_personal_package():
    init_file = PERSONAL_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        init_file,
        submodule_search_locations=[str(PERSONAL_DIR)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the personal package")
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = package
    spec.loader.exec_module(package)
    return package


def main() -> int:
    sys.path.insert(0, str(PROJECT_DIR))
    load_personal_package()
    os.environ["LAB_SOLUTION_PACKAGE"] = PACKAGE_NAME

    test_path = PROJECT_DIR / "tests" / "test_solution.py"
    test_module = types.ModuleType("personal_tests")
    test_module.__file__ = str(test_path)
    sys.modules[test_module.__name__] = test_module
    exec(compile(test_path.read_text(encoding="utf-8"), str(test_path), "exec"), test_module.__dict__)

    suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
