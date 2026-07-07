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
                 allow_ground_rules):
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
        self.specific_node_labels = {}
        self.specific_edge_labels = {}
        self.closed_world_predicates = []
        self.interp = None

    def reason(self, tmax, convergence_threshold, convergence_bound_threshold,
               verbose=True):
        self._tmax = tmax
        self.interp = Interpretation(
            self._graph, self._ipl, self._annotation_functions,
            self._head_functions, self._reverse_graph, self._atom_trace,
            self._save_graph_attributes_to_rule_trace, self._persistent,
            self._inconsistency_check, self._store_interpretation_changes,
            self._update_mode, self._allow_ground_rules,
            self.specific_node_labels, self.specific_edge_labels,
            self.closed_world_predicates)
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
    through rule bodies (oracle scripts/utils/filter_ruleset.py) — including
    the pinned de-duplication through an unordered set, which makes the
    surviving rules' ORDER an unpinned behavior; the query-consuming cases
    adjudicate it when they land."""

    def applicable_rules_from_query(query):
        applicable = []
        for rule in rules:
            if query == rule.get_target():
                applicable.append(rule)
                for clause in rule.get_clauses():
                    applicable.extend(applicable_rules_from_query(clause[1]))
        return applicable

    filtered_rules = []
    for q in queries:
        filtered_rules.extend(applicable_rules_from_query(q.get_predicate()))
    return list(set(filtered_rules))
