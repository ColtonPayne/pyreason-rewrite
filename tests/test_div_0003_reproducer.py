"""DIV-0003's pin-side reproducer (e2e: needs the live oracle env).

The record: docs/divergences/DIV-0003.md. On the fp schedule
(settings.fp_version=True) an infer_edges rule that re-derives an edge it
inferred at an earlier timestep looks up the edge's world in that
timestep's per-timestep dict, which never carries existing edges forward —
the numba typed-dict getitem raises the PAYLOAD-LESS KeyError()
(dictobject.py:778 in the oracle env) out of fp reason(), so `str(exc)` is
empty and the traceback's final line is bare `KeyError`. The rewrite, per
the operator's 2026-07-11 batch adjudication of item B17 (recorded
direction: DIV-0002's shape — same seam, same type, honest stable
message), raises KeyError at the same `_add_edge` existing-edge branch
with a stable message naming the edge and timestep (the fast-tier twin:
tests/test_rewrite_reasoning_core.py::
test_fp_infer_edges_rederivation_raises_the_adjudicated_stable_keyerror).
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ORACLE_PY = REPO / "oracle-env" / "bin" / "python"

PIN_SCRIPT = """
import networkx as nx
import pyreason as pr
pr.settings.verbose = False
pr.settings.atom_trace = True
pr.settings.fp_version = True
g = nx.DiGraph()
g.add_node('A', p=1)
g.add_node('B', q=1)
pr.load_graph(g)
pr.add_rule(pr.Rule('Linked(X, Y) <- p(X), q(Y)', 'r1', True))
pr.add_fact(pr.Fact('p(A) : [1, 1]', 'f1', 0, 2))
pr.add_fact(pr.Fact('q(B) : [1, 1]', 'f2', 0, 2))
interp = pr.reason(timesteps=2)
print("COMPLETED")
"""


@pytest.mark.e2e
def test_pinned_fp_infer_edges_rederivation_raises_payloadless_keyerror(tmp_path):
    """proves: at the pin, fp_version + an infer_edges rule whose inferred
    edge is re-derived at a later timestep raises builtins.KeyError with NO
    payload (the numba typed-dict getitem erases the key: the traceback's
    final line is bare 'KeyError', never 'KeyError: ...'), never reaching
    COMPLETED — the pin-side half of DIV-0003 (adjudicated: the rewrite
    raises the same type at the same seam with the stable, honest message
    the pin's payload-less raise cannot carry)."""
    result = subprocess.run(
        [str(ORACLE_PY), "-c", PIN_SCRIPT],
        cwd=tmp_path, capture_output=True, text=True, timeout=600)
    assert result.returncode != 0
    assert "COMPLETED" not in result.stdout
    lines = [l for l in result.stderr.splitlines() if l.strip()]
    assert lines[-1] == "KeyError"  # payload-less: no 'KeyError: ...' text
    assert re.search(r"raise KeyError\(\)", result.stderr)  # the typed-dict arm
