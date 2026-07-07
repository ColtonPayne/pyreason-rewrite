"""Seam tests for the reference reasoning core, at the module-global facade.

Every test drives the same surface the equivalence harness drives —
`pyreason.load_graph/add_rule/add_fact/reason` in, trace frames /
filter-sort frames / get_time out — against hand-derived expectations whose
semantics come from the pinned engine source (anchors in each docstring) and
the banked case artifacts. A fresh EngineState is swapped in per test, which
is exactly the embedder path the facade's one-line delegations exist for.
"""

import pytest

import networkx as nx

import pyreason
from pyreason import Fact, Query, Rule, Threshold
from pyreason._state import EngineState


@pytest.fixture
def pr(monkeypatch):
    """The facade over a fresh engine state — quiet, atom-traced."""
    fresh = EngineState()
    fresh.settings.verbose = False
    fresh.settings.atom_trace = True
    monkeypatch.setattr(pyreason, "_state_obj", fresh)
    monkeypatch.setattr(pyreason, "settings", fresh.settings)
    return pyreason


def _chain_graph():
    """A -> B -> C, each edge wearing the F attribute."""
    g = nx.DiGraph()
    g.add_nodes_from(["A", "B", "C"])
    g.add_edge("A", "B", F=1)
    g.add_edge("B", "C", F=1)
    return g


def _fan_graph():
    """A -> B and A -> C, both edges wearing Friends."""
    g = nx.DiGraph()
    g.add_nodes_from(["A", "B", "C"])
    g.add_edge("A", "B", Friends=1)
    g.add_edge("A", "C", Friends=1)
    return g


def _load_diffusion(pr, timesteps=None, **reason_kwargs):
    """The three-node diffusion program: pop spreads down the chain."""
    pr.load_graph(_chain_graph())
    pr.add_rule(Rule("pop(x) <-1 pop(y), F(y,x)", "pop_rule"))
    pr.add_fact(Fact("pop(A)", "pop_fact", 0, 2))
    if timesteps is not None:
        reason_kwargs["timesteps"] = timesteps
    return pr.reason(**reason_kwargs)


# --- the spine: derivation, trace rows, frames, time ---

def test_diffusion_trace_rows_and_time(pr):
    """proves: the fixed-point loop derives pop down the chain one delta per
    timestep, and the node trace banks (t, fp, node, label, bounds, name,
    Fact/Rule, clause groundings) rows in application order with fact rows
    before rule rows within a timestep — the hello-world shape at chain
    scale (interpretation.py:280-604, output.py:12-50 at the pin)."""
    interp = _load_diffusion(pr, timesteps=2)
    node_frame, edge_frame = pr.get_rule_trace(interp)
    assert node_frame.columns == [
        'Time', 'Fixed-Point-Operation', 'Node', 'Label', 'Old Bound',
        'New Bound', 'Occurred Due To', 'Consistent', 'Triggered By',
        'Inconsistency Message', 'Clause-1', 'Clause-2']
    rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    assert rows == [
        [0, 0, 'A', 'pop', '[0.0,1.0]', '[1.0,1.0]', 'pop_fact', True, 'Fact', '', None, None],
        [1, 1, 'A', 'pop', '[0.0,1.0]', '[1.0,1.0]', 'pop_fact', True, 'Fact', '', None, None],
        [1, 1, 'B', 'pop', '[0.0,1.0]', '[1.0,1.0]', 'pop_rule', True, 'Rule', '', ['A'], [('A', 'B')]],
        [2, 2, 'A', 'pop', '[0.0,1.0]', '[1.0,1.0]', 'pop_fact', True, 'Fact', '', None, None],
        # Clause-1 carries the CLAUSE's whole qualifying set (['A', 'B'] at
        # t=1), not a per-head slice — the same shape the banked hello-world
        # t=2 rows pin; only clauses sharing the head variable narrow.
        [2, 2, 'B', 'pop', '[0.0,1.0]', '[1.0,1.0]', 'pop_rule', True, 'Rule', '', ['A', 'B'], [('A', 'B')]],
        [2, 2, 'C', 'pop', '[0.0,1.0]', '[1.0,1.0]', 'pop_rule', True, 'Rule', '', ['A', 'B'], [('B', 'C')]],
    ]
    # Graph-attribute facts leave no trace rows by default
    assert [list(r) for r in edge_frame.itertuples(index=False, name=None)] == []
    assert pr.get_time() == 3


def test_filter_and_sort_nodes_frames(pr):
    """proves: filter_and_sort_nodes emits one frame per timestep 0..time,
    each holding the latest per-component change for the requested labels,
    insertion-ordered by the (stable) bound sort (filter.py:8-60)."""
    interp = _load_diffusion(pr, timesteps=2)
    frames = pr.filter_and_sort_nodes(interp, ['pop'])
    assert len(frames) == 3
    assert all(f.columns == ['component', 'pop'] for f in frames)
    as_rows = [[list(r) for r in f.itertuples(index=False, name=None)] for f in frames]
    assert as_rows == [
        [['A', [1.0, 1.0]]],
        [['A', [1.0, 1.0]], ['B', [1.0, 1.0]]],
        [['A', [1.0, 1.0]], ['B', [1.0, 1.0]], ['C', [1.0, 1.0]]],
    ]


def test_filter_and_sort_orders_by_bound_and_fills_defaults(pr):
    """proves: rows sort by the chosen bound endpoint (descending default,
    ascending on request), and a qualifying component's other requested
    labels fill with the [0,1] default cell (filter.py:33-49)."""
    g = nx.DiGraph()
    g.add_nodes_from(["A", "B"])
    pr.load_graph(g)
    pr.add_rule(Rule("dummy(x) <-1 p(x)", "dummy"))  # reason() requires rules
    pr.add_fact(Fact("p(A) : [0.2, 1]", "fa", 0, 0))
    pr.add_fact(Fact("p(B) : [0.9, 1]", "fb", 0, 0))
    pr.add_fact(Fact("q(B)", "fq", 0, 0))
    interp = pr.reason(timesteps=0)
    frames = pr.filter_and_sort_nodes(interp, ['p', 'q'])
    rows = [list(r) for r in frames[0].itertuples(index=False, name=None)]
    assert rows == [['B', [0.9, 1.0], [1.0, 1.0]], ['A', [0.2, 1.0], [0, 1]]]
    ascending = pr.filter_and_sort_nodes(interp, ['p'], descending=False)
    assert [r[0] for r in ascending[0].itertuples(index=False, name=None)] == ['A', 'B']


def test_edge_rule_trace_and_edge_frames(pr):
    """proves: an edge-head rule derives per existing (source, target) pair,
    the edge trace banks tuple components with per-clause groundings, and
    filter_and_sort_edges frames carry tuple component cells — the
    edge-rule-frames shape (interpretation.py:1064-1278, filter.py:62-117)."""
    pr.load_graph(_fan_graph())
    pr.add_rule(Rule("trusted(x,y) <-1 pop(x), Friends(x,y)", "trusted_rule"))
    pr.add_fact(Fact("pop(A)", "pop_fact", 0, 0))
    interp = pr.reason(timesteps=1)
    _, edge_frame = pr.get_rule_trace(interp)
    rows = [list(r) for r in edge_frame.itertuples(index=False, name=None)]
    assert rows == [
        [1, 1, ('A', 'B'), 'trusted', '[0.0,1.0]', '[1.0,1.0]', 'trusted_rule',
         True, 'Rule', '', ['A'], [('A', 'B')]],
        [1, 1, ('A', 'C'), 'trusted', '[0.0,1.0]', '[1.0,1.0]', 'trusted_rule',
         True, 'Rule', '', ['A'], [('A', 'C')]],
    ]
    frames = pr.filter_and_sort_edges(interp, ['trusted'])
    assert [list(r) for r in frames[0].itertuples(index=False, name=None)] == []
    assert [list(r) for r in frames[1].itertuples(index=False, name=None)] == [
        [('A', 'B'), [1.0, 1.0]], [('A', 'C'), [1.0, 1.0]]]


# --- threshold gating ---

def test_threshold_gates_at_clause_level(pr):
    """proves: a number/total threshold consumes the clause's WHOLE-graph
    qualifying count, not a per-head count — two disconnected pairs each
    holding one qualifier still satisfy thresh=2 together, so both heads
    derive; thresh=3 fails and nothing derives
    (interpretation.py:1364-1377/1475-1503)."""
    def program(thresh):
        g = nx.DiGraph()
        g.add_nodes_from(["A", "B", "C", "D"])
        g.add_edge("A", "B", Friends=1)
        g.add_edge("C", "D", Friends=1)
        pr.load_graph(g)
        pr.add_rule(Rule("trendy(x) <-1 Friends(x,y), popular(y)", "trendy_rule",
                         custom_thresholds=[
                             Threshold("greater_equal", ("number", "total"), 1),
                             Threshold("greater_equal", ("number", "total"), thresh)]))
        pr.add_fact(Fact("popular(B)", "f_b", 0, 1))
        pr.add_fact(Fact("popular(D)", "f_d", 0, 1))
        return pr.reason(timesteps=1)

    interp = program(2)
    frames = pr.filter_and_sort_nodes(interp, ['trendy'])
    assert [r[0] for r in frames[1].itertuples(index=False, name=None)] == ['A', 'C']

    pyreason._state_obj.__init__()  # fresh engine for the failing twin
    pyreason._state_obj.settings.verbose = False
    interp = program(3)
    frames = pr.filter_and_sort_nodes(interp, ['trendy'])
    assert [list(r) for r in frames[1].itertuples(index=False, name=None)] == []


def test_threshold_percent_total_both_arms(pr):
    """proves: percent/total 100 requires every candidate grounding of the
    clause to qualify — 2/2 popular friends derive social(A) while 1/2 busy
    friends never derive overloaded(A) (interpretation.py:1489-1501, the
    thresh*0.01 scaling and ratio-over-candidates branch)."""
    pct = [Threshold("greater_equal", ("number", "total"), 1),
           Threshold("greater_equal", ("percent", "total"), 100)]
    pr.load_graph(_fan_graph())
    pr.add_rule(Rule("social(x) <-1 Friends(x,y), popular(y)", "social_rule",
                     custom_thresholds=list(pct)))
    pr.add_rule(Rule("overloaded(x) <-1 Friends(x,y), busy(y)", "overloaded_rule",
                     custom_thresholds=list(pct)))
    pr.add_fact(Fact("popular(B)", "f1", 0, 1))
    pr.add_fact(Fact("popular(C)", "f2", 0, 1))
    pr.add_fact(Fact("busy(B)", "f3", 0, 1))
    interp = pr.reason(timesteps=1)
    frames = pr.filter_and_sort_nodes(interp, ['social', 'overloaded'])
    rows = [list(r) for r in frames[1].itertuples(index=False, name=None)]
    assert rows == [['A', [1.0, 1.0], [0, 1]]]


def test_threshold_available_counts_label_carriers(pr):
    """proves: the 'available' quantifier re-bases the percent denominator
    on candidates that carry the clause label at all, while 'total' keeps
    every candidate — one qualifying carrier out of two candidates passes
    percent/available 100 and fails percent/total 100
    (interpretation.py:1365-1372)."""
    for qtype, expected in ((("percent", "available"), ['A']),
                            (("percent", "total"), [])):
        pyreason._state_obj.__init__()
        pyreason._state_obj.settings.verbose = False
        pr.load_graph(_fan_graph())
        pr.add_rule(Rule("social(x) <-1 Friends(x,y), popular(y)", "social_rule",
                         custom_thresholds=[
                             Threshold("greater_equal", ("number", "total"), 1),
                             Threshold("greater_equal", qtype, 100)]))
        pr.add_fact(Fact("popular(B)", "f1", 0, 1))  # C never carries popular
        interp = pr.reason(timesteps=1)
        frames = pr.filter_and_sort_nodes(interp, ['social'])
        assert [r[0] for r in frames[1].itertuples(index=False, name=None)] == expected


def test_dict_thresholds_default_unnamed_clauses(pr):
    """proves: the dict custom_thresholds form defaults unnamed clause
    indices to greater_equal number/total 1 and gates the named one — the
    {1: thresh 2} single-qualifier program derives nothing, matching the
    list form (rule_parser.py:161-173 consumed at interpretation.py:880)."""
    pr.load_graph(_fan_graph())
    pr.add_rule(Rule("trendy(x) <-1 Friends(x,y), popular(y)", "trendy_rule",
                     custom_thresholds={
                         1: Threshold("greater_equal", ("number", "total"), 2)}))
    pr.add_fact(Fact("popular(B)", "f_b", 0, 1))
    interp = pr.reason(timesteps=1)
    frames = pr.filter_and_sort_nodes(interp, ['trendy'])
    assert all(list(f.itertuples(index=False, name=None)) == [] for f in frames)


# --- convergence modes ---

def test_convergence_modes_stop_at_pinned_times(pr):
    """proves: timesteps=-1 selects perfect convergence (runs past the fact
    horizon until no rule conclusion is pending); convergence_threshold=0
    stops at the first zero-change timestep; convergence_bound_threshold
    dominates a count threshold that would otherwise stop at t=0
    (interpretation.py:176-188/654-680) — hand-derived stop times 5/4/4 on
    the chain-diffusion program."""
    times = {}
    for key, kwargs in (
            ('perfect', dict(timesteps=-1)),
            ('delta_interp', dict(timesteps=-1, convergence_threshold=0)),
            ('delta_bound', dict(timesteps=-1, convergence_threshold=500,
                                 convergence_bound_threshold=0.001))):
        pyreason._state_obj.__init__()
        pyreason._state_obj.settings.verbose = False
        pyreason._state_obj.settings.atom_trace = True
        _load_diffusion(pr, **kwargs)
        times[key] = pr.get_time()
    assert times == {'perfect': 5, 'delta_interp': 4, 'delta_bound': 4}


def test_rederived_bound_counts_zero_toward_convergence(pr):
    """proves: an update that lands the same bound the component held at the
    previous timestep contributes zero change — previous bounds ride through
    updates (interval.intersect_jitted), so re-derivation alone cannot hold
    convergence open (interpretation.py:1601-1617)."""
    g = nx.DiGraph()
    g.add_nodes_from(["A"])
    pr.load_graph(g)
    pr.add_rule(Rule("q(x) <-1 p(x)", "qr"))
    pr.add_fact(Fact("p(A)", "fp", 0, 10))  # fact keeps re-applying
    _ = pr.reason(timesteps=-1, convergence_threshold=0)
    # t0: p new (1 change) + q pending; t1: p re-applied (0) + q new (1);
    # t2: both re-land their previous bounds -> 0 changes -> converged at 2
    assert pr.get_time() == 3


# --- annotation and head functions ---

def test_registered_annotation_function_produces_bound(pr):
    """proves: a rule head naming a registered 2-arg annotation function gets
    its returned (lower, upper) as the derived bound, clamped into [0,1]
    (interpretation.py:584-593/1914-1931)."""
    def half_mean(annotations, weights):
        total = sum(ann.lower * weights[i]
                    for i, clause in enumerate(annotations) for ann in clause)
        return total / 2, 1.5  # upper deliberately out of range -> clamps to 1

    g = nx.DiGraph()
    g.add_nodes_from(["A"])
    pr.load_graph(g)
    pr.add_annotation_function(half_mean)
    pr.add_rule(Rule("combo(x) : half_mean <- p(x) : [0.1, 1]", "combo_rule"))
    pr.add_fact(Fact("p(A) : [0.5, 1]", "fp", 0, 0))
    interp = pr.reason(timesteps=1)
    node_frame, _ = pr.get_rule_trace(interp)
    rule_rows = [list(r) for r in node_frame.itertuples(index=False, name=None)
                 if r[8] == 'Rule']
    assert [r[3] for r in rule_rows] == ['combo']
    assert rule_rows[0][5] == '[0.25,1.0]'


def test_six_arg_annotation_function_sees_clause_metadata(pr):
    """proves: a 6-arg registrand receives the per-clause qualified atoms and
    labels/variables even with atom_trace off — the extended-arity flag, not
    the trace knob, gates the metadata build (interpretation.py:224-231/
    1002-1010)."""
    seen = {}

    def probe_fn(annotations, weights, qualified_nodes, qualified_edges,
                 clause_labels, clause_variables):
        seen['labels'] = [l.get_value() for l in clause_labels]
        seen['vars'] = [list(v) for v in clause_variables]
        seen['nodes'] = [list(q) for q in qualified_nodes]
        return 0.5, 1.0

    pyreason._state_obj.settings.atom_trace = False
    g = nx.DiGraph()
    g.add_nodes_from(["A"])
    pr.load_graph(g)
    pr.add_annotation_function(probe_fn)
    pr.add_rule(Rule("combo(x) : probe_fn <- p(x) : [0.1, 1]", "combo_rule"))
    pr.add_fact(Fact("p(A) : [0.5, 1]", "fp", 0, 0))
    pr.reason(timesteps=1)
    assert seen == {'labels': ['p'], 'vars': [['x']], 'nodes': [['A']]}


def test_annotation_function_arity_gate_and_unregistered_name(pr):
    """proves: registration rejects a non-2/6-arg callable with the pinned
    TypeError text (pyreason.py:1471-1479), and a rule head naming a function
    nobody registered raises NameError("name 'annotation' is not defined")
    from reason() while get_time still reads the constructed interpretation
    (the banked annotation-fn-unregistered-name observations)."""
    def three_args(a, b, c):
        return 0, 1

    with pytest.raises(TypeError) as exc_info:
        pr.add_annotation_function(three_args)
    assert str(exc_info.value) == (
        "Annotation function 'three_args' must accept exactly 2 positional "
        "args (annotations, weights) or exactly 6 positional args (annotations, "
        "weights, qualified_nodes, qualified_edges, clause_labels, clause_variables); "
        "got 3.")

    g = nx.DiGraph()
    g.add_nodes_from(["A"])
    pr.load_graph(g)
    pr.add_rule(Rule("combo(x) : nobody <- p(x) : [0.1, 1]", "combo_rule"))
    pr.add_fact(Fact("p(A) : [0.5, 1]", "fp", 0, 0))
    with pytest.raises(NameError) as exc_info:
        pr.reason(timesteps=1)
    assert str(exc_info.value) == "name 'annotation' is not defined"
    assert pr.get_time() == 1


def test_head_function_registered_and_unregistered(pr):
    """proves: a registered head function's return becomes the head
    grounding; an UNREGISTERED head-function name grounds the head to the
    empty list, so reason() completes with zero rule rows — the silent side
    of the pinned asymmetry (interpretation.py:2316-2338)."""
    def pick_first(fn_arg_values):
        return [fn_arg_values[0][0]]

    g = nx.DiGraph()
    g.add_nodes_from(["A", "B"])
    pr.load_graph(g)
    pr.add_head_function(pick_first)
    pr.add_rule(Rule("Processed(pick_first(X)) <- starter(X)", "head_rule"))
    pr.add_fact(Fact("starter(A)", "fs", 0, 0))
    pr.add_fact(Fact("starter(B)", "fs2", 0, 0))
    interp = pr.reason(timesteps=1)
    frames = pr.filter_and_sort_nodes(interp, ['Processed'])
    assert [r[0] for r in frames[0].itertuples(index=False, name=None)] == ['A']

    pyreason._state_obj.__init__()
    pyreason._state_obj.settings.verbose = False
    pyreason._state_obj.settings.atom_trace = True
    pr.load_graph(g)
    pr.add_rule(Rule("Processed(nobody(X)) <- starter(X)", "head_rule"))
    pr.add_fact(Fact("starter(A)", "fs", 0, 0))
    interp = pr.reason(timesteps=1)
    node_frame, _ = pr.get_rule_trace(interp)
    assert all(r[8] != 'Rule' for r in node_frame.itertuples(index=False, name=None))
    assert pr.get_time() == 1  # perfect convergence at t=0, nothing pending


# --- closed-world predicates ---

def test_closed_world_predicate_reads_absence_as_false(pr):
    """proves: with busy registered closed-world, an absent (or vacuous)
    busy bound satisfies the busy(x):[0,0] clause and available derives for
    the never-busy node; without registration the same program derives
    nothing (interpretation.py:1757-1778; the closed-world-off twin)."""
    for register, expected in ((True, ['A']), (False, [])):
        pyreason._state_obj.__init__()
        pyreason._state_obj.settings.verbose = False
        pr.load_graph(_fan_graph())
        if register:
            pr.add_closed_world_predicate("busy")
        pr.add_rule(Rule("available(x) <-1 Friends(x,y), busy(x) : [0,0]", "avail"))
        pr.add_fact(Fact("busy(B)", "fb", 0, 1))
        interp = pr.reason(timesteps=1)
        frames = pr.filter_and_sort_nodes(interp, ['available'])
        assert [r[0] for r in frames[1].itertuples(index=False, name=None)] == expected


# --- IPL, queries, clause reordering, guards ---

def test_ipl_update_tightens_complement_with_trace_row(pr):
    """proves: an update to p propagates 1-complement bounds onto its IPL
    partner q with an 'IPL'-triggered trace row naming the source predicate
    (interpretation.py:1562-1599)."""
    g = nx.DiGraph()
    g.add_nodes_from(["A"])
    pr.load_graph(g)
    pr.add_rule(Rule("dummy(x) <-1 p(x)", "dummy"))
    pr.add_inconsistent_predicate("p", "q")
    pr.add_fact(Fact("p(A)", "fp", 0, 0))
    interp = pr.reason(timesteps=0)
    node_frame, _ = pr.get_rule_trace(interp)
    rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    assert [r[3] for r in rows] == ['p', 'q']
    ipl_row = rows[1]
    assert ipl_row[5] == '[0.0,0.0]'
    assert ipl_row[8] == 'IPL'
    assert ipl_row[6] == 'IPL: p'


def test_queries_filter_ruleset(pr):
    """proves: reason(queries=[...]) keeps only rules that can support the
    queried predicate — the dropped rule fires for nobody and get_rules()
    reflects the filtered set (pyreason.py:1594-1595,
    filter_ruleset.py:1-34)."""
    pr.load_graph(_fan_graph())
    pr.add_rule(Rule("social(x) <-1 Friends(x,y), popular(y)", "social_rule"))
    pr.add_rule(Rule("lonely(x) <-1 Friends(x,y), busy(y)", "lonely_rule"))
    pr.add_fact(Fact("popular(B)", "f1", 0, 1))
    pr.add_fact(Fact("busy(B)", "f2", 0, 1))
    interp = pr.reason(timesteps=1, queries=[Query("social(A)")])
    assert [r.get_rule_name() for r in pr.get_rules()] == ['social_rule']
    frames = pr.filter_and_sort_nodes(interp, ['social', 'lonely'])
    rows = [list(r) for r in frames[1].itertuples(index=False, name=None)]
    assert rows == [['A', [1.0, 1.0], [0, 1]]]


def test_clause_reorder_on_edge_heavy_graph_restores_author_order(pr):
    """proves: on a graph with more edges than nodes the engine grounds with
    node clauses moved ahead of edge clauses (observable through
    get_rules()' live clause list), while trace clause columns render back
    in the author's order through the clause map
    (pyreason.py:1598-1606, output.py:91-123)."""
    g = nx.DiGraph()
    g.add_nodes_from(["A", "B", "C"])
    for s, t in (("A", "B"), ("A", "C"), ("B", "C"), ("C", "A")):
        g.add_edge(s, t, F=1)
    pr.load_graph(g)
    pr.add_rule(Rule("t(x) <-1 F(x,y), pop(y)", "t_rule"))
    pr.add_fact(Fact("pop(B)", "fb", 0, 0))
    interp = pr.reason(timesteps=1)
    # Grounding order: the live rule's first clause is now the node clause
    assert [c[0] for c in pr.get_rules()[0].get_clauses()] == ['node', 'edge']
    node_frame, _ = pr.get_rule_trace(interp)
    rule_rows = [list(r) for r in node_frame.itertuples(index=False, name=None)
                 if r[8] == 'Rule']
    # Author order restored: Clause-1 is the F(x,y) edge clause
    assert rule_rows == [[1, 1, 'A', 't', '[0.0,1.0]', '[1.0,1.0]', 't_rule',
                          True, 'Rule', '', [('A', 'B')], ['B']]]


def test_reason_requires_rules_and_accessors_expose_run(pr):
    """proves: reason() with no rules raises the pinned bare Exception; after
    a run, get_interpretation/get_logic_program hand out the live objects
    (identity with the reason() return) and get_time is time+1
    (pyreason.py:1549-1550/529-558)."""
    pr.load_graph(_chain_graph())
    with pytest.raises(Exception) as exc_info:
        pr.reason(timesteps=1)
    assert str(exc_info.value) == 'There are no rules, use `add_rule` or `add_rules_from_file`'

    interp = _load_diffusion(pr, timesteps=2)
    assert pr.get_interpretation() is interp
    assert pr.get_logic_program().interp is interp
    assert pr.get_time() == interp.time + 1 == 3


def test_store_off_flips_atom_trace_and_gates_views(pr):
    """proves: reason() force-flips the public atom_trace knob off when
    change storage is off, and the trace/filter views refuse with the pinned
    assertion text (pyreason.py:1584-1585/1666/1682)."""
    pyreason._state_obj.settings.store_interpretation_changes = False
    interp = _load_diffusion(pr, timesteps=1)
    assert pyreason.settings.atom_trace is False
    with pytest.raises(AssertionError) as exc_info:
        pr.get_rule_trace(interp)
    assert str(exc_info.value).startswith(
        'store interpretation changes setting is off, turn on to save rule trace')
    with pytest.raises(AssertionError):
        pr.filter_and_sort_nodes(interp, ['pop'])


# --- the knob-arm semantics (session 19) ---

def _conflict_program(pr, inconsistency_check=None):
    """The inconsistency-ipl-resolve program: sick/healthy declared IPL,
    both asserted on Alice (IPL conflict), tired(Bob) asserted with two
    non-overlapping bounds (same-predicate conflict)."""
    if inconsistency_check is not None:
        pyreason._state_obj.settings.inconsistency_check = inconsistency_check
    g = nx.DiGraph()
    g.add_nodes_from(["Alice", "Bob", "Carol"])
    g.add_edge("Alice", "Bob", contact=1)
    g.add_edge("Bob", "Carol", contact=1)
    pr.load_graph(g)
    pr.add_inconsistent_predicate("sick", "healthy")
    pr.add_rule(Rule("sick(y):[0.5,0.7] <- sick(x):[0.5,1.0], contact(x,y)", "spread_rule"))
    pr.add_fact(Fact("sick(Alice):[0.8,1.0]", "alice_sick_fact", 0, 0))
    pr.add_fact(Fact("healthy(Alice):[0.9,1.0]", "alice_healthy_fact", 0, 0))
    pr.add_fact(Fact("tired(Bob):[0.8,1.0]", "bob_tired_fact_1", 0, 0))
    pr.add_fact(Fact("tired(Bob):[0.0,0.1]", "bob_tired_fact_2", 0, 0))
    return pr.reason(timesteps=2)


def test_inconsistency_resolve_pins_vacuous_static_with_message(pr):
    """proves: under the default inconsistency_check=True, an IPL conflict
    and a same-predicate bound conflict each bank a Consistent=False trace
    row carrying the pinned message, pin the atom (and its IPL complement)
    to static [0,1], and the pinned static bounds stop all later derivation
    (interpretation.py:1960-2083; banked inconsistency-ipl-resolve)."""
    interp = _conflict_program(pr)
    node_frame, _ = pr.get_rule_trace(interp)
    rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    # (label, new bound, consistent, triggered by) per row, banked shape
    assert [(r[3], r[5], r[7], r[8]) for r in rows] == [
        ('sick', '[0.8,1.0]', True, 'Fact'),
        ('healthy', '[0.0,0.19999999999999996]', True, 'IPL'),
        ('healthy', '[0.0,1.0]', False, 'Fact'),
        ('sick', '[0.0,1.0]', False, 'IPL'),
        ('tired', '[0.8,1.0]', True, 'Fact'),
        ('tired', '[0.0,1.0]', False, 'Fact'),
    ]
    assert rows[2][9] == ('Inconsistency occurred. Grounding healthy(Alice) '
                          'conflicts with grounding sick(Alice). Setting bounds '
                          'to [0,1] and static=True for this timestep.')
    assert rows[5][9] == ('Inconsistency occurred. Conflicting bounds for '
                          'tired(Bob). Update from [0.800, 1.000] to '
                          '[0.000, 0.100] is not allowed. Setting bounds to '
                          '[0,1] and static=True for this timestep.')
    # Static [0,1] sick(Alice) satisfies no clause bound: nothing derives,
    # perfect convergence fires at t=0.
    assert pr.get_time() == 1
    frames = pr.filter_and_sort_nodes(interp, ['sick', 'healthy', 'tired'])
    assert [list(r) for r in frames[0].itertuples(index=False, name=None)] == [
        ['Alice', [0, 1], [0, 1], [0, 1]],
        ['Bob', [0, 1], [0, 1], [0, 1]],
    ]


def test_inconsistency_override_forces_bounds_through(pr):
    """proves: inconsistency_check=False forces a conflicting update through
    the override path instead of resolving — the second bound replaces the
    first wholesale (yielding the pinned INVERTED sick(Alice) interval
    [0.8,0.099...] via IPL), every row stays Consistent=True, and the rule
    still fires down the chain (interpretation.py:311-323 override arm;
    banked inconsistency-ipl-override)."""
    interp = _conflict_program(pr, inconsistency_check=False)
    node_frame, _ = pr.get_rule_trace(interp)
    rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    assert all(r[7] is True for r in rows)
    assert [(r[2], r[3], r[5]) for r in rows[:6]] == [
        ('Alice', 'sick', '[0.8,1.0]'),
        ('Alice', 'healthy', '[0.0,0.19999999999999996]'),
        ('Alice', 'healthy', '[0.9,1.0]'),
        ('Alice', 'sick', '[0.8,0.09999999999999998]'),
        ('Bob', 'tired', '[0.8,1.0]'),
        ('Bob', 'tired', '[0.0,0.1]'),
    ]
    # The forced-through sick(Alice) still satisfies the [0.5,1] clause
    # lower bound check, so sick spreads to Bob and Carol at fp 1 and 2.
    assert [(r[0], r[1], r[2], r[3]) for r in rows[6:]] == [
        (0, 1, 'Bob', 'sick'), (0, 1, 'Bob', 'healthy'),
        (0, 2, 'Carol', 'sick'), (0, 2, 'Carol', 'healthy'),
    ]


def test_abort_on_inconsistency_is_dead_at_the_pin(pr):
    """proves: abort_on_inconsistency=True changes NOTHING but its own
    readback — the conflict program resolves identically to the default arm
    and nothing aborts (the knob's name appears only inside the pinned
    _Settings, pyreason.py:49/:70/:118-123/:284-294; banked
    abort-on-inconsistency-on digest-equals its default twin)."""
    baseline = _conflict_program(pr)
    base_frame, _ = pr.get_rule_trace(baseline)
    base_rows = [list(r) for r in base_frame.itertuples(index=False, name=None)]

    fresh = EngineState()
    fresh.settings.verbose = False
    fresh.settings.atom_trace = True
    fresh.settings.abort_on_inconsistency = True
    import unittest.mock as mock
    with mock.patch.object(pyreason, "_state_obj", fresh), \
            mock.patch.object(pyreason, "settings", fresh.settings):
        interp = _conflict_program(pr)
        assert pyreason.settings.abort_on_inconsistency is True
        frame, _ = pr.get_rule_trace(interp)
        rows = [list(r) for r in frame.itertuples(index=False, name=None)]
    assert rows == base_rows


def _update_mode_program(pr, update_mode=None):
    """The update-mode twin program: two same-atom wide(A) facts, a rule
    whose clause bound [0.1,1] discriminates intersect from override."""
    if update_mode is not None:
        pyreason._state_obj.settings.update_mode = update_mode
    g = nx.DiGraph()
    g.add_nodes_from(["A", "B"])
    g.add_edge("A", "B", rel=1)
    pr.load_graph(g)
    pr.add_rule(Rule("derived(y) <-1 wide(x):[0.1,1.0], rel(x,y)", "derived_rule"))
    pr.add_fact(Fact("wide(A):[0.2,1.0]", "wide_fact_1", 0, 0))
    pr.add_fact(Fact("wide(A):[0.0,0.8]", "wide_fact_2", 0, 0))
    return pr.reason(timesteps=2)


def test_update_mode_default_intersects_same_atom_facts(pr):
    """proves: under the default update_mode='intersection' two same-atom
    facts intersect ([0.2,1] then [0,0.8] -> [0.2,0.8]), which satisfies the
    rule's [0.1,1] clause bound so derived(B) appears at t=1
    (world.update at the pin; banked update-mode-default)."""
    interp = _update_mode_program(pr)
    frames = pr.filter_and_sort_nodes(interp, ['wide', 'derived'])
    assert [list(r) for r in frames[0].itertuples(index=False, name=None)] == [
        ['A', [0.2, 0.8], [0, 1]]]
    assert [list(r) for r in frames[1].itertuples(index=False, name=None)] == [
        ['B', [0, 1], [1, 1]]]


def test_update_mode_override_replaces_bounds_wholesale(pr):
    """proves: update_mode='override' replaces bounds instead of
    intersecting (set_lower_upper vs world.update at the pin): the second
    fact wins ([0,0.8]), its lower bound fails the [0.1,1] clause bound, and
    derived(B) never appears (banked update-mode-override)."""
    interp = _update_mode_program(pr, update_mode='override')
    frames = pr.filter_and_sort_nodes(interp, ['wide', 'derived'])
    assert [list(r) for r in frames[0].itertuples(index=False, name=None)] == [
        ['A', [0, 0.8], [0, 1]]]
    assert all(f.empty for f in frames[1:])


def test_update_mode_junk_string_behaves_as_intersection(pr):
    """proves: the update_mode setter type-checks only, so an unrecognized
    string silently behaves as intersection (every consumption site is a
    string-equality against 'override') while the knob reads back the junk
    verbatim (banked update-mode-junk-string digest-equals its default
    twin on every reasoning probe)."""
    interp = _update_mode_program(pr, update_mode='junk')
    assert pyreason.settings.update_mode == 'junk'
    frames = pr.filter_and_sort_nodes(interp, ['wide', 'derived'])
    assert [list(r) for r in frames[0].itertuples(index=False, name=None)] == [
        ['A', [0.2, 0.8], [0, 1]]]
    assert [list(r) for r in frames[1].itertuples(index=False, name=None)] == [
        ['B', [0, 1], [1, 1]]]


def _static_graph_facts_program(pr, static_graph_facts=None):
    """The static-graph-facts twin program: one attributed node + edge under
    persistent=False, so the stamping decides whether the graph-attribute
    bounds survive the per-timestep reset."""
    pyreason._state_obj.settings.persistent = False
    if static_graph_facts is not None:
        pyreason._state_obj.settings.static_graph_facts = static_graph_facts
    g = nx.DiGraph()
    g.add_node("A", special=1)
    g.add_node("B")
    g.add_edge("A", "B", rel=1)
    pr.load_graph(g)
    pr.add_rule(Rule("derived(y) <-1 special(x), rel(x,y)", "derived_rule"))
    return pr.reason(timesteps=2)


def test_static_graph_facts_on_escapes_reset_and_rederives(pr):
    """proves: with the default static_graph_facts=True the generated
    graph-attribute facts are stamped static at load time
    (graphml_parser.py:60/90 via pyreason.py:603), so under persistent=False
    the special/rel bounds escape the per-timestep reset, the rule regrounds
    every step (derived(B) at t=1 AND t=2), and the regrounding holds
    perfect convergence open through t=2 (get_time 3; banked
    static-graph-facts-on)."""
    interp = _static_graph_facts_program(pr)
    assert pyreason.settings.static_graph_facts is True
    assert pr.get_time() == 3
    frames = pr.filter_and_sort_nodes(interp, ['derived'])
    assert len(frames) == 3
    assert [list(r) for r in frames[1].itertuples(index=False, name=None)] == [
        ['B', [1, 1]]]
    assert [list(r) for r in frames[2].itertuples(index=False, name=None)] == [
        ['B', [1, 1]]]


def test_static_graph_facts_off_resets_and_converges_earlier(pr):
    """proves: static_graph_facts=False stamps the graph-attribute facts
    non-static, so under persistent=False the special/rel bounds reset to
    [0,1] at every t>0 (interpretation.py:260-273), the rule grounds only at
    t=0 (derived(B) at t=1 only), and perfect convergence fires a step
    earlier (get_time 2; banked static-graph-facts-off)."""
    interp = _static_graph_facts_program(pr, static_graph_facts=False)
    assert pr.get_time() == 2
    frames = pr.filter_and_sort_nodes(interp, ['derived'])
    assert len(frames) == 2
    assert [list(r) for r in frames[1].itertuples(index=False, name=None)] == [
        ['B', [1, 1]]]


def _hello_world_graph():
    """The hello-world friends graph (docs/hello-world.py) — the program the
    fp/parallel twin cases run."""
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary", "Justin", "Dog", "Cat"])
    for s, t in (("Justin", "Mary"), ("John", "Mary"), ("John", "Justin")):
        g.add_edge(s, t, Friends=1)
    for s, t in (("Mary", "Cat"), ("Justin", "Cat"), ("Justin", "Dog"),
                 ("John", "Dog")):
        g.add_edge(s, t, owns=1)
    return g


def _hello_world_run(pr, **settings):
    for knob, value in settings.items():
        setattr(pyreason._state_obj.settings, knob, value)
    pr.load_graph(_hello_world_graph())
    pr.add_rule(Rule("popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)",
                     "popular_rule"))
    pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
    return pr.reason(timesteps=2)


def test_fp_version_runs_the_pinned_fp_schedule(pr):
    """proves: fp_version=True selects the fp schedule, whose observable
    output is the pinned fp variant's, not the default kernel's — fact rows
    for all timesteps sort before the rule rows their pass produced, trace
    rows carry the PASS counter (facts and first-pass conclusions at fp 0,
    the second-pass John derivation at fp 1), the t=2 Justin re-derivation
    duplicates its Friends grounding (the per-timestep worlds re-enter the
    shared predicate map each timestep), and the t=2 frame orders
    [Mary, Justin, John] (banked fp-version-on, interpretation_fp.py:251-807)."""
    interp = _hello_world_run(pr, fp_version=True)
    assert pr.get_time() == 3
    node_frame, _ = pr.get_rule_trace(interp)
    rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    assert [(r[0], r[1], r[2], r[8]) for r in rows] == [
        (0, 0, 'Mary', 'Fact'), (1, 0, 'Mary', 'Fact'), (2, 0, 'Mary', 'Fact'),
        (1, 0, 'Justin', 'Rule'), (2, 0, 'Justin', 'Rule'),
        (2, 1, 'John', 'Rule'),
    ]
    # The pass-0 t=1 grounding sees Mary in the predicate map twice (t=0 and
    # t=1 fact applications), so the enqueued t=2 conclusion carries the
    # duplicated qualified edge.
    assert rows[4][11] == [('Justin', 'Mary'), ('Justin', 'Mary')]
    # John's pass-1 grounding: Mary three times, Justin twice.
    assert rows[5][11] == [('John', 'Mary')] * 3 + [('John', 'Justin')] * 2
    frames = pr.filter_and_sort_nodes(interp, ['popular'])
    assert [r[0] for r in frames[2].itertuples(index=False, name=None)] == [
        'Mary', 'Justin', 'John']


def test_parallel_masks_fp_and_runs_the_default_schedule(pr):
    """proves: parallel_computing=True masks fp_version entirely (the pinned
    dispatch checks parallel first, program.py:42-47) and the parallel arm's
    observable output is the default kernel's (banked parallel-computing-on
    and parallel-fp-precedence digest-equal the default twin): fp counters
    advance per inner fixed-point round, fact rows interleave per timestep,
    no grounding duplicates, and the t=2 frame orders [Mary, John, Justin]."""
    interp = _hello_world_run(pr, fp_version=True, parallel_computing=True)
    assert pyreason.settings.parallel_computing is True
    assert pyreason.settings.fp_version is True
    assert pr.get_time() == 3
    node_frame, _ = pr.get_rule_trace(interp)
    rows = [list(r) for r in node_frame.itertuples(index=False, name=None)]
    assert [(r[0], r[1], r[2], r[8]) for r in rows] == [
        (0, 0, 'Mary', 'Fact'),
        (1, 1, 'Mary', 'Fact'), (1, 1, 'Justin', 'Rule'),
        (2, 2, 'Mary', 'Fact'), (2, 2, 'John', 'Rule'), (2, 2, 'Justin', 'Rule'),
    ]
    assert rows[5][11] == [('Justin', 'Mary')]
    frames = pr.filter_and_sort_nodes(interp, ['popular'])
    assert [r[0] for r in frames[2].itertuples(index=False, name=None)] == [
        'Mary', 'John', 'Justin']
