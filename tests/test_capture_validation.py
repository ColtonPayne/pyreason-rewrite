"""Fast-tier tests for harness/capture.py's case-schema guard.

validate_case runs before the engine import, so these need no engine env; they
prove authoring faults exit as usage, never wearing the engine-failure label.
"""

from types import SimpleNamespace

from harness.capture import PROBE_KINDS, probe_expect_raise, validate_case

VALID = {"id": "c", "inputs": {"settings": {}},
         "probes": [{"id": "p", "kind": "get_time"}]}


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
    """proves: the expect_raise probe reduces a constructor raise to
    {raised, type, message} and records acceptance as {raised: false} — both
    are compared observations, neither is a capture failure."""

    def rule(text, name, infer_edges):
        raise ValueError(f"bad rule: {text}")

    pr = SimpleNamespace(Rule=rule, Fact=lambda *a: None)
    raised = probe_expect_raise(pr, {"construct": "rule", "args": {"text": "x"}})
    assert raised == {"raised": True, "type": "ValueError",
                      "message": "bad rule: x"}
    accepted = probe_expect_raise(pr, {"construct": "fact", "args": {"text": "f(a)"}})
    assert accepted == {"raised": False}


def test_probe_kinds_cover_the_capture_dispatch():
    """proves: the validation whitelist and the run_probe dispatch agree on the
    probe surface (a kind added to one but not the other is caught here)."""
    import inspect

    from harness import capture

    dispatch_source = inspect.getsource(capture.run_probe)
    for kind in PROBE_KINDS:
        assert f'"{kind}"' in dispatch_source
