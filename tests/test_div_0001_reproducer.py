"""DIV-0001's pin-side reproducer (e2e: needs the live oracle env).

The record: docs/divergences/DIV-0001.md. A query matching a self-recursive
rule's head drives the pinned filter_ruleset's unguarded recursion through
the clause targets until the process dies (C-stack exhaustion before
Python's RecursionError can surface — no artifact, so no harness case can
bank it). The rewrite deliberately terminates instead (the seam test
tests/test_rewrite_output_surface.py::test_filter_ruleset_terminates_on_
self_recursive_rule); this test is the failing-against-the-pin half of the
pair AC-6 asks an intentional divergence to carry.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ORACLE_PY = REPO / "oracle-env" / "bin" / "python"

PIN_SCRIPT = """
import networkx as nx
import pyreason as pr
from pyreason import Rule, Fact, Query

pr.settings.verbose = False
g = nx.DiGraph()
g.add_edge("John", "Mary", Friends=1)
pr.load_graph(g)
pr.add_rule(Rule("popular(x) <-1 popular(y), Friends(x,y)", "self_rule"))
pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
pr.reason(timesteps=2, queries=[Query("popular(John)")])
print("COMPLETED")
"""


@pytest.mark.e2e
def test_pinned_filter_ruleset_dies_on_self_recursive_query_match(tmp_path):
    """proves: at the pin, reason(queries=[...]) on a query matching a
    self-recursive rule's head kills the engine process outright (nonzero
    death with no Python traceback text reaching stdout's COMPLETED marker
    — the unguarded filter_ruleset recursion, filter_ruleset.py:22-24),
    which is the behavior DIV-0001 records the rewrite deliberately
    diverging from."""
    result = subprocess.run(
        [str(ORACLE_PY), "-c", PIN_SCRIPT], cwd=tmp_path,
        capture_output=True, text=True, timeout=600)
    assert result.returncode != 0
    assert "COMPLETED" not in result.stdout
