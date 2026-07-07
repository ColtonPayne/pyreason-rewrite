"""The Interval value type — the bounds object the whole engine computes over.

Behavior target: the pinned oracle's Python-proxy interval, reached through the
aliased public constructor `pyreason.interval.closed` (oracle
scripts/interval/interval.py + the `closed` wrapper in interval_type.py:143-145).
The banked interval-ops artifacts pin the contract this class carries:

- Construction seeds the previous bounds from the current ones; bounds are
  stored as floats so the repr text renders like the oracle's numpy floats
  ('[0.0,1.0]', never '[0,1]').
- Bounds are accepted unvalidated — an inverted pair (lower > upper)
  constructs; the clamp lives in `intersection`, which returns [0.0, 1.0]
  when the raw intersection is empty.
- Equality, hash, and containment consult only the current bounds — the
  static flag and the previous bounds are invisible to them.
- `reset()` banks the current bounds into the previous ones and widens to
  [0.0, 1.0]; it ignores the static flag (the static guard lives at engine
  call sites, not here).
- `intersection()` seeds the result's previous bounds from self's CURRENT
  bounds — the proxy-arm behavior (interval.py:69 at the pin). The pinned
  jitted overload seeds from self's previous bounds instead; only the proxy
  arm is reachable without compiling jitted code, so the proxy arm is the
  equivalence target (the two-implementation divergence is on the campaign
  board, not silently absorbed here).
"""


class Interval:
    """One [lower, upper] bound pair with a static flag and previous bounds."""

    __slots__ = ("_lower", "_upper", "_static", "_prev_lower", "_prev_upper")

    def __init__(self, lower, upper, static=False, prev_lower=None, prev_upper=None):
        self._lower = float(lower)
        self._upper = float(upper)
        self._static = static
        # Construction seeds prev from current (the pinned proxy __new__
        # passes lower/upper twice); intersection() overrides explicitly.
        self._prev_lower = float(lower if prev_lower is None else prev_lower)
        self._prev_upper = float(upper if prev_upper is None else prev_upper)

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    @property
    def prev_lower(self):
        return self._prev_lower

    @property
    def prev_upper(self):
        return self._prev_upper

    def is_static(self):
        return self._static

    def set_lower_upper(self, lower, upper):
        self._lower = float(lower)
        self._upper = float(upper)

    def reset(self):
        self._prev_lower = self._lower
        self._prev_upper = self._upper
        self._lower = 0.0
        self._upper = 1.0

    def has_changed(self):
        return not (self._lower == self._prev_lower
                    and self._upper == self._prev_upper)

    def intersection(self, interval):
        lower = max(self._lower, interval.lower)
        upper = min(self._upper, interval.upper)
        if lower > upper:
            lower, upper = 0.0, 1.0
        # prev seeded from self's CURRENT bounds — the pinned proxy arm.
        return Interval(lower, upper, False, self._lower, self._upper)

    def to_str(self):
        return self.__repr__()

    def __eq__(self, interval):
        # Duck-typed like the pin: a non-interval argument raises
        # AttributeError rather than returning NotImplemented.
        return interval.lower == self._lower and interval.upper == self._upper

    def __hash__(self):
        return hash((self._lower, self._upper))

    def __contains__(self, item):
        return self._lower <= item.lower and self._upper >= item.upper

    def __repr__(self):
        return f"[{self._lower},{self._upper}]"


def closed(lower, upper, static=False):
    """The public interval constructor: bounds coerced to float, previous
    bounds seeded from the current ones."""
    return Interval(lower, upper, static)
