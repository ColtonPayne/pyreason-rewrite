"""Fast-tier tests for harness/compare.py — the stdlib comparison seam.

These prove the canonical form, digest stability, ordering-as-contract, and the
per-probe tolerance policy without importing any engine.
"""

from harness.compare import (approx_equal, canonical, canonical_json,
                             compare_probes, digest)


class FakeInterval:
    """Duck-typed stand-in for an engine interval (never imports one)."""

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper


def test_canonical_reduces_interval_likes_and_tuples():
    """proves: objects with numeric lower/upper reduce to [l,u] pairs and tuples
    to lists, so artifacts from any engine share one canonical vocabulary."""
    value = {"bound": FakeInterval(0.25, 1.0), "component": ("a", "b")}
    assert canonical(value) == {"bound": [0.25, 1.0], "component": ["a", "b"]}


def test_digest_ignores_dict_order_but_not_list_order():
    """proves: dict key order never affects a digest while list (row/event) order
    always does — ordering is part of the compared value."""
    assert digest({"x": 1, "y": 2}) == digest({"y": 2, "x": 1})
    assert digest([1, 2]) != digest([2, 1])


def test_canonical_json_is_deterministic():
    """proves: the canonical JSON of a nested value is byte-stable across calls,
    the property digest tripwires rely on."""
    value = {"rows": [[0.1, "n1", FakeInterval(0, 1)]], "t": 2}
    assert canonical_json(value) == canonical_json(value)


def test_approx_equal_bounds_numeric_leaves_only():
    """proves: a tolerance forgives numeric drift up to the bound but never a
    structural difference or an over-bound delta."""
    assert approx_equal([1.0, {"u": 0.5}], [1.0 + 1e-10, {"u": 0.5 - 1e-10}], 1e-9)
    assert not approx_equal([1.0], [1.1], 1e-9)
    assert not approx_equal([1.0], [1.0, 2.0], 1e-9)
    assert not approx_equal(True, 1, 1e-9)


def test_compare_probes_exact_by_default_tolerance_by_policy():
    """proves: probes compare exactly unless the case's policy names them with a
    tolerance — no global epsilon exists."""
    a = {"p": [0.5], "q": [0.5]}
    b = {"p": [0.5 + 1e-12], "q": [0.5 + 1e-12]}
    assert compare_probes(a, b) == ["p", "q"]
    policy = {"p": {"tolerance": 1e-9, "rationale": "test"}}
    assert compare_probes(a, b, policy) == ["q"]


def test_compare_probes_flags_missing_probe():
    """proves: a probe present in one artifact and absent in the other is a
    mismatch, never silently skipped."""
    assert compare_probes({"p": 1}, {}) == ["p"]
