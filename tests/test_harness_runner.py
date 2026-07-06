"""Fast-tier tests for harness/run.py — the judge taxonomy and the capture seam.

The seam under test is the injected capture callable: these prove the runner
composes capture → artifact → verdict correctly (pass / divergent /
irreproducible / error) without any engine environment.
"""

import json

from harness.compare import digest
from harness.run import judge_case, load_artifact, run_case

CASE = {"id": "c1", "comparison": {"probes": {}}}


def art(probes, exe="pyX"):
    return {"schema": 1, "case_id": "c1",
            "engine": {"executable": exe}, "env": {"PYTHONHASHSEED": "0"},
            "probes": probes,
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


def test_judge_self_proof_never_reports_divergence():
    """proves: with one engine on both sides, a cross-pair mismatch judges as
    irreproducibility — self-proof mode cannot produce an engine finding."""
    pa, pb = {"x": [1]}, {"x": [2]}
    verdict = judge_case(CASE, quad(pa, pa, pb, pb), self_proof=True)
    assert verdict["status"] == "irreproducible"


def test_judge_irreproducible_reports_every_unstable_engine():
    """proves: a same-engine repeat mismatch is that engine's irreproducibility
    (never a finding), and both engines are named when both are unstable."""
    verdict = judge_case(CASE, quad({"x": [1]}, {"x": [2]}, {"x": [1]}, {"x": [1]}))
    assert verdict["status"] == "irreproducible"
    assert verdict["detail"] == "engine-a"
    both = judge_case(CASE, quad({"x": [1]}, {"x": [2]}, {"x": [3]}, {"x": [4]}))
    assert both["detail"] == "engine-a, engine-b"


def test_judge_error_when_a_capture_failed():
    """proves: a failed or missing capture judges as error, carrying the engine
    run name and the recorded failure."""
    artifacts = quad({"x": [1]}, {"x": [1]}, {"x": [1]}, {"x": [1]})
    artifacts["b2"] = {"schema": 1, "case_id": "c1", "error": "ValueError('boom')"}
    verdict = judge_case(CASE, artifacts)
    assert verdict["status"] == "error"
    assert "b2" in verdict["detail"] and "boom" in verdict["detail"]


def test_judge_error_on_identity_or_env_mismatch():
    """proves: repeat pairs that did not share an engine executable and env
    fingerprint judge as error — the metadata is asserted, not decorative."""
    artifacts = quad({"x": [1]}, {"x": [1]}, {"x": [1]}, {"x": [1]})
    artifacts["a2"] = art({"x": [1]}, exe="other-python")
    verdict = judge_case(CASE, artifacts)
    assert verdict["status"] == "error"
    assert "identity" in verdict["detail"]


def test_load_artifact_maps_failures_to_error_artifacts(tmp_path):
    """proves: a missing artifact, an unreadable artifact, and a nonzero capture
    exit each become that run's error artifact — one bad run never crashes or
    silently passes the batch."""
    missing = load_artifact(tmp_path / "nope.json", returncode=1)
    assert "exited 1" in missing["error"]
    corrupt = tmp_path / "c.json"
    corrupt.write_text('{"schema": 1, "probes"')
    assert "unreadable" in load_artifact(corrupt, returncode=0)["error"]
    stale = tmp_path / "s.json"
    stale.write_text(json.dumps(art({"x": [1]})))
    assert "despite" in load_artifact(stale, returncode=137)["error"]
    assert "error" not in load_artifact(stale, returncode=0)


def test_run_case_drives_four_captures_through_the_seam(tmp_path):
    """proves: run_case captures each case twice per engine through the injected
    capture callable and judges from the artifacts it wrote."""
    case_path = tmp_path / "case.json"
    case_path.write_text(json.dumps(
        {"id": "seam", "inputs": {},
         "probes": [{"id": "x", "kind": "get_time"}], "comparison": {}}))
    calls = []

    def fake_capture(exe, case_p, out_p):
        calls.append(exe)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(art({"x": [1]}, exe=exe)))
        return 0

    verdict = run_case(case_path, "pyA", "pyB", tmp_path / "results",
                       capture=fake_capture)
    assert verdict["status"] == "pass"
    assert calls == ["pyA", "pyA", "pyB", "pyB"]
