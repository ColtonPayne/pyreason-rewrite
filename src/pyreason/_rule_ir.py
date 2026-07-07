"""The internal rule record — what `get_rules()` returns elements of.

Mirrors the pinned oracle's internal rule (oracle scripts/rules/rule_internal.py)
as a plain record: the parser's full output is stored (it IS the parse's
meaning — clauses, thresholds, annotation function, weights, head functions,
edges, flags), and the exposed methods are exactly the ones the current
equivalence surface consumes: the fingerprint getters (name/type/target/
head_variables/delta/bnd/clauses), `set_rule_name` (the add-rule seam assigns
generated names through it), and the reasoning-core getters the engine reads
per grounding pass (thresholds, annotation function, weights, head functions,
edges, static flag, head negation) plus the clause/threshold setters the
clause-reordering optimization rewrites through. Pinned methods still without
a consumer (equality/hash) land with the packets whose cases consume them.
"""


class RuleIR:

    def __init__(self, rule_name, rule_type, target, head_variables, delta,
                 clauses, bnd, thresholds, ann_fn, weights, head_fns,
                 head_fns_vars, edges, static, head_negated=False):
        self._rule_name = rule_name
        self._type = rule_type
        self._target = target
        self._head_variables = head_variables
        self._delta = delta
        self._clauses = clauses
        self._bnd = bnd
        self._thresholds = thresholds
        self._ann_fn = ann_fn
        self._weights = weights
        self._head_fns = head_fns
        self._head_fns_vars = head_fns_vars
        self._edges = edges
        self._static = static
        self._head_negated = head_negated

    def get_rule_name(self):
        return self._rule_name

    def set_rule_name(self, rule_name):
        self._rule_name = rule_name

    def get_rule_type(self):
        return self._type

    def get_target(self):
        return self._target

    def get_head_variables(self):
        return self._head_variables

    def get_delta(self):
        return self._delta

    def get_clauses(self):
        return self._clauses

    def set_clauses(self, clauses):
        self._clauses = clauses

    def get_bnd(self):
        return self._bnd

    def get_thresholds(self):
        return self._thresholds

    def set_thresholds(self, thresholds):
        self._thresholds = thresholds

    def get_annotation_function(self):
        return self._ann_fn

    def get_weights(self):
        return self._weights

    def get_head_function(self):
        return self._head_fns

    def get_head_function_vars(self):
        return self._head_fns_vars

    def get_edges(self):
        return self._edges

    def is_static_rule(self):
        return self._static

    def is_head_negated(self):
        return self._head_negated
