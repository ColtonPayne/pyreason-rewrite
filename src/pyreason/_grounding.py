"""Rule grounding — clause evaluation, threshold gating, head resolution.

Behavior target: the pinned `_ground_rule` family (oracle
scripts/interpretation/interpretation.py:809-1503 at e1a94af3). Pure
functions over the interpretation's explicit containers; every list is
order-preserving because grounding order is trace-row order downstream.

The load-bearing pinned semantics, kept deliberately:

- Threshold gating is CLAUSE-LEVEL: a threshold compares the clause's
  whole-graph qualifying count against the clause's full candidate grounding
  (interpretation.py:1364-1392), before head candidates are enumerated — so
  a satisfied clause can license every head grounding at once
  (threshold-number-gate-clause-level is the discriminating case).
- 'total' counts the candidate grounding; 'available' re-qualifies it under
  the vacuous [0,1] bound (label presence, interpretation.py:1371-1372).
- The percent branch scales thresh by 0.01 and is False on an empty
  candidate set (interpretation.py:1489-1501).
- An absent label never satisfies any clause bound: `World.is_satisfied`
  raises on a missing key and the guards here catch to False
  (interpretation.py:1756-1778) — the open-world reading of absence, unless
  the predicate is registered closed-world, where an absent-or-vacuous bound
  is read as [0,0] (interpretation.py:1763-1772).
- Variable refinement propagates along the clause dependency graph both ways
  until a fixed point (refine_groundings, interpretation.py:1306-1361).
- A head function named by a rule resolves against the registered functions'
  __name__s; a no-match SILENTLY grounds the head to the pre-seeded empty
  list (interpretation.py:2330-2338) — the rule fires for no one. (The
  annotation side of that asymmetry raises; see _interpretation.annotate.)
"""

from . import interval


# --- satisfaction of one atom -------------------------------------------------

def is_satisfied_node(interpretations_node, comp, na, closed_world_predicates):
    l, bnd = na
    if l is None or bnd is None:
        return True
    try:
        world = interpretations_node[comp]
        if l in closed_world_predicates:
            if l not in world.world:
                # Absent = unknown [0,1] = closed-world [0,0]
                return interval.closed(0, 0) in bnd
            world_bnd = world.world[l]
            if world_bnd.lower == 0.0 and world_bnd.upper == 1.0:
                return interval.closed(0, 0) in bnd
        return world.is_satisfied(l, bnd)
    except (KeyError, AttributeError):
        return False


def is_satisfied_edge(interpretations_edge, comp, na, closed_world_predicates):
    l, bnd = na
    if l is None or bnd is None:
        return True
    try:
        world = interpretations_edge[comp]
        if l in closed_world_predicates:
            if l not in world.world:
                return interval.closed(0, 0) in bnd
            world_bnd = world.world[l]
            if world_bnd.lower == 0.0 and world_bnd.upper == 1.0:
                return interval.closed(0, 0) in bnd
        return world.is_satisfied(l, bnd)
    except (KeyError, AttributeError):
        return False


def get_qualified_node_groundings(interpretations_node, grounding, clause_l,
                                  clause_bnd, closed_world_predicates):
    return [n for n in grounding
            if is_satisfied_node(interpretations_node, n, (clause_l, clause_bnd),
                                 closed_world_predicates)]


def get_qualified_edge_groundings(interpretations_edge, grounding, clause_l,
                                  clause_bnd, closed_world_predicates):
    return [e for e in grounding
            if is_satisfied_edge(interpretations_edge, e, (clause_l, clause_bnd),
                                 closed_world_predicates)]


# --- threshold gating ---------------------------------------------------------

def _satisfies_threshold(num_neigh, num_qualified_component, threshold):
    """One clause's gate: (comparison, (number|percent, total|available), thresh)."""
    if threshold[1][0] == 'number':
        if threshold[0] == 'greater_equal':
            return num_qualified_component >= threshold[2]
        if threshold[0] == 'greater':
            return num_qualified_component > threshold[2]
        if threshold[0] == 'less_equal':
            return num_qualified_component <= threshold[2]
        if threshold[0] == 'less':
            return num_qualified_component < threshold[2]
        if threshold[0] == 'equal':
            return num_qualified_component == threshold[2]

    elif threshold[1][0] == 'percent':
        if num_neigh == 0:
            return False
        if threshold[0] == 'greater_equal':
            return num_qualified_component / num_neigh >= threshold[2] * 0.01
        if threshold[0] == 'greater':
            return num_qualified_component / num_neigh > threshold[2] * 0.01
        if threshold[0] == 'less_equal':
            return num_qualified_component / num_neigh <= threshold[2] * 0.01
        if threshold[0] == 'less':
            return num_qualified_component / num_neigh < threshold[2] * 0.01
        if threshold[0] == 'equal':
            return num_qualified_component / num_neigh == threshold[2] * 0.01


def check_node_grounding_threshold_satisfaction(interpretations_node, grounding,
                                                qualified_grounding, clause_label,
                                                threshold, closed_world_predicates):
    quantifier_type = threshold[1][1]
    if quantifier_type == 'total':
        neigh_len = len(grounding)
    else:  # 'available': candidates that carry the label at all
        neigh_len = len(get_qualified_node_groundings(
            interpretations_node, grounding, clause_label,
            interval.closed(0, 1), closed_world_predicates))
    return _satisfies_threshold(neigh_len, len(qualified_grounding), threshold)


def check_edge_grounding_threshold_satisfaction(interpretations_edge, grounding,
                                                qualified_grounding, clause_label,
                                                threshold, closed_world_predicates):
    quantifier_type = threshold[1][1]
    if quantifier_type == 'total':
        neigh_len = len(grounding)
    else:
        neigh_len = len(get_qualified_edge_groundings(
            interpretations_edge, grounding, clause_label,
            interval.closed(0, 1), closed_world_predicates))
    return _satisfies_threshold(neigh_len, len(qualified_grounding), threshold)


def check_all_clause_satisfaction(interpretations_node, interpretations_edge,
                                  clauses, thresholds, groundings, groundings_edges,
                                  closed_world_predicates):
    """Re-check every clause's threshold over the (possibly refined)
    groundings — the per-head-grounding safety net (interpretation.py:1284-1303)."""
    satisfaction = True
    for i, clause in enumerate(clauses):
        clause_type, clause_label, clause_variables, clause_bnd = \
            clause[0], clause[1], clause[2], clause[3]
        if clause_type == 'node':
            grounding = groundings[clause_variables[0]]
            qualified = get_qualified_node_groundings(
                interpretations_node, grounding, clause_label, clause_bnd,
                closed_world_predicates)
            satisfaction = check_node_grounding_threshold_satisfaction(
                interpretations_node, grounding, qualified, clause_label,
                thresholds[i], closed_world_predicates) and satisfaction
        elif clause_type == 'edge':
            grounding = groundings_edges[(clause_variables[0], clause_variables[1])]
            qualified = get_qualified_edge_groundings(
                interpretations_edge, grounding, clause_label, clause_bnd,
                closed_world_predicates)
            satisfaction = check_edge_grounding_threshold_satisfaction(
                interpretations_edge, grounding, qualified, clause_label,
                thresholds[i], closed_world_predicates) and satisfaction
    return satisfaction


# --- candidate grounding of one clause ----------------------------------------

def get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes):
    """Candidates for a node clause: a previous grounding wins; otherwise the
    predicate's known carriers, otherwise all nodes."""
    if l in predicate_map:
        return predicate_map[l] if clause_var_1 not in groundings else groundings[clause_var_1]
    return nodes if clause_var_1 not in groundings else groundings[clause_var_1]


def get_rule_edge_clause_grounding(clause_var_1, clause_var_2, groundings,
                                   groundings_edges, neighbors, reverse_neighbors,
                                   predicate_map, l, edges):
    """Candidates for an edge clause — four cases by which variables were
    already grounded (interpretation.py:1405-1449)."""
    # Case 1: neither variable seen — the predicate's carriers, or all edges
    if clause_var_1 not in groundings and clause_var_2 not in groundings:
        return predicate_map[l] if l in predicate_map else edges

    edge_groundings = []
    # Case 2: only the target seen — sources of each target grounding
    if clause_var_1 not in groundings and clause_var_2 in groundings:
        for n in groundings[clause_var_2]:
            edge_groundings.extend((nn, n) for nn in reverse_neighbors[n])
    # Case 3: only the source seen — neighbors of each source grounding
    elif clause_var_1 in groundings and clause_var_2 not in groundings:
        for n in groundings[clause_var_1]:
            edge_groundings.extend((n, nn) for nn in neighbors[n])
    # Case 4: both seen
    else:
        if (clause_var_1, clause_var_2) in groundings_edges:
            return groundings_edges[(clause_var_1, clause_var_2)]
        groundings_clause_var_2_set = set(groundings[clause_var_2])
        for n in groundings[clause_var_1]:
            edge_groundings.extend(
                (n, nn) for nn in neighbors[n] if nn in groundings_clause_var_2_set)
    return edge_groundings


# --- refinement along the clause dependency graph ------------------------------

def refine_groundings(clause_variables, groundings, groundings_edges,
                      dependency_graph_neighbors, dependency_graph_reverse_neighbors):
    """Propagate a variable's narrowed grounding to every variable connected
    to it through an edge clause, transitively, until a fixed point."""
    all_variables_refined = list(clause_variables)
    variables_just_refined = list(clause_variables)
    new_variables_refined = []
    while len(variables_just_refined) > 0:
        for refined_variable in variables_just_refined:
            if refined_variable in dependency_graph_neighbors:
                for neighbor in dependency_graph_neighbors[refined_variable]:
                    old_edge_groundings = groundings_edges[(refined_variable, neighbor)]
                    new_node_groundings = groundings[refined_variable]

                    groundings[neighbor] = []
                    qualified_groundings = [e for e in old_edge_groundings
                                            if e[0] in new_node_groundings]
                    seen = set()
                    for e in qualified_groundings:
                        if e[1] not in seen:
                            groundings[neighbor].append(e[1])
                            seen.add(e[1])
                    groundings_edges[(refined_variable, neighbor)] = qualified_groundings

                    if neighbor not in all_variables_refined:
                        new_variables_refined.append(neighbor)

            if refined_variable in dependency_graph_reverse_neighbors:
                for reverse_neighbor in dependency_graph_reverse_neighbors[refined_variable]:
                    old_edge_groundings = groundings_edges[(reverse_neighbor, refined_variable)]
                    new_node_groundings = groundings[refined_variable]

                    groundings[reverse_neighbor] = []
                    qualified_groundings = [e for e in old_edge_groundings
                                            if e[1] in new_node_groundings]
                    seen = set()
                    for e in qualified_groundings:
                        if e[0] not in seen:
                            groundings[reverse_neighbor].append(e[0])
                            seen.add(e[0])
                    groundings_edges[(reverse_neighbor, refined_variable)] = qualified_groundings

                    if reverse_neighbor not in all_variables_refined:
                        new_variables_refined.append(reverse_neighbor)

        variables_just_refined = list(new_variables_refined)
        all_variables_refined.extend(new_variables_refined)
        new_variables_refined = []


# --- head functions -------------------------------------------------------------

def call_head_function(fn_name, fn_arg_values, head_functions):
    """Resolve a head function by __name__ and call it; a no-match returns
    the pre-seeded EMPTY grounding list — the pinned silent arm
    (interpretation.py:2330-2338)."""
    func_result = []
    for func in head_functions:
        if hasattr(func, '__name__') and func.__name__ == fn_name:
            func_result = func(fn_arg_values)
            break
    return func_result


def determine_node_head_vars(head_fns, head_fns_vars, groundings, head_functions):
    """Apply the (single) head function of a node rule, if any. An argument
    variable without a grounding rides as itself."""
    head_groundings = []
    is_func = False
    fn_name = head_fns[0]
    fn_vars = head_fns_vars[0]
    if fn_name != '' and len(fn_vars) > 0:
        fn_arg_values = [groundings[fn_var] if fn_var in groundings else [fn_var]
                         for fn_var in fn_vars]
        head_groundings = call_head_function(fn_name, fn_arg_values, head_functions)
        is_func = True
    return head_groundings, is_func


def determine_edge_head_vars(head_fns, head_fns_vars, groundings, head_functions):
    """Apply the head functions of an edge rule's two head variables, if any."""
    head_groundings = [[], []]
    is_func = [False, False]
    for i in range(2):
        fn_name = head_fns[i]
        fn_vars = head_fns_vars[i]
        if fn_name != '' and len(fn_vars) > 0:
            fn_arg_values = [groundings[fn_var] if fn_var in groundings else [fn_var]
                             for fn_var in fn_vars]
            head_groundings[i] = call_head_function(fn_name, fn_arg_values, head_functions)
            is_func[i] = True
    return head_groundings, is_func
