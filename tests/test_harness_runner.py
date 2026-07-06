"""Fast-tier tests for harness/run.py — the judge taxonomy and the capture seam.

The seam under test is the injected capture callable: these prove the runner
composes capture → artifact → verdict correctly (pass / divergent /
irreproducible / error) without any engine environment.
"""

import json

from harness.run import judge_case, run_case

CASE = {"id": "c1", "comparison": {"probes": {}}}


def art(probes):
    from harness.compare import digest

    return {"schema": 1, "case_id": "c1", "probes": probes,
            "digests": {k: digest(v) for k, v in probes.items()}}


def quad(a1, a2, b1, b2):
    return {"a1": art(a1), "a2": art(a2), "b1": art(b1), "b2": art(b2)}


def test_judge_pass_when_all_four_agree():
    """proves: identical repeat pairs on both engines judge as pass."""
    p = {"x": [1, 2]}
    assert judge_case(CASE, quad(p, p, p, p))["status"] == "pass"


def test_judge_divergent_names_the_probes():
    """proves: reproducible engines whose outputs differ judge as divergent and
    the verdict names exactly the mismatching probes."""
    pa, pb = {"x": [1], "y": [2]}, {"x": [1], "y": [3]}
    verdict = judge_case(CASE, quad(pa, pa, pb, pb))
    assert verdict["status"] == "divergent"
    assert verdict["probes"] == ["y"]


def test_judge_irreproducible_is_not_a_divergence():
    """proves: a same-engine repeat mismatch is reported as that engine's
    irreproducibility — a harness/environment failure, never an engine finding."""
    verdict = judge_case(CASE, quad({"x": [1]}, {"x": [2]}, {"x": [1]}, {"x": [1]}))
    assert verdict["status"] == "irreproducible"
    assert verdict["detail"] == "engine-a"


def test_judge_error_when_a_capture_failed():
    """proves: a failed or missing capture judges as error, carrying the engine
    run name and the recorded failure."""
    artifacts = quad({"x": [1]}, {"x": [1]}, {"x": [1]}, {"x": [1]})
    artifacts["b2"] = {"schema": 1, "case_id": "c1", "error": "ValueError('boom')"}
    verdict = judge_case(CASE, artifacts)
    assert verdict["status"] == "error"
    assert "b2" in verdict["detail"] and "boom" in verdict["detail"]


def test_run_case_drives_four_captures_through_the_seam(tmp_path):
    """proves: run_case captures each case twice per engine through the injected
    capture callable and judges from the artifacts it wrote."""
    case_path = tmp_path / "case.json"
    case_path.write_text(json.dumps(
        {"id": "seam", "inputs": {}, "probes": [], "comparison": {}}))
    calls = []

    def fake_capture(exe, case_p, out_p):
        calls.append(exe)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(art({"x": [1]})))
        return 0

    verdict = run_case(case_path, "pyA", "pyB", tmp_path / "results",
                       capture=fake_capture)
    assert verdict["status"] == "pass"
    assert calls == ["pyA", "pyA", "pyB", "pyB"]
