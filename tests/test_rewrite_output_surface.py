"""Seam tests for the output surface, at the module-global facade.

The slice-6 territory: the stdout redirect (`settings.output_to_file` /
`output_file_name`), the memory-profile observation wrapper's peak-MB line
(stdlib-only in the rewrite — the pinned memory_profiler backend is a
dependency this campaign never installs), save_rule_trace's CSV pair, and
reason(queries=...)'s ruleset filtering. Every expected value is hand-derived
from the pinned source (anchors in the docstrings) and cross-checked against
the results-phase3-slice6 oracle-vs-rewrite artifacts. These are I/O-seam
tests on purpose: files read back from the confined tmp cwd, sys.stdout
identity checked — not just the pure helpers underneath.
"""

import csv
import os
import re
import sys

import pytest

import networkx as nx

import pyreason
from pyreason import Fact, Query, Rule
from pyreason import _program
from pyreason._state import EngineState

# The peak-MB line the pinned profiled branch prints (pyreason.py:1520) and
# the harness canonicalizes (PEAK_MB_RE, harness/capture.py) — the fixed text
# plus any decimal/scientific number is the contractual shape.
PEAK_MB_RE = re.compile(r"^Program used -?\d+(?:\.\d+)?(?:e[+-]?\d+)? "
                        r"MB of memory$", re.M)
# The pinned redirect / trace-file stamp (pyreason.py:1511): %Y%m%d-%H%M%S.
STAMP = r"\d{8}-\d{6}"


@pytest.fixture
def pr(monkeypatch, tmp_path):
    """The facade over a fresh engine state, confined to a tmp cwd (the
    redirect path and save_rule_trace's default folder are cwd-relative at
    the pin), with sys.stdout restored after the engine's rebind."""
    fresh = EngineState()
    fresh.settings.verbose = False
    fresh.settings.atom_trace = True
    monkeypatch.setattr(pyreason, "_state_obj", fresh)
    monkeypatch.setattr(pyreason, "settings", fresh.settings)
    monkeypatch.chdir(tmp_path)
    # The engine rebinds sys.stdout and never restores it (pinned semantics);
    # monkeypatch snapshots the current object and puts it back at teardown.
    monkeypatch.setattr(sys, "stdout", sys.stdout)
    return pyreason


def _popular_graph():
    """The hello-world graph: three friends and their pets (7 edges > 5
    nodes, so the clause-reorder pass runs)."""
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary", "Justin", "Dog", "Cat"])
    for e in [("Justin", "Mary"), ("John", "Mary"), ("John", "Justin")]:
        g.add_edge(*e, Friends=1)
    for e in [("Mary", "Cat"), ("Justin", "Cat"), ("Justin", "Dog"),
              ("John", "Dog")]:
        g.add_edge(*e, owns=1)
    return g


def _load_popular(pr):
    pr.load_graph(_popular_graph())
    pr.add_rule(Rule("popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)",
                     "popular_rule"))
    pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))


def _load_two_rule_query_program(pr):
    """The reason-queries pair's program: two independent rules, facts for
    both bodies."""
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary", "Justin"])
    g.add_edge("John", "Mary", Friends=1)
    g.add_edge("John", "Justin", Friends=1)
    pr.load_graph(g)
    pr.add_rule(Rule("cool(x) <-1 popular(x)", "cool_rule"))
    pr.add_rule(Rule("busy(x) <-1 owner(x)", "busy_rule"))
    pr.add_fact(Fact("popular(Mary)", "popular_fact", 0, 2))
    pr.add_fact(Fact("owner(John)", "owner_fact", 0, 2))


def _txt_files():
    return sorted(p for p in os.listdir(".") if p.endswith(".txt"))


def _csv_files(folder="."):
    return sorted(p for p in os.listdir(folder) if p.endswith(".csv"))


# --- the output-to-file family ---

def test_output_to_file_rebinds_stdout_and_writes_redirect_file(pr):
    """proves: with output_to_file on, reason() rebinds this process's
    sys.stdout to ./pyreason_output_<stamp>.txt opened in the cwd and the
    verbose reasoning prints land in that file, not on the prior stdout
    (oracle pyreason.py:1513-1514/:1541-1542)."""
    before = sys.stdout
    pr.settings.verbose = True
    pr.settings.output_to_file = True
    _load_popular(pr)
    pr.reason(timesteps=2)
    assert sys.stdout is not before  # actually rebound, never restored
    sys.stdout.flush()
    files = _txt_files()
    assert len(files) == 1
    assert re.fullmatch(rf"pyreason_output_{STAMP}\.txt", files[0])
    content = open(files[0]).read()
    for line in ("Filtering rules based on queries",
                 "Optimizing rules by moving node clauses ahead of edge clauses",
                 "Timestep: 0", "Timestep: 2", "\nConverged at time: 2",
                 "Fixed Point iterations: 3"):
        assert line in content


def test_output_file_name_interpolated_verbatim_into_redirect_path(pr):
    """proves: the output_file_name knob's string is interpolated verbatim
    into the redirect file's name when output_to_file is on (oracle
    pyreason.py:1514 — no path validation)."""
    pr.settings.output_to_file = True
    pr.settings.output_file_name = "campaign_redirect"
    _load_popular(pr)
    pr.reason(timesteps=2)
    sys.stdout.flush()
    files = _txt_files()
    assert len(files) == 1
    assert re.fullmatch(rf"campaign_redirect_{STAMP}\.txt", files[0])


def test_output_file_name_inert_when_output_to_file_off(pr):
    """proves: with output_to_file left default False, a set output_file_name
    writes nothing anywhere and stdout is never rebound — the knob's only
    consumption sites are the redirect-guarded opens (oracle
    pyreason.py:1514/:1542)."""
    before = sys.stdout
    pr.settings.output_file_name = "campaign_redirect"
    _load_popular(pr)
    pr.reason(timesteps=2)
    assert sys.stdout is before
    assert _txt_files() == []


# --- the memory-profile family ---

def test_memory_profile_prints_peak_line_after_reasoning(pr, capsys):
    """proves: with memory_profile on, reason() prints the pinned
    '\\nProgram used <number> MB of memory' line (fixed text, run-varying
    number — oracle pyreason.py:1520) to stdout after the reasoning
    completes, and returns the same interpretation the direct branch would
    (get_time still answers over it)."""
    pr.settings.memory_profile = True
    _load_popular(pr)
    pr.reason(timesteps=2)
    out = capsys.readouterr().out
    assert PEAK_MB_RE.search(out)
    # The observation wrapper's retval is the interpretation itself
    assert pr.get_time() == 3


def test_memory_profile_default_off_prints_no_peak_line(pr, capsys):
    """proves: with memory_profile left default False, reason() takes the
    direct dispatch branch and no peak-MB line is printed (oracle
    pyreason.py:1522)."""
    _load_popular(pr)
    pr.reason(timesteps=2)
    assert not PEAK_MB_RE.search(capsys.readouterr().out)


def test_memory_profile_peak_line_lands_in_redirect_file(pr):
    """proves: with memory_profile AND output_to_file both on, the peak-MB
    line lands in the redirect file after the verbose reasoning prints —
    the interaction-output class (oracle pyreason.py:1513-1520)."""
    pr.settings.verbose = True
    pr.settings.memory_profile = True
    pr.settings.output_to_file = True
    _load_popular(pr)
    pr.reason(timesteps=2)
    sys.stdout.flush()
    files = _txt_files()
    assert len(files) == 1
    content = open(files[0]).read()
    match = PEAK_MB_RE.search(content)
    assert match
    assert "Fixed Point iterations: 3" in content[:match.start()]


def test_memory_profile_is_stdlib_only(pr):
    """proves: the rewrite's profiled branch never imports memory_profiler
    (or any other non-stdlib backend) — the peak measurement rides the
    stdlib resource module, so a profiled reason() leaves memory_profiler
    unloaded (AC-2: no new dependency)."""
    pr.settings.memory_profile = True
    _load_popular(pr)
    pr.reason(timesteps=2)
    assert "memory_profiler" not in sys.modules
    assert "resource" in sys.modules


# --- the save_rule_trace family ---

def test_save_rule_trace_writes_csv_pair_into_cwd(pr):
    """proves: save_rule_trace with the pinned default folder './' writes
    rule_trace_{nodes,edges}_<stamp>.csv into the cwd, stamped with the last
    reason()'s timestamp, and the node CSV's cells round-trip to
    get_rule_trace's frame (str-rendered) with the atom-trace Clause-1..4
    header (oracle output.py:99-105)."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    pr.save_rule_trace(interp)
    stamp = pr._state_obj.timestamp
    assert _csv_files() == [f"rule_trace_edges_{stamp}.csv",
                            f"rule_trace_nodes_{stamp}.csv"]
    with open(f"rule_trace_nodes_{stamp}.csv", newline="") as f:
        rows = list(csv.reader(f))
    frame = pr.get_rule_trace(interp)[0]
    assert rows[0] == frame.columns
    assert rows[0][:10] == ['Time', 'Fixed-Point-Operation', 'Node', 'Label',
                            'Old Bound', 'New Bound', 'Occurred Due To',
                            'Consistent', 'Triggered By', 'Inconsistency Message']
    assert rows[0][10:] == ['Clause-1', 'Clause-2', 'Clause-3', 'Clause-4']
    expected = [["" if cell is None else str(cell) for cell in row]
                for row in frame.itertuples(index=False, name=None)]
    assert rows[1:] == expected


def test_save_rule_trace_folder_variant_writes_identical_files(pr):
    """proves: a caller-passed folder is joined verbatim (oracle
    pyreason.py:1645 folder passthrough) and receives the byte-identical
    CSV pair the default './' call writes."""
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    pr.save_rule_trace(interp)
    os.mkdir("traces")
    pr.save_rule_trace(interp, "traces")
    stamp = pr._state_obj.timestamp
    for kind in ("nodes", "edges"):
        name = f"rule_trace_{kind}_{stamp}.csv"
        assert open(name, "rb").read() == open(os.path.join("traces", name), "rb").read()


def test_save_rule_trace_atom_trace_off_keeps_fixed_header_and_placeholders(pr):
    """proves: with atom_trace off the saved node CSV keeps exactly the
    fixed 10-column header (no Clause-i columns) and every row's Old Bound
    and Occurred Due To stay the '-' placeholders on this IPL-free program
    — the engine banked empty trace names, so the r[7]-name fallback never
    fires (oracle output.py:23-25, interpretation.py:1544-1549)."""
    pr.settings.atom_trace = False
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    pr.save_rule_trace(interp)
    stamp = pr._state_obj.timestamp
    with open(f"rule_trace_nodes_{stamp}.csv", newline="") as f:
        rows = list(csv.reader(f))
    assert len(rows[0]) == 10
    assert len(rows) > 1
    for row in rows[1:]:
        assert row[4] == "-" and row[6] == "-"


def test_save_rule_trace_store_off_asserts_before_any_write(pr):
    """proves: with store_interpretation_changes off, save_rule_trace fails
    its assert with the pinned (get_rule_trace-shared) message before any
    file I/O — the confined cwd stays empty (oracle pyreason.py:1652)."""
    pr.settings.store_interpretation_changes = False
    _load_popular(pr)
    interp = pr.reason(timesteps=2)
    with pytest.raises(AssertionError,
                       match=r"store interpretation changes setting is off, "
                             r"turn on to save rule trace"):
        pr.save_rule_trace(interp)
    assert _csv_files() == []


# --- the reason(queries=...) pair ---

def test_reason_queries_filters_ruleset_permanently(pr):
    """proves: reason(queries=[Query('cool(Mary)')]) filters the two-rule
    set by predicate to the one rule targeting 'cool' and the narrowing is
    permanent — post-reason get_rules holds only cool_rule and the trace
    carries no busy derivation even though owner(John) would have fired
    busy_rule (oracle pyreason.py:1591-1595, filter_ruleset.py:17)."""
    _load_two_rule_query_program(pr)
    interp = pr.reason(timesteps=2, queries=[Query("cool(Mary)")])
    assert [r.get_rule_name() for r in pr.get_rules()] == ["cool_rule"]
    labels = {row[3] for row in
              pr.get_rule_trace(interp)[0].itertuples(index=False, name=None)}
    assert "cool" in labels and "busy" not in labels


def test_reason_queries_no_match_raises_pinned_fingerprint_error(pr):
    """proves: a query matching no rule's target filters the ruleset to
    empty and reason() then raises the pinned kernel-dispatch ValueError
    verbatim; the filtering already happened and is permanent — post-raise
    get_rules returns the empty list, and the program object exists holding
    a live interpretation exactly as the pin's does (oracle
    pyreason.py:1594-1595 + the numba dispatch raise)."""
    _load_two_rule_query_program(pr)
    with pytest.raises(ValueError,
                       match=r"cannot compute fingerprint of empty list"):
        pr.reason(timesteps=2, queries=[Query("famous(Mary)")])
    assert pr.get_rules() == []
    program = pr.get_logic_program()
    assert program is not None and program.interp is not None


def test_reason_queries_keep_transitive_body_support(pr):
    """proves: the query filter keeps rules reachable transitively through
    surviving rules' clause targets, not just direct target matches (oracle
    filter_ruleset.py:22-24) — a cool query keeps the popular rule feeding
    cool's body."""
    g = nx.DiGraph()
    g.add_nodes_from(["John", "Mary"])
    g.add_edge("John", "Mary", Friends=1)
    pr.load_graph(g)
    pr.add_rule(Rule("cool(x) <-1 popular(x)", "cool_rule"))
    pr.add_rule(Rule("popular(x) <-1 famous(x)", "popular_rule"))
    pr.add_rule(Rule("busy(x) <-1 owner(x)", "busy_rule"))
    pr.add_fact(Fact("famous(Mary)", "famous_fact", 0, 2))
    pr.reason(timesteps=2, queries=[Query("cool(Mary)")])
    assert {r.get_rule_name() for r in pr.get_rules()} == {"cool_rule",
                                                           "popular_rule"}


def test_filter_ruleset_terminates_on_self_recursive_rule(pr):
    """proves: the rewrite's filter_ruleset expands each predicate at most
    once, so a query matching a self-recursive rule's head terminates and
    returns the reachable rule set — the recorded deliberate divergence
    from the pin, whose unguarded recursion crashes the pinned process
    outright on this un-caseable input (screened SIGSEGV, banked on
    type:Query's board row; ledger session 14's guard-the-recursion
    contract)."""
    rule_ir = Rule("popular(x) <-1 popular(y), Friends(x,y)", "self_rule").rule
    survivors = _program.filter_ruleset([Query("popular(John)")], [rule_ir])
    assert survivors == [rule_ir]
