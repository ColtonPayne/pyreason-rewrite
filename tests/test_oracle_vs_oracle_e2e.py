"""The AC-2 self-proof, e2e-marked: oracle-vs-oracle on the seed corpus.

Needs the live oracle environment (`oracle-env/`, built per
tools/oracle_smoke.py's docstring) — the gate deselects it; run explicitly with
`uv run pytest -m e2e`.
"""

from pathlib import Path

import pytest

from harness import run as harness_run

REPO = Path(__file__).resolve().parents[1]
ORACLE_PYTHON = REPO / "oracle-env" / "bin" / "python"


@pytest.mark.e2e
def test_oracle_vs_oracle_seed_corpus(tmp_path):
    """proves: on this machine the pinned oracle is reproducible against itself
    over the committed seed corpus — repeats green, digests stable — the
    precondition for any rewrite claim to count."""
    if not ORACLE_PYTHON.exists():
        pytest.skip("oracle-env/ not built on this machine")
    rc = harness_run.main([
        "--cases", str(REPO / "harness" / "cases"),
        "--engine-a", str(ORACLE_PYTHON),
        "--results", str(tmp_path),
    ])
    assert rc == 0
