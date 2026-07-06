"""The stdlib compare layer: canonicalize, digest, and compare probe outputs.

Imports nothing from either engine — engine objects are reduced by duck-typing
(interval-likes to `[lower, upper]`, numpy scalars via `.item()`), so the same
canonical form is computable inside an engine env (capture time) and outside
(compare time). Ordering within lists is part of the compared value; dict key
order is not (canonical JSON sorts keys).
"""

import hashlib
import json


def canonical(value):
    """Reduce a probe output to plain JSON-serializable data, recursively."""
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    lower, upper = getattr(value, "lower", None), getattr(value, "upper", None)
    if isinstance(lower, (int, float)) and isinstance(upper, (int, float)):
        return [float(lower), float(upper)]
    item = getattr(value, "item", None)
    if callable(item):
        return canonical(item())
    return str(value)


def canonical_json(value) -> str:
    return json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


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
            same = approx_equal(probes_a[probe_id], probes_b[probe_id], tol)
        else:
            same = canonical_json(probes_a[probe_id]) == canonical_json(probes_b[probe_id])
        if not same:
            mismatches.append(probe_id)
    return mismatches
