"""Fast-tier tripwires pinning campaign-env dependency versions against their
recorded expectations.

Not a lockfile check — uv.lock already pins resolution. This is the seam the
lockfile cannot cover: the version the running interpreter actually imports,
asserted in the same tier every commit runs, so a silently moved environment
(a rebuilt venv, a lock update that slipped past the ledger) trips loudly
before any capture is compared under it.
"""

import yaml

# Operator-approved for the campaign env in ledger session 22 (the
# `load_inconsistent_predicate_list` YAML path); pinned in uv.lock.
PYYAML_EXPECTED = "6.0.3"


def test_pyyaml_version_matches_the_recorded_expectation():
    """proves: the campaign env's imported pyyaml is exactly the 6.0.3 the
    operator approved in session 22 — the version the IPL/YAML-consuming case
    family was screened under."""
    assert yaml.__version__ == PYYAML_EXPECTED, (
        f"pyyaml moved: this environment imports {yaml.__version__}, the "
        f"recorded expectation is {PYYAML_EXPECTED} (operator-approved in "
        f"docs/ledger/session-22.md; pinned in uv.lock). If the move is "
        f"legitimate — an operator-approved lock update — re-screen the "
        f"YAML-consuming case family against the oracle pin BEFORE accepting "
        f"it: run the ipl-* cases (ipl-load-basic, ipl-load-malformed, "
        f"ipl-load-null-overwrite, ipl-atom-trace-off-trace — the "
        f"load_inconsistent_predicate_list path) oracle-vs-rewrite via "
        f"harness.run, confirm ALL PASS, then update PYYAML_EXPECTED here "
        f"citing the new screen. Never update the expected version without "
        f"that re-screen banked."
    )
