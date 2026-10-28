"""Enforce the dependency rule from architecture.md: the engine imports only the stdlib."""

import ast
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[2] / "app" / "engine"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def test_engine_imports_only_standard_library_and_itself() -> None:
    violations: list[str] = []
    for path in ENGINE_DIR.rglob("*.py"):
        for module in imported_modules(path):
            root = module.split(".")[0]
            if root in sys.stdlib_module_names:
                continue
            if module == "app.engine" or module.startswith("app.engine."):
                continue
            violations.append(f"{path.relative_to(ENGINE_DIR)} imports {module}")
    assert violations == []
