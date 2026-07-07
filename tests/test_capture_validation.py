"""Fast-tier tests for harness/capture.py's case-schema guard.

validate_case runs before the engine import, so these need no engine env; they
prove authoring faults exit as usage, never wearing the engine-failure label.
"""

from types import SimpleNamespace

from harness.capture import (PROBE_KINDS, probe_expect_raise,
                             run_probe_recorded, run_step, validate_case)

VALID = {"id": "c", "inputs": {"settings": {}},
         "probes": [{"id": "p", "kind": "get_time"}]}

VALID_STEPS = {"id": "c", "inputs": {"settings": {}}, "steps": [
    {"id": "s1", "op": "reason", "args": {"timesteps": 1},
     "probes": [{"id": "p1", "kind": "get_time"},
                {"id": "p2", "kind": "rule_trace_node"}]},
    {"id": "s2", "op": "reset",
     "probes": [{"id": "p3", "kind": "get_time", "allow_raise": True}]},
]}


def test_valid_case_passes_the_guard():
    """proves: a well-formed case with a known probe kind clears validation."""
    assert validate_case(VALID) is None


def test_probe_less_case_is_rejected():
    """proves: a case with no probes is refused — a probe-less case would judge
    as a vacuous pass while proving nothing."""
    assert "no probes" in validate_case({**VALID, "probes": []})


def test_unknown_probe_kind_is_rejected():
    """proves: a probe kind outside the capture's surface is an authoring fault
    caught before the engine runs, naming the kind."""
    bad = {**VALID, "probes": [{"id": "p", "kind": "interpretation_dcit"}]}
    assert "interpretation_dcit" in validate_case(bad)


def test_duplicate_probe_ids_are_rejected():
    """proves: probe ids must be unique — duplicates would silently collapse in
    the artifact's probe map."""
    bad = {**VALID, "probes": [{"id": "p", "kind": "get_time"},
                               {"id": "p", "kind": "get_time"}]}
    assert "unique" in validate_case(bad)


def test_output_to_file_requires_an_output_file_probe():
    """proves: settings.output_to_file=true is refused unless the case carries
    an output_file probe — the redirect file is a compared observation, never
    an unread side effect — and clears validation once one is present, in the
    one-step and steps forms alike."""
    bad = {**VALID, "inputs": {"settings": {"output_to_file": True}}}
    assert "output_file" in validate_case(bad)
    ok = {**bad, "probes": [{"id": "p", "kind": "output_file"}]}
    assert validate_case(ok) is None
    steps_bad = {"id": "c", "inputs": {"settings": {"output_to_file": True}},
                 "steps": [{"id": "s", "op": "reason", "outcome_only": True}]}
    assert "output_file" in validate_case(steps_bad)
    steps_ok = {**steps_bad, "steps": [
        {"id": "s", "op": "reason",
         "probes": [{"id": "p", "kind": "output_file"}]}]}
    assert validate_case(steps_ok) is None


def test_output_to_file_false_needs_no_probe():
    """proves: only the true position demands the probe — an explicit false
    (the readback-twin shape) validates bare, since no file can be written."""
    case = {**VALID, "inputs": {"settings": {"output_to_file": False}}}
    assert validate_case(case) is None


def test_output_file_probe_refuses_allow_raise():
    """proves: allow_raise on an output_file probe is rejected — it reads the
    capture's own confined directory, so a read fault there is a harness
    failure that must fail the capture, never a banked engine observation."""
    bad = {**VALID, "probes": [
        {"id": "p", "kind": "output_file", "allow_raise": True}]}
    assert "allow_raise" in validate_case(bad)


def test_output_file_probe_reads_and_canonicalizes(tmp_path, monkeypatch):
    """proves: the output_file probe returns every .txt in the working
    directory sorted by name, with the engine's wall-clock stamp reduced to
    '<timestamp>' and contents verbatim — and an empty directory reads as [],
    the default-stdout twin's no-file observation."""
    from harness.capture import run_probe

    monkeypatch.chdir(tmp_path)
    probe = {"id": "p", "kind": "output_file"}
    assert run_probe(None, None, probe) == []
    (tmp_path / "pyreason_output_20260707-003744.txt").write_text("Timestep: 0\n")
    (tmp_path / "custom.txt").write_text("x")
    (tmp_path / "not-observed.log").write_text("ignored")
    assert run_probe(None, None, probe) == [
        {"name": "custom.txt", "content": "x"},
        {"name": "pyreason_output_<timestamp>.txt", "content": "Timestep: 0\n"},
    ]


def test_fresh_output_dir_clears_stale_files(tmp_path):
    """proves: the per-capture output directory is emptied on every capture —
    a redirect file left by a prior run cannot bank as this run's observation."""
    from harness.capture import fresh_output_dir

    out = tmp_path / "a1.json"
    outdir = fresh_output_dir(out)
    assert outdir == tmp_path / "a1.outdir"
    (outdir / "pyreason_output_20260707-000000.txt").write_text("stale")
    assert list(fresh_output_dir(out).iterdir()) == []


def test_case_wants_output_dir_covers_knob_and_probe():
    """proves: the capture confines its working directory exactly when the
    case turns the redirect on or observes the redirect surface — in either
    case form — and never otherwise, so existing cases keep their cwd."""
    from harness.capture import case_wants_output_dir

    assert not case_wants_output_dir(VALID)
    assert not case_wants_output_dir(VALID_STEPS)
    assert case_wants_output_dir(
        {**VALID, "inputs": {"settings": {"output_to_file": True}}})
    assert case_wants_output_dir(
        {**VALID, "probes": [{"id": "p", "kind": "output_file"}]})
    assert case_wants_output_dir({**VALID_STEPS, "steps": [
        {"id": "s", "op": "reason",
         "probes": [{"id": "p", "kind": "output_file"}]}]})


def test_expect_raise_probe_requires_construct_and_args():
    """proves: an expect_raise probe missing a known construct or a text-bearing
    args dict is an authoring fault caught before the engine runs."""
    no_construct = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "args": {"text": ""}}]}
    assert "construct" in validate_case(no_construct)
    no_text = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "construct": "rule", "args": {}}]}
    assert "text" in validate_case(no_text)


def test_expect_raise_only_case_needs_no_reason_block():
    """proves: a case holding only expect_raise probes validates without an
    inputs.reason block — malformed-DSL cases never run the reasoner."""
    case = {"id": "c", "inputs": {},
            "probes": [{"id": "p", "kind": "expect_raise", "construct": "fact",
                        "args": {"text": ""}}]}
    assert validate_case(case) is None


def test_interpretation_probe_without_reason_block_is_rejected():
    """proves: a probe that consumes reason()'s interpretation cannot ride a
    case that never reasons — the fault names the probe."""
    case = {"id": "c", "inputs": {},
            "probes": [{"id": "p", "kind": "rule_trace_node"}]}
    assert "reason" in validate_case(case)


def test_malformed_ipl_input_is_rejected():
    """proves: inputs.ipl must be [pred, pred] string pairs — a lone predicate
    or non-string entry is an authoring fault, not an engine failure."""
    assert "ipl" in validate_case(
        {**VALID, "inputs": {"ipl": [["sick"]]}})
    assert "ipl" in validate_case(
        {**VALID, "inputs": {"ipl": [["sick", 3]]}})
    assert validate_case(
        {**VALID, "inputs": {"ipl": [["sick", "healthy"]]}}) is None


def test_probe_expect_raise_records_raise_and_acceptance():
    """proves: the expect_raise probe reduces a constructor raise to the
    module-qualified exception type + message, and an acceptance to the parse
    fingerprint — two engines accepting the same text into different parses
    cannot compare equal on a bare 'accepted'."""

    def rule(text, name, infer_edges):
        raise ValueError(f"bad rule: {text}")

    def fact(text, name, start, end, static):
        return SimpleNamespace(
            pred=SimpleNamespace(get_value=lambda: "f"), component="a",
            bound=[1, 1], type="node")

    pr = SimpleNamespace(Rule=rule, Fact=fact)
    raised = probe_expect_raise(pr, {"construct": "rule", "args": {"text": "x"}})
    assert raised == {"raised": True, "type": "builtins.ValueError",
                      "message": "bad rule: x"}
    accepted = probe_expect_raise(pr, {"construct": "fact", "args": {"text": "f(a)"}})
    assert accepted == {"raised": False,
                        "parse": {"pred": "f", "component": "a",
                                  "bound": [1, 1], "type": "node"}}


def test_probe_expect_raise_missing_constructor_is_a_capture_failure():
    """proves: an engine with no Rule/Fact constructor fails the capture
    outright instead of recording the AttributeError as engine behavior —
    a harness/binding fault never wears the compared-observation label."""
    import pytest

    with pytest.raises(AttributeError):
        probe_expect_raise(SimpleNamespace(),
                           {"construct": "rule", "args": {"text": "x"}})


def test_interp_probe_kinds_partition_the_probe_surface():
    """proves: every probe kind is either interpretation-consuming or one of
    the five standalone kinds — a new kind added to the dispatch without a
    reason-block ruling reds here instead of mislabeling exits later."""
    from harness.capture import INTERP_PROBE_KINDS

    assert PROBE_KINDS == INTERP_PROBE_KINDS | {"get_time", "get_setting",
                                                "expect_raise", "output_file",
                                                "accessor_fingerprint"}


def test_get_setting_probe_requires_a_pinned_knob_name():
    """proves: a get_setting probe whose knob is missing, empty, non-string,
    or off the pinned 18-knob surface is an authoring fault caught before the
    engine runs — a typo'd knob cannot bank as engine behavior."""
    for knob in (None, "", 123, "atom_trce"):
        probe = {"id": "p", "kind": "get_setting"}
        if knob is not None:
            probe["knob"] = knob
        assert "knob" in validate_case({**VALID, "probes": [probe]}), knob


def test_get_setting_probe_validates_inside_steps_too():
    """proves: the knob-name check covers a get_setting probe riding a step —
    the shape the atom-trace-flip case uses — not only the top-level list."""
    bad = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_fact", "args": {"text": "f(a)"},
         "probes": [{"id": "p", "kind": "get_setting", "knob": "atom_trce"}]}]}
    assert "knob" in validate_case(bad)
    ok = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_fact", "args": {"text": "f(a)"},
         "probes": [{"id": "p", "kind": "get_setting", "knob": "atom_trace"}]}]}
    assert validate_case(ok) is None


def test_unknown_settings_knob_in_inputs_is_rejected():
    """proves: a case whose inputs.settings names a knob off the pinned
    surface is refused — setattr would otherwise silently create an attribute
    the engine never consults, testing the default while pinning nothing."""
    bad = {**VALID, "inputs": {"settings": {"atom_trce": True}}}
    assert "atom_trce" in validate_case(bad)


def test_get_setting_probe_refuses_allow_raise():
    """proves: allow_raise on a get_setting probe is rejected — the blanket
    catch would bank the capture's own unknown-knob refusal as engine
    behavior, passing self-proof on a typo."""
    bad = {**VALID, "probes": [
        {"id": "p", "kind": "get_setting", "knob": "atom_trace",
         "allow_raise": True}]}
    assert "allow_raise" in validate_case(bad)


def test_get_setting_probe_reads_the_knob_however_it_is_stored():
    """proves: the get_setting probe returns the public knob value without
    caring how the engine's settings object stores it (a plain attribute here,
    a property in the oracle) — the compared thing is the value, so an engine
    with different internals can never fail the probe structurally; one truly
    missing the knob is a capture failure, never a banked observation."""
    import pytest

    from harness.capture import run_probe

    pr = SimpleNamespace(settings=SimpleNamespace(atom_trace=False))
    assert run_probe(pr, None, {"id": "p", "kind": "get_setting",
                                "knob": "atom_trace"}) is False
    with pytest.raises(AttributeError):
        run_probe(pr, None, {"id": "p", "kind": "get_setting",
                             "knob": "persistent"})


def test_valid_steps_case_passes_the_guard():
    """proves: a well-formed multi-step case — reason with probes, then a reset
    with an allow_raise probe — clears validation."""
    assert validate_case(VALID_STEPS) is None


def test_steps_exclude_top_level_probes_and_inputs_reason():
    """proves: the two case forms cannot mix — a steps case smuggling top-level
    probes or an inputs.reason block is an authoring fault, since ordering
    between the two would be ambiguous."""
    assert "top level" in validate_case({**VALID_STEPS, "probes": [
        {"id": "x", "kind": "get_time"}]})
    assert "mutually exclusive" in validate_case(
        {**VALID_STEPS, "inputs": {"reason": {"timesteps": 1}}})


def test_empty_or_malformed_steps_are_rejected():
    """proves: an empty step list, an unknown op, and a step without a string
    id are each named authoring faults."""
    assert "non-empty" in validate_case({**VALID_STEPS, "steps": []})
    assert "'rest'" in validate_case({**VALID_STEPS, "steps": [
        {"id": "s", "op": "rest"}]})
    assert "id" in validate_case({**VALID_STEPS, "steps": [{"op": "reset"}]})


def test_reset_ops_take_no_args_and_add_fact_needs_text():
    """proves: args ride only the ops that consume them — a reset op carrying
    args and an add_fact without fact text are authoring faults, not silently
    dropped inputs."""
    assert "takes no args" in validate_case({**VALID_STEPS, "steps": [
        {"id": "s", "op": "reset", "args": {"timesteps": 1}}]})
    assert "text" in validate_case({**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_fact", "args": {"name": "f"}}]})


def test_step_and_probe_ids_share_one_namespace():
    """proves: a step id colliding with a probe id is rejected — outcomes and
    probe outputs land in the artifact's single probe map, so a collision
    would silently overwrite one observation with the other."""
    assert "unique" in validate_case({**VALID_STEPS, "steps": [
        {"id": "s1", "op": "reason",
         "probes": [{"id": "s1", "kind": "get_time"}]}]})


def test_interp_probe_before_first_reason_step_is_rejected():
    """proves: an interpretation-consuming probe placed before any reason step
    is caught statically — there is no interpretation for it to observe."""
    bad = {**VALID_STEPS, "steps": [
        {"id": "s1", "op": "reset",
         "probes": [{"id": "p", "kind": "rule_trace_node"}]},
        {"id": "s2", "op": "reason"}]}
    assert "no reason step precedes" in validate_case(bad)


def test_unknown_reason_args_are_rejected_in_both_forms():
    """proves: a typo'd reason kwarg is an authoring fault in the steps form
    and the one-step form alike — otherwise the engine's TypeError would bank
    as behavior and self-proof would pass while testing nothing."""
    assert "restrat" in validate_case({**VALID_STEPS, "steps": [
        {"id": "s", "op": "reason", "args": {"restrat": False},
         "probes": [{"id": "p", "kind": "get_time"}]}]})
    assert "restrat" in validate_case(
        {**VALID, "inputs": {"reason": {"restrat": False}}})


def test_probe_less_reason_step_needs_outcome_only():
    """proves: a successful reason step that nothing observes cannot bank a
    vacuous {'raised': false} — the author either probes its result or
    declares outcome_only, making an unobserved reason an explicit choice."""
    bad = {**VALID_STEPS, "steps": [{"id": "s", "op": "reason"}]}
    assert "outcome_only" in validate_case(bad)
    ok = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "reason", "outcome_only": True}]}
    assert validate_case(ok) is None


def test_expect_raise_probe_refuses_allow_raise():
    """proves: allow_raise on an expect_raise probe is rejected — the probe
    records raises itself, and the blanket catch would bank a missing-
    constructor binding fault as engine behavior."""
    bad = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "construct": "rule",
         "args": {"text": "x"}, "allow_raise": True}]}
    assert "allow_raise" in validate_case(bad)


def test_allow_raise_must_be_boolean():
    """proves: a non-boolean allow_raise is an authoring fault — a truthy
    string would silently widen the raise escape hatch."""
    assert "allow_raise" in validate_case({**VALID, "probes": [
        {"id": "p", "kind": "get_time", "allow_raise": "yes"}]})


def test_run_step_records_a_raise_as_the_outcome():
    """proves: a step op that raises banks the module-qualified exception as
    data and leaves the interpretation untouched — a raising op is a compared
    observation, never a capture failure."""

    def reason(**kwargs):
        raise TypeError("List() argument must be iterable")

    outcome, interp = run_step(SimpleNamespace(reason=reason),
                               {"id": "s", "op": "reason"}, "old")
    assert outcome == {"raised": True, "type": "builtins.TypeError",
                       "message": "List() argument must be iterable"}
    assert interp == "old"


def test_run_step_advances_interpretation_only_on_successful_reason():
    """proves: a successful reason step swaps in its returned interpretation,
    and a reset op leaves the caller's stale reference in place — matching
    what a user holding the returned object sees after pr.reset()."""
    pr = SimpleNamespace(reason=lambda **kw: "new", reset=lambda: None)
    outcome, interp = run_step(pr, {"id": "s", "op": "reason"}, "old")
    assert (outcome, interp) == ({"raised": False}, "new")
    outcome, interp = run_step(pr, {"id": "s", "op": "reset"}, "new")
    assert (outcome, interp) == ({"raised": False}, "new")


def test_run_probe_recorded_gates_the_raise_escape_hatch():
    """proves: without allow_raise a probe exception propagates as a capture
    failure, and with it the raise (or the wrapped value) is recorded as
    data — a typo'd probe cannot silently bank an exception as behavior."""
    import pytest

    def get_time():
        raise AttributeError("'NoneType' object has no attribute 'time'")

    pr_raising = SimpleNamespace(get_time=get_time)
    probe = {"id": "p", "kind": "get_time"}
    with pytest.raises(AttributeError):
        run_probe_recorded(pr_raising, None, probe)
    recorded = run_probe_recorded(pr_raising, None,
                                  {**probe, "allow_raise": True})
    assert recorded == {"raised": True, "type": "builtins.AttributeError",
                        "message": "'NoneType' object has no attribute 'time'"}
    pr_ok = SimpleNamespace(get_time=lambda: 3)
    assert run_probe_recorded(pr_ok, None, {**probe, "allow_raise": True}) \
        == {"raised": False, "value": 3}


def test_probe_kinds_cover_the_capture_dispatch():
    """proves: the validation whitelist and the run_probe dispatch agree on the
    probe surface (a kind added to one but not the other is caught here)."""
    import inspect

    from harness import capture

    dispatch_source = inspect.getsource(capture.run_probe)
    for kind in PROBE_KINDS:
        assert f'"{kind}"' in dispatch_source


FIXTURE = "harness/fixtures/chain-ab.graphml"


def test_graphml_path_fixture_case_passes_the_guard():
    """proves: a case naming a committed repo-relative GraphML fixture clears
    validation — and the fixture this session's cases lean on actually exists."""
    case = {**VALID, "inputs": {"graph": {"graphml_path": FIXTURE}}}
    assert validate_case(case) is None


def test_graphml_path_rejects_the_authoring_faults():
    """proves: an absolute path, a ..-escaping path, a missing file, an
    empty/non-string path, and a graphml_path mixed with inline graph keys are
    each refused before the engine runs — a mistyped fixture is exit-2 usage,
    never an engine finding."""
    faults = [
        ({"graphml_path": "/abs/elsewhere.graphml"}, "repo-relative"),
        ({"graphml_path": "../elsewhere.graphml"}, "outside the repo"),
        ({"graphml_path": "harness/fixtures/no-such.graphml"}, "no committed file"),
        ({"graphml_path": ""}, "non-empty string"),
        ({"graphml_path": 3}, "non-empty string"),
        ({"graphml_path": FIXTURE, "nodes": ["A"]}, "exclusive forms"),
    ]
    for graph_spec, expected in faults:
        fault = validate_case({**VALID, "inputs": {"graph": graph_spec}})
        assert fault and expected in fault, (graph_spec, fault)


def test_non_object_graph_input_is_rejected():
    """proves: inputs.graph must be an object in either form — a bare string
    path would otherwise reach build_graph and wear the engine-failure label."""
    assert "object" in validate_case(
        {**VALID, "inputs": {"graph": FIXTURE}})


def test_accessor_fingerprint_requires_a_known_accessor():
    """proves: an accessor_fingerprint probe whose accessor is missing, empty,
    or off the three-name get-family surface is an authoring fault caught
    before the engine runs — in the top-level list and inside steps alike."""
    for accessor in (None, "", "get_rules", "interp"):
        probe = {"id": "p", "kind": "accessor_fingerprint"}
        if accessor is not None:
            probe["accessor"] = accessor
        assert "accessor" in validate_case({**VALID, "probes": [probe]}), accessor
    bad_step = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "reset",
         "probes": [{"id": "p", "kind": "accessor_fingerprint",
                     "accessor": "get_rules"}]}]}
    assert "accessor" in validate_case(bad_step)
    ok = {**VALID, "probes": [
        {"id": "p", "kind": "accessor_fingerprint", "accessor": "rules"}]}
    assert validate_case(ok) is None


def test_accessor_fingerprint_needs_no_reason_block():
    """proves: accessor_fingerprint probes validate without an inputs.reason
    block — the accessors' before-any-reason returns (None / a raise) are
    themselves the compared observations."""
    case = {"id": "c", "inputs": {}, "probes": [
        {"id": "r", "kind": "accessor_fingerprint", "accessor": "rules"},
        {"id": "i", "kind": "accessor_fingerprint", "accessor": "interpretation",
         "allow_raise": True}]}
    assert validate_case(case) is None


def test_accessor_fingerprint_renders_the_three_accessors():
    """proves: the fingerprint reduces each accessor's return to comparable
    data — None passes through untouched, a rule list becomes per-rule dicts
    carrying the ordered clause list, and the program/interpretation branches
    carry presence plus identity-with-the-reason-return, so an engine handing
    back a copy instead of the live object cannot compare equal."""
    from harness.capture import run_probe

    clause = ("edge", SimpleNamespace(get_value=lambda: "Friends"),
              ["x", "y"], [1, 1], "")
    rule = SimpleNamespace(
        get_rule_name=lambda: "r1", get_rule_type=lambda: "node",
        get_target=lambda: SimpleNamespace(get_value=lambda: "popular"),
        get_head_variables=lambda: ["x"], get_delta=lambda: 1,
        get_bnd=lambda: [1, 1], get_clauses=lambda: [clause])
    interp = SimpleNamespace(time=2)
    program = SimpleNamespace(interp=interp)
    pr = SimpleNamespace(get_rules=lambda: [rule],
                         get_logic_program=lambda: program,
                         get_interpretation=lambda: interp)

    def probe(accessor):
        return {"id": "p", "kind": "accessor_fingerprint", "accessor": accessor}

    assert run_probe(pr, interp, probe("rules")) == [
        {"name": "r1", "type": "node", "target": "popular",
         "head_variables": ["x"], "delta": 1, "bnd": [1, 1],
         "clauses": [["edge", "Friends", ["x", "y"], [1, 1], ""]]}]
    assert run_probe(pr, interp, probe("logic_program")) == {
        "interp_present": True, "interp_is_reason_return": True}
    assert run_probe(pr, None, probe("logic_program")) == {
        "interp_present": True, "interp_is_reason_return": False}
    assert run_probe(pr, interp, probe("interpretation")) == {
        "time": 2, "is_reason_return": True}

    pr_bare = SimpleNamespace(get_rules=lambda: None,
                              get_logic_program=lambda: None,
                              get_interpretation=lambda: None)
    assert run_probe(pr_bare, None, probe("rules")) is None
    assert run_probe(pr_bare, None, probe("logic_program")) is None
    assert run_probe(pr_bare, None, probe("interpretation")) is None
    program.interp = None
    assert run_probe(pr, None, probe("logic_program")) == {
        "interp_present": False, "interp_is_reason_return": None}


def test_save_rule_trace_folder_must_stay_confined():
    """proves: a save_rule_trace folder that is absolute, path-separated,
    '..', empty, or a non-string is refused before the engine runs — an
    engine-written trace file can never land outside the per-capture
    directory — while a plain segment and the folder-less default validate."""
    good = {**VALID, "inputs": {"reason": {}}}
    for folder in ("/abs", "a/b", "..", ".", "", 3):
        bad = {**good, "probes": [
            {"id": "p", "kind": "save_rule_trace", "folder": folder}]}
        assert "folder" in validate_case(bad), folder
    ok_plain = {**good, "probes": [
        {"id": "p", "kind": "save_rule_trace", "folder": "traces"}]}
    assert validate_case(ok_plain) is None
    ok_default = {**good, "probes": [{"id": "p", "kind": "save_rule_trace"}]}
    assert validate_case(ok_default) is None


def test_save_rule_trace_probe_requires_a_reason():
    """proves: save_rule_trace consumes the interpretation like the trace-view
    probes — without an inputs.reason block (or a preceding reason step) the
    case is an authoring fault naming the probe."""
    case = {"id": "c", "inputs": {},
            "probes": [{"id": "p", "kind": "save_rule_trace"}]}
    assert "reason" in validate_case(case)


def test_save_rule_trace_probe_confines_the_capture_cwd():
    """proves: a case carrying a save_rule_trace probe gets the confined
    per-capture working directory — the pinned default folder is the cwd, so
    without confinement the engine would write CSVs into the repo root."""
    from harness.capture import case_wants_output_dir

    case = {**VALID, "inputs": {"reason": {}},
            "probes": [{"id": "p", "kind": "save_rule_trace"}]}
    assert case_wants_output_dir(case)


def test_save_rule_trace_probe_calls_engine_and_reads_back(tmp_path, monkeypatch):
    """proves: the probe hands the engine the pinned default (no folder arg)
    or the named subdirectory it creates first, then returns the written CSVs
    sorted by name with the reason-time stamp reduced to '<timestamp>' and
    contents verbatim — the compared observation is the files themselves."""
    from harness.capture import run_probe

    monkeypatch.chdir(tmp_path)
    calls = []

    def save_rule_trace(interpretation, folder=None):
        target = tmp_path if folder is None else tmp_path / folder
        calls.append((interpretation, folder))
        (target / "rule_trace_nodes_20260707-014926.csv").write_text("nodes\n")
        (target / "rule_trace_edges_20260707-014926.csv").write_text("edges\n")

    pr = SimpleNamespace(save_rule_trace=save_rule_trace)
    default = run_probe(pr, "interp", {"id": "p", "kind": "save_rule_trace"})
    assert calls == [("interp", None)]
    assert default == [
        {"name": "rule_trace_edges_<timestamp>.csv", "content": "edges\n"},
        {"name": "rule_trace_nodes_<timestamp>.csv", "content": "nodes\n"},
    ]
    sub = run_probe(pr, "interp", {"id": "p", "kind": "save_rule_trace",
                                   "folder": "traces"})
    assert calls[1] == ("interp", "traces")
    assert (tmp_path / "traces").is_dir()
    assert [f["name"] for f in sub] == [
        "rule_trace_edges_<timestamp>.csv", "rule_trace_nodes_<timestamp>.csv"]


def test_run_case_routes_graphml_path_through_load_graphml(monkeypatch):
    """proves: a graphml_path case drives the engine's load_graphml with the
    fixture resolved against the repo root (never the caller's cwd), and the
    inline load_graph path stays untouched."""
    import sys
    from types import ModuleType

    from harness.capture import REPO, run_case

    fake = ModuleType("pyreason")
    calls = {"graphml": [], "graph": []}
    fake.settings = SimpleNamespace()
    fake.load_graphml = lambda path: calls["graphml"].append(path)
    fake.load_graph = lambda graph: calls["graph"].append(graph)
    fake.get_time = lambda: 0
    monkeypatch.setitem(sys.modules, "pyreason", fake)

    case = {"id": "c", "inputs": {"graph": {"graphml_path": FIXTURE}},
            "probes": [{"id": "t", "kind": "get_time"}]}
    artifact = run_case(case)
    assert calls["graphml"] == [str(REPO / FIXTURE)]
    assert calls["graph"] == []
    assert artifact["probes"]["t"] == 0
