"""MVP acceptance: the preflight doctor against the real federated substrate.

Marked e2e — the pre-commit gate deselects it; run explicitly with
`uv run pytest -m e2e`. On the campaign's second-laptop start this same doctor
runs as Step 0 and its JSON report banks as ledger session 0.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

DOCTOR = Path(__file__).resolve().parent.parent / "tools" / "hive_preflight.py"


@pytest.mark.e2e
def test_preflight_passes_on_this_machine():
    """proves: every federated hivemind mechanism this repo consumes — manifest entry,
    hstate, the corpus link gate, the lrag pyreason-analysis probe, the oracle pin,
    the ledger seam, git wiring — answers end-to-end from this machine."""
    proc = subprocess.run(
        [sys.executable, str(DOCTOR), "--json"],
        capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, f"preflight failed:\n{proc.stdout}\n{proc.stderr}"
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    assert len(report["results"]) == 10
