"""Seam tests for the graph boundary — load_graphml, the attribute-coercion
ladder, the reverse_digraph load-path split, and the graph-attribute knobs.

Every expectation is the pinned behavior (oracle pyreason.py:569-608,
graphml_parser.py:15-94 at e1a94af3), cross-checked against the banked
session-15 oracle artifacts for the load-graphml-basic /
load-graphml-no-attr-parse / graphml-attr-coercions / graphml-empty /
reverse-digraph pair / graph-attr-parsing pair / save-graph-attrs-to-trace
pair cases. The GraphML fixtures are the committed harness fixtures — the
same files the equivalence cases load, so the seam under test here is the
one the harness compares.
"""

from pathlib import Path

import pytest

import networkx as nx

import pyreason
from pyreason import Rule
from pyreason._graph import _attribute_to_label_bound
from pyreason._state import EngineState

FIXTURES = Path(__file__).resolve().parent.parent / "harness" / "fixtures"


@pytest.fixture
def pr(monkeypatch):
    """The facade over a fresh engine state — quiet, atom-traced."""
    fresh = EngineState()
    fresh.settings.verbose = False
    fresh.settings.atom_trace = True
    monkeypatch.setattr(pyreason, "_state_obj", fresh)
    monkeypatch.setattr(pyreason, "settings", fresh.settings)
    return pyreason


def _node_rows(frames):
    """Each frame's rows as plain lists — the shape the harness compares."""
    return [[list(r) for r in f.itertuples(index=False, name=None)] for f in frames]


# --- load_graphml: parse + attribute grounding ---

def test_load_graphml_parses_file_and_grounds_attribute_facts(pr):
    """proves: load_graphml reads the GraphML fixture into a DiGraph
    (typed values per the file's attr.type keys) and, with
    graph_attribute_parsing at its default True, grounds special=1 and
    rel=1 into graph-attribute facts a rule can consume — derived(B) at
    t=1 and t=2, get_time 3 (pyreason.py:569-581, graphml_parser.py:15-20)."""
    pr.load_graphml(str(FIXTURES / "chain-ab.graphml"))
    graph = pyreason._state_obj.graph
    assert dict(graph.nodes(data=True)) == {"A": {"special": 1}, "B": {}}
    assert list(graph.edges(data=True)) == [("A", "B", {"rel": 1})]
    pr.add_rule(Rule("derived(y) <-1 special(x), rel(x,y)", "derived_rule"))
    interp = pr.reason(timesteps=2)
    frames = pr.filter_and_sort_nodes(interp, ["derived"])
    assert _node_rows(frames) == [[], [["B", [1.0, 1.0]]], [["B", [1.0, 1.0]]]]
    assert pr.get_time() == 3


def test_load_graphml_attr_parse_off_skips_attribute_grounding(pr):
    """proves: with graph_attribute_parsing=False load_graphml still parses
    the graph but leaves all four attribute products empty, so nothing ever
    changes and the perfect-convergence exit fires at t=0 — get_time 1, one
    empty frame (pyreason.py:582-586, interpretation.py:674-680)."""
    pr.settings.graph_attribute_parsing = False
    pr.load_graphml(str(FIXTURES / "chain-ab.graphml"))
    state = pyreason._state_obj
    assert state.graph.number_of_nodes() == 2  # the graph itself still loads
    assert state.graph_facts_node == [] and state.graph_facts_edge == []
    assert state.specific_graph_node_labels == {}
    assert state.specific_graph_edge_labels == {}
    pr.add_rule(Rule("derived(y) <-1 special(x), rel(x,y)", "derived_rule"))
    interp = pr.reason(timesteps=2)
    assert _node_rows(pr.filter_and_sort_nodes(interp, ["derived"])) == [[]]
    assert pr.get_time() == 1


def test_load_graphml_empty_graph_reasons_without_raising(pr):
    """proves: the zero-node GraphML fixture parses into an empty DiGraph,
    attribute parsing walks nothing, and reason(timesteps=1) completes —
    get_time 1 and an empty t=0 interpretation dict (the bound-empty-graph
    arm; the inert rule clears reason()'s no-rules guard)."""
    pr.load_graphml(str(FIXTURES / "empty.graphml"))
    assert pyreason._state_obj.graph.number_of_nodes() == 0
    pr.add_rule(Rule("inert(x) <-1 never(x)", "inert_rule"))
    interp = pr.reason(timesteps=1)
    assert pr.get_time() == 1
    assert interp.get_dict() == {0: {}}


# --- reverse_digraph: the load-path split ---

def test_reverse_digraph_reverses_graphml_edges_at_load(pr):
    """proves: reverse_digraph=True makes load_graphml reverse every edge
    after read_graphml (graphml_parser.py:18-19) — the fixture's A->B
    becomes B->A, so 'derived(y) <-1 rel(x,y)' derives derived(A) with the
    trace grounding [(B, A)]; the default-False load keeps A->B and derives
    derived(B) instead."""
    for reverse, derived_node, edge in ((False, "B", ("A", "B")),
                                        (True, "A", ("B", "A"))):
        pyreason._state_obj.__init__()
        pyreason._state_obj.settings.verbose = False
        pyreason._state_obj.settings.atom_trace = True
        pyreason._state_obj.settings.reverse_digraph = reverse
        pr.load_graphml(str(FIXTURES / "chain-ab.graphml"))
        assert list(pyreason._state_obj.graph.edges) == [edge]
        pr.add_rule(Rule("derived(y) <-1 rel(x,y)", "derived_rule"))
        interp = pr.reason(timesteps=2)
        frames = pr.filter_and_sort_nodes(interp, ["derived"])
        assert _node_rows(frames)[1] == [[derived_node, [1.0, 1.0]]]
        node_frame, _ = pr.get_rule_trace(interp)
        rule_rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
        assert rule_rows[0][10] == [edge]  # Clause-1 grounding carries the loaded direction


def test_load_graph_never_reads_reverse_digraph(pr):
    """proves: the inline load_graph path ignores reverse_digraph even when
    set — the pinned load-path knob asymmetry (pyreason.py:589-599 carries
    no read of the knob)."""
    pr.settings.reverse_digraph = True
    g = nx.DiGraph()
    g.add_edge("A", "B", rel=1)
    pr.load_graph(g)
    assert list(pyreason._state_obj.graph.edges) == [("A", "B")]


# --- the attribute-coercion ladder (the all-silent hazard cluster) ---

@pytest.mark.parametrize("key,value,expected", [
    # bound-attr-numeric-in-range: v in [0,1] -> bound [v, 1] under the bare key
    ("score", 0.4, ("score", 0.4, 1)),
    ("score", "0.5", ("score", 0.5, 1)),
    # bound-attr-zero-one-edges: 1 -> [1,1]; 0 -> the vacuous [0,1]
    ("flag", 1, ("flag", 1.0, 1)),
    ("flag", 0, ("flag", 0.0, 1)),
    # bound-attr-comma-pair: integer pair in range sets BOTH bounds
    ("pair", "0,1", ("pair", 0, 1)),
    ("pair2", "0,0", ("pair2", 0, 0)),
    # malformed-attr-comma-float: int() raises, silently swallowed — the
    # composed label at [1,1], never a bound
    ("fpair", "0.3,0.7", ("fpair-0.3,0.7", 1, 1)),
    # malformed-attr-out-of-range / malformed-attr-nonnumeric: composed label
    ("big", 1.5, ("big-1.5", 1, 1)),
    ("word", "abc", ("word-abc", 1, 1)),
])
def test_attribute_coercion_ladder_matches_pin(key, value, expected):
    """proves: the attribute ladder reproduces the pinned coercions —
    in-range numerics become [v,1] bounds, integer comma pairs in range set
    both bounds, and every malformed value silently composes a key-value
    label at [1,1], never raising (graphml_parser.py:35-55; the session-9
    all-silent characterization)."""
    assert _attribute_to_label_bound(key, value) == expected


def test_graphml_coercion_cluster_observable_rows(pr):
    """proves: over the committed coercion fixture with
    save_graph_attributes_to_trace on, the observable rows land exactly as
    the pin coerces — score [0.4,1] and edge w [0.5,1]; flag only for the
    value-1 node (the 0 arm coerces to the vacuous [0,1] whose no-change
    update leaves NO row, like the '0,1' pair); pair2 '0,0' becomes the
    [0,0] bound under the bare key; 'fpair-0.3,0.7' composes at [1,1]; and
    nothing lands under the malformed values' bare keys."""
    pr.settings.save_graph_attributes_to_trace = True
    pr.load_graphml(str(FIXTURES / "attr-coercions.graphml"))
    pr.add_rule(Rule("inert(x) <-1 never(x)", "inert_rule"))
    interp = pr.reason(timesteps=1)
    # Nothing changes after the t=0 attribute grounding, so the
    # perfect-convergence exit fires at t=0: one frame per probe (the banked
    # oracle artifact's get_time is 1)
    assert pr.get_time() == 1
    last = {label: _node_rows(pr.filter_and_sort_nodes(interp, [label]))[-1]
            for label in ("score", "flag", "pair", "pair2", "fpair-0.3,0.7")}
    assert last["score"] == [["N1", [0.4, 1.0]]]
    assert last["flag"] == [["N3", [1.0, 1.0]]]
    assert last["pair"] == []
    assert last["pair2"] == [["N8", [0.0, 0.0]]]
    assert last["fpair-0.3,0.7"] == [["N5", [1.0, 1.0]]]
    bare = pr.filter_and_sort_nodes(interp, ["fpair", "big", "word"])
    assert _node_rows(bare) == [[]]
    edge_frames = pr.filter_and_sort_edges(interp, ["w"])
    edge_rows = [[list(r) for r in f.itertuples(index=False, name=None)]
                 for f in edge_frames]
    assert edge_rows[-1] == [[("N1", "N2"), [0.5, 1.0]]]


# --- save_graph_attributes_to_trace: the trace gate ---

def _graph_attr_program(pr):
    g = nx.DiGraph()
    g.add_node("A", special=1)
    g.add_node("B")
    g.add_edge("A", "B", rel=1)
    pr.load_graph(g)
    pr.add_rule(Rule("derived(y) <-1 special(x), rel(x,y)", "derived_rule"))
    return pr.reason(timesteps=2)


def test_save_graph_attributes_to_trace_on_banks_graph_fact_rows(pr):
    """proves: with the knob on, 'graph-attribute-fact' rows enter both
    traces — the t=0 gate applications plus the static-fact reapplications
    per later timestep (interpretation.py:297/:373/:1538/:1657) — while the
    derived bounds stay what the off arm derives."""
    pr.settings.save_graph_attributes_to_trace = True
    interp = _graph_attr_program(pr)
    node_frame, edge_frame = pr.get_rule_trace(interp)
    node_rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    fact_rows = [r for r in node_rows if r[6] == "graph-attribute-fact"]
    assert [(r[0], r[2], r[3]) for r in fact_rows] == [
        (0, "A", "special"), (1, "A", "special"), (2, "A", "special")]
    edge_rows = [list(r) for r in edge_frame.itertuples(index=False, name=None)]
    assert [(r[0], r[2], r[3]) for r in edge_rows] == [
        (0, ("A", "B"), "rel"), (1, ("A", "B"), "rel"), (2, ("A", "B"), "rel")]
    assert [r[2] for r in node_rows if r[8] == "Rule"] == ["B", "B"]


def test_save_graph_attributes_to_trace_off_suppresses_graph_fact_rows(pr):
    """proves: at the default False the gates suppress every
    'graph-attribute-fact' row — the node trace carries only the
    rule-derived rows and the edge trace stays empty — while derivation
    itself is untouched (trace contents only, never derived bounds)."""
    interp = _graph_attr_program(pr)
    node_frame, edge_frame = pr.get_rule_trace(interp)
    node_rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    assert [(r[2], r[8]) for r in node_rows] == [("B", "Rule"), ("B", "Rule")]
    assert [list(r) for r in edge_frame.itertuples(index=False, name=None)] == []
    frames = pr.filter_and_sort_nodes(interp, ["derived"])
    assert _node_rows(frames)[1] == [["B", [1.0, 1.0]]]
