"""The Label value type — the string-valued name object predicates wear.

Behavior target: the pinned oracle's plain label class (oracle
scripts/components/label.py, reached through the aliased `pyreason.label`).
Equality and hash go by string value alone — same-text distinct objects
compare and hash equal, the mechanism behind predicate-map and world lookups.
`__eq__` calls `get_value()` on its argument BEFORE the isinstance guard, so
comparing against a plain string raises AttributeError — a pinned observable
(label-ops), kept rather than "fixed".
"""


class Label:

    def __init__(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def __eq__(self, label):
        result = (self._value == label.get_value()) and isinstance(label, type(self))
        return result

    def __str__(self):
        return self._value

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return self.get_value()
