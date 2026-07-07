"""One component's world — its Label -> Interval bound map.

Behavior target: the pinned jitted world (oracle scripts/components/world.py
+ the overloads in numba_wrapper/numba_types/world_type.py). `update` runs
the JITTED intersection arm (`interval.intersect_jitted`): the updated bound
is a NEW interval object whose previous bounds ride through from the bound
being replaced — replacing (not mutating) is what keeps banked trace copies
and rule-collection references pointing at the pre-update values, and the
preserved previous bounds are what convergence deltas are measured against.
"""

from . import interval


class World:

    __slots__ = ("_world",)

    def __init__(self, labels):
        self._world = {lbl: interval.closed(0.0, 1.0) for lbl in labels}

    @property
    def world(self):
        return self._world

    def is_satisfied(self, label, bnd):
        """Whether this world's bound for `label` sits inside `bnd`.

        Raises KeyError when the label is absent — the pinned engine reaches
        this only through guards (`is_satisfied_node/edge`) that catch and
        return False, making absent-label the never-satisfied arm.
        """
        return self._world[label] in bnd

    def update(self, label, bnd):
        current = self._world[label]
        self._world[label] = interval.intersect_jitted(current, bnd)

    def get_bound(self, label):
        return self._world[label]
