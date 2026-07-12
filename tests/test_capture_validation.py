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
    the eight standalone kinds — a new kind added to the dispatch without a
    reason-block ruling reds here instead of mislabeling exits later."""
    from harness.capture import INTERP_PROBE_KINDS

    assert PROBE_KINDS == INTERP_PROBE_KINDS | {"get_time", "get_setting",
                                                "expect_raise", "output_file",
                                                "accessor_fingerprint",
                                                "apply_input",
                                                "interval_probe",
                                                "label_probe"}


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


APPLY_OK = {"id": "p", "kind": "apply_input", "op": "add_rule_from_csv",
            "args": {"missing_path": "harness/fixtures/no-such.csv"}}


def test_apply_input_requires_a_known_op_and_args_object():
    """proves: an apply_input probe with an unknown op or a non-object args is
    an authoring fault caught before the engine runs, naming the op."""
    assert "apply op" in validate_case({**VALID, "probes": [
        {**APPLY_OK, "op": "add_rules_form_file"}]})
    assert "'args'" in validate_case({**VALID, "probes": [
        {"id": "p", "kind": "apply_input", "op": "add_rule_from_csv",
         "args": "x"}]})


def test_apply_input_path_spellings_declare_the_existence_state():
    """proves: a file-taking apply op needs exactly one of path/missing_path,
    a 'path' must name a committed file (a typo'd happy arm cannot bank
    FileNotFoundError as engine behavior and pass self-proof), and a
    'missing_path' must NOT exist (the case cannot claim a missing-file
    observation while banking a load)."""
    both = {**APPLY_OK, "args": {"path": FIXTURE, "missing_path": "x"}}
    assert "exactly one" in validate_case({**VALID, "probes": [both]})
    neither = {**APPLY_OK, "args": {}}
    assert "exactly one" in validate_case({**VALID, "probes": [neither]})
    typo = {**APPLY_OK, "args": {"path": "harness/fixtures/no-such.csv"}}
    assert "no committed file" in validate_case({**VALID, "probes": [typo]})
    present = {**APPLY_OK, "args": {"missing_path": FIXTURE}}
    assert "existing file" in validate_case({**VALID, "probes": [present]})
    ok_path = {**APPLY_OK, "args": {"path": FIXTURE}}
    assert validate_case({**VALID, "probes": [ok_path]}) is None
    assert validate_case({**VALID, "probes": [APPLY_OK]}) is None


def test_apply_input_paths_stay_confined_to_the_repo():
    """proves: an absolute, empty, non-string, or ..-escaping path is refused
    in either spelling — applied inputs are committed fixtures, never files
    outside the repo."""
    for rel in ("/abs/f.csv", "", 3, "../elsewhere.csv"):
        for key in ("path", "missing_path"):
            bad = {**APPLY_OK, "args": {key: rel}}
            fault = validate_case({**VALID, "probes": [bad]})
            assert fault is not None, (key, rel)


def test_apply_input_kwargs_are_whitelisted_per_op_and_boolean():
    """proves: an apply op's keyword args are held to the pinned signature —
    an unknown kwarg or a non-boolean value is an authoring fault, so a typo'd
    kwarg cannot bank the engine's TypeError as behavior."""
    unknown = {**APPLY_OK, "args": {"missing_path": "x.csv",
                                    "infer_edges": True}}
    assert "unknown arg" in validate_case({**VALID, "probes": [unknown]})
    nonbool = {**APPLY_OK, "op": "add_rules_from_file",
               "args": {"missing_path": "x.txt", "raise_errors": "yes"}}
    assert "boolean" in validate_case({**VALID, "probes": [nonbool]})
    ok = {**APPLY_OK, "op": "add_rules_from_file",
          "args": {"missing_path": "x.txt", "raise_errors": True,
                   "infer_edges": False}}
    assert validate_case({**VALID, "probes": [ok]}) is None


def test_apply_input_closed_world_takes_exactly_a_string_name():
    """proves: add_closed_world_predicate applies with exactly a string
    'name' — a non-string or path-shaped args dict is an authoring fault (the
    non-string add is silent at the pin and its reason-time raise carries a
    run-varying message, unbankable under exact compare)."""
    base = {"id": "p", "kind": "apply_input",
            "op": "add_closed_world_predicate"}
    assert "string 'name'" in validate_case({**VALID, "probes": [
        {**base, "args": {"name": 3}}]})
    assert "string 'name'" in validate_case({**VALID, "probes": [
        {**base, "args": {"path": FIXTURE}}]})
    ok = {**base, "args": {"name": "busy"}}
    assert validate_case({**VALID, "probes": [ok]}) is None


def test_apply_input_refuses_allow_raise():
    """proves: allow_raise on an apply_input probe is rejected — the probe
    records raises itself, and the blanket catch would bank a missing-loader
    binding fault as engine behavior."""
    bad = {**APPLY_OK, "allow_raise": True}
    assert "allow_raise" in validate_case({**VALID, "probes": [bad]})


def test_apply_input_validates_as_a_step_op_too():
    """proves: the apply ops are step ops with identical validation — the
    same authoring faults exit 2 in the steps form, and a well-formed loader
    step followed by a probed reason step clears the guard."""
    bad = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_fact_from_csv",
         "args": {"path": "harness/fixtures/no-such.csv"}}]}
    assert "no committed file" in validate_case(bad)
    ok = {**VALID_STEPS, "steps": [
        {"id": "load", "op": "add_fact_from_csv",
         "args": {"missing_path": "harness/fixtures/no-such.csv"}},
        {"id": "run", "op": "reason",
         "probes": [{"id": "t", "kind": "get_time"}]}]}
    assert validate_case(ok) is None


def test_apply_input_needs_no_reason_block():
    """proves: apply_input probes validate without an inputs.reason block —
    the malformed-loader arms' outcome records are themselves the compared
    observations and never touch an interpretation."""
    case = {"id": "c", "inputs": {}, "probes": [APPLY_OK]}
    assert validate_case(case) is None


def test_probe_apply_input_records_raise_and_acceptance():
    """proves: the apply_input probe reduces a loader raise to the
    module-qualified exception type + message and an acceptance to
    {'raised': false}, resolving the path against the repo root and passing
    the whitelisted kwargs through — the outcome is the observation either
    way."""
    from harness.capture import REPO, probe_apply_input

    calls = []

    def add_rules_from_file(path, **kwargs):
        calls.append((path, kwargs))
        if "missing" in path:
            raise FileNotFoundError(f"[Errno 2] No such file: {path}")

    pr = SimpleNamespace(add_rules_from_file=add_rules_from_file)
    ok = probe_apply_input(pr, {
        "op": "add_rules_from_file",
        "args": {"path": "harness/fixtures/rules-multi.txt",
                 "raise_errors": True}})
    assert ok == {"raised": False}
    assert calls[0] == (str(REPO / "harness/fixtures/rules-multi.txt"),
                        {"raise_errors": True})
    raised = probe_apply_input(pr, {
        "op": "add_rules_from_file", "args": {"missing_path": "missing.txt"}})
    assert raised == {"raised": True, "type": "builtins.FileNotFoundError",
                      "message": f"[Errno 2] No such file: {REPO / 'missing.txt'}"}
    cwa_calls = []
    pr_cwa = SimpleNamespace(add_closed_world_predicate=cwa_calls.append)
    assert probe_apply_input(pr_cwa, {
        "op": "add_closed_world_predicate",
        "args": {"name": "busy"}}) == {"raised": False}
    assert cwa_calls == ["busy"]


def test_probe_apply_input_missing_loader_is_a_capture_failure():
    """proves: an engine without the loader binding fails the capture outright
    instead of recording the AttributeError as engine behavior — in the probe
    form and the step form alike (run_step resolves the callable outside its
    outcome-recording try)."""
    import pytest

    from harness.capture import probe_apply_input

    with pytest.raises(AttributeError):
        probe_apply_input(SimpleNamespace(), {
            "op": "add_rule_from_csv", "args": {"missing_path": "x.csv"}})
    with pytest.raises(AttributeError):
        run_step(SimpleNamespace(),
                 {"id": "s", "op": "add_rule_from_csv",
                  "args": {"missing_path": "x.csv"}}, None)


def test_run_step_applies_loader_ops_and_records_their_outcome():
    """proves: a loader step op drives the same executor as the probe form —
    the engine callable gets the repo-resolved path, a raise banks as the
    step's outcome record, and the interpretation is never advanced."""
    from harness.capture import REPO

    calls = []

    def add_fact_from_csv(path, **kwargs):
        calls.append((path, kwargs))
        raise ValueError("Row 1: Missing required 'fact_text'")

    pr = SimpleNamespace(add_fact_from_csv=add_fact_from_csv)
    outcome, interp = run_step(pr, {
        "id": "s", "op": "add_fact_from_csv",
        "args": {"path": "harness/fixtures/chain-ab.graphml",
                 "raise_errors": True}}, "old")
    assert calls == [(str(REPO / "harness/fixtures/chain-ab.graphml"),
                      {"raise_errors": True})]
    assert outcome == {"raised": True, "type": "builtins.ValueError",
                       "message": "Row 1: Missing required 'fact_text'"}
    assert interp == "old"


def test_canonicalize_peak_mb_is_gated_on_memory_profile():
    """proves: the peak-MB canonicalization is a per-case opt-in that only a
    memory_profile case may declare — anywhere else the flag could only mask
    engine-authored text — and a non-boolean flag is an authoring fault."""
    probe = {"id": "p", "kind": "output_file", "canonicalize_peak_mb": True}
    bad = {**VALID, "probes": [probe]}
    assert "memory_profile" in validate_case(bad)
    nonbool = {**VALID, "inputs": {"settings": {"memory_profile": True}},
               "probes": [{**probe, "canonicalize_peak_mb": "yes"}]}
    assert "canonicalize_peak_mb" in validate_case(nonbool)
    ok = {**VALID, "inputs": {"settings": {"memory_profile": True}},
          "probes": [probe]}
    assert validate_case(ok) is None


def test_output_file_probe_canonicalizes_only_the_peak_mb_line(tmp_path, monkeypatch):
    """proves: with canonicalize_peak_mb the run-varying peak number reduces
    to '<peak-mb>' wherever the pinned line appears while every other
    character survives verbatim — and without the flag the same content is
    untouched, so the canonicalization can never leak into other cases."""
    from harness.capture import run_probe

    monkeypatch.chdir(tmp_path)
    content = ("Timestep: 0\n"
               "\nProgram used 103.203125 MB of memory\n"
               "Program used memory\n")
    (tmp_path / "pyreason_output_20260707-024738.txt").write_text(content)
    flagged = run_probe(None, None, {"id": "p", "kind": "output_file",
                                     "canonicalize_peak_mb": True})
    assert flagged == [{"name": "pyreason_output_<timestamp>.txt",
                        "content": ("Timestep: 0\n"
                                    "\nProgram used <peak-mb> MB of memory\n"
                                    "Program used memory\n")}]
    plain = run_probe(None, None, {"id": "p", "kind": "output_file"})
    assert plain[0]["content"] == content


def test_reason_queries_must_be_query_text_strings():
    """proves: a reason 'queries' arg that is not a list of non-empty strings
    is an authoring fault in both case forms — the capture constructs the
    pinned Query objects from the texts, so a malformed spec must never reach
    the engine wearing a behavior label — while a well-formed list validates."""
    for queries in ("cool(Mary)", ["cool(Mary)", 3], [""], [None]):
        bad_steps = {**VALID_STEPS, "steps": [
            {"id": "s", "op": "reason", "args": {"queries": queries},
             "probes": [{"id": "p", "kind": "get_time"}]}]}
        assert "queries" in validate_case(bad_steps), queries
        bad_flat = {**VALID, "inputs": {"reason": {"queries": queries}}}
        assert "queries" in validate_case(bad_flat), queries
    ok = {**VALID, "inputs": {"reason": {"queries": ["cool(Mary)"], "timesteps": 2}}}
    assert validate_case(ok) is None


def test_build_reason_args_constructs_query_objects():
    """proves: the capture turns query-text strings into engine Query objects
    in declared order and leaves query-less args untouched (same dict object,
    so existing cases' call shape is byte-identical)."""
    from harness.capture import build_reason_args

    pr = SimpleNamespace(Query=lambda text: ("Q", text))
    args = {"timesteps": 2, "queries": ["cool(Mary)", "busy(John)"]}
    built = build_reason_args(pr, args)
    assert built == {"timesteps": 2,
                     "queries": [("Q", "cool(Mary)"), ("Q", "busy(John)")]}
    assert args["queries"] == ["cool(Mary)", "busy(John)"]  # input not mutated
    plain = {"timesteps": 2}
    assert build_reason_args(pr, plain) is plain


def test_expect_raise_query_construct_fingerprints_the_parse():
    """proves: construct='query' renders the four parsed fields plus the
    echoed text on acceptance — a silent misparse banks the misparse itself —
    and validates like the other text constructs."""
    no_text = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "construct": "query", "args": {}}]}
    assert "text" in validate_case(no_text)
    ok = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "construct": "query",
         "args": {"text": "popular(Mary)"}}]}
    assert validate_case(ok) is None

    class Query:
        def __init__(self, text):
            self.text = text

        def get_predicate(self):
            return SimpleNamespace(get_value=lambda: "popular")

        def get_component(self):
            return "Mary"

        def get_component_type(self):
            return "node"

        def get_bounds(self):
            return [1, 1]

        def __str__(self):
            return self.text

    accepted = probe_expect_raise(
        SimpleNamespace(Query=Query),
        {"construct": "query", "args": {"text": "popular(Mary)"}})
    assert accepted == {"raised": False, "parse": {
        "pred": "popular", "component": "Mary", "component_type": "node",
        "bounds": [1, 1], "text": "popular(Mary)"}}


def test_expect_raise_threshold_construct_takes_the_pinned_triple():
    """proves: construct='threshold' takes exactly the pinned constructor's
    three parameters (a text-shaped or partial args dict is an authoring
    fault), hands a list quantifier_type over as the documented tuple, and
    fingerprints the stored triple on acceptance."""
    partial = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "construct": "threshold",
         "args": {"quantifier": "greater_equal"}}]}
    assert "threshold" in validate_case(partial)
    ok = {**VALID, "probes": [
        {"id": "p", "kind": "expect_raise", "construct": "threshold",
         "args": {"quantifier": "greater_equal",
                  "quantifier_type": ["number", "total"], "thresh": 1}}]}
    assert validate_case(ok) is None

    seen = []

    class Threshold:
        def __init__(self, quantifier, quantifier_type, thresh):
            seen.append((quantifier, quantifier_type, thresh))
            self.quantifier = quantifier
            self.quantifier_type = quantifier_type
            self.thresh = thresh

        def to_tuple(self):
            return self.quantifier, self.quantifier_type, self.thresh

    accepted = probe_expect_raise(
        SimpleNamespace(Threshold=Threshold),
        {"construct": "threshold",
         "args": {"quantifier": "greater_equal",
                  "quantifier_type": ["number", "total"], "thresh": 1}})
    assert seen == [("greater_equal", ("number", "total"), 1)]
    assert accepted == {"raised": False, "parse": {
        "quantifier": "greater_equal", "quantifier_type": ("number", "total"),
        "thresh": 1, "to_tuple": ("greater_equal", ("number", "total"), 1)}}


def test_interval_probe_validates_its_two_numeric_specs():
    """proves: an interval_probe missing make/other, carrying a non-numeric
    or boolean bound, an unknown spec key, or a non-boolean static is an
    authoring fault caught before the engine runs; allow_raise is refused
    (a raise in the fixed pipeline is a binding fault, not an observation)."""
    base = {"id": "p", "kind": "interval_probe",
            "make": {"lower": 0.25, "upper": 0.75},
            "other": {"lower": 0.5, "upper": 1, "static": True}}
    assert validate_case({**VALID, "probes": [base]}) is None
    for mutation in (
            {"make": None},
            {"make": {"lower": 0.25}},
            {"make": {"lower": "0.25", "upper": 1}},
            {"make": {"lower": True, "upper": 1}},
            {"make": {"lower": 0.25, "upper": 1, "extra": 1}},
            {"other": {"lower": 0.25, "upper": 1, "static": "yes"}},
            {"allow_raise": True},
    ):
        bad = {**base, **mutation}
        assert validate_case({**VALID, "probes": [bad]}) is not None, mutation


def test_label_probe_validates_its_string_values():
    """proves: a label_probe needs string 'value' and 'other' (the pinned
    value class is string-valued; non-string rejection is jit-context-only)
    and refuses allow_raise — it records its one raising relation itself."""
    base = {"id": "p", "kind": "label_probe", "value": "popular",
            "other": "unpopular"}
    assert validate_case({**VALID, "probes": [base]}) is None
    for mutation in ({"value": 3}, {"other": None}, {"allow_raise": True}):
        bad = {**base, **mutation}
        assert validate_case({**VALID, "probes": [bad]}) is not None, mutation


def test_probe_interval_runs_the_fixed_pipeline_in_order():
    """proves: the interval probe constructs through the engine's aliased
    closed(), records relations and intersection on the fresh pair, then the
    reset transition, then the post-reset intersection — the arm that pins
    the proxy's prev-bound seeding — reducing every field to plain data."""
    from harness.capture import probe_interval

    class FakeInterval:
        def __init__(self, lower, upper, static):
            self.lower, self.upper = lower, upper
            self._static = static
            self.prev_lower, self.prev_upper = lower, upper

        def is_static(self):
            return self._static

        def to_str(self):
            return f"[{self.lower},{self.upper}]"

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

        def __hash__(self):
            return hash((self.lower, self.upper))

        def __contains__(self, item):
            return self.lower <= item.lower and self.upper >= item.upper

        def intersection(self, other):
            lower = max(self.lower, other.lower)
            upper = min(self.upper, other.upper)
            if lower > upper:
                lower, upper = 0.0, 1.0
            out = FakeInterval(lower, upper, False)
            # proxy seeding: prev from self's CURRENT bounds
            out.prev_lower, out.prev_upper = self.lower, self.upper
            return out

        def has_changed(self):
            return (self.lower, self.upper) != (self.prev_lower, self.prev_upper)

        def reset(self):
            self.prev_lower, self.prev_upper = self.lower, self.upper
            self.lower, self.upper = 0.0, 1.0

    pr = SimpleNamespace(interval=SimpleNamespace(closed=FakeInterval))
    record = probe_interval(pr, {
        "id": "p", "kind": "interval_probe",
        "make": {"lower": 0.25, "upper": 0.75},
        "other": {"lower": 0.5, "upper": 1.0}})
    assert record["constructed"] == {
        "lower": 0.25, "upper": 0.75, "static": False,
        "prev_lower": 0.25, "prev_upper": 0.75, "repr": "[0.25,0.75]"}
    assert record["eq"] is False and record["hash_eq"] is False
    assert record["other_in_self"] is False and record["self_in_other"] is False
    assert record["intersection"]["lower"] == 0.5
    assert record["intersection"]["prev_lower"] == 0.25  # pre-reset seeding
    assert record["has_changed_fresh"] is False
    assert record["post_reset"] == {
        "lower": 0.0, "upper": 1.0, "static": False,
        "prev_lower": 0.25, "prev_upper": 0.75, "repr": "[0.0,1.0]"}
    assert record["has_changed_post_reset"] is True
    # post-reset intersection: prev seeded from the reset CURRENT bounds
    assert record["post_reset_intersection"]["prev_lower"] == 0.0
    assert record["post_reset_intersection"]["prev_upper"] == 1.0


def test_probe_label_records_relations_and_the_raising_arm():
    """proves: the label probe banks value/str/repr and the equality/hash
    relations (never raw hash numbers), and reduces the plain-string equality
    raise to a raise record instead of failing the capture."""
    from harness.capture import probe_label

    class FakeLabel:
        def __init__(self, value):
            self._value = value

        def get_value(self):
            return self._value

        def __eq__(self, label):
            return self._value == label.get_value()

        def __hash__(self):
            return hash(self._value)

        def __str__(self):
            return self._value

        def __repr__(self):
            return self._value

    pr = SimpleNamespace(label=SimpleNamespace(Label=FakeLabel))
    record = probe_label(pr, {"id": "p", "kind": "label_probe",
                              "value": "popular", "other": "unpopular"})
    assert record == {
        "value": "popular", "str": "popular", "repr": "popular",
        "eq_same_text": True, "eq_other_text": False,
        "hash_eq_same_text": True, "hash_eq_other_text": False,
        "eq_plain_str": {"raised": True, "type": "builtins.AttributeError",
                         "message": "'str' object has no attribute 'get_value'"}}


def test_registry_ops_validate_names_against_the_committed_registry():
    """proves: a callable-registering apply op takes exactly a string 'name'
    that must be in harness/reference_fns.py's registry — a typo'd name is an
    authoring fault, never a banked resolution failure — in the probe form
    and the step form alike."""
    base = {"id": "p", "kind": "apply_input", "op": "add_annotation_function"}
    assert "string 'name'" in validate_case({**VALID, "probes": [
        {**base, "args": {"name": 3}}]})
    assert "string 'name'" in validate_case({**VALID, "probes": [
        {**base, "args": {"path": FIXTURE}}]})
    assert "unknown reference function" in validate_case({**VALID, "probes": [
        {**base, "args": {"name": "clause_lower_maen"}}]})
    ok = {**base, "args": {"name": "clause_lower_mean"}}
    assert validate_case({**VALID, "probes": [ok]}) is None
    bad_step = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_head_function",
         "args": {"name": "no_such_fn"}}]}
    assert "unknown reference function" in validate_case(bad_step)
    ok_step = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_head_function",
         "args": {"name": "first_clause_first_grounding"}}]}
    assert validate_case(ok_step) is None


def test_registry_module_is_stdlib_only_and_names_match():
    """proves: harness/reference_fns.py imports without an engine environment
    (this fast tier has neither numba nor networkx) and every non-shadow
    registry key is its function's __name__ — the engine matches registrands
    by __name__, so a key/name drift would make a case register one function
    while the rule DSL names another. Shadow entries invert that on purpose
    (they exist to register a SECOND callable under an existing engine-visible
    name — the duplicate-name arms, batch B3): each shadow key must differ
    from its function's __name__, which must equal its declared target's, and
    the target must be a non-shadow registry entry."""
    from harness import reference_fns

    assert reference_fns.numba is None  # unbound outside resolve()
    for name, fn in reference_fns.REGISTRY.items():
        if name in reference_fns.SHADOWS:
            target = reference_fns.SHADOWS[name]
            assert name != fn.__name__
            assert fn.__name__ == target
            assert target in reference_fns.REGISTRY
            assert target not in reference_fns.SHADOWS
            assert fn is not reference_fns.REGISTRY[target]
        else:
            assert name == fn.__name__
    # the arity stubs the reject arms lean on measure as the pinned gate sees
    # them: co_argcount 3 and 0
    assert reference_fns.three_positional_stub.__code__.co_argcount == 3
    assert reference_fns.star_args_stub.__code__.co_argcount == 0


def test_resolve_plain_arm_hands_over_the_committed_function_unwrapped(monkeypatch):
    """proves: in an engine environment without numba (this campaign env —
    asserted, never assumed), resolve() returns exactly the committed registry
    function, identity-preserved with its __name__ intact (the engine matches
    registrands by __name__), and binds the module-global `numba` to the
    builtin-list stand-in — the accommodation's plain arm, exercised for real
    at the import seam, no mocks."""
    import importlib.util

    from harness import reference_fns

    assert importlib.util.find_spec("numba") is None  # the env invariant
    monkeypatch.setattr(reference_fns, "numba", None)  # restore after
    fn = reference_fns.resolve("clause_lower_mean")
    assert fn is reference_fns.REGISTRY["clause_lower_mean"]
    assert fn.__name__ == "clause_lower_mean"
    assert reference_fns.numba is reference_fns._PLAIN_NUMBA


def test_resolve_numba_arm_njit_wraps_via_the_import_seam(monkeypatch):
    """proves: where `import numba` succeeds inside resolve(), the returned
    callable is exactly njit(committed function) and the module-global `numba`
    is bound to the imported module — the oracle env consumes registrands as
    the pin does. Simulated per the fast-tier constraint (this env carries no
    numba): a stand-in module is planted in sys.modules, which is precisely
    the seam resolve()'s `import numba` consumes, so the arm decision and the
    wrap both run for real."""
    import sys
    from types import ModuleType

    from harness import reference_fns

    fake = ModuleType("numba")
    wrapped = []

    def njit(fn):
        wrapped.append(fn)
        return ("dispatcher", fn)

    fake.njit = njit
    monkeypatch.setitem(sys.modules, "numba", fake)
    monkeypatch.setattr(reference_fns, "numba", None)  # restore after
    out = reference_fns.resolve("first_clause_first_grounding")
    assert wrapped == [reference_fns.REGISTRY["first_clause_first_grounding"]]
    assert out == ("dispatcher",
                   reference_fns.REGISTRY["first_clause_first_grounding"])
    assert reference_fns.numba is fake


def test_head_registrand_plain_arm_returns_a_builtin_list(monkeypatch):
    """proves: after the plain-arm resolve(), the head reference function's
    pinned return contract (`numba.typed.List` of grounding strings,
    interpretation.py:2316-2338) reduces to the builtin list a plain-python
    engine's head-function caller consumes — the one registrand that touches
    the `numba` module global works end-to-end without numba."""
    from harness import reference_fns

    monkeypatch.setattr(reference_fns, "numba", None)  # restore after
    fn = reference_fns.resolve("first_clause_first_grounding")
    result = fn([["A", "B"], ["B"]])
    assert type(result) is list
    assert result == ["A"]


def test_resolve_broken_numba_propagates_not_downgrades(monkeypatch):
    """proves: the discriminator's third arm — a numba that is PRESENT but
    BROKEN (the import machinery finds it but exec raises a plain
    ImportError, not ModuleNotFoundError) propagates out of resolve() and
    fails the capture loudly; it does NOT select the plain arm and does NOT
    bind the _PLAIN_NUMBA stand-in. This is the accommodation's
    ModuleNotFoundError-only choice, exercised at the same import seam the
    numba-arm test uses (slice-7 review probe)."""
    import importlib.abc
    import importlib.machinery
    import sys

    import pytest

    from harness import reference_fns

    class BrokenLoader(importlib.abc.Loader):
        def create_module(self, spec):
            return None

        def exec_module(self, module):
            raise ImportError("simulated broken numba: exec failed")

    class BrokenFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == "numba":
                return importlib.machinery.ModuleSpec("numba", BrokenLoader())
            return None

    finder = BrokenFinder()
    sys.meta_path.insert(0, finder)
    monkeypatch.setattr(reference_fns, "numba", None)  # restore after
    try:
        with pytest.raises(ImportError) as exc_info:
            reference_fns.resolve("clause_lower_mean")
        assert not isinstance(exc_info.value, ModuleNotFoundError)
        assert reference_fns.numba is not reference_fns._PLAIN_NUMBA
    finally:
        sys.meta_path.remove(finder)
        sys.modules.pop("numba", None)


def test_registry_step_op_hands_the_resolved_callable_to_the_engine(monkeypatch):
    """proves: a registry step op resolves the named reference function
    outside the outcome-recording try (a resolution fault fails the capture)
    and hands exactly the resolved callable to the engine registrar, whose
    raise-or-accept is the banked outcome."""
    import pytest

    from harness import capture

    sentinel = object()
    monkeypatch.setattr(capture.reference_fns, "resolve",
                        lambda name: sentinel if name == "clause_lower_mean"
                        else (_ for _ in ()).throw(ImportError("no numba here")))
    seen = []
    pr = SimpleNamespace(add_annotation_function=seen.append)
    outcome, interp = run_step(pr, {
        "id": "s", "op": "add_annotation_function",
        "args": {"name": "clause_lower_mean"}}, "old")
    assert outcome == {"raised": False} and interp == "old"
    assert seen == [sentinel]

    def rejecting(fn):
        raise TypeError("Annotation function 'x' must accept exactly 2 ...")

    outcome, _ = run_step(SimpleNamespace(add_annotation_function=rejecting), {
        "id": "s", "op": "add_annotation_function",
        "args": {"name": "clause_lower_mean"}}, None)
    assert outcome["raised"] is True and outcome["type"] == "builtins.TypeError"
    pr_head = SimpleNamespace(add_head_function=seen.append)
    with pytest.raises(ImportError):
        run_step(pr_head, {"id": "s", "op": "add_head_function",
                           "args": {"name": "star_args_stub"}}, None)


def test_add_rule_step_op_builds_thresholds_and_weights():
    """proves: an add_rule step drives the shared rule builder — text/name/
    infer_edges positionally, list- and dict-form custom_thresholds built into
    engine Threshold objects (dict keys int-converted), and weights passed as
    the JSON list — while a threshold-less spec passes no extra kwargs, so
    existing rule inputs keep their exact call shape."""
    rules, thresholds = [], []

    class Threshold:
        def __init__(self, quantifier, quantifier_type, thresh):
            thresholds.append((quantifier, quantifier_type, thresh))
            self.triple = (quantifier, quantifier_type, thresh)

    def rule(text, name, infer_edges, **kwargs):
        rules.append((text, name, infer_edges, kwargs))
        return "rule-obj"

    pr = SimpleNamespace(Rule=rule, Threshold=Threshold,
                         add_rule=lambda r: None)
    outcome, _ = run_step(pr, {
        "id": "s", "op": "add_rule",
        "args": {"text": "t(x) <-1 f(x)", "name": "r1",
                 "custom_thresholds": [
                     {"quantifier": "greater_equal",
                      "quantifier_type": ["number", "total"], "thresh": 1}],
                 "weights": [1, 2]}}, None)
    assert outcome == {"raised": False}
    assert thresholds == [("greater_equal", ("number", "total"), 1)]
    text, name, infer_edges, kwargs = rules[0]
    assert (text, name, infer_edges) == ("t(x) <-1 f(x)", "r1", False)
    assert kwargs["weights"] == [1, 2]
    assert [t.triple for t in kwargs["custom_thresholds"]] \
        == [("greater_equal", ("number", "total"), 1)]

    outcome, _ = run_step(pr, {
        "id": "s", "op": "add_rule",
        "args": {"text": "t(x) <-1 f(x)",
                 "custom_thresholds": {
                     "1": {"quantifier": "greater_equal",
                           "quantifier_type": ["number", "total"],
                           "thresh": 2}}}}, None)
    assert outcome == {"raised": False}
    dict_kwargs = rules[1][3]
    assert list(dict_kwargs["custom_thresholds"]) == [1]  # int-converted key

    outcome, _ = run_step(pr, {
        "id": "s", "op": "add_rule", "args": {"text": "t(x) <-1 f(x)"}}, None)
    assert rules[2][3] == {}  # no smuggled kwargs on the plain shape


def test_rule_specs_validate_in_inputs_and_step_form():
    """proves: a rule spec without text, a malformed threshold spec, a
    non-integer dict key, a bad custom_thresholds container, and non-numeric
    weights are each authoring faults in inputs.rules and the add_rule step
    alike — a spec fault must never reach the engine as a behavior claim."""
    good_t = {"quantifier": "greater_equal",
              "quantifier_type": ["number", "total"], "thresh": 1}
    faults = [
        ({"name": "r"}, "text"),
        ({"text": "t", "custom_thresholds": "x"}, "custom_thresholds"),
        ({"text": "t", "custom_thresholds": [{"quantifier": "ge"}]}, "threshold"),
        ({"text": "t", "custom_thresholds": {"one": good_t}}, "integer"),
        ({"text": "t",
          "custom_thresholds": [{**good_t, "quantifier": 3}]}, "quantifier"),
        ({"text": "t",
          "custom_thresholds": [{**good_t, "quantifier_type": [1]}]},
         "quantifier_type"),
        ({"text": "t", "weights": [1, "x"]}, "weights"),
        ({"text": "t", "weights": [True]}, "weights"),
    ]
    for spec, expected in faults:
        fault = validate_case({**VALID, "inputs": {"rules": [spec]}})
        assert fault and expected in fault, (spec, fault)
        step_fault = validate_case({**VALID_STEPS, "steps": [
            {"id": "s", "op": "add_rule", "args": spec}]})
        assert step_fault and expected in step_fault, (spec, step_fault)
    ok = {**VALID, "inputs": {"rules": [
        {"text": "t(x) <-1 f(x)", "custom_thresholds": [good_t],
         "weights": [1.5]}]}}
    assert validate_case(ok) is None


def test_registrand_cases_snapshot_and_restore_the_kernel_cache(tmp_path):
    """proves: a case that registers a reference function — in the step or the
    probe spelling — is flagged for kernel-cache restoration while every other
    case is not, and the snapshot/restore pair returns the engine env's
    bundled cache to its pre-capture state: files the capture added are
    removed and rewritten index files get their prior bytes back, while
    untouched files survive byte-identical — the bundled cache must never
    accumulate dispatcher-bearing entries (their pickled index keys reference
    harness.reference_fns, loadable only with the repo root on sys.path, and
    a fresh process's dispatchers never match them anyway)."""
    from harness.capture import (case_registers_functions,
                                 restore_kernel_cache, snapshot_kernel_cache)

    step_case = {**VALID_STEPS, "steps": [
        {"id": "s", "op": "add_annotation_function",
         "args": {"name": "clause_lower_mean"}}]}
    probe_case = {**VALID, "probes": [
        {"id": "p", "kind": "apply_input", "op": "add_head_function",
         "args": {"name": "first_clause_first_grounding"}}]}
    assert case_registers_functions(step_case)
    assert case_registers_functions(probe_case)
    assert not case_registers_functions(VALID)
    assert not case_registers_functions(VALID_STEPS)

    # a synthetic bundled cache: one kernel dir with an index + a data file
    kernel = tmp_path / "interpretation_abc"
    kernel.mkdir()
    (kernel / "reason.nbi").write_bytes(b"clean-index")
    (kernel / "reason.1.nbc").write_bytes(b"warm-kernel")
    names, indexes = snapshot_kernel_cache(tmp_path)

    # the capture appends a dispatcher-bearing overload and rewrites the index
    (kernel / "reason.2.nbc").write_bytes(b"dispatcher-specialization")
    (kernel / "reason.nbi").write_bytes(b"index-naming-harness.reference_fns")
    (kernel / "annotate.nbi").write_bytes(b"new-index")

    restore_kernel_cache(tmp_path, names, indexes)
    assert sorted(p.name for p in kernel.iterdir()) \
        == ["reason.1.nbc", "reason.nbi"]
    assert (kernel / "reason.nbi").read_bytes() == b"clean-index"
    assert (kernel / "reason.1.nbc").read_bytes() == b"warm-kernel"

    # both directions are total on a missing/absent cache dir
    empty_names, empty_indexes = snapshot_kernel_cache(None)
    assert (empty_names, empty_indexes) == (set(), {})
    restore_kernel_cache(None, empty_names, empty_indexes)
    restore_kernel_cache(tmp_path / "no-such-dir", set(), {})


def _fake_engine(monkeypatch, **attrs):
    """A stand-in pyreason module for engine-free run_case tests — the same
    sys.modules pattern the graphml routing test uses."""
    import sys
    from types import ModuleType

    fake = ModuleType("pyreason")
    fake.settings = SimpleNamespace()
    for name, value in attrs.items():
        setattr(fake, name, value)
    monkeypatch.setitem(sys.modules, "pyreason", fake)
    return fake


def test_run_case_echoes_the_full_case_record(monkeypatch):
    """proves: the artifact echoes the parsed case verbatim under 'case' — an
    artifact is self-describing without the case file — and the echo stays
    outside the digested probe map."""
    from harness.capture import run_case

    _fake_engine(monkeypatch, get_time=lambda: 7)
    case = {"id": "c", "inputs": {"settings": {}},
            "purpose": "echo-check",
            "probes": [{"id": "t", "kind": "get_time"}],
            "comparison": {"probes": {}}}
    artifact = run_case(case)
    assert artifact["case"] == case
    assert set(artifact["digests"]) == {"t"}


def test_run_case_times_each_probe_outside_the_probe_map(monkeypatch):
    """proves: every probe's wall-clock lands in timing.probes_s keyed by
    probe id, in the one-step form, as numbers — and timing is never digested,
    so it can never move a verdict."""
    from harness.capture import run_case

    _fake_engine(monkeypatch, get_time=lambda: 7)
    case = {"id": "c", "inputs": {"settings": {}},
            "probes": [{"id": "t1", "kind": "get_time"},
                       {"id": "t2", "kind": "get_time"}]}
    artifact = run_case(case)
    probes_s = artifact["timing"]["probes_s"]
    assert set(probes_s) == {"t1", "t2"}
    assert all(isinstance(v, (int, float)) and not isinstance(v, bool)
               and v >= 0 for v in probes_s.values())
    assert set(artifact["digests"]) == {"t1", "t2"}


def test_steps_form_times_step_probes_alongside_steps_s(monkeypatch):
    """proves: in the steps form each step probe's wall-clock lands in
    timing.probes_s (keyed by probe id) beside the existing per-step steps_s —
    step outcomes are timed as steps, probes as probes."""
    from harness.capture import run_case

    _fake_engine(monkeypatch, reason=lambda **kw: "interp",
                 get_time=lambda: 3)
    case = {"id": "c", "inputs": {"settings": {}}, "steps": [
        {"id": "s1", "op": "reason", "args": {"timesteps": 1},
         "probes": [{"id": "p1", "kind": "get_time"}]}]}
    artifact = run_case(case)
    assert set(artifact["timing"]["steps_s"]) == {"s1"}
    assert set(artifact["timing"]["probes_s"]) == {"p1"}
    assert artifact["probes"]["s1"] == {"raised": False}
    assert artifact["probes"]["p1"] == 3


def test_error_artifacts_echo_the_case_record(monkeypatch, tmp_path):
    """proves: both post-parse error artifacts — invalid case (exit 2) and
    engine failure (exit 1) — echo the parsed case under 'case', so an error
    artifact is as self-describing as a healthy one; the pre-parse
    unreadable-file artifact carries no echo (there is no parsed case yet)."""
    import json

    from harness import capture

    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"id": "bad-case"}))  # no inputs: a fault
    out = tmp_path / "invalid-artifact.json"
    assert capture.main([str(invalid), str(out)]) == 2
    artifact = json.loads(out.read_text())
    assert artifact["case"] == {"id": "bad-case"}
    assert artifact["error"].startswith("invalid case")

    _fake_engine(monkeypatch)  # no get_time: the probe raises in-engine
    case = {"id": "boom", "inputs": {"settings": {}},
            "probes": [{"id": "t", "kind": "get_time"}], "comparison": {}}
    case_path = tmp_path / "boom.json"
    case_path.write_text(json.dumps(case))
    out = tmp_path / "boom-artifact.json"
    assert capture.main([str(case_path), str(out)]) == 1
    artifact = json.loads(out.read_text())
    assert artifact["case"] == case
    assert "AttributeError" in artifact["error"]

    unreadable = tmp_path / "unreadable.json"
    unreadable.write_text("{not json")
    out = tmp_path / "unreadable-artifact.json"
    assert capture.main([str(unreadable), str(out)]) == 2
    artifact = json.loads(out.read_text())
    assert "case" not in artifact and artifact["case_id"] is None
