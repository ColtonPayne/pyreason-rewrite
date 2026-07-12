"""DIV-0002's pin-side reproducer (e2e: needs the live oracle env).

The record: docs/divergences/DIV-0002.md. An IPL YAML whose pair entries
are YAML integers passes parse_ipl's pure-Python arms (Label's constructor
checks nothing) and dies at the typed-list append: unbox_label
(label_type.py:86-94) unboxes `_value` as a numba string, and an int read
as a unicode struct raises ValueError with an ADDRESS-DERIVED message —
4 fresh pin processes gave 4 distinct texts in the slice-8 review, so the
harness scores the input irreproducible on the pin itself and no
exact-compare case can bank the arm. The rewrite, per the operator
adjudication of 2026-07-11 (option (a)), raises the same ValueError type
at the same append seam with a stable, honest message (the fast-tier
twin: tests/test_rewrite_state_loaders.py::
test_ipl_yaml_nonstring_entries_raise_stable_valueerror).
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ORACLE_PY = REPO / "oracle-env" / "bin" / "python"

PIN_SCRIPT = """
import pyreason as pr
pr.settings.verbose = False
pr.load_inconsistent_predicate_list({path!r})
print("COMPLETED")
"""


@pytest.mark.e2e
def test_pinned_ipl_loader_raises_unstable_valueerror_on_nonstring_entries(tmp_path):
    """proves: at the pin, load_inconsistent_predicate_list over an IPL
    file whose pair entries are YAML integers raises builtins.ValueError
    from the typed-list unbox (message shape 'character U+... is not in
    range [U+0000; U+10ffff]' — the int read as a unicode struct), never
    reaching COMPLETED — the pin-side half of DIV-0002 (adjudicated: the
    rewrite raises the same type at the same seam, but with the stable
    message the pin's address-derived text cannot be)."""
    ipl = tmp_path / "nonstring-ipl.yaml"
    ipl.write_text("ipl:\n  - [1, 2]\n")
    result = subprocess.run(
        [str(ORACLE_PY), "-c", PIN_SCRIPT.format(path=str(ipl))],
        cwd=tmp_path, capture_output=True, text=True, timeout=600)
    assert result.returncode != 0
    assert "COMPLETED" not in result.stdout
    assert "ValueError" in result.stderr
    assert re.search(
        r"character U\+[0-9a-fA-F]+ is not in range \[U\+0000; U\+10ffff\]",
        result.stderr)
