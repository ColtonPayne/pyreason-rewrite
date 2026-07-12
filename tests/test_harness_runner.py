"""Fast-tier tests for harness/run.py — the judge taxonomy and the capture seam.

The seam under test is the injected capture callable: these prove the runner
composes capture → artifact → verdict correctly (pass / divergent /
irreproducible / error) without any engine environment.
"""

import json

from harness.compare import digest
from harness.run import (CAPTURE_NAMES, MARKER_NAME, judge_case,
                         load_artifact, run_case)

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


def make_case(tmp_path, case_id="seam"):
    case_path = tmp_path / f"{case_id}.json"
    case_path.write_text(json.dumps(
        {"id": case_id, "inputs": {},
         "probes": [{"id": "x", "kind": "get_time"}], "comparison": {}}))
    return case_path


def counting_capture(calls):
    def fake_capture(exe, case_p, out_p):
        calls.append(exe)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(art({"x": [1]}, exe=exe)))
        return 0
    return fake_capture


def test_run_case_drives_four_captures_through_the_seam(tmp_path):
    """proves: run_case captures each case twice per engine through the injected
    capture callable and judges from the artifacts it wrote."""
    case_path = make_case(tmp_path)
    calls = []
    verdict, prior = run_case(case_path, "pyA", "pyB", tmp_path / "results",
                              capture=counting_capture(calls))
    assert verdict["status"] == "pass"
    assert prior is False
    assert calls == ["pyA", "pyA", "pyB", "pyB"]


def test_completed_case_writes_a_marker_and_resumes_without_recapture(tmp_path):
    """proves: a completed case leaves a completion marker decidable from the
    results dir alone, and a re-invocation re-judges it from the on-disk
    artifacts — identical verdict, zero new captures, prior=True."""
    case_path = make_case(tmp_path)
    results = tmp_path / "results"
    calls = []
    first, prior1 = run_case(case_path, "pyA", "pyB", results,
                             capture=counting_capture(calls))
    marker = json.loads((results / "seam" / MARKER_NAME).read_text())
    assert marker["schema"] == 1
    assert set(marker["returncodes"]) == set(CAPTURE_NAMES)
    assert set(marker["artifacts"]) == set(CAPTURE_NAMES)

    second, prior2 = run_case(case_path, "pyA", "pyB", results,
                              capture=counting_capture(calls))
    assert (prior1, prior2) == (False, True)
    assert second == first
    assert len(calls) == 4  # nothing captured on the resume pass


def test_identity_mismatch_invalidates_the_marker(tmp_path):
    """proves: a marker only vouches for its own invocation — a changed case
    file, a different engine executable, or a different partner engine each
    force a full re-capture of that case."""
    case_path = make_case(tmp_path)
    results = tmp_path / "results"
    calls = []
    run_case(case_path, "pyA", "pyB", results, capture=counting_capture(calls))

    _, prior = run_case(case_path, "pyA", "pyC", results,
                        capture=counting_capture(calls))
    assert prior is False and len(calls) == 8

    case_path.write_text(case_path.read_text() + " ")
    _, prior = run_case(case_path, "pyA", "pyC", results,
                        capture=counting_capture(calls))
    assert prior is False and len(calls) == 12


def test_damaged_artifact_or_missing_marker_reruns_the_case(tmp_path):
    """proves: the two interruption shapes — a deleted marker (killed before
    completion) and a truncated artifact (killed mid-write) — each read as
    incomplete, so the case re-captures whole instead of judging debris."""
    case_path = make_case(tmp_path)
    results = tmp_path / "results"
    calls = []
    run_case(case_path, "pyA", "pyB", results, capture=counting_capture(calls))

    (results / "seam" / MARKER_NAME).unlink()
    _, prior = run_case(case_path, "pyA", "pyB", results,
                        capture=counting_capture(calls))
    assert prior is False and len(calls) == 8

    artifact = results / "seam" / "b1.json"
    artifact.write_text(artifact.read_text()[:40])
    _, prior = run_case(case_path, "pyA", "pyB", results,
                        capture=counting_capture(calls))
    assert prior is False and len(calls) == 12
    verdict, prior = run_case(case_path, "pyA", "pyB", results,
                              capture=counting_capture(calls))
    assert prior is True and len(calls) == 12
    assert verdict["status"] == "pass"


def test_stale_marker_is_removed_before_recapture_begins(tmp_path):
    """proves: a re-run deletes the stale marker before its first capture, so
    an interruption mid-recapture can never leave an old marker vouching for a
    partially refreshed case dir."""
    case_path = make_case(tmp_path)
    results = tmp_path / "results"
    run_case(case_path, "pyA", "pyB", results, capture=counting_capture([]))
    artifact = results / "seam" / "a2.json"
    artifact.write_text(artifact.read_text()[:40])  # now incomplete

    def dying_capture(exe, case_p, out_p):
        raise RuntimeError("host interruption")

    try:
        run_case(case_path, "pyA", "pyB", results, capture=dying_capture)
    except RuntimeError:
        pass
    assert not (results / "seam" / MARKER_NAME).exists()


def test_error_verdict_is_still_a_completed_case(tmp_path):
    """proves: a capture that exits nonzero (artifact absent) completes the
    case with an error verdict, and a re-invocation resumes to the identical
    error verdict rather than silently retrying — forcing a retry is the
    explicit act of deleting the marker or the case dir."""
    case_path = make_case(tmp_path)
    results = tmp_path / "results"
    calls = []

    def failing_capture(exe, case_p, out_p):
        calls.append(exe)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if len(calls) == 3:  # b1 dies without an artifact
            return 137
        out_p.write_text(json.dumps(art({"x": [1]}, exe=exe)))
        return 0

    first, _ = run_case(case_path, "pyA", "pyB", results,
                        capture=failing_capture)
    assert first["status"] == "error" and "b1" in first["detail"]
    second, prior = run_case(case_path, "pyA", "pyB", results,
                             capture=failing_capture)
    assert prior is True and len(calls) == 4
    assert second == first


def test_resumed_report_equals_a_clean_run_and_says_resumed(tmp_path, monkeypatch, capsys):
    """proves: after an artificial interruption (one marker deleted), a
    re-invocation recaptures only the incomplete case, its report's verdicts
    equal the uninterrupted report's, and the resume block plus console SAY it
    was resumed — while a single-invocation report says resumed: false."""
    from harness import run as harness_run

    cases = tmp_path / "cases"
    cases.mkdir()
    for cid in ("c-one", "c-two", "c-three"):
        make_case(cases, cid)
    calls = []
    monkeypatch.setattr(harness_run, "capture_subprocess",
                        counting_capture(calls))
    results = tmp_path / "results"
    argv = ["--cases", str(cases), "--engine-a", "pyA", "--engine-b", "pyB",
            "--results", str(results)]

    assert harness_run.main(argv) == 0
    clean = json.loads((results / "report.json").read_text())
    assert clean["resume"] == {"resumed": False, "prior_complete": [],
                               "captured_this_invocation":
                                   ["c-one", "c-three", "c-two"]}
    assert len(calls) == 12

    (results / "c-two" / MARKER_NAME).unlink()  # the interruption
    capsys.readouterr()
    assert harness_run.main(argv) == 0
    resumed = json.loads((results / "report.json").read_text())
    assert resumed["verdicts"] == clean["verdicts"]
    assert resumed["resume"] == {"resumed": True,
                                 "prior_complete": ["c-one", "c-three"],
                                 "captured_this_invocation": ["c-two"]}
    assert len(calls) == 16  # only c-two recaptured
    console = capsys.readouterr().out
    assert "RESUMED — 2 prior-complete, 1 captured this invocation" in console
    assert console.count("[prior-complete]") == 2
