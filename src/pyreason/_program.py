"""The logic program — the object `get_logic_program()` hands out.

Behavior target: the pinned Program (oracle scripts/program/program.py) minus
its numba plumbing: it binds the loaded graph + fact/rule/IPL inputs to a
fresh Interpretation per reason() call and re-drives the SAME interpretation
on reason_again(). `interp` is the exact attribute the pinned accessors read
(pyreason.py:546), so it is contract here, not convenience. Clause
reordering and query-driven ruleset filtering live here too — both rewrite
the rule list before the program is built, exactly where the pinned _reason
applies them (pyreason.py:1594-1606).
"""

from ._interpretation import Interpretation


class Program:

    def __init__(self, graph, facts_node, facts_edge, rules, ipl,
                 annotation_functions, head_functions, reverse_graph, atom_trace,
                 save_graph_attributes_to_rule_trace, persistent,
                 inconsistency_check, store_interpretation_changes, update_mode,
                 allow_ground_rules, parallel_computing=False, fp_version=False):
        self._graph = graph
        self._facts_node = facts_node
        self._facts_edge = facts_edge
        self._rules = rules
        self._ipl = ipl
        self._annotation_functions = annotation_functions
        self._head_functions = head_functions
        self._reverse_graph = reverse_graph
        self._atom_trace = atom_trace
        self._save_graph_attributes_to_rule_trace = save_graph_attributes_to_rule_trace
        self._persistent = persistent
        self._inconsistency_check = inconsistency_check
        self._store_interpretation_changes = store_interpretation_changes
        self._update_mode = update_mode
        self._allow_ground_rules = allow_ground_rules
        self._parallel_computing = parallel_computing
        self._fp_version = fp_version
        self.specific_node_labels = {}
        self.specific_edge_labels = {}
        self.closed_world_predicates = []
        self.interp = None

    def reason(self, tmax, convergence_threshold, convergence_bound_threshold,
               verbose=True):
        self._tmax = tmax
        # The pinned dispatch (program.py:42-47) selects among three engine
        # variants: parallel first, then fp, then the default. The parallel
        # variant's whole source diff is a prange decorator flip and its
        # output digest-equals the default kernel's on the pinned surface
        # (banked parallel-computing-on / parallel-fp-precedence artifacts),
        # so only the fp variant is output-distinct: the one reference core
        # runs the fp SCHEDULE exactly when the pin would construct
        # InterpretationFP — fp_version set and parallel_computing off.
        fp_mode = self._fp_version and not self._parallel_computing
        # The pinned Program stamps the specific-label maps onto ONLY the
        # default Interpretation class (program.py:34-38 — upstream's own
        # TODO marks it), so the fp variant always reasons with EMPTY
        # specific labels; reproduced at the same seam. The closed-world
        # list IS stamped onto all variants (program.py:37-39).
        specific_node_labels = {} if fp_mode else self.specific_node_labels
        specific_edge_labels = {} if fp_mode else self.specific_edge_labels
        rules_empty = self._rules is not None and len(self._rules) == 0
        self.interp = Interpretation(
            self._graph, self._ipl, self._annotation_functions,
            self._head_functions, self._reverse_graph, self._atom_trace,
            self._save_graph_attributes_to_rule_trace, self._persistent,
            self._inconsistency_check, self._store_interpretation_changes,
            self._update_mode, self._allow_ground_rules,
            specific_node_labels, specific_edge_labels,
            self.closed_world_predicates, fp_mode=fp_mode)
        # The pinned engine cannot reason over an EMPTY ruleset: the plain
        # empty list only filter_ruleset produces (loaded rulesets ride numba
        # typed lists at the pin, and both engines' loaders leave a zero-rule
        # load as None → the no-rules Exception upstream) fails numba's
        # kernel-argument fingerprinting at dispatch. Reproduced verbatim at
        # the same seam — after the Interpretation is constructed and
        # assigned, so the post-raise program holds a live interp exactly as
        # the pin's does (reason-queries-no-match banks the raise record).
        if rules_empty:
            raise ValueError('cannot compute fingerprint of empty list')
        self.interp.start_fp(self._tmax, self._facts_node, self._facts_edge,
                             self._rules, verbose, convergence_threshold,
                             convergence_bound_threshold)
        return self.interp

    def reason_again(self, tmax, restart, convergence_threshold,
                     convergence_bound_threshold, facts_node, facts_edge,
                     verbose=True):
        assert self.interp is not None, 'Call reason before calling reason again'
        if restart:
            self._tmax = tmax
        else:
            self._tmax = self.interp.time + tmax
        self.interp.start_fp(self._tmax, facts_node, facts_edge, self._rules,
                             verbose, convergence_threshold,
                             convergence_bound_threshold, again=True,
                             restart=restart)
        return self.interp

    def reset_graph(self):
        self._graph = None
        self.interp = None

    def reset_rules(self):
        self._rules = None

    def reset_facts(self):
        self._facts_node = None
        self._facts_edge = None


def reorder_clauses(rule):
    """Move node clauses ahead of edge clauses, stably, thresholds riding
    along (oracle scripts/utils/reorder_clauses.py). Returns the mutated rule
    and the {new index: original index} map the trace output uses to render
    clause columns back in the author's order."""
    node_clauses = []
    edge_clauses = []
    reordered_clauses_map = {}

    for index, clause in enumerate(rule.get_clauses()):
        if clause[0] == 'node':
            node_clauses.append((index, clause))
        else:
            edge_clauses.append((index, clause))

    thresholds = rule.get_thresholds()
    reordered_clauses = []
    reordered_thresholds = []
    for new_index, (original_index, clause) in enumerate(node_clauses + edge_clauses):
        reordered_clauses.append(clause)
        reordered_thresholds.append(thresholds[original_index])
        reordered_clauses_map[new_index] = original_index

    rule.set_clauses(reordered_clauses)
    rule.set_thresholds(reordered_thresholds)
    return rule, reordered_clauses_map


def filter_ruleset(queries, rules):
    """Keep the rules that can support some query's predicate, transitively
    through rule bodies (oracle scripts/utils/filter_ruleset.py) — matching
    by predicate ONLY (bounds and component play no part, the pin's :17),
    including the pinned de-duplication through an unordered set, which
    makes multi-survivor ORDER an unpinned behavior (committed cases keep
    survivor sets <= 1).

    Deliberate divergence from the pin, on an un-caseable input: the pinned
    recursion is unguarded, so a query matching a self-recursive rule's head
    crashes the pinned process outright (unbounded recursion through the
    clause targets, SIGSEGV before Python's RecursionError — screened
    2026-07-07, banked on type:Query's board row as un-caseable: no artifact
    exists to compare). Here each predicate expands at most once (`seen`),
    which terminates on every cyclic ruleset and returns the identical
    reachable-rule SET on every acyclic one — the recorded
    guard-the-recursion contract (ledger session 14, idea seeds).
    """

    def applicable_rules_from_query(query, seen):
        applicable = []
        for rule in rules:
            if query == rule.get_target():
                applicable.append(rule)
                for clause in rule.get_clauses():
                    target = clause[1]
                    if target not in seen:
                        seen.add(target)
                        applicable.extend(
                            applicable_rules_from_query(target, seen))
        return applicable

    filtered_rules = []
    for q in queries:
        filtered_rules.extend(
            applicable_rules_from_query(q.get_predicate(), set()))
    return list(set(filtered_rules))
