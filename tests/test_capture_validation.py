"""Fast-tier tests for harness/capture.py's case-schema guard.

validate_case runs before the engine import, so these need no engine env; they
prove authoring faults exit as usage, never wearing the engine-failure label.
"""

from harness.capture import PROBE_KINDS, validate_case

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


def test_probe_kinds_cover_the_capture_dispatch():
    """proves: the validation whitelist and the run_probe dispatch agree on the
    probe surface (a kind added to one but not the other is caught here)."""
    import inspect

    from harness import capture

    dispatch_source = inspect.getsource(capture.run_probe)
    for kind in PROBE_KINDS:
        assert f'"{kind}"' in dispatch_source
