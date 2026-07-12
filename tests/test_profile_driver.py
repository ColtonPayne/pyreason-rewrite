"""Fast-tier tests for harness/profile.py's pure layer — pstats-row
extraction, percentage accounting, and table formatting the Phase-4
profile report cites. No engine, no profiler run: the measured seam is
exercised by the banked profiling runs themselves
(docs/perf/profile-phase4.md)."""

import pytest

from harness.profile import (format_rows, func_label, top_rows,
                             total_profiled_s)

# pstats entry shape: {(file, line, name): (cc, nc, tt, ct, callers)}
STATS = {
    ("/repo/src/pyreason/core.py", 10, "ground"): (5, 5, 6.0, 9.0, {}),
    ("/repo/src/pyreason/core.py", 50, "fire"): (20, 25, 3.0, 3.5, {}),
    ("~", 0, "<built-in method builtins.len>"): (100, 100, 1.0, 1.0, {}),
    ("/repo/src/pyreason/api.py", 5, "reason"): (1, 1, 0.0, 10.0, {}),
}


def test_func_label_shortens_paths_and_names_builtins():
    """proves: real functions label as parent/file:line(name); pstats'
    '~' built-in convention labels by name alone."""
    assert func_label(("/repo/src/pyreason/core.py", 10, "ground")) \
        == "pyreason/core.py:10(ground)"
    assert func_label(("~", 0, "<built-in method builtins.len>")) \
        == "<built-in method builtins.len>"


def test_total_profiled_s_sums_self_time():
    """proves: the percentage denominator is the sum of self times (tt) —
    cProfile's own total — not a sum of cumulative times."""
    assert total_profiled_s(STATS) == pytest.approx(10.0)


def test_top_rows_sorts_by_cumulative_and_truncates():
    """proves: sort_by='cumulative' ranks by ct descending and returns
    exactly n rows — the entry point (highest ct, zero tt) ranks first."""
    rows = top_rows(STATS, "cumulative", 2)
    assert [r["func"] for r in rows] == [
        "pyreason/api.py:5(reason)", "pyreason/core.py:10(ground)"]
    assert rows[0]["cum_pct"] == pytest.approx(100.0)
    assert rows[0]["self_pct"] == pytest.approx(0.0)


def test_top_rows_sorts_by_self_time_with_percentages():
    """proves: sort_by='self' ranks by tt descending and each row carries
    self seconds and self% of the total profiled time."""
    rows = top_rows(STATS, "self", 3)
    assert [r["func"] for r in rows] == [
        "pyreason/core.py:10(ground)", "pyreason/core.py:50(fire)",
        "<built-in method builtins.len>"]
    assert rows[0]["self_s"] == pytest.approx(6.0)
    assert rows[0]["self_pct"] == pytest.approx(60.0)
    assert rows[1]["self_pct"] == pytest.approx(30.0)


def test_top_rows_rejects_unknown_sort_key_and_survives_empty_stats():
    """proves: an unknown sort key is a named error (never a silent
    default), and empty stats yield empty rows with no zero-division."""
    with pytest.raises(ValueError, match="unknown sort key"):
        top_rows(STATS, "tottime", 3)
    assert top_rows({}, "self", 3) == []


def test_format_rows_renders_calls_and_recursion_marker():
    """proves: the text table carries the title, seconds/percent columns,
    and pstats' nc/cc marker only when calls are recursive."""
    text = format_rows(top_rows(STATS, "self", 2), "top 2 by self time")
    assert text.splitlines()[0] == "top 2 by self time"
    assert "6.000" in text and "60.0" in text
    assert "pyreason/core.py:10(ground)" in text
    assert "25/20" in text          # recursive: nc != cc
    assert "5/5" not in text        # non-recursive: plain count
