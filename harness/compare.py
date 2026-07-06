"""The stdlib compare layer: canonicalize, digest, and compare probe outputs.

Imports nothing from either engine — engine objects are reduced by duck-typing
(interval-likes to `[lower, upper]`, non-float numpy scalars via `.item()`;
`numpy.float64` is already a `float` subclass and takes the float branch), so
the same canonical form is computable inside an engine env (capture time) and
outside (compare time). Ordering within lists is part of the compared value;
dict key order is not (canonical JSON sorts keys).

Canonical-form decisions (each keeps a wrong verdict impossible rather than
convenient): numeric *type* is not part of the compared contract — integral
floats reduce to ints so `[0, 1]` and `[0.0, 1.0]` share one digest; non-finite
floats reduce to the sentinel strings "NaN"/"Infinity"/"-Infinity" so the exact
and tolerance paths agree on them and artifacts stay strict JSON; a dict whose
keys collide after `str()` raises rather than silently dropping an entry; any
type this layer cannot reduce deterministically (sets included) raises at
capture time — an unreducible probe output is a schema gap, never a digest.
"""

import hashlib
import json
import math


def canonical(value):
    """Reduce a probe output to plain JSON-serializable data, recursively."""
    if isinstance(value, bool) or isinstance(value, (str, int)) or value is None:
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return int(value) if value.is_integer() else value
    if isinstance(value, dict):
        reduced = {str(k): canonical(v) for k, v in value.items()}
        if len(reduced) != len(value):
            raise ValueError(f"dict keys collide after str(): {sorted(map(str, value))}")
        return reduced
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    lower, upper = getattr(value, "lower", None), getattr(value, "upper", None)
    if isinstance(lower, (int, float)) and isinstance(upper, (int, float)):
        return [canonical(float(lower)), canonical(float(upper))]
    item = getattr(value, "item", None)
    if callable(item) and not isinstance(value, (set, frozenset)):
        return canonical(item())
    raise TypeError(f"cannot canonicalize {type(value).__name__!r} deterministically")


def canonical_json(value) -> str:
    return json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def approx_equal(a, b, tolerance: float) -> bool:
    """Recursive comparison of two canonical values with a numeric tolerance.

    Structure (types, lengths, keys) must match exactly; only numeric leaves may
    differ, by at most `tolerance`. Bools are not numbers here.
    """
    num_a = isinstance(a, (int, float)) and not isinstance(a, bool)
    num_b = isinstance(b, (int, float)) and not isinstance(b, bool)
    if num_a and num_b:
        return abs(a - b) <= tolerance
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(
            approx_equal(a[k], b[k], tolerance) for k in a
        )
    if isinstance(a, list):
        return len(a) == len(b) and all(
            approx_equal(x, y, tolerance) for x, y in zip(a, b)
        )
    return a == b


def compare_probes(probes_a: dict, probes_b: dict, policy: dict | None = None):
    """Compare two artifacts' canonical probe maps under a case's comparison policy.

    `policy` maps probe id -> {"tolerance": float, "rationale": str}; probes not
    named there compare exactly. Returns the list of mismatching probe ids.
    """
    policy = policy or {}
    mismatches = []
    for probe_id in sorted(set(probes_a) | set(probes_b)):
        if probe_id not in probes_a or probe_id not in probes_b:
            mismatches.append(probe_id)
            continue
        tol = policy.get(probe_id, {}).get("tolerance")
        if tol is not None:
            same = approx_equal(canonical(probes_a[probe_id]),
                                canonical(probes_b[probe_id]), tol)
        else:
            same = canonical_json(probes_a[probe_id]) == canonical_json(probes_b[probe_id])
        if not same:
            mismatches.append(probe_id)
    return mismatches
