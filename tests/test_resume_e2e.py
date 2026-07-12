"""E2E exercise of the runner's per-case resume over live oracle captures.

Needs the live oracle environment (`oracle-env/`); the gate deselects it. Run
explicitly with `uv run pytest tests/test_resume_e2e.py -m e2e`. Deliberately
small — three reason-free cases (~1.6 s per capture on this machine): the
resume semantics under test are identical at any corpus size.
"""

import json
import shutil
from pathlib import Path

import pytest

from harness import run as harness_run
from harness.run import MARKER_NAME

REPO = Path(__file__).resolve().parents[1]
ORACLE_PYTHON = REPO / "oracle-env" / "bin" / "python"
# Reason-free committed cases — cheap captures, full artifact schema.
MINI_CORPUS = ("interval-ops", "label-ops", "query-construct")


@pytest.mark.e2e
def test_mini_sweep_resume_equals_a_clean_run(tmp_path):
    """proves: on live oracle self-proof captures, a sweep interrupted two
    ways (one case's marker deleted, another's artifact truncated) resumes
    over the same results dir recapturing only the incomplete cases — the
    untouched case's artifacts are not rewritten — and the resumed report's
    verdicts equal the uninterrupted report's while its resume block and a
    fresh dir's report say honestly which invocation shape produced them."""
    if not ORACLE_PYTHON.exists():
        pytest.skip("oracle-env/ not built on this machine")
    cases = tmp_path / "cases"
    cases.mkdir()
    for cid in MINI_CORPUS:
        shutil.copy(REPO / "harness" / "cases" / f"{cid}.json",
                    cases / f"{cid}.json")
    results = tmp_path / "results"
    argv = ["--cases", str(cases), "--engine-a", str(ORACLE_PYTHON),
            "--results", str(results)]

    assert harness_run.main(argv) == 0
    clean = json.loads((results / "report.json").read_text())
    assert clean["resume"]["resumed"] is False
    assert clean["resume"]["captured_this_invocation"] == list(MINI_CORPUS)

    # The two interruption shapes: killed before completion (no marker) and
    # killed mid-write (truncated artifact, marker present).
    (results / "interval-ops" / MARKER_NAME).unlink()
    trunc = results / "label-ops" / "b1.json"
    trunc.write_text(trunc.read_text()[:100])
    untouched = sorted((results / "query-construct").glob("*.json"))
    before = [(p.name, p.stat().st_mtime_ns) for p in untouched]

    assert harness_run.main(argv) == 0
    resumed = json.loads((results / "report.json").read_text())
    assert resumed["verdicts"] == clean["verdicts"]
    assert all(v["status"] == "pass" for v in resumed["verdicts"])
    assert resumed["resume"] == {
        "resumed": True,
        "prior_complete": ["query-construct"],
        "captured_this_invocation": ["interval-ops", "label-ops"]}
    after = [(p.name, p.stat().st_mtime_ns) for p in untouched]
    assert after == before  # the completed case was re-judged, not re-captured
