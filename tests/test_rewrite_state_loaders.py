"""Seam tests for the rewrite's explicit state, loader family, settings, and
module-global facade.

Loader expectations are the banked oracle behaviors from the loader-family
malformed cases (rules-from-file-malformed, rule-from-csv-malformed,
rule-from-json-malformed, fact-from-csv-malformed, fact-from-json-malformed):
message text verbatim, partial-load state observed through the rule list —
the same seam the harness fingerprints. Loader tests write their own files
via tmp_path so they exercise the real file I/O path; the happy-path tests
load the committed harness fixtures instead — the same files the five
*-basic equivalence cases load.
"""

import json
from pathlib import Path

import networkx as nx
import pytest
import yaml.parser

import pyreason
from pyreason import _loaders
from pyreason._settings import Settings
from pyreason._state import EngineState, add_inconsistent_predicate, add_rule
from pyreason.label import Label
from pyreason.rule import Rule


def _raises_msg(exc_type, msg, fn):
    with pytest.raises(exc_type) as exc_info:
        fn()
    assert str(exc_info.value) == msg
    return exc_info.value


@pytest.fixture
def state():
    s = EngineState()
    s.settings.verbose = False
    return s


# --- explicit state ---

def test_engine_states_are_independent():
    """proves: two EngineStates share nothing — rules added to one leave the
    other's fresh-state Nones intact (the no-hidden-state seam)."""
    a, b = EngineState(), EngineState()
    add_rule(a, Rule("trendy(x) <-1 popular(x)"))
    assert len(a.rules) == 1
    assert b.rules is None and b.program is None


def test_add_rule_autonames_by_position_and_warns_on_duplicate(state):
    """proves: a None rule name becomes rule_<position>; re-adding a taken
    name warns (never raises) and still appends — pinned add semantics."""
    add_rule(state, Rule("trendy(x) <-1 popular(x)"))
    assert state.rules[0].get_rule_name() == "rule_0"
    with pytest.warns(UserWarning, match="rule_0 has already been added"):
        add_rule(state, Rule("trendy(x) <-1 popular(x)", "rule_0"))
    assert len(state.rules) == 2


# --- settings ---

def test_settings_defaults_match_pin():
    """proves: a fresh Settings carries the 18 pinned defaults."""
    s = Settings()
    assert s.verbose is True
    assert s.output_to_file is False
    assert s.output_file_name == "pyreason_output"
    assert s.graph_attribute_parsing is True
    assert s.abort_on_inconsistency is False
    assert s.memory_profile is False
    assert s.reverse_digraph is False
    assert s.atom_trace is False
    assert s.save_graph_attributes_to_trace is False
    assert s.canonical is False
    assert s.persistent is False
    assert s.inconsistency_check is True
    assert s.static_graph_facts is True
    assert s.store_interpretation_changes is True
    assert s.parallel_computing is False
    assert s.update_mode == "intersection"
    assert s.allow_ground_rules is False
    assert s.fp_version is False


def test_settings_setters_validate_types_with_pinned_messages():
    """proves: a wrong-typed set raises TypeError with the pinned message
    per knob family (bool knobs, output_file_name, update_mode), and the
    strict isinstance check rejects int-for-bool."""
    s = Settings()
    _raises_msg(TypeError, "value has to be a bool", lambda: setattr(s, "verbose", 1))
    _raises_msg(TypeError, "file_name has to be a string", lambda: setattr(s, "output_file_name", 3))
    _raises_msg(TypeError, "value has to be a str", lambda: setattr(s, "update_mode", True))
    s.verbose = False
    assert s.verbose is False


def test_settings_canonical_aliases_persistent_and_reset_restores():
    """proves: canonical reads and writes the persistent store (the pinned
    deprecated alias), and reset() restores defaults."""
    s = Settings()
    s.canonical = True
    assert s.persistent is True
    s.persistent = False
    assert s.canonical is False
    s.verbose = False
    s.reset()
    assert s.verbose is True and s.persistent is False


# --- module-global facade ---

def test_facade_fresh_state_accessors():
    """proves: on the pristine module, get_rules and get_logic_program
    return None, get_interpretation raises the pinned bare Exception, and
    get_time swallows that raise into 0 — the accessors-fresh-state class."""
    fresh = EngineState()
    orig = pyreason._state_obj
    pyreason._state_obj = fresh
    try:
        assert pyreason.get_rules() is None
        assert pyreason.get_logic_program() is None
        _raises_msg(Exception, "No interpretation found. Please run `pr.reason()` first",
                    pyreason.get_interpretation)
        assert pyreason.get_time() == 0
    finally:
        pyreason._state_obj = orig


def test_facade_delegates_to_its_one_state():
    """proves: facade mutators write into the module's one EngineState —
    add_rule through the facade is visible through get_rules — and the
    public settings object is that state's settings."""
    fresh = EngineState()
    orig_state, orig_settings = pyreason._state_obj, pyreason.settings
    pyreason._state_obj, pyreason.settings = fresh, fresh.settings
    try:
        pyreason.add_rule(pyreason.Rule("trendy(x) <-1 popular(x)"))
        assert [r.get_rule_name() for r in pyreason.get_rules()] == ["rule_0"]
        assert pyreason.settings is fresh.settings
    finally:
        pyreason._state_obj, pyreason.settings = orig_state, orig_settings


# --- add_rules_from_file ---

BADLINE = "trendy(x) <-1 popular(x)\nthis line is not a rule\ninfluencer(x) <-1 trendy(x)\n"


def test_rules_from_file_missing_file_raises_bare_errno(state, tmp_path):
    """proves: a missing rules file raises open()'s own FileNotFoundError
    (errno text, no loader wrap) — the pinned missing-file arm."""
    path = tmp_path / "nope.txt"
    _raises_msg(FileNotFoundError, f"[Errno 2] No such file or directory: '{path}'",
                lambda: _loaders.add_rules_from_file(state, str(path)))


def test_rules_from_file_raise_errors_wraps_line_and_keeps_partial_load(state, tmp_path):
    """proves: under raise_errors=True the bad middle line raises
    ValueError('Line 2: ...') AFTER line 1 loaded — the raise-then-continue
    state contamination the case pins."""
    path = tmp_path / "rules.txt"
    path.write_text(BADLINE)
    _raises_msg(ValueError,
                "Line 2: Failed to parse rule 'this line is not a rule' - "
                "Rule must contain exactly one '<-' separator, found 0. "
                "Use the format: 'head(X) <- body(X)'",
                lambda: _loaders.add_rules_from_file(state, str(path), raise_errors=True))
    assert [r.get_rule_name() for r in state.rules] == ["rule_0"]


def test_rules_from_file_default_warns_skips_and_leaves_name_gap(state, tmp_path):
    """proves: the default raise_errors=False warns, skips the bad line, and
    names by filtered-line index + preexisting count — the pinned
    rule_1/rule_3 name gap after a prior partial load."""
    path = tmp_path / "rules.txt"
    path.write_text(BADLINE)
    with pytest.raises(ValueError):
        _loaders.add_rules_from_file(state, str(path), raise_errors=True)
    with pytest.warns(UserWarning, match="Line 2: Failed to parse rule"):
        _loaders.add_rules_from_file(state, str(path))
    assert [r.get_rule_name() for r in state.rules] == ["rule_0", "rule_1", "rule_3"]


# --- add_rule_from_csv ---

def test_rule_csv_missing_file_and_empty_file_arms(state, tmp_path):
    """proves: a missing CSV raises the wrapped 'CSV file not found' text;
    a zero-byte CSV warns and returns without raising or loading."""
    missing = tmp_path / "nope.csv"
    _raises_msg(FileNotFoundError, f"CSV file not found: {missing}",
                lambda: _loaders.add_rule_from_csv(state, str(missing)))
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.warns(UserWarning, match="is empty, no rules loaded"):
        _loaders.add_rule_from_csv(state, str(empty))
    assert state.rules is None


def test_rule_csv_missing_text_wraps_with_doubled_row_prefix(state, tmp_path):
    """proves: an empty rule_text cell raises with the doubled Row prefix —
    the inner row message re-wrapped by the row-level except."""
    path = tmp_path / "rules.csv"
    path.write_text(",no_rule_here,,\n")
    _raises_msg(ValueError, "Row 1: Failed to parse rule - Row 1: Missing required 'rule_text'",
                lambda: _loaders.add_rule_from_csv(state, str(path)))


def test_rule_csv_duplicate_name_raises_after_partial_load(state, tmp_path):
    """proves: a file-local duplicate name raises at row 2 AFTER row 1
    loaded — the partial-load contamination the closing fingerprint pins."""
    path = tmp_path / "rules.csv"
    path.write_text("trendy(x) <-1 popular(x),same_name,,\n"
                    "influencer(x) <-1 trendy(x),same_name,,\n")
    _raises_msg(ValueError,
                "Row 2: Failed to parse rule - Row 2: Loaded name 'same_name' "
                "is a duplicate - all rule names must be unique.",
                lambda: _loaders.add_rule_from_csv(state, str(path)))
    assert [r.get_rule_name() for r in state.rules] == ["same_name"]


def test_rule_csv_wide_row_raises_pinned_tokenizer_text(state, tmp_path):
    """proves: a row with more fields than the first row fails wholesale
    with the pinned pandas C-tokenizer text (trailing newline included)
    inside the 'Error reading CSV file' wrap, loading nothing."""
    path = tmp_path / "rules.csv"
    path.write_text("trendy(x) <-1 popular(x),ok_row,,\n"
                    "popular(x) <-1 popular(y) : [0.5,1],unquoted_row,,\n")
    _raises_msg(ValueError,
                f"Error reading CSV file {path}: Error tokenizing data. "
                "C error: Expected 4 fields in line 2, saw 5\n",
                lambda: _loaders.add_rule_from_csv(state, str(path)))
    assert state.rules is None


def test_rule_csv_tokenizer_line_is_record_ordinal_not_physical_line(state, tmp_path):
    """proves: the tokenizer message's line number counts records — a quoted
    field spanning two physical lines counts once, so the wide second record
    reports 'line 2' (pinned pandas semantics, verified against the oracle
    env in the session-16 review; reader.line_num would say 3)."""
    path = tmp_path / "rules.csv"
    path.write_text('"n(x)<-\no(x)",r9,,\n'
                    "q(x)<-s(x),r10,,extra,\n")
    _raises_msg(ValueError,
                f"Error reading CSV file {path}: Error tokenizing data. "
                "C error: Expected 4 fields in line 2, saw 5\n",
                lambda: _loaders.add_rule_from_csv(state, str(path)))


def test_rule_csv_blank_lines_count_in_tokenizer_line_number(state, tmp_path):
    """proves: skipped blank lines still advance the tokenizer message's
    record count — a wide row after three blank lines reports 'line 5'
    (pinned pandas semantics, verified against the oracle env)."""
    path = tmp_path / "rules.csv"
    path.write_text("a(x)<-b(x),r1,,\n\n\n\nc(x)<-d(x),r2,,extra,\n")
    _raises_msg(ValueError,
                f"Error reading CSV file {path}: Error tokenizing data. "
                "C error: Expected 4 fields in line 5, saw 5\n",
                lambda: _loaders.add_rule_from_csv(state, str(path)))


def test_rule_csv_short_row_pads_empty_missing_name_autogenerates(state, tmp_path):
    """proves: a row with fewer fields than the first row pads with '' —
    its missing name cell autonames rule_<n>, never a 'nan' name (pinned
    pandas keep_default_na=False read, verified against the oracle env)."""
    path = tmp_path / "rules.csv"
    path.write_text("a(x)<-b(x),namedrow,,\nz(x)<-y(x)\n")
    _loaders.add_rule_from_csv(state, str(path))
    assert [r.get_rule_name() for r in state.rules] == ["namedrow", "rule_1"]


def test_rule_csv_non_utf8_file_takes_the_pinned_valueerror_wrap(state, tmp_path):
    """proves: a non-UTF8 CSV raises ValueError('Error reading CSV file
    ...: <codec text>') — the pinned wrap, never a raw UnicodeDecodeError
    (codec text verified equal against the oracle env)."""
    path = tmp_path / "rules.csv"
    path.write_bytes(b"a(x)<-b(x),r1,,\n\xff\xfe bad bytes,r2,,\n")
    _raises_msg(ValueError,
                f"Error reading CSV file {path}: 'utf-8' codec can't decode "
                "byte 0xff in position 16: invalid start byte",
                lambda: _loaders.add_rule_from_csv(state, str(path)))


def test_rule_csv_exact_header_row_is_skipped(state, tmp_path):
    """proves: a first row exactly matching the pinned header is skipped and
    row numbering still starts the first data row at Row 2."""
    path = tmp_path / "rules.csv"
    path.write_text("rule_text,name,infer_edges,set_static\n"
                    "trendy(x) <-1 popular(x),r1,,\n")
    _loaders.add_rule_from_csv(state, str(path))
    assert [r.get_rule_name() for r in state.rules] == ["r1"]


# --- add_rule_from_json ---

def test_rule_json_document_level_arms(state, tmp_path):
    """proves: missing file, invalid JSON syntax (json's own position text),
    and a non-array document raise the pinned document-level messages before
    any rule loads."""
    missing = tmp_path / "nope.json"
    _raises_msg(FileNotFoundError, f"JSON file not found: {missing}",
                lambda: _loaders.add_rule_from_json(state, str(missing)))
    bad = tmp_path / "bad.json"
    bad.write_text('[{"rule_text": "trendy(x) <-1 popular(x)",]')
    _raises_msg(ValueError,
                f"Invalid JSON format in file {bad}: Expecting property name "
                "enclosed in double quotes: line 1 column 43 (char 42)",
                lambda: _loaders.add_rule_from_json(state, str(bad)))
    notarray = tmp_path / "na.json"
    notarray.write_text('{"not": "an array"}')
    _raises_msg(ValueError, "JSON file must contain an array of rule objects, got dict",
                lambda: _loaders.add_rule_from_json(state, str(notarray)))
    assert state.rules is None


def test_rule_json_item_and_threshold_arms_wrap_doubled(state, tmp_path):
    """proves: a string item, a threshold missing 'thresh' (KeyError text
    verbatim), and a non-integer custom_thresholds key all re-wrap with the
    doubled Item prefix and load nothing."""
    item = tmp_path / "item.json"
    item.write_text('["trendy(x) <-1 popular(x)"]')
    _raises_msg(ValueError, "Item 0: Failed to parse rule - Item 0: Expected object, got str",
                lambda: _loaders.add_rule_from_json(state, str(item)))

    thr = tmp_path / "thr.json"
    thr.write_text(json.dumps([{"rule_text": "trendy(x) <-1 popular(x)", "name": "t",
                                "custom_thresholds": [{"quantifier": "greater_equal",
                                                       "quantifier_type": ["number", "total"]}]}]))
    _raises_msg(ValueError,
                "Item 0: Failed to parse rule - Item 0, threshold 0: Invalid threshold - 'thresh'",
                lambda: _loaders.add_rule_from_json(state, str(thr)))

    badkey = tmp_path / "badkey.json"
    badkey.write_text(json.dumps([{"rule_text": "trendy(x) <-1 popular(x)", "name": "t",
                                   "custom_thresholds": {"one": {"quantifier": "greater_equal",
                                                                 "quantifier_type": ["number", "total"],
                                                                 "thresh": 1}}}]))
    _raises_msg(ValueError,
                "Item 0: Failed to parse rule - Item 0: custom_thresholds dict key "
                "'one' must be an integer clause index",
                lambda: _loaders.add_rule_from_json(state, str(badkey)))
    assert state.rules is None


# --- add_fact_from_csv ---

def test_fact_csv_malformed_arms(state, tmp_path):
    """proves: missing file, an invalid static cell (doubled Row prefix),
    a missing fact_text cell, and a zero-byte file take the four banked
    fact-CSV arms."""
    missing = tmp_path / "nope.csv"
    _raises_msg(FileNotFoundError, f"CSV file not found: {missing}",
                lambda: _loaders.add_fact_from_csv(state, str(missing)))

    bad_static = tmp_path / "facts.csv"
    bad_static.write_text("popular(Mary),bad-static,0,2,maybe\n")
    _raises_msg(ValueError, "Row 1: Failed to parse fact - Row 1: Invalid static value 'maybe'",
                lambda: _loaders.add_fact_from_csv(state, str(bad_static)))

    no_text = tmp_path / "notext.csv"
    no_text.write_text(",no-text,0,0,\n")
    _raises_msg(ValueError, "Row 1: Failed to parse fact - Row 1: Missing required 'fact_text'",
                lambda: _loaders.add_fact_from_csv(state, str(no_text)))

    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.warns(UserWarning, match="is empty, no facts loaded"):
        _loaders.add_fact_from_csv(state, str(empty))
    assert state.node_facts is None and state.edge_facts is None


def test_fact_csv_happy_row_loads_with_coercions(state, tmp_path):
    """proves: a full happy row loads through the same seam — times
    int-coerce, static string-coerces, and the fact lands in the node list."""
    path = tmp_path / "facts.csv"
    path.write_text("popular(Mary),seen,0,3,true\n")
    _loaders.add_fact_from_csv(state, str(path))
    fact, = state.node_facts
    assert (fact.name, fact.start_time, fact.end_time, fact.static) == ("seen", 0, 3, True)


# --- add_fact_from_json ---

def test_fact_json_malformed_arms(state, tmp_path):
    """proves: bad start_time (doubled Item prefix), unparseable fact_text
    (single prefix — the fact parser's message carries no item tag), and an
    intra-file duplicate name raising AFTER item 0 loaded take the banked
    fact-JSON arms."""
    badtime = tmp_path / "badtime.json"
    badtime.write_text('[{"fact_text": "popular(Mary)", "name": "bad-time", "start_time": "soon"}]')
    _raises_msg(ValueError, "Item 0: Failed to parse fact - Item 0: Invalid start_time 'soon'",
                lambda: _loaders.add_fact_from_json(state, str(badtime)))

    badtext = tmp_path / "badtext.json"
    badtext.write_text('[{"fact_text": "popular(", "name": "bad-text"}]')
    _raises_msg(ValueError, "Item 0: Failed to parse fact - Missing closing parenthesis in fact",
                lambda: _loaders.add_fact_from_json(state, str(badtext)))

    dup = tmp_path / "dup.json"
    dup.write_text('[{"fact_text": "popular(Mary)", "name": "dup"},'
                   ' {"fact_text": "popular(John)", "name": "dup"}]')
    _raises_msg(ValueError,
                "Item 1: Failed to parse fact - Item 1: Loaded name 'dup' is a "
                "duplicate - all fact names must be unique.",
                lambda: _loaders.add_fact_from_json(state, str(dup)))
    assert [f.name for f in state.node_facts] == ["dup"]


# --- loader happy paths over the committed harness fixtures ---
# The same files the equivalence cases load — the seam under test is the one
# the harness fingerprints; expectations cross-checked against the banked
# session-15 oracle artifacts for the five *-basic loader cases.

FIXTURES = Path(__file__).resolve().parent.parent / "harness" / "fixtures"


def _fact_shape(f):
    return (f.name, str(f.pred), f.component, str(f.bound),
            f.start_time, f.end_time, f.static)


def test_fact_csv_happy_fixture_rows_reach_the_state(state):
    """proves: over the committed facts.csv fixture the exact-match header
    row is skipped, a quoted comma-bearing cell parses as one edge fact with
    its interval bound, an all-empty-params row auto-names fact_2 through
    the shared node+edge counter with truthy 'yes' static, and a two-field
    short row pads to defaults (start/end 0, static False)."""
    _loaders.add_fact_from_csv(state, str(FIXTURES / "facts.csv"))
    assert [_fact_shape(f) for f in state.node_facts] == [
        ("csv-popular", "popular", "Mary", "[1.0,1.0]", 0, 2, False),
        ("fact_2", "special", "Justin", "[1.0,1.0]", 0, 0, True),
        ("csv-short", "seen", "Dog", "[1.0,1.0]", 0, 0, False),
    ]
    assert [_fact_shape(f) for f in state.edge_facts] == [
        ("csv-edge", "Friends", ("John", "Mary"), "[0.9,1.0]", 0, 2, False),
    ]


def test_fact_json_happy_fixture_items_reach_the_state(state, capsys):
    """proves: over the committed facts.json fixture a named windowed fact,
    an unnamed bounded fact auto-named fact_1, and a static boolean fact all
    load with their declared windows/bounds — and the closing loaded-count
    print is unconditional (pyreason.py:1290, the one loader not gated on
    verbose)."""
    _loaders.add_fact_from_json(state, str(FIXTURES / "facts.json"))
    assert [_fact_shape(f) for f in state.node_facts] == [
        ("json-popular", "popular", "Mary", "[1.0,1.0]", 0, 2, False),
        ("fact_1", "special", "John", "[0.7,1.0]", 1, 2, False),
        ("json-static", "special", "Justin", "[1.0,1.0]", 0, 0, True),
    ]
    assert state.edge_facts == []
    assert "Loaded 3 facts" in capsys.readouterr().out


def test_rule_csv_happy_fixture_rows_reach_the_state(state):
    """proves: over the committed rules.csv fixture the exact-match header
    row is skipped and three rules load in row order — a full row whose
    explicit [0.5,1] bound rides its body clause, an all-empty-params row
    auto-named rule_1 through add_rule, and a quoted comma-bearing row with
    infer_edges 'yes' coerced true (an edge-target rule)."""
    _loaders.add_rule_from_csv(state, str(FIXTURES / "rules.csv"))
    assert [r.get_rule_name() for r in state.rules] == [
        "csv_full", "rule_1", "csv_quoted"]
    full = state.rules[0]
    assert str(full.get_clauses()[0][3]) == "[0.5,1.0]"
    assert state.rules[2].get_rule_type() == "edge"


def test_rule_json_happy_fixture_items_reach_the_state(state):
    """proves: over the committed rules.json fixture all four accepted item
    forms load in item order — a plain rule, custom_thresholds in the list
    form, the dict form (string clause-index key '1' parsed to int, the
    unnamed clause 0 defaulted), and a weights list replacing the default
    per-clause 1.0."""
    _loaders.add_rule_from_json(state, str(FIXTURES / "rules.json"))
    assert [r.get_rule_name() for r in state.rules] == [
        "json_basic", "json_thresh_list", "json_thresh_dict", "json_weights"]
    assert state.rules[1].get_thresholds() == [
        ("greater_equal", ("number", "total"), 1)]
    assert state.rules[2].get_thresholds() == [
        ("greater_equal", ("number", "total"), 1.0),
        ("greater_equal", ("percent", "total"), 100)]
    assert list(state.rules[3].get_weights()) == [2.0]


def test_rules_from_file_happy_rules_reach_reasoning(monkeypatch):
    """proves: the committed rules-multi.txt fixture's comment and blank
    lines are skipped, its two rules load as rule_0/rule_1 (zero offset —
    no rule preloaded), and the loaded rules actually drive reasoning:
    popular(A) derives trendy(A) at t=1 and influencer(A) at t=2 through
    the file-loaded chain."""
    fresh = EngineState()
    fresh.settings.verbose = False
    fresh.settings.atom_trace = True
    monkeypatch.setattr(pyreason, "_state_obj", fresh)
    monkeypatch.setattr(pyreason, "settings", fresh.settings)
    g = nx.DiGraph()
    g.add_nodes_from(["A"])
    pyreason.load_graph(g)
    pyreason.add_rules_from_file(str(FIXTURES / "rules-multi.txt"))
    assert [r.get_rule_name() for r in fresh.rules] == ["rule_0", "rule_1"]
    pyreason.add_fact(pyreason.Fact("popular(A)", "pop", 0, 2))
    interp = pyreason.reason(timesteps=2)
    frames = pyreason.filter_and_sort_nodes(interp, ["trendy", "influencer"])
    rows = [[list(r) for r in f.itertuples(index=False, name=None)] for f in frames]
    assert rows[1] == [["A", [1.0, 1.0], [0, 1]]]
    assert rows[2] == [["A", [1.0, 1.0], [1.0, 1.0]]]


# --- load_inconsistent_predicate_list (the IPL YAML loader) ---
# Behavior target: the pinned yaml_parser.parse_ipl (yaml_parser.py:187-196)
# reached through pyreason.py:611-618's wholesale rebind; arms banked by
# ipl-load-basic / ipl-load-null-overwrite / ipl-load-malformed.


def test_ipl_yaml_happy_fixture_replaces_prior_pairs(state):
    """proves: over the committed ipl.yaml the one [popular, unpopular]
    pair loads as a Label pair, and the load REPLACES a pair added via
    add_inconsistent_predicate rather than merging — the pinned wholesale
    rebind (pyreason.py:616-617; contrast the add's append)."""
    add_inconsistent_predicate(state, "sick", "healthy")
    _loaders.load_inconsistent_predicate_list(state, str(FIXTURES / "ipl.yaml"))
    assert state.ipl == [(Label("popular"), Label("unpopular"))]


def test_ipl_yaml_null_value_loads_an_empty_list(state):
    """proves: an 'ipl:' key holding null fails parse_ipl's `is not None`
    guard and loads as an EMPTY list, not None — so a null file still
    overwrites: the pair added beforehand is gone and reasoning would see
    zero complement pairs (the ipl-load-null-overwrite semantics)."""
    add_inconsistent_predicate(state, "popular", "unpopular")
    _loaders.load_inconsistent_predicate_list(state, str(FIXTURES / "ipl-null.yaml"))
    assert state.ipl == []


def test_ipl_yaml_malformed_arms_raise_and_leave_prior_ipl(state):
    """proves: the four malformed arms raise the pin's four DISTINCT
    exception types — a missing file open()'s FileNotFoundError, a document
    without the 'ipl' key the subscript KeyError (message is the quoted
    key), a one-element pair the [1] IndexError, and unparseable YAML
    yaml.parser.ParserError — and each raise leaves the previously-held IPL
    untouched (the pin parses fully before rebinding)."""
    add_inconsistent_predicate(state, "sick", "healthy")
    prior = list(state.ipl)

    with pytest.raises(FileNotFoundError):
        _loaders.load_inconsistent_predicate_list(
            state, str(FIXTURES / "no-such-ipl.yaml"))
    _raises_msg(KeyError, "'ipl'",
                lambda: _loaders.load_inconsistent_predicate_list(
                    state, str(FIXTURES / "ipl-missing-key.yaml")))
    _raises_msg(IndexError, "list index out of range",
                lambda: _loaders.load_inconsistent_predicate_list(
                    state, str(FIXTURES / "ipl-short-pair.yaml")))
    with pytest.raises(yaml.parser.ParserError):
        _loaders.load_inconsistent_predicate_list(
            state, str(FIXTURES / "ipl-bad.yaml"))

    assert state.ipl == prior


def test_facade_ipl_loader_reads_through_the_public_api(monkeypatch):
    """proves: pyreason.load_inconsistent_predicate_list is the I/O seam
    the harness drives — a real committed YAML file read through the
    module-global facade lands the Label pair in the module's one
    EngineState."""
    fresh = EngineState()
    fresh.settings.verbose = False
    monkeypatch.setattr(pyreason, "_state_obj", fresh)
    monkeypatch.setattr(pyreason, "settings", fresh.settings)
    pyreason.load_inconsistent_predicate_list(str(FIXTURES / "ipl.yaml"))
    assert fresh.ipl == [(Label("popular"), Label("unpopular"))]


def test_ipl_yaml_nonstring_entries_load_provisionally(state, tmp_path):
    """proves: (DIV-0002, provisional pending adjudication) an IPL pair
    whose entries are YAML integers loads into the rewrite's plain-list
    IPL without raising — where the pin's typed-list append raises a
    builtins.ValueError whose message is address-derived and same-engine
    unstable (docs/divergences/DIV-0002.md; pin-side reproducer
    tests/test_div_0002_reproducer.py). This test documents the rewrite's
    current arm; it flips with the fix if the operator adjudicates the
    guarded raise."""
    ipl_file = tmp_path / "nonstring-ipl.yaml"
    ipl_file.write_text("ipl:\n  - [1, 2]\n")
    _loaders.load_inconsistent_predicate_list(state, str(ipl_file))
    assert state.ipl == [(Label(1), Label(2))]
