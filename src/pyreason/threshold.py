"""The Threshold value type — one clause's satisfaction gate.

Behavior target: the pinned oracle's threshold class (oracle
scripts/threshold/threshold.py). The constructor validates quantifier and
quantifier_type membership; `thresh` is stored with NO validation (negative
and non-numeric values pass and `to_tuple()` returns them verbatim) — a
pinned observable (threshold-construct), kept rather than tightened. The
membership check indexes quantifier_type positionally, so a length-1 tuple
raises IndexError('tuple index out of range') and a bare string is checked
character-wise (its first character fails membership → 'Invalid quantifier
type') — both banked arms.
"""


class Threshold:
    """A threshold for a clause in a rule.

    Attributes:
        quantifier (str): the comparison operator, e.g. 'greater_equal'.
        quantifier_type (tuple): ('number' or 'percent', 'total' or 'available').
        thresh: the threshold value to compare against (stored verbatim).
    """

    def __init__(self, quantifier, quantifier_type, thresh):
        if quantifier not in ("greater_equal", "greater", "less_equal", "less", "equal"):
            raise ValueError("Invalid quantifier")

        if quantifier_type[0] not in ("number", "percent") or quantifier_type[1] not in ("total", "available"):
            raise ValueError("Invalid quantifier type")

        self.quantifier = quantifier
        self.quantifier_type = quantifier_type
        self.thresh = thresh

    def to_tuple(self):
        """The threshold as the (quantifier, quantifier_type, thresh) tuple
        the rule representation stores."""
        return self.quantifier, self.quantifier_type, self.thresh
