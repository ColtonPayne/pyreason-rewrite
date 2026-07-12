"""Deterministic generator for the AC-4 workload-ladder graph fixtures.

Writes `harness/fixtures/perf-ladder-{small,medium,large}.graphml` — one
committed GraphML fixture per ladder rung (rationale for the rung sizes:
docs/perf/ladder.md). Stdlib-only and fully seeded: every byte of every
fixture is a pure function of the RUNGS table below, so `uv run python
tools/gen_perf_fixtures.py` regenerates the committed files identically
(the script fails loudly if a fixture on disk differs from what it would
write, unless --write is passed). No randomness survives to measure time:
the fixtures are committed artifacts, and both the equivalence harness and
the benchmark runner consume the same files.

Graph shape per rung (matching the committed chain-ab.graphml GraphML
dialect so the pinned loader's proven happy path is the one exercised):

- Nodes `n0000`..`n{N-1}` (zero-padded, width 4), no node attributes.
- A ring backbone `n_i -> n_(i+1) mod N`, relation label cycling
  rel0/rel1/rel2 with i — guarantees the graph is connected and every
  relation label reaches every neighborhood, so the rule chain in the
  ladder cases derives at every tier (screened non-empty at authoring).
- `edges - N` extra random directed edges (seeded `random.Random`, no
  self-loops, no duplicate (source, target) pairs — a DiGraph would merge
  them silently), relation label drawn uniformly from rel0/rel1/rel2.
- Every edge carries exactly one relation attribute with value 1 (long) —
  the in-range coercion arm the graph-attribute ladder proved equivalent;
  attribute values other than 1 are deliberately out of scope here.
"""

import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "harness" / "fixtures"

RELS = ("rel0", "rel1", "rel2")

# rung -> (nodes, edges, seed). Edge counts include the N-edge ring backbone.
# Sizes are the committed ladder design — change them only with a matching
# docs/perf/ladder.md rationale edit and a regeneration of the fixtures.
RUNGS = {
    "small": (50, 150, 20260711),
    "medium": (400, 2400, 20260712),
    "large": (1000, 6000, 20260713),
}


def node_name(i: int) -> str:
    return f"n{i:04d}"


def build_edges(n_nodes: int, n_edges: int, seed: int) -> list:
    """The rung's edge list as (source, target, rel) — ring first, then
    seeded random extras; deterministic for a given (n_nodes, n_edges, seed)."""
    rng = random.Random(seed)
    edges = []
    seen = set()
    for i in range(n_nodes):
        pair = (node_name(i), node_name((i + 1) % n_nodes))
        edges.append((*pair, RELS[i % len(RELS)]))
        seen.add(pair)
    while len(edges) < n_edges:
        src = rng.randrange(n_nodes)
        dst = rng.randrange(n_nodes)
        pair = (node_name(src), node_name(dst))
        if src == dst or pair in seen:
            continue
        seen.add(pair)
        edges.append((*pair, rng.choice(RELS)))
    return edges


def render_graphml(n_nodes: int, edges: list) -> str:
    """The fixture text — same GraphML dialect as chain-ab.graphml (namespaced
    header, typed keys, directed graph) so networkx's reader sees the shape
    the pinned loader was proven over."""
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
        'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">',
    ]
    for i, rel in enumerate(RELS):
        lines.append(f'  <key id="d{i}" for="edge" attr.name="{rel}" '
                     f'attr.type="long" />')
    lines.append('  <graph edgedefault="directed">')
    for i in range(n_nodes):
        lines.append(f'    <node id="{node_name(i)}" />')
    for src, dst, rel in edges:
        key = f"d{RELS.index(rel)}"
        lines.append(f'    <edge source="{src}" target="{dst}">')
        lines.append(f'      <data key="{key}">1</data>')
        lines.append('    </edge>')
    lines.append('  </graph>')
    lines.append('</graphml>')
    return "\n".join(lines) + "\n"


def fixture_text(rung: str) -> str:
    n_nodes, n_edges, seed = RUNGS[rung]
    return render_graphml(n_nodes, build_edges(n_nodes, n_edges, seed))


def main(argv=None) -> int:
    write = "--write" in (argv if argv is not None else sys.argv[1:])
    status = 0
    for rung in RUNGS:
        path = FIXTURES / f"perf-ladder-{rung}.graphml"
        text = fixture_text(rung)
        if path.exists() and path.read_text() == text:
            print(f"{path.name}: up to date")
            continue
        if write:
            path.write_text(text)
            print(f"{path.name}: written")
        else:
            print(f"{path.name}: STALE or missing — rerun with --write "
                  f"(and re-screen docs/perf/ladder.md if sizes changed)")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
