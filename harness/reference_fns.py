"""The named-function registry for the callable-registering surface rows.

`add_annotation_function` and `add_head_function` take Python callables, which
cannot ride the JSON case format — so cases select *committed reference
functions* by name (the `add_annotation_function`/`add_head_function` apply
ops carry `{"name": ...}`), and the capture resolves the name to a callable at
registration time. An unknown name is an authoring fault (exit 2), validated
against REGISTRY before the engine imports.

This module is stdlib-only at import, like the rest of the harness: the fast
tier imports it to validate names without an engine environment. The pinned
engine requires registrands to be numba-njit-compilable at reason time (a
plain-python registrand passes the registration-time arity gate but fails
numba argument typing when reason() first dispatches — screened live
2026-07-07, not banked: the TypingError message embeds engine-environment
paths), so `resolve()` applies the `numba.njit` decoration inside the engine
environment rather than at import — but only where numba imports (the
conditional-njit accommodation, slice-2 review finding L1): an engine
environment without numba is by construction not running the pinned engine,
and handing it an njit dispatcher is impossible anyway, so resolve() there
returns the committed function plain, exactly as a plain-python engine
consumes callables. The `numba` module global below exists for the pinned
return contract: a head function must *return* `numba.typed.List` (the pinned
`_call_head_function` unboxes its objmode result to
`types.ListType(types.unicode_type)`, interpretation.py:2316-2338), and njit
compilation resolves that name as a module global at first call — after
resolve() has bound it. On the plain arm resolve() binds the same global to
`_PLAIN_NUMBA`, under which that contract reduces to the builtin list.

Registered names are matched by the engine against the callable's `__name__`
(annotate/interpretation.py:1920, _call_head_function/interpretation.py:2334),
so REGISTRY keys are exactly the functions' `__name__`s — a fast-tier test
holds that pairing.

Reference-function contract: deterministic, closed-form arithmetic only —
their outputs land in banked reasoning observations and must compare exactly
across fresh processes. The return-shape reject registrands below return
deliberately wrong shapes; their observable is the engine's reason-time
raise, screened stable on the pinned engine (2026-07-12, 2 fresh processes
per arm) before being cased.
"""

numba = None  # bound by resolve() inside the engine environment


class _PLAIN_NUMBA:
    """What the module-global `numba` means in an engine environment without
    numba (see resolve()): the head-registrand return contract's
    `numba.typed.List([...])` reduces to the builtin list, which is the shape
    a plain-python engine's head-function caller consumes. Nothing else is
    provided on purpose — a reference function reaching for any other numba
    surface should fail loudly in the plain arm, not limp."""
    class typed:
        List = list


def clause_lower_mean(annotations, weights):
    """2-arg annotation form: weight-scaled mean of the qualifying atoms'
    lower bounds; upper is the max qualifying upper. Values are chosen by the
    cases to be exact binary fractions."""
    total = 0.0
    count = 0
    upper = 0.0
    for i, clause in enumerate(annotations):
        for ann in clause:
            total += ann.lower * weights[i]
            count += 1
            if ann.upper > upper:
                upper = ann.upper
    return total / count, upper


def clause_zero_grounding_eighths(annotations, weights, qualified_nodes,
                                  qualified_edges, clause_labels,
                                  clause_variables):
    """6-arg annotation form: lower = (qualifying groundings of clause 0) / 8,
    capped at 1 — consumes the extended per-clause metadata the 2-arg form
    never sees, so a derived bound of e.g. [0.25, 1] proves the engine routed
    the extended signature."""
    count = len(qualified_nodes[0]) + len(qualified_edges[0])
    lower = count / 8.0
    if lower > 1.0:
        lower = 1.0
    return lower, 1.0


def first_clause_first_grounding(groundings):
    """Head function: ground the head variable to the first grounding of its
    first argument (the oracle test-suite's identity shape)."""
    return numba.typed.List([groundings[0][0]])


def three_positional_stub(annotations, weights, extra):
    """Deliberately wrong arity (3): the annotation registrar's reject arm."""
    return 0.0, 1.0


def star_args_stub(*args):
    """Deliberately zero declared positionals (co_argcount ignores *args):
    the registrar's varargs reject arm — and, njit-wrapped but never
    referenced by any rule, the head registrar's silent-acceptance arm."""
    return 0.0, 1.0


def bound_triple(annotations, weights):
    """2-arg annotation form returning a 3-TUPLE — the return-shape reject
    arm (slice-2 review L3): the pinned annotate() objmode block coerces the
    registrand's return to Tuple((float64, float64)) at its exit
    (interpretation.py:1918), so a 3-tuple fails at reason time with
    ValueError('size mismatch for tuple, expected 2 element(s) but got 3')."""
    return 0.25, 0.75, 0.5


def first_annotation_interval(annotations, weights):
    """2-arg annotation form returning the first qualifying atom's BOUND
    OBJECT instead of a (lower, upper) pair — the board's Interval-return
    arm (slice-2 review L3): the pinned objmode coercion rejects the boxed
    interval at reason time with TypeError('bad argument type for built-in
    operation')."""
    return annotations[0][0]


def head_first_grounding_bare(groundings):
    """Head function returning a BARE grounding string instead of the pinned
    list-of-strings contract — the head return-shape arm: the pinned
    _call_head_function objmode block unboxes its result to
    types.ListType(types.unicode_type) (interpretation.py:2332), so a str
    fails at reason time with TypeError("can't unbox a <class 'str'> as a
    <class 'numba.typed.typedlist.List'>")."""
    return groundings[0][0]


def clause_lower_mean_shadow(annotations, weights):
    """clause_lower_mean's duplicate-name twin (__name__ rebound below —
    see SHADOWS): registered alongside it, the pinned annotate() match loop
    has NO break (interpretation.py:1919-1930), so every same-named
    registrand runs and the LAST registration's result wins — batch item B3.
    A constant exact-binary return distinct from clause_lower_mean's makes
    the winner unambiguous in the banked bound."""
    return 0.5, 0.75


clause_lower_mean_shadow.__name__ = "clause_lower_mean"


def first_clause_first_grounding_shadow(groundings):
    """first_clause_first_grounding's duplicate-name twin (__name__ rebound
    below — see SHADOWS): grounds the head to the LAST grounding of its
    first argument, so which registration the resolver consumed is visible
    in the grounded head. The pinned _call_head_function loop BREAKS on the
    first __name__ match (interpretation.py:2334-2336) — the FIRST
    registration wins, the sharp asymmetry with the annotation side's
    last-wins."""
    return numba.typed.List([groundings[0][len(groundings[0]) - 1]])


first_clause_first_grounding_shadow.__name__ = "first_clause_first_grounding"


REGISTRY = {fn.__name__: fn for fn in (
    clause_lower_mean, clause_zero_grounding_eighths,
    first_clause_first_grounding, three_positional_stub, star_args_stub,
    bound_triple, first_annotation_interval, head_first_grounding_bare)}

# Duplicate-name twins: the registry KEY (what a case's apply op selects)
# deliberately differs from the function's __name__ (what the engine's
# match loops consume) — the only way one case can register two distinct
# callables under one engine-visible name, which is exactly what the
# duplicate-name arms (batch B3) observe. SHADOWS records each twin's
# engine-visible target; the fast-tier registry gate asserts key==__name__
# for every non-shadow entry and __name__==target for every shadow.
SHADOWS = {
    "clause_lower_mean_shadow": "clause_lower_mean",
    "first_clause_first_grounding_shadow": "first_clause_first_grounding",
}
REGISTRY["clause_lower_mean_shadow"] = clause_lower_mean_shadow
REGISTRY["first_clause_first_grounding_shadow"] = first_clause_first_grounding_shadow


def resolve(name: str):
    """Resolve a registry name to the callable the case registers, in the
    form THIS engine environment consumes — the conditional-njit
    accommodation (slice-2 review L1). Where numba imports (the pinned
    engine's environment — its kernels require njit-dispatcher registrands),
    the function is njit-wrapped exactly as the pin's own callers wrap
    theirs; where numba is ABSENT, the committed function is returned plain
    and the module-global `numba` is bound to the builtin-list stand-in, so
    a numba-less engine consumes the same committed source as a plain
    callable. Only ModuleNotFoundError selects the plain arm: a numba that
    is present but broken is an engine-environment fault and must fail the
    capture loudly, never silently downgrade the oracle side to plain
    registrands. Validation vouched for the name, so a KeyError here is a
    harness fault, never engine data."""
    global numba
    try:
        import numba as _numba
    except ModuleNotFoundError:
        numba = _PLAIN_NUMBA
        return REGISTRY[name]
    numba = _numba
    return _numba.njit(REGISTRY[name])
