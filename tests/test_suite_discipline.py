"""The suite's own evidence discipline, mechanized (charter AC-5.4).

The repo rule: every test carries a one-line `proves:` docstring matched to
what it actually asserts. Until session 33 that rule was enforced by review
habit; this test makes it a standing fast-tier check, so a test landing
without its claim fails the gate instead of surviving until an audit samples
it. AST-based (no imports, no collection side effects), so it covers every
test function in tests/ including e2e-marked ones the gate deselects.
"""

import ast
from pathlib import Path

TESTS = Path(__file__).resolve().parent


def test_every_test_function_carries_a_proves_docstring():
    """proves: every function named test* in every tests/test_*.py carries a
    docstring containing 'proves:' — the AC-5.4 evidence discipline as a
    mechanized gate check, not a sampled convention."""
    missing = []
    total = 0
    for path in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test"):
                total += 1
                if "proves:" not in (ast.get_docstring(node) or ""):
                    missing.append(f"{path.name}:{node.lineno}:{node.name}")
    assert total > 0
    assert not missing, (
        f"{len(missing)}/{total} test functions lack a proves: docstring:\n"
        + "\n".join(missing))
