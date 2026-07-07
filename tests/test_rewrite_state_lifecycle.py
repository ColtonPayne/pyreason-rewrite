"""Seam tests for the cross-run state lifecycle, at the module-global facade.

The territory AC-5 names: the reset family's exact clear/survive split,
reason(again=..., restart=...) resume semantics, the persistent/canonical
knob's reasoning effect, and the interpretation's dict view. Every expected
value is hand-derived from the pinned source (anchors in the docstrings) and
cross-checked against the banked oracle artifacts for the session-18 case
family; the deliberately-reproduced pinned quirks (half-cleared program,
List(None) TypeError, restart-true KeyError) are the compared behaviors, not
accidents.
"""

import pytest

import networkx as nx

import pyreason
from pyreason import Fact, Rule
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


def _popular_graph():
    """The hello-world graph: three friends and their pets."""
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary", "Justin", "Dog", "Cat"])
    for e in [("Justin", "Mary"), ("John", "Mary"), ("John", "Justin")]:
        g.add_edge(*e, Friends=1)
    for e in [("Mary", "Cat"), ("Justin", "Cat"), ("Justin", "Dog"),
              ("John", "Dog")]:
        g.add_edge(*e, owns=1)
    return g


def _load_popular(pr, fact_end=2, extra_facts=()):
    pr.load_graph(_popular_graph())
    pr.add_rule(Rule("popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)",
                     "popular_rule"))
    pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, fact_end))
    for f in extra_facts:
        pr.add_fact(f)


def _rows(frame):
    return list(frame.itertuples(index=False, name=None))


# --- the reset family ---

def test_reset_with_no_program_clears_inputs_and_get_time_answers_zero(pr):
    """proves: reset() before any reason() clears the loaded rules/facts so a
    subsequent reason() raises the no-rules Exception, while get_time still
    answers 0 through the missing-program catch (oracle pyreason.py:487-507,
    549-558)."""
    _load_popular(pr)
    pr.reset()
    assert pr.get_time() == 0
    assert pr.get_rules() is None
    assert pr.get_logic_program() is None
    with pytest.raises(Exception, match=r'There are no rules'):
        pr.reason(timesteps=1)


def test_reset_with_live_program_leaves_it_half_cleared(pr):
    """proves: reset() after a reason() keeps the program object itself but
    nulls its interpretation — get_logic_program returns the SAME object with
    interp None, get_interpretation returns None without raising, and
    get_time trips the pinned AttributeError on None.time instead of
    answering 0 (oracle pyreason.py:498-504 + program.reset_graph)."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    program_before = pr.get_logic_program()
    assert program_before.interp is interp

    pr.reset()
    assert pr.get_logic_program() is program_before
    assert program_before.interp is None
    assert pr.get_interpretation() is None
    with pytest.raises(AttributeError, match=r"'NoneType' object has no attribute 'time'"):
        pr.get_time()


def test_reset_keeps_settings_clause_maps_and_stale_trace_consumable(pr):
    """proves: reset() does NOT touch settings or the clause maps, so a
    caller's stale interpretation reference still renders the full
    atom-traced rule trace afterwards (oracle reset() clears only
    facts/graph/rules, pyreason.py:487-507; __clause_maps survives)."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    rows_before = _rows(pr.get_rule_trace(interp)[0])

    pr.reset()
    assert pr.settings.atom_trace is True  # settings survive
    node_frame, _ = pr.get_rule_trace(interp)  # stale reference, still renders
    assert _rows(node_frame) == rows_before
    assert 'Clause-1' in node_frame.columns  # clause maps survived the reset


def test_reset_then_fresh_and_resumed_reason_raise_the_pinned_pair(pr):
    """proves: after a with-program reset(), a fresh reason() raises the
    no-rules Exception and a resumed reason(again=True) raises the pinned
    fact-conversion TypeError — the half-cleared ordering interaction
    (oracle pyreason.py:1549-1550, 1636)."""
    _load_popular(pr)
    pr.reason(timesteps=2)
    pr.reset()
    with pytest.raises(Exception, match=r'There are no rules'):
        pr.reason(timesteps=1)
    with pytest.raises(TypeError, match=r'List\(\) argument must be iterable'):
        pr.reason(timesteps=1, again=True)


def test_reset_rules_keeps_interpretation_facts_and_graph(pr):
    """proves: reset_rules() clears rules and the annotation/head-function
    registries but leaves the interpretation (get_time still answers), the
    loaded graph, and the fact-name ledger — re-adding a rule and a fact
    reasons again without reloading the graph (oracle pyreason.py:517-527)."""
    _load_popular(pr)
    pr.reason(timesteps=2)
    pr.add_annotation_function(lambda annotations, weights: (0.5, 1.0))
    state = pyreason._state_obj

    pr.reset_rules()
    assert pr.get_time() == 3          # interpretation survives
    assert pr.get_rules() is None
    assert state.annotation_functions == [] and state.head_functions == []
    with pytest.raises(Exception, match=r'There are no rules'):
        pr.reason(timesteps=1)

    # Graph survived: re-seed rule + fact and a fresh run derives again
    pr.add_rule(Rule("popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)",
                     "popular_rule"))
    pr.add_fact(Fact("popular(Mary)", "re_seed", 0, 2))
    interp = pr.reason(timesteps=2)
    assert interp.time == 2


def test_reset_settings_changes_the_next_runs_trace_shape(pr):
    """proves: reset_settings() restores the defaults (atom_trace off), so a
    rebuilt run's trace loses its Clause columns and 'Occurred Due To'
    degrades to the '-' placeholder while 'Triggered By' still names
    Fact/Rule — the always class observed through trace shape, matching the
    banked reset-settings-restore trace-atom-off rows (oracle
    pyreason.py:561-565; defaults at 65-83)."""
    _load_popular(pr)
    interp1 = pr.reason(timesteps=2)
    frame1, _ = pr.get_rule_trace(interp1)
    assert 'Clause-1' in frame1.columns

    pr.reset_settings()
    assert pr.settings.atom_trace is False and pr.settings.verbose is True
    pr.settings.verbose = False  # keep the test quiet; not part of the claim

    pr.add_fact(Fact("popular(Mary)", "re_seed", 0, 2))
    interp2 = pr.reason(timesteps=2)
    frame2, _ = pr.get_rule_trace(interp2)
    assert all(not c.startswith('Clause-') for c in frame2.columns)
    rows2 = _rows(frame2)
    assert [r[6] for r in rows2] == ['-'] * len(rows2)   # no atom detail
    assert {r[8] for r in rows2} == {'Fact', 'Rule'}     # sources still named


# --- reason(again=..., restart=...) ---

def test_again_with_no_program_degrades_to_a_fresh_run(pr):
    """proves: reason(again=True) as the first reasoning call takes the
    fresh-run branch (the `not again or program is None` short-circuit,
    oracle pyreason.py:1516) — it completes and yields the same time and
    node frames as a literal fresh run."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2, again=True)
    assert pr.get_time() == 3
    frames = pr.filter_and_sort_nodes(interp, ["popular"])
    assert [_rows(f) for f in frames] == [
        [("Mary", [1.0, 1.0])],
        [("Mary", [1.0, 1.0]), ("Justin", [1.0, 1.0])],
        [("Mary", [1.0, 1.0]), ("John", [1.0, 1.0]), ("Justin", [1.0, 1.0])],
    ]


def test_bare_again_with_no_new_facts_raises_the_pinned_typeerror(pr):
    """proves: reason() clears the fact lists on exit, so an immediate
    reason(again=True) with nothing added since raises the pinned
    TypeError('List() argument must be iterable') instead of silently
    resuming (oracle pyreason.py:1622-1624 clears, 1636 converts None)."""
    _load_popular(pr)
    pr.reason(timesteps=2)
    with pytest.raises(TypeError, match=r'List\(\) argument must be iterable'):
        pr.reason(timesteps=1, again=True)
    assert pr.get_time() == 3  # the failed resume left the clock alone


def test_again_restart_false_continues_the_timeline(pr):
    """proves: reason(again=True, restart=False) extends tmax from the
    resumed clock (program.py:57), so time grows 3 -> 4 and the resume
    fact's 0-0 window sits behind the clock — the final frame is empty and
    the interpretation dict gains an empty t=3 layer."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    assert pr.get_time() == 3

    pr.add_fact(Fact("popular(Justin)", "resume_fact", 0, 0))
    interp2 = pr.reason(timesteps=2, again=True, restart=False)
    assert interp2 is interp  # the same interpretation is re-driven
    assert pr.get_time() == 4

    frames = pr.filter_and_sort_nodes(interp2, ["popular"])
    assert len(frames) == 4 and _rows(frames[3]) == []
    d = interp2.get_dict()
    assert sorted(d) == [0, 1, 2, 3]
    assert d[3] == {comp: {} for comp in d[3]}  # nothing landed at t=3


def test_again_restart_true_resets_clock_under_an_intact_trace(pr):
    """proves: reason(again=True, restart=True) after a completed run resets
    the clock (time 0, get_time 1) while the rule trace keeps the first
    run's t=1,2 rows, so the trace-reconstructing views — get_dict and
    filter_and_sort_nodes — raise the pinned KeyError(1), while
    get_rule_trace still renders every row (program.py:54-56; the banked
    oracle-bug-candidate this packet reproduces deliberately)."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    rows_before = len(_rows(pr.get_rule_trace(interp)[0]))

    pr.add_fact(Fact("popular(Justin)", "resume_fact", 0, 0))
    interp2 = pr.reason(timesteps=2, again=True, restart=True)
    assert pr.get_time() == 1
    with pytest.raises(KeyError) as exc_dict:
        interp2.get_dict()
    assert exc_dict.value.args == (1,)
    with pytest.raises(KeyError) as exc_nodes:
        pr.filter_and_sort_nodes(interp2, ["popular"])
    assert exc_nodes.value.args == (1,)
    assert len(_rows(pr.get_rule_trace(interp2)[0])) >= rows_before


# --- persistent / canonical over the reasoning loop ---

def test_persistent_off_resets_bounds_each_timestep_except_static(pr):
    """proves: with persistent at its default False every non-static bound
    resets to [0,1] at each new timestep — a 0-0 fact's derivation travels
    instead of accumulating — while a static fact's bound escapes the reset
    (interpretation.py:260-270 at the pin; the persistent-off case's banked
    frames)."""
    _load_popular(pr, fact_end=0,
                  extra_facts=[Fact("special(Dog)", "special_fact", 0, 0, True)])
    interp = pr.reason(timesteps=2)
    frames = pr.filter_and_sort_nodes(interp, ["popular", "special"])
    assert [_rows(f) for f in frames] == [
        [("Mary", [1.0, 1.0], [0, 1]), ("Dog", [0, 1], [1.0, 1.0])],
        [("Dog", [0, 1], [1.0, 1.0]), ("Justin", [1.0, 1.0], [0, 1])],
        [("Dog", [0, 1], [1.0, 1.0]), ("John", [1.0, 1.0], [0, 1])],
    ]


def test_persistent_on_accumulates_and_get_dict_propagates(pr):
    """proves: persistent=True skips the per-timestep reset, so a bound set
    once persists without re-derivation — invisible to the change-driven
    filter frames (identical to persistent-off's, the banked contrast) but
    visible through get_dict's persistent arm, which stamps each change onto
    every later timestep (oracle interpretation.py:707-740; the banked
    persistent-on/off interp-dict diff is exactly Mary@1,2 + Justin@2)."""
    pr.settings.persistent = True
    _load_popular(pr, fact_end=0,
                  extra_facts=[Fact("special(Dog)", "special_fact", 0, 0, True)])
    interp = pr.reason(timesteps=2)
    frames = pr.filter_and_sort_nodes(interp, ["popular", "special"])
    # The trace shows only CHANGES, so the frames match persistent-off's
    assert [_rows(f) for f in frames] == [
        [("Mary", [1.0, 1.0], [0, 1]), ("Dog", [0, 1], [1.0, 1.0])],
        [("Dog", [0, 1], [1.0, 1.0]), ("Justin", [1.0, 1.0], [0, 1])],
        [("Dog", [0, 1], [1.0, 1.0]), ("John", [1.0, 1.0], [0, 1])],
    ]

    d = interp.get_dict()
    assert d[1]["Mary"]["popular"] == (1.0, 1.0)    # stamped forward
    assert d[2]["Mary"]["popular"] == (1.0, 1.0)
    assert d[2]["Justin"]["popular"] == (1.0, 1.0)  # t=1 change, stamped to 2
    assert d[1]["John"] == {}                        # derived only at t=2


def test_get_dict_nonpersistent_keeps_changes_at_their_own_timestep(pr):
    """proves: get_dict rebuilds {t: {component: {label: (l, u)}}} from the
    stored trace — every graph component appears at every timestep (empty
    map when untouched), and without persistent a change stays at its own
    timestep only (oracle interpretation.py:707-740)."""
    _load_popular(pr, fact_end=0)
    interp = pr.reason(timesteps=2)
    d = interp.get_dict()
    assert sorted(d) == [0, 1, 2]
    assert set(d[0]) == set(interp.nodes) | set(interp.edges)
    assert d[0]["Mary"] == {"popular": (1.0, 1.0)}
    assert "popular" not in d[1]["Mary"]  # non-persistent: no forward stamp
    assert d[1]["Justin"] == {"popular": (1.0, 1.0)}
    assert d[0][("John", "Dog")] == {}


def test_canonical_knob_drives_the_same_reset_skip_as_persistent(pr):
    """proves: setting canonical=True alone flips the shared persistent
    store and the reasoning loop skips the per-timestep reset exactly as
    under persistent=True — the alias is live at the loop seam, not just at
    the settings object (oracle pyreason.py:357/:167; interpretation.py:260)."""
    pr.settings.canonical = True
    assert pr.settings.persistent is True
    _load_popular(pr, fact_end=0)
    interp = pr.reason(timesteps=2)
    d = interp.get_dict()
    assert d[2]["Mary"]["popular"] == (1.0, 1.0)  # persisted through t=2
