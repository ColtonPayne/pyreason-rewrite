"""Fast-tier seam tests for tools/hive_preflight.py.

The seam under test is the injected command runner + tmp-dir repo/umbrella roots:
these prove the doctor's aggregation, exit codes, and failure reporting without
touching the real hivemind substrate (the marked e2e test covers that).
"""

import json

import pytest

import hive_preflight

SHA = "e1a94af33e1f9d925c9df8284113dd0e14fe8a73"


def make_roots(tmp_path, pin_sha=SHA, manifest_entry=True):
    """A minimal on-disk repo root + umbrella root the filesystem checks accept."""
    root = tmp_path / "pyreason-rewrite"
    (root / "oracle").mkdir(parents=True)
    (root / "oracle" / "PIN").write_text(f"{pin_sha}\n# pinned oracle\n")
    (root / "docs" / "ledger").mkdir(parents=True)
    umbrella = tmp_path / "ai-hivemind"
    umbrella.mkdir()
    entry = f'pyreason-rewrite = "{root}"\n' if manifest_entry else ""
    (umbrella / "repos.toml").write_text(f'ai-hivemind = "."\n{entry}')
    return root, umbrella


def green_run_cmd(argv, timeout=0, cwd=None):
    """Fake runner where every federated mechanism answers healthy."""
    if "rev-parse" in argv:
        return 0, SHA + "\n"
    if "--porcelain" in argv:
        return 0, ""
    if argv[-1] == "user.name":
        return 0, "Colton\n"
    if argv[-1] == "user.email":
        return 0, "colton@example.com\n"
    if argv[-1] == "core.hooksPath":
        return 0, "scripts/hooks\n"
    if "retrieve" in argv:
        return 0, "1  note · dyuman-pryeason · pyreason-analysis\n"
    return 0, "ok\n"


def run_doctor(root, umbrella, run_cmd, extra_args=()):
    return hive_preflight.main(
        ["--umbrella", str(umbrella), "--json", *extra_args],
        run_cmd=run_cmd, root=root,
    )


def test_all_green_exits_zero(tmp_path, capsys):
    """proves: a machine where every federated mechanism answers yields exit 0 and an
    all-ok JSON report covering all ten checks."""
    root, umbrella = make_roots(tmp_path)
    assert run_doctor(root, umbrella, green_run_cmd) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert len(report["results"]) == 10
    assert all(r["ok"] for r in report["results"])


def test_failing_mechanism_exits_one_with_hint(tmp_path, capsys):
    """proves: one red mechanism (the corpus link gate) turns the doctor red — exit 1
    with that check's actionable hint in the report."""
    root, umbrella = make_roots(tmp_path)

    def red_links(argv, timeout=0, cwd=None):
        if "links" in argv:
            return 1, "stale links block in docs/foo.md\n"
        return green_run_cmd(argv, timeout, cwd)

    assert run_doctor(root, umbrella, red_links) == 1
    report = json.loads(capsys.readouterr().out)
    failed = [r for r in report["results"] if not r["ok"]]
    assert [r["name"] for r in failed] == ["links-gate"]
    assert "hive-state-links" in failed[0]["hint"]


def test_oracle_pin_drift_fails(tmp_path, capsys):
    """proves: an oracle clone whose HEAD drifted off oracle/PIN fails the pin check,
    so campaign work never silently builds on the wrong upstream commit."""
    root, umbrella = make_roots(tmp_path, pin_sha="0" * 40)
    assert run_doctor(root, umbrella, green_run_cmd) == 1
    report = json.loads(capsys.readouterr().out)
    pin = next(r for r in report["results"] if r["name"] == "oracle-pin")
    assert pin["ok"] is False


def test_missing_manifest_entry_fails_with_hint(tmp_path, capsys):
    """proves: an umbrella manifest without this repo's entry fails manifest-entry and
    the hint names the exact repos.toml edit."""
    root, umbrella = make_roots(tmp_path, manifest_entry=False)
    assert run_doctor(root, umbrella, green_run_cmd) == 1
    report = json.loads(capsys.readouterr().out)
    entry = next(r for r in report["results"] if r["name"] == "manifest-entry")
    assert entry["ok"] is False
    assert "repos.toml" in entry["hint"]


def test_crashing_check_is_failure_not_crash(tmp_path, capsys):
    """proves: a probe that raises is reported as that check's failure — the doctor
    still emits a full report and exits 1 instead of crashing."""
    root, umbrella = make_roots(tmp_path)
    (umbrella / "repos.toml").write_text("not [valid toml\n")
    assert run_doctor(root, umbrella, green_run_cmd) == 1
    report = json.loads(capsys.readouterr().out)
    assert len(report["results"]) == 10
    entry = next(r for r in report["results"] if r["name"] == "manifest-entry")
    assert entry["ok"] is False and "crashed" in entry["detail"]


def test_usage_error_exits_two(tmp_path):
    """proves: an unknown flag exits 2, matching the hivemind 0/1/2 exit-code
    convention (0 ok / 1 operational / 2 usage-config)."""
    root, umbrella = make_roots(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_doctor(root, umbrella, green_run_cmd, extra_args=["--bogus"])
    assert exc.value.code == 2
