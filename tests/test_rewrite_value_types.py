"""Seam tests for the rewrite's public value types (src/pyreason).

Each expectation is the banked oracle behavior from the type-row cases
(interval-ops, label-ops, threshold-construct) — the messages and shapes
asserted here are the ones the differential harness compares verbatim.
"""

import pytest

from pyreason.interval import closed
from pyreason.label import Label
from pyreason.threshold import Threshold


def test_interval_construction_seeds_prev_from_current():
    """proves: closed() stores float bounds and seeds prev_lower/prev_upper
    from the constructed bounds, with the static flag defaulting off."""
    iv = closed(0.25, 0.75)
    assert (iv.lower, iv.upper) == (0.25, 0.75)
    assert (iv.prev_lower, iv.prev_upper) == (0.25, 0.75)
    assert iv.is_static() is False
    assert iv.has_changed() is False


def test_interval_repr_renders_floats():
    """proves: to_str/repr render float text ('[0.0,1.0]', never '[0,1]'),
    matching the pinned numpy-float rendering the artifacts bank."""
    assert closed(0, 1).to_str() == "[0.0,1.0]"
    assert repr(closed(0.25, 0.5)) == "[0.25,0.5]"


def test_interval_equality_and_hash_ignore_static_and_prev():
    """proves: == and hash consult only the current bounds — a static/plain
    pair with equal bounds compares and hashes equal."""
    a, b = closed(0.25, 0.5, True), closed(0.25, 0.5)
    b.reset()
    b.set_lower_upper(0.25, 0.5)  # same bounds, different prev
    assert a == b
    assert hash(a) == hash(b)


def test_interval_contains_is_bound_inclusion():
    """proves: `other in iv` is inclusion of other's bounds within iv's."""
    assert closed(0.5, 0.75) in closed(0.25, 1.0)
    assert closed(0.25, 1.0) not in closed(0.5, 0.75)


def test_interval_inverted_bounds_accepted_and_intersection_clamps():
    """proves: an inverted pair (lower > upper) constructs unvalidated, and
    an empty intersection clamps to [0.0, 1.0] — the pinned closed-arm pair."""
    iv = closed(0.75, 0.25)
    assert (iv.lower, iv.upper) == (0.75, 0.25)
    clamped = iv.intersection(closed(0.875, 1.0))
    assert (clamped.lower, clamped.upper) == (0.0, 1.0)


def test_interval_reset_banks_prev_and_widens_ignoring_static():
    """proves: reset() sets prev to the pre-reset bounds and widens to
    [0.0, 1.0] even on a static interval (the static guard is the caller's)."""
    iv = closed(0.25, 0.5, True)
    iv.reset()
    assert (iv.lower, iv.upper) == (0.0, 1.0)
    assert (iv.prev_lower, iv.prev_upper) == (0.25, 0.5)
    assert iv.is_static() is True
    assert iv.has_changed() is True


def test_intersection_seeds_prev_from_self_current_bounds():
    """proves: intersection() seeds the result's prev bounds from self's
    CURRENT bounds — the pinned proxy arm interval-ops banks (the jitted
    overload's prev-seeding is out of reach and not reproduced)."""
    iv = closed(0.25, 0.75)
    iv.reset()  # current [0.0,1.0], prev [0.25,0.75]
    result = iv.intersection(closed(0.5, 1.0))
    assert (result.lower, result.upper) == (0.5, 1.0)
    assert (result.prev_lower, result.prev_upper) == (0.0, 1.0)
    assert result.is_static() is False


def test_label_equality_and_hash_by_string_value():
    """proves: same-text distinct Labels compare and hash equal, different
    text unequal — the value semantics predicate lookups rely on."""
    assert Label("popular") == Label("popular")
    assert hash(Label("popular")) == hash(Label("popular"))
    assert Label("popular") != Label("unpopular")
    assert str(Label("")) == "" and repr(Label("x")) == "x"


def test_label_eq_against_plain_string_raises_attributeerror():
    """proves: Label == plain-str raises AttributeError('str' object has no
    attribute 'get_value') — the pinned get_value-before-isinstance order,
    kept as banked behavior rather than fixed."""
    with pytest.raises(AttributeError, match="'str' object has no attribute 'get_value'"):
        Label("popular") == "popular"


def test_threshold_accepts_all_quantifiers_and_stores_verbatim():
    """proves: every pinned quantifier and quantifier_type combination
    constructs, and to_tuple() echoes the stored triple verbatim."""
    for q in ("greater_equal", "greater", "less_equal", "less", "equal"):
        t = Threshold(q, ("number", "total"), 1)
        assert t.to_tuple() == (q, ("number", "total"), 1)
    t = Threshold("less_equal", ("percent", "available"), 100)
    assert t.to_tuple() == ("less_equal", ("percent", "available"), 100)


def test_threshold_thresh_is_unvalidated():
    """proves: thresh stores negative and non-numeric values without
    validation — the pinned no-check arm threshold-construct banks."""
    assert Threshold("greater_equal", ("number", "total"), -5).thresh == -5
    assert Threshold("greater_equal", ("percent", "total"), "many").thresh == "many"


def test_threshold_rejects_bad_quantifier_and_type():
    """proves: an unknown quantifier raises ValueError('Invalid quantifier');
    an unknown quantifier_type member, and a bare string checked
    character-wise, raise ValueError('Invalid quantifier type')."""
    with pytest.raises(ValueError, match="^Invalid quantifier$"):
        Threshold("at_least", ("number", "total"), 1)
    with pytest.raises(ValueError, match="^Invalid quantifier type$"):
        Threshold("greater_equal", ("number", "every"), 1)
    with pytest.raises(ValueError, match="^Invalid quantifier type$"):
        Threshold("greater_equal", "number", 1)


def test_threshold_short_tuple_raises_indexerror():
    """proves: a length-1 quantifier_type raises IndexError('tuple index out
    of range') from the positional membership check — the pinned shape fault."""
    with pytest.raises(IndexError, match="tuple index out of range"):
        Threshold("greater_equal", ("number",), 1)
