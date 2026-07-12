"""Fast-tier tests for harness/bench.py's pure layer — parsing, payload
validation, and the median/spread aggregation the banked baselines cite.
No engine, no subprocess: the measured seam is exercised e2e by the banked
baseline runs themselves (docs/perf/oracle-baselines.md)."""

import pytest

from harness.bench import (aggregate_case, child_payload_fault, parse_maxrss,
                           summarize)

TIME_L_TAIL = """\
some child stderr line
        7.73 real         8.12 user         2.55 sys
           336379904  maximum resident set size
               45411  page reclaims
                 293  page faults
"""


def _payload(import_s=1.0, setup_s=0.5, reason_s=2.0):
    return {"schema": 1, "mode": "bench-child", "case_id": "c",
            "import_s": import_s, "setup_s": setup_s, "reason_s": reason_s,
            "python": "3.10.20", "executable": "/x/python"}


def test_parse_maxrss_reads_the_time_l_block():
    """proves: parse_maxrss extracts the peak-RSS byte count from a real
    /usr/bin/time -l stderr shape, ignoring surrounding rusage lines."""
    assert parse_maxrss(TIME_L_TAIL) == 336379904


def test_parse_maxrss_last_match_wins_and_absence_is_none():
    """proves: with a child echo mimicking the rusage line, the trailing
    (real) block wins; text with no rusage block parses to None."""
    doctored = ("999  maximum resident set size\n" + TIME_L_TAIL)
    assert parse_maxrss(doctored) == 336379904
    assert parse_maxrss("child said nothing relevant\n") is None


def test_summarize_median_and_noise_band_odd_and_even():
    """proves: summarize banks median/min/max and spread=max-min (the
    control-repeat noise band) for both odd and even repeat counts."""
    odd = summarize([3.0, 1.0, 2.0])
    assert odd == {"n": 3, "median": 2.0, "min": 1.0, "max": 3.0,
                   "spread": 2.0, "values": [3.0, 1.0, 2.0]}
    even = summarize([4.0, 1.0, 2.0, 3.0])
    assert even["median"] == 2.5 and even["spread"] == 3.0 and even["n"] == 4


def test_summarize_empty_is_none():
    """proves: a metric with no observations summarizes to None instead of
    fabricating a number (maxrss may be absent if the OS tool changes)."""
    assert summarize([]) is None


def test_child_payload_fault_accepts_the_real_shape():
    """proves: a well-formed bench-child payload passes validation, so a
    healthy run is aggregable."""
    assert child_payload_fault(_payload()) is None


@pytest.mark.parametrize("mutate", [
    lambda p: p.pop("reason_s"),
    lambda p: p.update(reason_s=-0.1),
    lambda p: p.update(import_s=True),
    lambda p: p.update(mode="capture"),
    lambda p: p.update(schema=2),
])
def test_child_payload_fault_rejects_partial_or_foreign_payloads(mutate):
    """proves: missing/negative/boolean metrics and non-bench-child schemas
    are named faults — a half-written child payload can never aggregate."""
    payload = _payload()
    mutate(payload)
    assert child_payload_fault(payload) is not None


def test_aggregate_case_derives_cold_start_and_survives_missing_maxrss():
    """proves: cold_start_s summarizes import_s+reason_s per run, and
    maxrss_bytes aggregates only over runs that carry it (None when none do)."""
    runs = [
        {**_payload(import_s=1.0, reason_s=2.0), "maxrss_bytes": 100,
         "wall_s": 4.0},
        {**_payload(import_s=2.0, reason_s=4.0), "maxrss_bytes": None,
         "wall_s": 8.0},
        {**_payload(import_s=3.0, reason_s=6.0), "maxrss_bytes": 300,
         "wall_s": 12.0},
    ]
    agg = aggregate_case(runs)
    assert agg["cold_start_s"]["values"] == [3.0, 6.0, 9.0]
    assert agg["cold_start_s"]["median"] == 6.0
    assert agg["maxrss_bytes"] == {"n": 2, "median": 200, "min": 100,
                                   "max": 300, "spread": 200,
                                   "values": [100, 300]}
    assert agg["reason_s"]["spread"] == 4.0
    no_rss = aggregate_case([{**_payload(), "maxrss_bytes": None,
                              "wall_s": None}])
    assert no_rss["maxrss_bytes"] is None and no_rss["wall_s"] is None
