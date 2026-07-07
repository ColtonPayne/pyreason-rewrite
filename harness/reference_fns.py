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
environment rather than at import. The `numba` module global below exists for
the same reason: a head function must *return* `numba.typed.List` (the pinned
`_call_head_function` unboxes its objmode result to
`types.ListType(types.unicode_type)`, interpretation.py:2316-2338), and njit
compilation resolves that name as a module global at first call — after
resolve() has bound it.

Registered names are matched by the engine against the callable's `__name__`
(annotate/interpretation.py:1920, _call_head_function/interpretation.py:2334),
so REGISTRY keys are exactly the functions' `__name__`s — a fast-tier test
holds that pairing.

Reference-function contract: deterministic, closed-form arithmetic only —
their outputs land in banked reasoning observations and must compare exactly
across fresh processes.
"""

numba = None  # bound by resolve() inside the engine environment


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


REGISTRY = {fn.__name__: fn for fn in (
    clause_lower_mean, clause_zero_grounding_eighths,
    first_clause_first_grounding, three_positional_stub, star_args_stub)}


def resolve(name: str):
    """Resolve a registry name to the njit-wrapped callable the case
    registers. Engine-environment only (imports numba); validation vouched
    for the name, so a KeyError here is a harness fault, never engine data."""
    global numba
    import numba as _numba
    numba = _numba
    return _numba.njit(REGISTRY[name])
