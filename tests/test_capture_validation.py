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


def test_output_to_file_setting_is_forbidden():
    """proves: a case asking the engine to rebind stdout to an uncompared,
    timestamp-named file is refused until file output is a first-class probe."""
    bad = {**VALID, "inputs": {"settings": {"output_to_file": True}}}
    assert "output_to_file" in validate_case(bad)


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
    the two standalone kinds — a new kind added to the dispatch without a
    reason-block ruling reds here instead of mislabeling exits later."""
    from harness.capture import INTERP_PROBE_KINDS

    assert PROBE_KINDS == INTERP_PROBE_KINDS | {"get_time", "expect_raise"}


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
