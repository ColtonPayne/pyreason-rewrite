"""Seam tests for the rewrite's text-DSL entry points: Fact, Rule, Query.

Each malformed input is fed through the PUBLIC constructor (the seam the
harness drives), and the expected exception text is the banked oracle
message from fact-text-malformed / rule-text-malformed / query-construct —
asserted verbatim, because the differential harness compares raise messages
exactly.
"""

import re

import pytest

from pyreason import Fact, Query, Rule


def _raises_msg(exc_type, msg, fn):
    with pytest.raises(exc_type) as exc_info:
        fn()
    assert str(exc_info.value) == msg


# --- Fact text ---

@pytest.mark.parametrize("text,msg", [
    ("", "Fact text cannot be empty or whitespace only"),
    ("~~sick(Alice)", "Double negation is not allowed"),
    ("sick(Alice):[0,1]:[0,1]", "Fact text contains multiple colons (2), expected at most 1"),
    ("~", "Predicate-component cannot be empty"),
    ("sickAlice", "Missing opening parenthesis in fact"),
    ("sick((Alice)", "Invalid parentheses: found 2 '(' and 1 ')', expected exactly 1 of each"),
    ("sick)Alice(", "Invalid parentheses order: '(' must come before ')'"),
    ("sick()", "Component cannot be empty"),
    ("contact(Alice,Bob,Carol)", "Edge facts must have exactly 2 components, found 3"),
    ("contact(Alice,)", "Edge component 2 name cannot be empty"),
    ("1sick(Alice)", "Predicate name '1sick' cannot start with a digit. Must start with a letter or underscore"),
    ("si$ck(Alice)", "Predicate name 'si$ck' contains invalid characters. Must match [a-zA-Z_][a-zA-Z0-9_.\\-]*"),
    ("sick(Alice):[low,high]", "Invalid interval values: could not convert string to float: 'low'"),
    ("sick(Alice):[0,2]", "Interval upper bound 2.0 is out of valid range [0, 1]"),
    ("sick(Alice):[1,0]", "Interval lower bound 1.0 cannot be greater than upper bound 0.0"),
])
def test_fact_text_rejections_carry_banked_messages(text, msg):
    """proves: each malformed fact-text class raises ValueError with the
    exact banked oracle message (fact-text-malformed artifacts)."""
    _raises_msg(ValueError, msg, lambda: Fact(text))


def test_fact_predicate_charset_accepts_hyphen_and_dot():
    """proves: the pinned predicate regex accepts '-' and '.' — a hyphenated
    predicate is an accepted boundary shape, parsed with the default [1,1]."""
    f = Fact("si-ck.v2(Alice)")
    assert f.pred.get_value() == "si-ck.v2"
    assert f.component == "Alice"
    assert (f.bound.lower, f.bound.upper) == (1.0, 1.0)
    assert f.type == "node"


def test_fact_negated_explicit_interval_inverts_rounded():
    """proves: '~pred(x):[l,u]' stores [round(1-u,10), round(1-l,10)] — the
    pinned negation-with-explicit-bound transform including its rounding."""
    f = Fact("~sick(Alice):[0.2,0.8]")
    assert (f.bound.lower, f.bound.upper) == (0.2, 0.8)
    f2 = Fact("~sick(Alice):[0,0.8]")
    assert (f2.bound.lower, f2.bound.upper) == (0.2, 1.0)


# --- Rule text ---

@pytest.mark.parametrize("text,exc,msg", [
    (123, TypeError, "rule_text must be a string, got int"),
    ("", ValueError, "rule_text cannot be empty or whitespace only"),
    ("popular(x)", ValueError,
     "Rule must contain exactly one '<-' separator, found 0. Use the format: 'head(X) <- body(X)'"),
    ("popular(x) <- popular(y) <- popular(z)", ValueError,
     "Rule must contain exactly one '<-' separator, found 2. Use the format: 'head(X) <- body(X)'"),
    ("<-1 popular(y)", ValueError, "Rule head cannot be empty"),
    ("popular(x) <-1 popular(y),", ValueError,
     "Body clause 1 is empty. Check for trailing commas or double commas in the rule body"),
    ("popular(x) <-1 popular", ValueError,
     "Body clause 'popular' must contain parentheses around argument"),
    ("popular(x):[0.5] <-1 popular(y)", ValueError,
     "Bound must contain exactly 2 values, got 1: '0.5'. Note: Annotation function names cannot contain brackets '[' or ']'"),
    ("popular(x):[low,high] <-1 popular(y)", ValueError,
     "Bound lower value must be numeric, got 'low'. Note: Annotation function names cannot contain brackets '[' or ']'"),
    ("popular(x):[0,2] <-1 popular(y)", ValueError,
     "Bound upper value 2.0 is out of range [0, 1]"),
    ("popular(x):[1,0] <-1 popular(y)", ValueError,
     "Bound lower value 1.0 is greater than upper value 0.0"),
    ("popular(x) <-1 ~~popular(y)", ValueError,
     "Double negation '~~' is not allowed in body clause '~~popular(y)'"),
])
def test_rule_text_rejections_carry_banked_messages(text, exc, msg):
    """proves: each malformed rule-text class raises with the exact banked
    oracle message (rule-text-malformed artifacts), including the
    bracket-note suffix on bound-shaped head faults."""
    _raises_msg(exc, msg, lambda: Rule(text))


def test_rule_multichar_delta_consumed_as_one_integer():
    """proves: every leading body digit is consumed as one delta integer —
    '<-10' parses to delta 10 with the clause list intact, not an error."""
    r = Rule("popular(x) <-10 popular(y), Friends(x,y)").rule
    assert r.get_delta() == 10
    assert r.get_rule_name() is None
    assert r.get_rule_type() == "node"
    assert r.get_target().get_value() == "popular"
    assert list(r.get_head_variables()) == ["x"]
    assert len(r.get_clauses()) == 2


@pytest.mark.parametrize("text,delta", [
    ("popular(x) <- boss(x)", 0),          # no leading digits -> default 0
    ("popular(x) <-0 boss(x)", 0),         # explicit zero
    ("popular(x) <-65535 boss(x)", 65535),  # uint16 max, verbatim
    ("popular(x) <-65536 boss(x)", 0),      # wraps modulo 2**16
    ("popular(x) <-70000 boss(x)", 4464),   # 70000 - 65536
])
def test_rule_delta_wraps_at_uint16(text, delta):
    """proves: the stored delta wraps modulo 2**16 exactly as the pinned
    numba.types.uint16 cast does (rule_parser.py:243 at the pin; oracle
    fingerprints banked by the rule-delta-variants case: 65536 -> 0,
    70000 -> 4464)."""
    assert Rule(text).rule.get_delta() == delta


def test_rule_weights_nested_rectangular_list_accepted():
    """proves: a rectangular nested weights list is accepted with len() equal
    to its top-level row count — np.array([[1,2]]) is a (1,2) float array, so
    [[1,2]] passes a one-clause rule's length check exactly as the pin does
    (rule-json-weights-dtypes weights-nested probe, oracle acceptance banked
    2026-07-12)."""
    r = Rule("popular(x) <-1 boss(x)", "n", weights=[[1, 2]]).rule
    assert r.get_rule_name() == "n"


def test_rule_weights_none_entry_takes_finiteness_raise():
    """proves: a None weights entry converts to NaN the way
    np.array([None], dtype=float64) does, so it raises the finiteness
    ValueError — never the conversion TypeError (verified against the pinned
    numpy 2026-07-12)."""
    _raises_msg(ValueError,
                "weights must contain only finite values (no NaN or Inf)",
                lambda: Rule("popular(x) <-1 boss(x)", "n", weights=[None]))


def test_rule_weights_ragged_nested_list_takes_conversion_raise():
    """proves: a ragged nested weights list fails conversion (np.array
    raises on inhomogeneous shapes) and re-wraps as the pinned TypeError
    naming the input's own type."""
    _raises_msg(TypeError,
                "weights must be a numpy array or convertible to one, got list",
                lambda: Rule("popular(x) <-1 boss(x)", "n",
                             weights=[[1], [2, 3]]))


def test_rule_clause_shape_matches_fingerprint_contract():
    """proves: a parsed clause is the (type, Label, variables, Interval, op)
    tuple the accessor fingerprint renders — node clause, [1,1] default
    bound, empty operator."""
    r = Rule("trendy(x) <-1 popular(x)", "n").rule
    (ctype, lab, variables, bnd, op), = r.get_clauses()
    assert ctype == "node"
    assert lab.get_value() == "popular"
    assert list(variables) == ["x"]
    assert (bnd.lower, bnd.upper) == (1.0, 1.0)
    assert op == ""
    assert (r.get_bnd().lower, r.get_bnd().upper) == (1.0, 1.0)


# --- Query text ---

def test_query_parse_fields_across_forms():
    """proves: default [1,1] bounds, '~' inversion to [0,0], explicit bounds,
    edge components, and whitespace stripping parse to the pinned fields."""
    q = Query("popular(Mary)")
    assert (q.get_predicate().get_value(), q.get_component(),
            q.get_component_type()) == ("popular", "Mary", "node")
    assert (q.get_bounds().lower, q.get_bounds().upper) == (1.0, 1.0)

    assert (Query("~popular(Mary)").get_bounds().lower,
            Query("~popular(Mary)").get_bounds().upper) == (0.0, 0.0)

    q = Query("popular(Mary) : [0.2, 0.7]")
    assert (q.get_bounds().lower, q.get_bounds().upper) == (0.2, 0.7)
    assert str(q) == "popular(Mary) : [0.2, 0.7]"

    q = Query("Friends(John,Mary)")
    assert q.get_component() == ("John", "Mary")
    assert q.get_component_type() == "edge"


def test_query_silent_misparses_are_reproduced():
    """proves: the two pinned silent misparses parse the same wrong way here —
    no-paren text truncates pred/component to text[:-1], and negation with
    explicit bounds keeps '~' inside the predicate name (AC-6: reproduced
    and recorded, never silently repaired)."""
    q = Query("popularMary")
    assert q.get_predicate().get_value() == "popularMar"
    assert q.get_component() == "popularMar"

    q = Query("~popular(Mary):[0.5,1]")
    assert q.get_predicate().get_value() == "~popular"
    assert (q.get_bounds().lower, q.get_bounds().upper) == (0.5, 1.0)


def test_query_nonnumeric_bound_raises_float_message():
    """proves: a non-numeric bound raises ValueError with Python's float()
    message — the one raising query arm."""
    with pytest.raises(ValueError, match=re.escape("could not convert string to float: 'a'")):
        Query("popular(Mary):[a,b]")
