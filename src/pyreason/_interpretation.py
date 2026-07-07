"""The reference reasoning core — one set of semantic operations (grounding,
interval update, inconsistency resolution, annotation) over one explicit
Interpretation state, driven by one of two pinned schedules.

Behavior target: the pinned engine at e1a94af3. The oracle ships three
near-copy ~2400-line engine variants; their grounding/update/resolve/annotate
bodies are line-identical (verified by normalized body diff, session 19) and
only the loop orchestration differs. This module therefore carries the shared
semantics ONCE, plus two schedule functions over them:

- `reason` — the default schedule (oracle interpretation.py:242-686), also
  the observable behavior of the pinned parallel variant: its entire source
  diff is the prange decorator flip (interpretation_parallel.py:241), and the
  banked parallel-computing-on / parallel-fp-precedence artifacts digest-equal
  the default twin on every reasoning probe.
- `reason_fp` — the fp schedule (oracle interpretation_fp.py:251-807),
  selected by settings.fp_version when parallel_computing is off. Its
  observable output genuinely differs (fp-counter values, trace event order,
  duplicated atom-trace groundings, last-step frame row order — the banked
  fp-version-on artifact), so output equivalence forces this second schedule;
  see ADR 0003.

The Interpretation object IS the state: worlds, predicate maps, pending
fact/rule queues, and the trace live on it, and the functions below read and
mutate nothing else. Every list is order-preserving because queue order is
trace-row order and trace-row order is frame-row order. On the default
schedule `interpretations_node/_edge` map component -> World; on the fp
schedule they map timestep -> {component -> World} (the pinned fp state
shape) — no public view consumes them directly (the trace views and get_dict
read the trace lists and `time`), so the shape is internal to the schedule.

The pinned default timestep shape (interpretation.py:242-686):

  per timestep t:
    non-persistent reset of every non-static bound (banking prev bounds)
    apply due node facts, then due edge facts (queue order)
    inner fixed-point loop:
      apply due node-rule conclusions, then due edge-rule conclusions
      if anything updated: fp_cnt += 1, ground every rule and enqueue its
      conclusions at t + delta; delta-0 conclusions re-enter the inner loop
    convergence check (delta_interpretation | delta_bound | perfect)

The pinned fp shape (interpretation_fp.py:251-807, see reason_fp) instead
sweeps ALL timesteps applying facts and grounding rules, then applies every
queued conclusion, and repeats the whole sweep until a pass changes nothing —
with per-timestep world dicts and globally accumulating predicate maps
(the source of the duplicated atom-trace groundings).

Deliberately-reproduced pinned quirks (each named in the session report):
- A rule head naming an UNREGISTERED annotation function raises
  NameError("name 'annotation' is not defined") — the pinned objmode block
  only assigns its output variable inside the name-match loop
  (interpretation.py:1918-1931), so a no-match leaves it unbound. The
  matching loop has no break, so every same-named registrand is called and
  the last result wins.
- The unregistered HEAD-function arm is silent instead (empty head
  grounding, _grounding.call_head_function) — the pinned asymmetry.
- Static facts re-enqueue themselves at t+1 forever without extending
  max_facts_time (interpretation.py:340-343) — they ride, but never hold
  perfect convergence open.
- A re-derived unchanged bound counts zero toward either convergence delta,
  because updates preserve previous bounds (interval.intersect_jitted) and
  the change gate compares against them (interpretation.py:1601-1617).
"""

from . import interval
from ._grounding import (
    check_all_clause_satisfaction,
    check_edge_grounding_threshold_satisfaction,
    check_node_grounding_threshold_satisfaction,
    determine_edge_head_vars,
    determine_node_head_vars,
    get_qualified_edge_groundings,
    get_qualified_node_groundings,
    get_rule_edge_clause_grounding,
    get_rule_node_clause_grounding,
    refine_groundings,
)
from ._world import World
from .label import Label


class Interpretation:
    """One reasoning run's complete explicit state."""

    def __init__(self, graph, ipl, annotation_functions, head_functions,
                 reverse_graph, atom_trace, save_graph_attributes_to_rule_trace,
                 persistent, inconsistency_check, store_interpretation_changes,
                 update_mode, allow_ground_rules, specific_node_labels,
                 specific_edge_labels, closed_world_predicates, fp_mode=False):
        # fp_mode selects the fp schedule (reason_fp) and its pinned state
        # shape; the pinned fp variant also drops ground-atom counting
        # entirely (its reason() takes no num_ga), so the shared update/add
        # helpers gate their num_ga writes on this flag.
        self.fp_mode = fp_mode
        self.graph = graph
        self.ipl = ipl
        self.annotation_functions = annotation_functions
        self.head_functions = head_functions
        self.reverse_graph = reverse_graph
        self.atom_trace = atom_trace
        self.save_graph_attributes_to_rule_trace = save_graph_attributes_to_rule_trace
        self.persistent = persistent
        self.inconsistency_check = inconsistency_check
        self.store_interpretation_changes = store_interpretation_changes
        self.update_mode = update_mode
        self.allow_ground_rules = allow_ground_rules
        self.closed_world_predicates = closed_world_predicates

        # Ground-atom count per timestep (index = timestep)
        self.num_ga = [0]

        # Resume data: previous end time and fp-operation count
        self.time = 0
        self.prev_reasoning_data = [0, 0]

        # Pending queues. rules_to_be_applied_*_trace and
        # edges_to_be_added_edge_rule stay index-aligned with their queue.
        self.rules_to_be_applied_node_trace = []
        self.rules_to_be_applied_edge_trace = []
        self.facts_to_be_applied_node_trace = []
        self.facts_to_be_applied_edge_trace = []
        self.rules_to_be_applied_node = []
        self.rules_to_be_applied_edge = []
        self.facts_to_be_applied_node = []
        self.facts_to_be_applied_edge = []
        self.edges_to_be_added_edge_rule = []

        # The trace: one 9-tuple per stored change
        # (t, fp, comp, label, bound-copy, consistent, triggered_by, name, msg),
        # plus per-row atom detail (qualified nodes, qualified edges,
        # previous bound, name) when atom_trace is on.
        self.rule_trace_node_atoms = []
        self.rule_trace_edge_atoms = []
        self.rule_trace_node = []
        self.rule_trace_edge = []

        self.nodes = list(graph.nodes())
        self.edges = list(graph.edges())

        if fp_mode:
            # The pinned fp state shape (interpretation_fp.py:144-184):
            # timestep-keyed world dicts with only t=0 present and EMPTY —
            # no per-component worlds, no specific-label [0,1] seeding —
            # while the predicate maps are seeded from the specific labels
            # without world entries. (At the pin those specific labels are
            # additionally always empty on this path — the Program-level
            # stamping defect reproduced in _program.Program.reason.)
            self.interpretations_node = {0: {}}
            self.predicate_map_node = {l: list(ns)
                                       for l, ns in specific_node_labels.items()}
            self.interpretations_edge = {0: {}}
            self.predicate_map_edge = {l: list(es)
                                       for l, es in specific_edge_labels.items()}
        else:
            self.interpretations_node = {}
            self.predicate_map_node = {}
            for n in self.nodes:
                self.interpretations_node[n] = World([])
            for l, ns in specific_node_labels.items():
                self.predicate_map_node[l] = list(ns)
                for n in ns:
                    self.interpretations_node[n].world[l] = interval.closed(0.0, 1.0)
                    self.num_ga[0] += 1

            self.interpretations_edge = {}
            self.predicate_map_edge = {}
            for e in self.edges:
                self.interpretations_edge[e] = World([])
            for l, es in specific_edge_labels.items():
                self.predicate_map_edge[l] = list(es)
                for e in es:
                    self.interpretations_edge[e].world[l] = interval.closed(0.0, 1.0)
                    self.num_ga[0] += 1

        self.neighbors = {n: list(graph.neighbors(n)) for n in graph.nodes()}
        self.reverse_neighbors = _init_reverse_neighbors(self.neighbors)

    def start_fp(self, tmax, facts_node, facts_edge, rules, verbose,
                 convergence_threshold, convergence_bound_threshold,
                 again=False, restart=True):
        self.tmax = tmax
        self._convergence_mode, self._convergence_delta = _init_convergence(
            convergence_bound_threshold, convergence_threshold)
        max_facts_time = _init_facts(
            facts_node, facts_edge, self.facts_to_be_applied_node,
            self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace,
            self.facts_to_be_applied_edge_trace, self.atom_trace)
        self._start_fp(rules, max_facts_time, verbose, again, restart)

    def get_dict(self):
        """The interpretation's dict view, {t: {component: {label: (l, u)}}},
        rebuilt from the stored change trace (oracle interpretation.py:
        707-740): only traced changes appear (everything else reads as the
        empty per-component map); under persistent, each change also stamps
        every LATER timestep up to self.time. The timestep axis is
        range(self.time + 1), so a trace row whose t exceeds self.time — the
        restart-true resume state, where the clock reset under an intact
        trace — raises the pinned KeyError on that t.

        On the fp schedule the pinned view is DIFFERENT by defect: the fp
        variant's edge loop unpacks the row's component into a variable it
        never reads and indexes with the stale `edge` left over from the
        init loop (interpretation_fp.py:852-854), so every edge trace row
        lands on the LAST edge in self.edges, whatever its true component.
        Reproduced here for fp_mode (verified against the installed oracle,
        session-19 review probe probe-fp-getdict-edges); an edge row with no
        edges cannot arise (edge rows exist only for worlds _add_edge
        created, which appends to self.edges)."""
        interpretations = {}
        for t in range(self.time + 1):
            interpretations[t] = {}
            for node in self.nodes:
                interpretations[t][node] = {}
            for edge in self.edges:
                interpretations[t][edge] = {}

        for trace, is_edge_trace in ((self.rule_trace_node, False),
                                     (self.rule_trace_edge, True)):
            for change in trace:
                time, comp, l, bnd = change[0], change[2], change[3], change[4]
                if is_edge_trace and self.fp_mode:
                    comp = self.edges[-1]
                interpretations[time][comp][l.get_value()] = (bnd.lower, bnd.upper)
                if self.persistent:
                    for t in range(time + 1, self.time + 1):
                        interpretations[t][comp][l.get_value()] = (bnd.lower, bnd.upper)

        return interpretations

    def _start_fp(self, rules, max_facts_time, verbose, again, restart):
        if again:
            # The pinned fp _start_fp (interpretation_fp.py:228-232) does not
            # extend the ground-atom counts on resume; the default one does.
            if not self.fp_mode:
                self.num_ga.append(self.num_ga[-1])
            if restart:
                self.time = 0
                self.prev_reasoning_data[0] = 0
        # Per-rule flag: True iff the rule's annotation function is registered
        # with the extended 6-arg signature (gates per-grounding metadata).
        ann_fn_arity = {f.__name__: getattr(f, 'py_func', f).__code__.co_argcount
                        for f in self.annotation_functions}
        extended_ann_fn_flags = [
            r.get_annotation_function() != ''
            and ann_fn_arity.get(r.get_annotation_function(), 0) == 6
            for r in rules]
        if self.fp_mode:
            # max_facts_time is unused by the fp schedule (its perfect
            # convergence is pass-level "nothing updated", never a horizon).
            fp_cnt, t = reason_fp(self, rules, verbose, again,
                                  extended_ann_fn_flags)
        else:
            fp_cnt, t = reason(self, rules, max_facts_time, verbose, again,
                               extended_ann_fn_flags)
        self.time = t - 1
        # If we need to reason again, store the next timestep to start from
        self.prev_reasoning_data[0] = t
        self.prev_reasoning_data[1] = fp_cnt
        if verbose:
            print('Fixed Point iterations:', fp_cnt)


def _init_reverse_neighbors(neighbors):
    reverse_neighbors = {}
    for n, neighbor_nodes in neighbors.items():
        for neighbor_node in neighbor_nodes:
            if neighbor_node in reverse_neighbors and n not in reverse_neighbors[neighbor_node]:
                reverse_neighbors[neighbor_node].append(n)
            else:
                reverse_neighbors[neighbor_node] = [n]
        if n not in reverse_neighbors:
            reverse_neighbors[n] = []
    return reverse_neighbors


def _init_convergence(convergence_bound_threshold, convergence_threshold):
    """Mode selection (interpretation.py:176-188): both thresholds defaulted
    selects perfect convergence; a bound threshold dominates a count one."""
    if convergence_bound_threshold == -1 and convergence_threshold == -1:
        return 'perfect_convergence', 0
    if convergence_bound_threshold == -1:
        return 'delta_interpretation', convergence_threshold
    return 'delta_bound', convergence_bound_threshold


def _init_facts(facts_node, facts_edge, facts_to_be_applied_node,
                facts_to_be_applied_edge, facts_to_be_applied_node_trace,
                facts_to_be_applied_edge_trace, atom_trace):
    """Expand every fact into one queue entry per active timestep; the
    returned max time holds perfect convergence open."""
    max_time = 0
    for fact in facts_node:
        for t in range(fact.start_time, fact.end_time + 1):
            max_time = max(max_time, t)
            graph_attribute = fact.name == 'graph-attribute-fact'
            facts_to_be_applied_node.append(
                (t, fact.component, fact.pred, fact.bound, fact.static, graph_attribute))
            if atom_trace:
                facts_to_be_applied_node_trace.append(fact.name)
    for fact in facts_edge:
        for t in range(fact.start_time, fact.end_time + 1):
            max_time = max(max_time, t)
            graph_attribute = fact.name == 'graph-attribute-fact'
            facts_to_be_applied_edge.append(
                (t, fact.component, fact.pred, fact.bound, fact.static, graph_attribute))
            if atom_trace:
                facts_to_be_applied_edge_trace.append(fact.name)
    return max_time


def _apply_fact(interp, kind, i, t, fp_cnt, convergence_state,
                interpretations, predicate_map):
    """Apply one due fact queue entry (node or edge) — the shared body of the
    pinned per-kind fact loops (interpretation.py:285-343/362-418; the fp
    schedule's fact loops carry the identical body over its per-timestep
    world dict, interpretation_fp.py:363-433/446-514, so `interpretations`
    and `predicate_map` arrive from the caller's schedule)."""
    if kind == 'node':
        queue, trace = interp.facts_to_be_applied_node, interp.facts_to_be_applied_node_trace
        rule_trace, rule_trace_atoms = interp.rule_trace_node, interp.rule_trace_node_atoms
        rules_applied_trace = interp.rules_to_be_applied_node_trace
        check_consistent, update_fn, resolve = (
            check_consistent_node, _update_node, resolve_inconsistency_node)
    else:
        queue, trace = interp.facts_to_be_applied_edge, interp.facts_to_be_applied_edge_trace
        rule_trace, rule_trace_atoms = interp.rule_trace_edge, interp.rule_trace_edge_atoms
        rules_applied_trace = interp.rules_to_be_applied_edge_trace
        check_consistent, update_fn, resolve = (
            check_consistent_edge, _update_edge, resolve_inconsistency_edge)

    comp, l, bnd, static, graph_attribute = \
        queue[i][1], queue[i][2], queue[i][3], queue[i][4], queue[i][5]

    # A static bound needs no update — bank the reapplication (and any IPL
    # complements) in the trace and move on (interpretation.py:294-310).
    if l in interpretations[comp].world and interpretations[comp].world[l].is_static():
        if (interp.save_graph_attributes_to_rule_trace or not graph_attribute) \
                and interp.store_interpretation_changes:
            meta_name = trace[i] if interp.atom_trace else ''
            recorded = bnd if kind == 'node' else interpretations[comp].world[l]
            rule_trace.append((t, fp_cnt, comp, l, recorded, True, 'Fact', meta_name, ''))
            if interp.atom_trace:
                _update_rule_trace(rule_trace_atoms, [], [], bnd, trace[i])
            for p1, p2 in interp.ipl:
                if p1 == l:
                    rule_trace.append((t, fp_cnt, comp, p2, interpretations[comp].world[p2],
                                       True, 'IPL', f'IPL: {l.get_value()}', ''))
                    if interp.atom_trace:
                        _update_rule_trace(rule_trace_atoms, [], [],
                                           interpretations[comp].world[p2], trace[i])
                elif p2 == l:
                    rule_trace.append((t, fp_cnt, comp, p1, interpretations[comp].world[p1],
                                       True, 'IPL', f'IPL: {l.get_value()}', ''))
                    if interp.atom_trace:
                        _update_rule_trace(rule_trace_atoms, [], [],
                                           interpretations[comp].world[p1], trace[i])
    else:
        mode = 'graph-attribute-fact' if graph_attribute else 'fact'
        if check_consistent(interpretations, comp, (l, bnd)):
            override = interp.update_mode == 'override'
            u, changes = update_fn(interp, interpretations, predicate_map, comp,
                                   (l, bnd), rule_trace, fp_cnt, t, static,
                                   rules_applied_trace, i, trace, rule_trace_atoms,
                                   mode=mode, override=override)
            _bank_change(interp, convergence_state, u, changes)
        else:
            if interp.inconsistency_check:
                resolve(interp, interpretations, comp, (l, bnd), t, fp_cnt, i,
                        rule_trace, rule_trace_atoms, rules_applied_trace, trace,
                        mode=mode)
            else:
                u, changes = update_fn(interp, interpretations, predicate_map, comp,
                                       (l, bnd), rule_trace, fp_cnt, t, static,
                                       rules_applied_trace, i, trace, rule_trace_atoms,
                                       mode=mode, override=True)
                _bank_change(interp, convergence_state, u, changes)


def _bank_change(interp, convergence_state, updated, changes):
    """Fold one update's outcome into the timestep's convergence counters."""
    convergence_state['update'] = updated or convergence_state['update']
    if interp._convergence_mode == 'delta_bound':
        convergence_state['bound_delta'] = max(convergence_state['bound_delta'], changes)
    else:
        convergence_state['changes_cnt'] += changes


def reason(interp, rules, max_facts_time, verbose, again, extended_ann_fn_flags):
    """The temporal fixed-point loop (interpretation.py:240-686)."""
    t = interp.prev_reasoning_data[0]
    fp_cnt = interp.prev_reasoning_data[1]
    tmax = interp.tmax
    atom_trace = interp.atom_trace
    max_rules_time = 0
    timestep_loop = True
    while timestep_loop:
        if t == tmax:
            timestep_loop = False
        if verbose:
            print('Timestep:', t, flush=True)

        # Reset the interpretation at the start of a non-initial timestep when
        # non-persistent: every non-static bound widens to [0,1], banking its
        # current bounds as the previous ones convergence measures against.
        if t > 0 and not interp.persistent:
            for n in interp.nodes:
                w = interp.interpretations_node[n].world
                for l in w:
                    if not w[l].is_static():
                        w[l].reset()
            for e in interp.edges:
                w = interp.interpretations_edge[e].world
                for l in w:
                    if not w[l].is_static():
                        w[l].reset()

        # Convergence bookkeeping for this timestep
        convergence_state = {'changes_cnt': 0, 'bound_delta': 0, 'update': False}

        # Apply due facts — nodes then edges, queue order. A due fact for an
        # unknown component adds it to the graph first; a static fact
        # re-enqueues itself for the next timestep.
        facts_new = []
        facts_trace_new = []
        nodes_set = set(interp.nodes)
        for i in range(len(interp.facts_to_be_applied_node)):
            if interp.facts_to_be_applied_node[i][0] == t:
                comp = interp.facts_to_be_applied_node[i][1]
                if comp not in nodes_set:
                    _add_node(interp, comp, interp.interpretations_node)
                    nodes_set.add(comp)
                _apply_fact(interp, 'node', i, t, fp_cnt, convergence_state,
                            interp.interpretations_node, interp.predicate_map_node)
                if interp.facts_to_be_applied_node[i][4]:  # static: ride forward
                    entry = interp.facts_to_be_applied_node[i]
                    facts_new.append((entry[0] + 1,) + entry[1:])
                    if atom_trace:
                        facts_trace_new.append(interp.facts_to_be_applied_node_trace[i])
            else:
                facts_new.append(interp.facts_to_be_applied_node[i])
                if atom_trace:
                    facts_trace_new.append(interp.facts_to_be_applied_node_trace[i])
        interp.facts_to_be_applied_node[:] = facts_new
        if atom_trace:
            interp.facts_to_be_applied_node_trace[:] = facts_trace_new

        facts_new = []
        facts_trace_new = []
        edges_set = set(interp.edges)
        for i in range(len(interp.facts_to_be_applied_edge)):
            if interp.facts_to_be_applied_edge[i][0] == t:
                comp = interp.facts_to_be_applied_edge[i][1]
                if comp not in edges_set:
                    _add_edge(interp, comp[0], comp[1], Label(''), t,
                              interp.interpretations_node, interp.interpretations_edge)
                    edges_set.add(comp)
                _apply_fact(interp, 'edge', i, t, fp_cnt, convergence_state,
                            interp.interpretations_edge, interp.predicate_map_edge)
                if interp.facts_to_be_applied_edge[i][4]:
                    entry = interp.facts_to_be_applied_edge[i]
                    facts_new.append((entry[0] + 1,) + entry[1:])
                    if atom_trace:
                        facts_trace_new.append(interp.facts_to_be_applied_edge_trace[i])
            else:
                facts_new.append(interp.facts_to_be_applied_edge[i])
                if atom_trace:
                    facts_trace_new.append(interp.facts_to_be_applied_edge_trace[i])
        interp.facts_to_be_applied_edge[:] = facts_new
        if atom_trace:
            interp.facts_to_be_applied_edge_trace[:] = facts_trace_new

        in_loop = True
        while in_loop:
            # Stays False unless a delta-0 rule enqueues at this timestep
            in_loop = False

            # Apply due node-rule conclusions
            rules_to_remove_idx = set()
            for idx, entry in enumerate(interp.rules_to_be_applied_node):
                if entry[0] == t:
                    comp, l, bnd, set_static = entry[1], entry[2], entry[3], entry[4]
                    if check_consistent_node(interp.interpretations_node, comp, (l, bnd)):
                        override = interp.update_mode == 'override'
                        u, changes = _update_node(
                            interp, interp.interpretations_node, interp.predicate_map_node,
                            comp, (l, bnd), interp.rule_trace_node, fp_cnt, t, set_static,
                            interp.rules_to_be_applied_node_trace, idx,
                            interp.facts_to_be_applied_node_trace,
                            interp.rule_trace_node_atoms, mode='rule', override=override)
                        _bank_change(interp, convergence_state, u, changes)
                    else:
                        if interp.inconsistency_check:
                            resolve_inconsistency_node(
                                interp, interp.interpretations_node, comp, (l, bnd),
                                t, fp_cnt, idx, interp.rule_trace_node,
                                interp.rule_trace_node_atoms,
                                interp.rules_to_be_applied_node_trace,
                                interp.facts_to_be_applied_node_trace, mode='rule')
                        else:
                            u, changes = _update_node(
                                interp, interp.interpretations_node, interp.predicate_map_node,
                                comp, (l, bnd), interp.rule_trace_node, fp_cnt, t, set_static,
                                interp.rules_to_be_applied_node_trace, idx,
                                interp.facts_to_be_applied_node_trace,
                                interp.rule_trace_node_atoms, mode='rule', override=True)
                            _bank_change(interp, convergence_state, u, changes)
                    rules_to_remove_idx.add(idx)
            interp.rules_to_be_applied_node[:] = [
                x for j, x in enumerate(interp.rules_to_be_applied_node)
                if j not in rules_to_remove_idx]
            if atom_trace:
                interp.rules_to_be_applied_node_trace[:] = [
                    x for j, x in enumerate(interp.rules_to_be_applied_node_trace)
                    if j not in rules_to_remove_idx]

            # Apply due edge-rule conclusions (adding inferred edges first)
            rules_to_remove_idx = set()
            for idx, entry in enumerate(interp.rules_to_be_applied_edge):
                if entry[0] == t:
                    comp, l, bnd, set_static = entry[1], entry[2], entry[3], entry[4]
                    sources, targets, edge_l = interp.edges_to_be_added_edge_rule[idx]
                    edges_added, changes = _add_edges(
                        interp, sources, targets, edge_l, t,
                        interp.interpretations_node, interp.interpretations_edge)
                    convergence_state['changes_cnt'] += changes

                    if edge_l.get_value() != '':
                        for e in edges_added:
                            if interp.interpretations_edge[e].world[edge_l].is_static():
                                continue
                            if check_consistent_edge(interp.interpretations_edge, e, (edge_l, bnd)):
                                override = interp.update_mode == 'override'
                                u, changes = _update_edge(
                                    interp, interp.interpretations_edge, interp.predicate_map_edge,
                                    e, (edge_l, bnd), interp.rule_trace_edge, fp_cnt, t, set_static,
                                    interp.rules_to_be_applied_edge_trace, idx,
                                    interp.facts_to_be_applied_edge_trace,
                                    interp.rule_trace_edge_atoms, mode='rule', override=override)
                                _bank_change(interp, convergence_state, u, changes)
                            else:
                                if interp.inconsistency_check:
                                    resolve_inconsistency_edge(
                                        interp, interp.interpretations_edge, e, (edge_l, bnd),
                                        t, fp_cnt, idx, interp.rule_trace_edge,
                                        interp.rule_trace_edge_atoms,
                                        interp.rules_to_be_applied_edge_trace,
                                        interp.facts_to_be_applied_edge_trace, mode='rule')
                                else:
                                    u, changes = _update_edge(
                                        interp, interp.interpretations_edge, interp.predicate_map_edge,
                                        e, (edge_l, bnd), interp.rule_trace_edge, fp_cnt, t, set_static,
                                        interp.rules_to_be_applied_edge_trace, idx,
                                        interp.facts_to_be_applied_edge_trace,
                                        interp.rule_trace_edge_atoms, mode='rule', override=True)
                                    _bank_change(interp, convergence_state, u, changes)
                    else:
                        if check_consistent_edge(interp.interpretations_edge, comp, (l, bnd)):
                            override = interp.update_mode == 'override'
                            u, changes = _update_edge(
                                interp, interp.interpretations_edge, interp.predicate_map_edge,
                                comp, (l, bnd), interp.rule_trace_edge, fp_cnt, t, set_static,
                                interp.rules_to_be_applied_edge_trace, idx,
                                interp.facts_to_be_applied_edge_trace,
                                interp.rule_trace_edge_atoms, mode='rule', override=override)
                            _bank_change(interp, convergence_state, u, changes)
                        else:
                            if interp.inconsistency_check:
                                resolve_inconsistency_edge(
                                    interp, interp.interpretations_edge, comp, (l, bnd),
                                    t, fp_cnt, idx, interp.rule_trace_edge,
                                    interp.rule_trace_edge_atoms,
                                    interp.rules_to_be_applied_edge_trace,
                                    interp.facts_to_be_applied_edge_trace, mode='rule')
                            else:
                                u, changes = _update_edge(
                                    interp, interp.interpretations_edge, interp.predicate_map_edge,
                                    comp, (l, bnd), interp.rule_trace_edge, fp_cnt, t, set_static,
                                    interp.rules_to_be_applied_edge_trace, idx,
                                    interp.facts_to_be_applied_edge_trace,
                                    interp.rule_trace_edge_atoms, mode='rule', override=True)
                                _bank_change(interp, convergence_state, u, changes)
                    rules_to_remove_idx.add(idx)
            interp.rules_to_be_applied_edge[:] = [
                x for j, x in enumerate(interp.rules_to_be_applied_edge)
                if j not in rules_to_remove_idx]
            interp.edges_to_be_added_edge_rule[:] = [
                x for j, x in enumerate(interp.edges_to_be_added_edge_rule)
                if j not in rules_to_remove_idx]
            if atom_trace:
                interp.rules_to_be_applied_edge_trace[:] = [
                    x for j, x in enumerate(interp.rules_to_be_applied_edge_trace)
                    if j not in rules_to_remove_idx]

            # Fixed point: if anything updated, ground every rule and enqueue
            # its conclusions at t + delta.
            if convergence_state['update']:
                fp_cnt += 1
                for i, rule in enumerate(rules):
                    delta_t = rule.get_delta()
                    # Ground only if the conclusion can land inside the run
                    if t + delta_t <= tmax or tmax == -1 or again:
                        applicable_node_rules, applicable_edge_rules = _ground_rule(
                            interp, rule, extended_ann_fn_flags[i], t,
                            interp.interpretations_node, interp.interpretations_edge)

                        for applicable_rule in applicable_node_rules:
                            n, annotations, qualified_nodes, qualified_edges, _, \
                                clause_labels, clause_variables = applicable_rule
                            if rule.get_target() not in interp.interpretations_node[n].world \
                                    or not interp.interpretations_node[n].world[rule.get_target()].is_static():
                                bnd = annotate(interp.annotation_functions, rule,
                                               annotations, qualified_nodes,
                                               qualified_edges, clause_labels,
                                               clause_variables, rule.get_weights())
                                # A head negated at parse time already carries
                                # the folded bound; only an ann-fn-produced
                                # bound still needs the ~[l,u]=[1-u,1-l] flip.
                                if rule.get_annotation_function() != '' and rule.is_head_negated():
                                    bnd = (1 - bnd[1], 1 - bnd[0])
                                bnd_l = min(max(bnd[0], 0), 1)
                                bnd_u = min(max(bnd[1], 0), 1)
                                bnd = interval.closed(bnd_l, bnd_u)
                                max_rules_time = max(max_rules_time, t + delta_t)
                                interp.rules_to_be_applied_node.append(
                                    (t + delta_t, n, rule.get_target(), bnd, rule.is_static_rule()))
                                if atom_trace:
                                    interp.rules_to_be_applied_node_trace.append(
                                        (qualified_nodes, qualified_edges, rule.get_rule_name()))
                                if delta_t == 0:
                                    in_loop = True
                                    convergence_state['update'] = False

                        for applicable_rule in applicable_edge_rules:
                            e, annotations, qualified_nodes, qualified_edges, \
                                edges_to_add, clause_labels, clause_variables = applicable_rule
                            if len(edges_to_add[0]) > 0 \
                                    or rule.get_target() not in interp.interpretations_edge[e].world \
                                    or not interp.interpretations_edge[e].world[rule.get_target()].is_static():
                                bnd = annotate(interp.annotation_functions, rule,
                                               annotations, qualified_nodes,
                                               qualified_edges, clause_labels,
                                               clause_variables, rule.get_weights())
                                if rule.get_annotation_function() != '' and rule.is_head_negated():
                                    bnd = (1 - bnd[1], 1 - bnd[0])
                                bnd_l = min(max(bnd[0], 0), 1)
                                bnd_u = min(max(bnd[1], 0), 1)
                                bnd = interval.closed(bnd_l, bnd_u)
                                max_rules_time = max(max_rules_time, t + delta_t)
                                interp.edges_to_be_added_edge_rule.append(edges_to_add)
                                interp.rules_to_be_applied_edge.append(
                                    (t + delta_t, e, rule.get_target(), bnd, rule.is_static_rule()))
                                if atom_trace:
                                    interp.rules_to_be_applied_edge_trace.append(
                                        (qualified_nodes, qualified_edges, rule.get_rule_name()))
                                if delta_t == 0:
                                    in_loop = True
                                    convergence_state['update'] = False

        # Convergence check at the end of each timestep
        if interp._convergence_mode == 'delta_interpretation':
            if convergence_state['changes_cnt'] <= interp._convergence_delta:
                if verbose:
                    print(f"\nConverged at time: {t} with "
                          f"{int(convergence_state['changes_cnt'])} changes from the previous interpretation")
                # Be consistent with time returned when we don't converge
                t += 1
                break
        elif interp._convergence_mode == 'delta_bound':
            if convergence_state['bound_delta'] <= interp._convergence_delta:
                if verbose:
                    print(f"\nConverged at time: {t} with "
                          f"{float_to_str(convergence_state['bound_delta'])} as the maximum bound change from the previous interpretation")
                t += 1
                break
        else:  # perfect_convergence: nothing pending now or in the future
            if t >= max_facts_time and t >= max_rules_time:
                if verbose:
                    print(f'\nConverged at time: {t}')
                t += 1
                break

        t += 1
        interp.num_ga.append(interp.num_ga[-1])

    return fp_cnt, t


def _fp_copy_forward(interp, worlds_by_t, t, fp_cnt):
    """Create/refresh one timestep's world dict and copy the previous
    timestep's bounds into it — every bound under persistent, static bounds
    only otherwise (interpretation_fp.py:278-351). On the first pass
    (fp_cnt == 0) the dict is recreated and every eligible label copied; on
    later passes existing worlds persist and only missing labels fill in.
    Every component present at t-1 gets a world at t either way."""
    if t not in worlds_by_t or fp_cnt == 0:
        worlds_by_t[t] = {}
    if t > 0:
        last, cur = worlds_by_t[t - 1], worlds_by_t[t]
        for comp in last:
            if comp not in cur:
                cur[comp] = World([])
            w = last[comp].world
            new_w = cur[comp].world
            for l in w:
                if (interp.persistent or w[l].is_static()) \
                        and (fp_cnt == 0 or l not in new_w):
                    new_w[l] = w[l].copy()


def _fp_apply_rule_conclusion(interp, kind, interpretations, comp, l, bnd,
                              set_static, t_e, fp_cnt, idx, convergence_state):
    """Apply one queued rule conclusion on the fp schedule — the shared
    consistent/resolve/override triple of the pinned fp application loops
    (interpretation_fp.py:653-679 nodes, :703-763 edges). Returns True when
    the pass-level update flag should bump max_t_changes for t_e (the pinned
    bump sites live in the update branches, never the resolve branch)."""
    if kind == 'node':
        predicate_map, rule_trace = interp.predicate_map_node, interp.rule_trace_node
        rule_trace_atoms = interp.rule_trace_node_atoms
        rules_applied_trace = interp.rules_to_be_applied_node_trace
        facts_trace = interp.facts_to_be_applied_node_trace
        check_consistent, update_fn, resolve = (
            check_consistent_node, _update_node, resolve_inconsistency_node)
    else:
        predicate_map, rule_trace = interp.predicate_map_edge, interp.rule_trace_edge
        rule_trace_atoms = interp.rule_trace_edge_atoms
        rules_applied_trace = interp.rules_to_be_applied_edge_trace
        facts_trace = interp.facts_to_be_applied_edge_trace
        check_consistent, update_fn, resolve = (
            check_consistent_edge, _update_edge, resolve_inconsistency_edge)

    if check_consistent(interpretations, comp, (l, bnd)):
        override = interp.update_mode == 'override'
        u, changes = update_fn(interp, interpretations, predicate_map, comp,
                               (l, bnd), rule_trace, fp_cnt, t_e, set_static,
                               rules_applied_trace, idx, facts_trace,
                               rule_trace_atoms, mode='rule', override=override)
        _bank_change(interp, convergence_state, u, changes)
        return True
    if interp.inconsistency_check:
        resolve(interp, interpretations, comp, (l, bnd), t_e, fp_cnt, idx,
                rule_trace, rule_trace_atoms, rules_applied_trace, facts_trace,
                mode='rule')
        return False
    u, changes = update_fn(interp, interpretations, predicate_map, comp,
                           (l, bnd), rule_trace, fp_cnt, t_e, set_static,
                           rules_applied_trace, idx, facts_trace,
                           rule_trace_atoms, mode='rule', override=True)
    _bank_change(interp, convergence_state, u, changes)
    return True


def reason_fp(interp, rules, verbose, again, extended_ann_fn_flags):
    """The fp schedule (interpretation_fp.py:251-807): repeat whole-run
    passes until one changes nothing.

    Per pass (fp counter = pass index): sweep every timestep from the resume
    point — copy the previous timestep's persistent/static bounds forward,
    apply the timestep's due facts, ground every rule against THIS
    timestep's worlds and enqueue conclusions at t + delta — then, after the
    sweep, apply every queued conclusion (any timestep) and check
    convergence. The semantic operations are the same functions the default
    schedule drives; what differs is state shape and order:

    - worlds are per-timestep dicts seeded empty (facts/conclusions create
      them), so the same atom re-enters the shared predicate maps once per
      timestep that re-derives it — the pinned duplicated atom-trace
      groundings;
    - conclusions apply only between passes, so every trace row carries the
      pass counter, fact rows sort before the rule rows their pass produced,
      and re-derivations in later passes intersect to no change and bank no
      row;
    - perfect convergence is pass-level "nothing updated" (never the
      max-facts/rules-time horizon), and the returned end time is the last
      timestep any update touched, plus one (max_t_changes + 1,
      interpretation_fp.py:806-807).

    Pinned quirks reproduced deliberately: the per-timestep reset of the
    convergence counters means only the LAST swept timestep's fact changes
    join the pass's convergence data (interpretation_fp.py:353-356); a
    delta-0 conclusion CLEARS the update flag at enqueue time
    (:575-576/:620-621); and with tmax == -1 the timestep sweep has no exit
    (:272-273) — the pinned fp variant does not terminate on the
    run-to-convergence arm, so this port doesn't either. The pinned
    max_rules_time bookkeeping is dropped: the fp variant tracks it but no
    branch reads it."""
    fp_cnt = interp.prev_reasoning_data[1]
    tmax = interp.tmax
    atom_trace = interp.atom_trace
    interpretations_node = interp.interpretations_node
    interpretations_edge = interp.interpretations_edge
    max_t_changes = interp.prev_reasoning_data[0]
    update = True
    convergence_state = {'changes_cnt': 0, 'bound_delta': 0, 'update': False}
    while True:
        t = interp.prev_reasoning_data[0]
        if not update:
            break
        update = False

        timestep_loop = True
        while timestep_loop:
            if t == tmax:
                timestep_loop = False
            if verbose:
                print('Timestep:', t, flush=True)

            _fp_copy_forward(interp, interpretations_node, t, fp_cnt)
            _fp_copy_forward(interp, interpretations_edge, t, fp_cnt)

            # Convergence bookkeeping resets at every swept timestep
            # (interpretation_fp.py:353-356) — the applications after the
            # sweep keep accumulating into the last timestep's state.
            convergence_state = {'changes_cnt': 0, 'bound_delta': 0,
                                 'update': False}

            # Apply due facts — nodes then edges, queue order; a due fact for
            # an unknown component creates it (graph-wide when truly new, a
            # world at this timestep when only the timestep lacks one); a
            # static fact re-enqueues itself for the next timestep.
            facts_new = []
            facts_trace_new = []
            nodes_set = set(interp.nodes)
            for i in range(len(interp.facts_to_be_applied_node)):
                entry = interp.facts_to_be_applied_node[i]
                if entry[0] == t:
                    comp = entry[1]
                    if comp not in nodes_set:
                        nodes_set.add(comp)
                        _add_node(interp, comp, interpretations_node[t])
                    elif comp not in interpretations_node[t]:
                        interpretations_node[t][comp] = World([])
                    _apply_fact(interp, 'node', i, t, fp_cnt, convergence_state,
                                interpretations_node[t], interp.predicate_map_node)
                    if convergence_state['update']:
                        max_t_changes = max(max_t_changes, t)
                    if entry[4]:  # static: ride forward
                        facts_new.append((entry[0] + 1,) + entry[1:])
                        if atom_trace:
                            facts_trace_new.append(interp.facts_to_be_applied_node_trace[i])
                else:
                    facts_new.append(entry)
                    if atom_trace:
                        facts_trace_new.append(interp.facts_to_be_applied_node_trace[i])
            interp.facts_to_be_applied_node[:] = facts_new
            if atom_trace:
                interp.facts_to_be_applied_node_trace[:] = facts_trace_new

            facts_new = []
            facts_trace_new = []
            edges_set = set(interp.edges)
            for i in range(len(interp.facts_to_be_applied_edge)):
                entry = interp.facts_to_be_applied_edge[i]
                if entry[0] == t:
                    comp = entry[1]
                    if comp not in edges_set:
                        _add_edge(interp, comp[0], comp[1], Label(''), t,
                                  interpretations_node[t], interpretations_edge[t])
                        edges_set.add(comp)
                    elif comp not in interpretations_edge[t]:
                        interpretations_edge[t][comp] = World([])
                    _apply_fact(interp, 'edge', i, t, fp_cnt, convergence_state,
                                interpretations_edge[t], interp.predicate_map_edge)
                    if convergence_state['update']:
                        max_t_changes = max(max_t_changes, t)
                    if entry[4]:
                        facts_new.append((entry[0] + 1,) + entry[1:])
                        if atom_trace:
                            facts_trace_new.append(interp.facts_to_be_applied_edge_trace[i])
                else:
                    facts_new.append(entry)
                    if atom_trace:
                        facts_trace_new.append(interp.facts_to_be_applied_edge_trace[i])
            interp.facts_to_be_applied_edge[:] = facts_new
            if atom_trace:
                interp.facts_to_be_applied_edge_trace[:] = facts_trace_new

            # Ground every rule against THIS timestep's worlds; conclusions
            # queue for the between-pass application phase. (The pinned
            # per-rule threadsafe lists extend in rule order after the
            # prange — sequentially identical to appending per rule.)
            for i, rule in enumerate(rules):
                delta_t = rule.get_delta()
                if t + delta_t <= tmax or tmax == -1 or again:
                    applicable_node_rules, applicable_edge_rules = _ground_rule(
                        interp, rule, extended_ann_fn_flags[i], t,
                        interpretations_node[t], interpretations_edge[t])

                    for applicable_rule in applicable_node_rules:
                        n, annotations, qualified_nodes, qualified_edges, _, \
                            clause_labels, clause_variables = applicable_rule
                        if n not in interpretations_node[t] \
                                or rule.get_target() not in interpretations_node[t][n].world \
                                or not interpretations_node[t][n].world[rule.get_target()].is_static():
                            bnd = annotate(interp.annotation_functions, rule,
                                           annotations, qualified_nodes,
                                           qualified_edges, clause_labels,
                                           clause_variables, rule.get_weights())
                            if rule.get_annotation_function() != '' and rule.is_head_negated():
                                bnd = (1 - bnd[1], 1 - bnd[0])
                            bnd_l = min(max(bnd[0], 0), 1)
                            bnd_u = min(max(bnd[1], 0), 1)
                            bnd = interval.closed(bnd_l, bnd_u)
                            interp.rules_to_be_applied_node.append(
                                (t + delta_t, n, rule.get_target(), bnd, rule.is_static_rule()))
                            if atom_trace:
                                interp.rules_to_be_applied_node_trace.append(
                                    (qualified_nodes, qualified_edges, rule.get_rule_name()))
                            # The pinned delta-0 arm CLEARS the update flag
                            # (interpretation_fp.py:574-576).
                            if delta_t == 0:
                                convergence_state['update'] = False

                    for applicable_rule in applicable_edge_rules:
                        e, annotations, qualified_nodes, qualified_edges, \
                            edges_to_add, clause_labels, clause_variables = applicable_rule
                        if e not in interpretations_edge[t] \
                                or len(edges_to_add[0]) > 0 \
                                or rule.get_target() not in interpretations_edge[t][e].world \
                                or not interpretations_edge[t][e].world[rule.get_target()].is_static():
                            bnd = annotate(interp.annotation_functions, rule,
                                           annotations, qualified_nodes,
                                           qualified_edges, clause_labels,
                                           clause_variables, rule.get_weights())
                            if rule.get_annotation_function() != '' and rule.is_head_negated():
                                bnd = (1 - bnd[1], 1 - bnd[0])
                            bnd_l = min(max(bnd[0], 0), 1)
                            bnd_u = min(max(bnd[1], 0), 1)
                            bnd = interval.closed(bnd_l, bnd_u)
                            interp.edges_to_be_added_edge_rule.append(edges_to_add)
                            interp.rules_to_be_applied_edge.append(
                                (t + delta_t, e, rule.get_target(), bnd, rule.is_static_rule()))
                            if atom_trace:
                                interp.rules_to_be_applied_edge_trace.append(
                                    (qualified_nodes, qualified_edges, rule.get_rule_name()))
                            if delta_t == 0:
                                convergence_state['update'] = False

            t += 1

        # Between-pass application phase: every queued node conclusion, then
        # every queued edge conclusion, at its own entry timestep, with this
        # pass's fp counter — then the queues drain completely.
        for idx in range(len(interp.rules_to_be_applied_node)):
            t_e, comp, l, bnd, set_static = interp.rules_to_be_applied_node[idx]
            if comp not in interpretations_node[t_e]:
                interpretations_node[t_e][comp] = World([])
            bumped = _fp_apply_rule_conclusion(
                interp, 'node', interpretations_node[t_e], comp, l, bnd,
                set_static, t_e, fp_cnt, idx, convergence_state)
            if bumped and convergence_state['update']:
                max_t_changes = max(max_t_changes, t_e)
        interp.rules_to_be_applied_node.clear()
        if atom_trace:
            interp.rules_to_be_applied_node_trace.clear()

        for idx in range(len(interp.rules_to_be_applied_edge)):
            t_e, comp, l, bnd, set_static = interp.rules_to_be_applied_edge[idx]
            sources, targets, edge_l = interp.edges_to_be_added_edge_rule[idx]
            edges_added, changes = _add_edges(
                interp, sources, targets, edge_l, t_e,
                interpretations_node[t_e], interpretations_edge[t_e])
            convergence_state['changes_cnt'] += changes

            if edge_l.get_value() != '':
                for e in edges_added:
                    if interpretations_edge[t_e][e].world[edge_l].is_static():
                        continue
                    bumped = _fp_apply_rule_conclusion(
                        interp, 'edge', interpretations_edge[t_e], e, edge_l,
                        bnd, set_static, t_e, fp_cnt, idx, convergence_state)
                    if bumped and convergence_state['update']:
                        max_t_changes = max(max_t_changes, t_e)
            else:
                if comp not in interpretations_edge[t_e]:
                    interpretations_edge[t_e][comp] = World([])
                bumped = _fp_apply_rule_conclusion(
                    interp, 'edge', interpretations_edge[t_e], comp, l, bnd,
                    set_static, t_e, fp_cnt, idx, convergence_state)
                if bumped and convergence_state['update']:
                    max_t_changes = max(max_t_changes, t_e)
        interp.rules_to_be_applied_edge.clear()
        interp.edges_to_be_added_edge_rule.clear()
        if atom_trace:
            interp.rules_to_be_applied_edge_trace.clear()

        # Convergence check at the end of each pass
        # (interpretation_fp.py:774-800).
        if interp._convergence_mode == 'delta_interpretation':
            if convergence_state['changes_cnt'] <= interp._convergence_delta:
                if verbose:
                    print(f"\nConverged at time: {t} with "
                          f"{int(convergence_state['changes_cnt'])} changes from the previous interpretation")
                break
        elif interp._convergence_mode == 'delta_bound':
            if convergence_state['bound_delta'] <= interp._convergence_delta:
                if verbose:
                    print(f"\nConverged at time: {t} with "
                          f"{float_to_str(convergence_state['bound_delta'])} as the maximum bound change from the previous interpretation")
                break
        else:  # perfect_convergence: the pass changed nothing
            if not convergence_state['update']:
                if verbose:
                    print(f'\nConverged at fp: {fp_cnt}')
                break

        update = convergence_state['update']
        fp_cnt += 1

    return fp_cnt, max_t_changes + 1


def _ground_rule(interp, rule, extended_ann_fn, t, interpretations_node,
                 interpretations_edge):
    """Ground one rule against the current interpretation
    (interpretation.py:809-1281; the fp variant's _ground_rule body is
    line-identical and receives its per-timestep world dicts through the same
    parameters, interpretation_fp.py:932). Returns (applicable node rules,
    applicable edge rules): per satisfied head grounding, the annotation
    inputs and the per-clause qualified nodes/edges the trace rows carry."""
    rule_type = rule.get_rule_type()
    head_variables = rule.get_head_variables()
    head_fns = rule.get_head_function()
    head_fns_vars = rule.get_head_function_vars()
    clauses = rule.get_clauses()
    thresholds = rule.get_thresholds()
    ann_fn = rule.get_annotation_function()
    rule_edges = rule.get_edges()
    allow_ground_rules = interp.allow_ground_rules
    atom_trace = interp.atom_trace
    cwp = interp.closed_world_predicates

    head_var_1 = head_variables[0]

    applicable_rules_node = []
    applicable_rules_edge = []

    # Variable -> candidate nodes; (source var, target var) -> candidate edges
    groundings = {}
    groundings_edges = {}

    # Which variables each edge clause connects, both directions
    dependency_graph_neighbors = {}
    dependency_graph_reverse_neighbors = {}

    nodes_set = set(interp.nodes)
    edges_set = set(interp.edges)

    satisfaction = True
    for i, clause in enumerate(clauses):
        clause_type, clause_label, clause_variables, clause_bnd = \
            clause[0], clause[1], clause[2], clause[3]

        if clause_type == 'node':
            clause_var_1 = clause_variables[0]
            if allow_ground_rules and clause_var_1 in nodes_set:
                grounding = [clause_var_1]
            else:
                grounding = get_rule_node_clause_grounding(
                    clause_var_1, groundings, interp.predicate_map_node,
                    clause_label, interp.nodes)

            qualified_groundings = get_qualified_node_groundings(
                interpretations_node, grounding, clause_label, clause_bnd, cwp)
            groundings[clause_var_1] = qualified_groundings
            qualified_groundings_set = set(qualified_groundings)
            for c1, c2 in groundings_edges:
                if c1 == clause_var_1:
                    groundings_edges[(c1, c2)] = [
                        e for e in groundings_edges[(c1, c2)]
                        if e[0] in qualified_groundings_set]
                if c2 == clause_var_1:
                    groundings_edges[(c1, c2)] = [
                        e for e in groundings_edges[(c1, c2)]
                        if e[1] in qualified_groundings_set]

            # Clause-level gate: the threshold consumes the whole clause's
            # candidate/qualified counts, before heads are enumerated.
            satisfaction = check_node_grounding_threshold_satisfaction(
                interpretations_node, grounding, qualified_groundings,
                clause_label, thresholds[i], cwp) and satisfaction

        elif clause_type == 'edge':
            clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
            if allow_ground_rules and (clause_var_1, clause_var_2) in edges_set:
                grounding = [(clause_var_1, clause_var_2)]
            else:
                if allow_ground_rules:
                    if clause_var_1 in nodes_set and clause_var_1 not in groundings:
                        groundings[clause_var_1] = [clause_var_1]
                    if clause_var_2 in nodes_set and clause_var_2 not in groundings:
                        groundings[clause_var_2] = [clause_var_2]
                grounding = get_rule_edge_clause_grounding(
                    clause_var_1, clause_var_2, groundings, groundings_edges,
                    interp.neighbors, interp.reverse_neighbors,
                    interp.predicate_map_edge, clause_label, interp.edges)

            qualified_groundings = get_qualified_edge_groundings(
                interpretations_edge, grounding, clause_label, clause_bnd, cwp)

            satisfaction = check_edge_grounding_threshold_satisfaction(
                interpretations_edge, grounding, qualified_groundings,
                clause_label, thresholds[i], cwp) and satisfaction

            # Update the variable groundings (dedup preserving edge order)
            groundings[clause_var_1] = []
            groundings[clause_var_2] = []
            groundings_clause_1_set = set()
            groundings_clause_2_set = set()
            for e in qualified_groundings:
                if e[0] not in groundings_clause_1_set:
                    groundings[clause_var_1].append(e[0])
                    groundings_clause_1_set.add(e[0])
                if e[1] not in groundings_clause_2_set:
                    groundings[clause_var_2].append(e[1])
                    groundings_clause_2_set.add(e[1])

            groundings_edges[(clause_var_1, clause_var_2)] = qualified_groundings

            # Record the variable dependency both ways
            if clause_var_1 not in dependency_graph_neighbors:
                dependency_graph_neighbors[clause_var_1] = [clause_var_2]
            elif clause_var_2 not in dependency_graph_neighbors[clause_var_1]:
                dependency_graph_neighbors[clause_var_1].append(clause_var_2)
            if clause_var_2 not in dependency_graph_reverse_neighbors:
                dependency_graph_reverse_neighbors[clause_var_2] = [clause_var_1]
            elif clause_var_1 not in dependency_graph_reverse_neighbors[clause_var_2]:
                dependency_graph_reverse_neighbors[clause_var_2].append(clause_var_1)

        else:
            # Comparison clause — grounded by neither arm at the pin
            pass

        if satisfaction:
            refine_groundings(clause_variables, groundings, groundings_edges,
                              dependency_graph_neighbors,
                              dependency_graph_reverse_neighbors)
        if not satisfaction:
            break

    if satisfaction:
        if rule_type == 'node':
            # A head function (if any) replaces the head variable's grounding
            head_var_groundings, is_func = determine_node_head_vars(
                head_fns, head_fns_vars, groundings, interp.head_functions)
            if is_func:
                groundings[head_var_1] = head_var_groundings

            # An ungrounded head variable is treated as a ground atom
            head_var_1_in_nodes = head_var_1 in interp.nodes
            add_head_var_node_to_graph = False
            if allow_ground_rules and head_var_1_in_nodes:
                groundings[head_var_1] = [head_var_1]
            elif head_var_1 not in groundings:
                if not head_var_1_in_nodes:
                    add_head_var_node_to_graph = True
                groundings[head_var_1] = [head_var_1]

            for head_grounding in groundings[head_var_1]:
                qualified_nodes = []
                qualified_edges = []
                annotations = []
                clause_labels_out = []
                clause_variables_out = []
                edges_to_be_added = ([], [], rule_edges[-1])

                # Refinement may have narrowed groundings since the clause
                # pass — re-check every clause before accepting this head
                satisfaction = check_all_clause_satisfaction(
                    interpretations_node, interpretations_edge, clauses,
                    thresholds, groundings, groundings_edges, cwp)
                if not satisfaction:
                    continue

                for i, clause in enumerate(clauses):
                    clause_type, clause_label, clause_variables = \
                        clause[0], clause[1], clause[2]

                    if clause_type == 'node':
                        clause_var_1 = clause_variables[0]
                        if atom_trace or extended_ann_fn:
                            if clause_var_1 == head_var_1:
                                qualified_nodes.append([head_grounding])
                            else:
                                qualified_nodes.append(list(groundings[clause_var_1]))
                            qualified_edges.append([])
                            if extended_ann_fn:
                                clause_labels_out.append(clause_label)
                                clause_variables_out.append(list(clause_variables))
                        if ann_fn != '':
                            a = []
                            if clause_var_1 == head_var_1:
                                a.append(interpretations_node[head_grounding].world[clause_label])
                            else:
                                for qn in groundings[clause_var_1]:
                                    a.append(interpretations_node[qn].world[clause_label])
                            annotations.append(a)

                    elif clause_type == 'edge':
                        clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
                        if atom_trace or extended_ann_fn:
                            qualified_nodes.append([])
                            if clause_var_1 == head_var_1:
                                qualified_edges.append(
                                    [e for e in groundings_edges[(clause_var_1, clause_var_2)]
                                     if e[0] == head_grounding])
                            elif clause_var_2 == head_var_1:
                                qualified_edges.append(
                                    [e for e in groundings_edges[(clause_var_1, clause_var_2)]
                                     if e[1] == head_grounding])
                            else:
                                qualified_edges.append(
                                    list(groundings_edges[(clause_var_1, clause_var_2)]))
                            if extended_ann_fn:
                                clause_labels_out.append(clause_label)
                                clause_variables_out.append(list(clause_variables))
                        if ann_fn != '':
                            a = []
                            if clause_var_1 == head_var_1:
                                for e in groundings_edges[(clause_var_1, clause_var_2)]:
                                    if e[0] == head_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            elif clause_var_2 == head_var_1:
                                for e in groundings_edges[(clause_var_1, clause_var_2)]:
                                    if e[1] == head_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            else:
                                for qe in groundings_edges[(clause_var_1, clause_var_2)]:
                                    a.append(interpretations_edge[qe].world[clause_label])
                            annotations.append(a)
                    else:
                        pass

                if add_head_var_node_to_graph:
                    _add_node(interp, head_var_1, interpretations_node)

                applicable_rules_node.append(
                    (head_grounding, annotations, qualified_nodes, qualified_edges,
                     edges_to_be_added, clause_labels_out, clause_variables_out))

        elif rule_type == 'edge':
            head_var_1 = head_variables[0]
            head_var_2 = head_variables[1]

            head_var_groundings, is_func = determine_edge_head_vars(
                head_fns, head_fns_vars, groundings, interp.head_functions)
            if is_func[0]:
                groundings[head_var_1] = head_var_groundings[0]
            if is_func[1]:
                groundings[head_var_2] = head_var_groundings[1]

            head_var_1_in_nodes = head_var_1 in interp.nodes
            head_var_2_in_nodes = head_var_2 in interp.nodes
            add_head_var_1_node_to_graph = False
            add_head_var_2_node_to_graph = False
            add_head_edge_to_graph = False
            if allow_ground_rules and head_var_1_in_nodes:
                groundings[head_var_1] = [head_var_1]
            if allow_ground_rules and head_var_2_in_nodes:
                groundings[head_var_2] = [head_var_2]

            if head_var_1 not in groundings:
                if not head_var_1_in_nodes:
                    add_head_var_1_node_to_graph = True
                groundings[head_var_1] = [head_var_1]
            if head_var_2 not in groundings:
                if not head_var_2_in_nodes:
                    add_head_var_2_node_to_graph = True
                groundings[head_var_2] = [head_var_2]

            if not head_var_1_in_nodes and not head_var_2_in_nodes:
                add_head_edge_to_graph = True

            head_var_1_groundings = groundings[head_var_1]
            head_var_2_groundings = groundings[head_var_2]

            source, target, _ = rule_edges
            infer_edges = source != '' and target != ''

            # Infer-edges pairs every combination; otherwise only existing edges
            valid_edge_groundings = []
            for g1 in head_var_1_groundings:
                for g2 in head_var_2_groundings:
                    if infer_edges or (g1, g2) in edges_set:
                        valid_edge_groundings.append((g1, g2))

            for valid_e in valid_edge_groundings:
                head_var_1_grounding, head_var_2_grounding = valid_e[0], valid_e[1]
                qualified_nodes = []
                qualified_edges = []
                annotations = []
                clause_labels_out = []
                clause_variables_out = []
                edges_to_be_added = ([], [], rule_edges[-1])

                # Refine a COPY of the groundings for this head pair — the
                # source-to-target pairing isn't known ahead of time
                temp_groundings = groundings.copy()
                temp_groundings_edges = groundings_edges.copy()

                temp_groundings[head_var_1] = [head_var_1_grounding]
                temp_groundings[head_var_2] = [head_var_2_grounding]
                for c1, c2 in temp_groundings_edges.keys():
                    if c1 == head_var_1 and c2 == head_var_2:
                        temp_groundings_edges[(c1, c2)] = [
                            e for e in temp_groundings_edges[(c1, c2)]
                            if e == (head_var_1_grounding, head_var_2_grounding)]
                    elif c1 == head_var_2 and c2 == head_var_1:
                        temp_groundings_edges[(c1, c2)] = [
                            e for e in temp_groundings_edges[(c1, c2)]
                            if e == (head_var_2_grounding, head_var_1_grounding)]
                    elif c1 == head_var_1:
                        temp_groundings_edges[(c1, c2)] = [
                            e for e in temp_groundings_edges[(c1, c2)]
                            if e[0] == head_var_1_grounding]
                    elif c2 == head_var_1:
                        temp_groundings_edges[(c1, c2)] = [
                            e for e in temp_groundings_edges[(c1, c2)]
                            if e[1] == head_var_1_grounding]
                    elif c1 == head_var_2:
                        temp_groundings_edges[(c1, c2)] = [
                            e for e in temp_groundings_edges[(c1, c2)]
                            if e[0] == head_var_2_grounding]
                    elif c2 == head_var_2:
                        temp_groundings_edges[(c1, c2)] = [
                            e for e in temp_groundings_edges[(c1, c2)]
                            if e[1] == head_var_2_grounding]

                refine_groundings(head_variables, temp_groundings,
                                  temp_groundings_edges, dependency_graph_neighbors,
                                  dependency_graph_reverse_neighbors)

                satisfaction = check_all_clause_satisfaction(
                    interpretations_node, interpretations_edge, clauses,
                    thresholds, temp_groundings, temp_groundings_edges, cwp)
                if not satisfaction:
                    continue

                if infer_edges:
                    # No self loops while inferring unless the head variables coincide
                    if source != target and head_var_1_grounding == head_var_2_grounding:
                        continue
                    edges_to_be_added[0].append(head_var_1_grounding)
                    edges_to_be_added[1].append(head_var_2_grounding)

                for i, clause in enumerate(clauses):
                    clause_type, clause_label, clause_variables = \
                        clause[0], clause[1], clause[2]

                    if clause_type == 'node':
                        clause_var_1 = clause_variables[0]
                        if atom_trace or extended_ann_fn:
                            if clause_var_1 == head_var_1:
                                qualified_nodes.append([head_var_1_grounding])
                            elif clause_var_1 == head_var_2:
                                qualified_nodes.append([head_var_2_grounding])
                            else:
                                qualified_nodes.append(list(temp_groundings[clause_var_1]))
                            qualified_edges.append([])
                            if extended_ann_fn:
                                clause_labels_out.append(clause_label)
                                clause_variables_out.append(list(clause_variables))
                        if ann_fn != '':
                            a = []
                            if clause_var_1 == head_var_1:
                                a.append(interpretations_node[head_var_1_grounding].world[clause_label])
                            elif clause_var_1 == head_var_2:
                                a.append(interpretations_node[head_var_2_grounding].world[clause_label])
                            else:
                                for qn in temp_groundings[clause_var_1]:
                                    a.append(interpretations_node[qn].world[clause_label])
                            annotations.append(a)

                    elif clause_type == 'edge':
                        clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
                        if atom_trace or extended_ann_fn:
                            qualified_nodes.append([])
                            es = temp_groundings_edges[(clause_var_1, clause_var_2)]
                            if clause_var_1 == head_var_1 and clause_var_2 == head_var_2:
                                qualified_edges.append(
                                    [e for e in es if e[0] == head_var_1_grounding
                                     and e[1] == head_var_2_grounding])
                            elif clause_var_1 == head_var_2 and clause_var_2 == head_var_1:
                                qualified_edges.append(
                                    [e for e in es if e[0] == head_var_2_grounding
                                     and e[1] == head_var_1_grounding])
                            elif clause_var_1 == head_var_1:
                                qualified_edges.append(
                                    [e for e in es if e[0] == head_var_1_grounding])
                            elif clause_var_1 == head_var_2:
                                qualified_edges.append(
                                    [e for e in es if e[0] == head_var_2_grounding])
                            elif clause_var_2 == head_var_1:
                                qualified_edges.append(
                                    [e for e in es if e[1] == head_var_1_grounding])
                            elif clause_var_2 == head_var_2:
                                qualified_edges.append(
                                    [e for e in es if e[1] == head_var_2_grounding])
                            else:
                                qualified_edges.append(list(es))
                            if extended_ann_fn:
                                clause_labels_out.append(clause_label)
                                clause_variables_out.append(list(clause_variables))
                        if ann_fn != '':
                            a = []
                            es = temp_groundings_edges[(clause_var_1, clause_var_2)]
                            if clause_var_1 == head_var_1 and clause_var_2 == head_var_2:
                                for e in es:
                                    if e[0] == head_var_1_grounding and e[1] == head_var_2_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            elif clause_var_1 == head_var_2 and clause_var_2 == head_var_1:
                                for e in es:
                                    if e[0] == head_var_2_grounding and e[1] == head_var_1_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            elif clause_var_1 == head_var_1:
                                for e in es:
                                    if e[0] == head_var_1_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            elif clause_var_1 == head_var_2:
                                for e in es:
                                    if e[0] == head_var_2_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            elif clause_var_2 == head_var_1:
                                for e in es:
                                    if e[1] == head_var_1_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            elif clause_var_2 == head_var_2:
                                for e in es:
                                    if e[1] == head_var_2_grounding:
                                        a.append(interpretations_edge[e].world[clause_label])
                            else:
                                for qe in es:
                                    a.append(interpretations_edge[qe].world[clause_label])
                            annotations.append(a)

                if add_head_var_1_node_to_graph and head_var_1_grounding == head_var_1:
                    _add_node(interp, head_var_1, interpretations_node)
                if add_head_var_2_node_to_graph and head_var_2_grounding == head_var_2:
                    _add_node(interp, head_var_2, interpretations_node)
                if add_head_edge_to_graph and (head_var_1, head_var_2) == \
                        (head_var_1_grounding, head_var_2_grounding):
                    _add_edge(interp, head_var_1, head_var_2, Label(''), t,
                              interpretations_node, interpretations_edge)

                e = (head_var_1_grounding, head_var_2_grounding)
                applicable_rules_edge.append(
                    (e, annotations, qualified_nodes, qualified_edges,
                     edges_to_be_added, clause_labels_out, clause_variables_out))

    return applicable_rules_node, applicable_rules_edge


def annotate(annotation_functions, rule, annotations, qualified_nodes,
             qualified_edges, clause_labels, clause_variables, weights):
    """Resolve and invoke the rule's annotation function; without one, the
    rule's parsed head bound is the annotation.

    Pinned quirks kept (interpretation.py:1914-1931): the name-match loop has
    no break, so EVERY registered function with the matching __name__ runs
    and the last result wins; a name that matches NO registrand raises
    NameError("name 'annotation' is not defined") — the pinned objmode block
    only assigns its output variable inside the match loop, so a no-match
    leaves it unbound, and this port raises the same observable.
    """
    func_name = rule.get_annotation_function()
    if func_name == '':
        return rule.get_bnd().lower, rule.get_bnd().upper
    annotation = _UNSET = object()
    for func in annotation_functions:
        if func.__name__ == func_name:
            py_func = getattr(func, 'py_func', func)
            nargs = py_func.__code__.co_argcount
            if nargs == 6:
                annotation = func(annotations, weights, qualified_nodes,
                                  qualified_edges, clause_labels, clause_variables)
            else:
                annotation = func(annotations, weights)
    if annotation is _UNSET:
        raise NameError("name 'annotation' is not defined")
    return annotation


def check_consistent_node(interpretations, comp, na):
    world = interpretations[comp]
    bnd = world.world[na[0]] if na[0] in world.world else interval.closed(0, 1)
    return not ((na[1].lower > bnd.upper) or (bnd.lower > na[1].upper))


def check_consistent_edge(interpretations, comp, na):
    world = interpretations[comp]
    bnd = world.world[na[0]] if na[0] in world.world else interval.closed(0, 1)
    return not ((na[1].lower > bnd.upper) or (bnd.lower > na[1].upper))


def _update_rule_trace(rule_trace_atoms, qn, qe, prev_bnd, name):
    rule_trace_atoms.append((qn, qe, prev_bnd.copy(), name))


def _update_component(interp, interpretations, predicate_map, comp, na, rule_trace,
                      fp_cnt, t_cnt, static, rules_to_be_applied_trace, idx,
                      facts_to_be_applied_trace, rule_trace_atoms, mode, override):
    """Apply one (label, bound) to one component — nodes and edges share the
    pinned body verbatim (_update_node/_update_edge, interpretation.py:
    1506-1740). Returns (updated, change): `change` is the count (or max
    bound delta) this update contributes toward convergence, zero when the
    new bound equals the component's previous-timestep bound."""
    updated = False
    # The pinned guard catches a missing component; keep it that narrow so an
    # implementation fault can't silently bank as (False, 0).
    try:
        world = interpretations[comp]
    except KeyError:
        return (False, 0)
    l, bnd = na
    updated_bnds = []

    # A label new to this world starts at the vacuous bound. The fp variant
    # dropped ground-atom counting (its _update_* take no num_ga), and its
    # per-pass timesteps would index past the default schedule's per-timestep
    # counter anyway — gate, don't guess.
    if l not in world.world:
        world.world[l] = interval.closed(0, 1)
        if not interp.fp_mode:
            interp.num_ga[t_cnt] += 1
        if l in predicate_map:
            predicate_map[l].append(comp)
        else:
            predicate_map[l] = [comp]

    prev_bnd = world.world[l].copy()

    if override:
        world.world[l].set_lower_upper(bnd.lower, bnd.upper)
    else:
        world.update(l, bnd)
    world.world[l].set_static(static)
    if world.world[l] != prev_bnd:
        updated = True
        updated_bnds.append(world.world[l])

        if (interp.save_graph_attributes_to_rule_trace or not mode == 'graph-attribute-fact') \
                and interp.store_interpretation_changes:
            triggered_by = 'Fact' if mode in ('fact', 'graph-attribute-fact') else 'Rule'
            meta_name = ''
            if interp.atom_trace:
                if mode in ('fact', 'graph-attribute-fact'):
                    meta_name = facts_to_be_applied_trace[idx]
                elif mode == 'rule':
                    meta_name = rules_to_be_applied_trace[idx][2]
            rule_trace.append((t_cnt, fp_cnt, comp, l, world.world[l].copy(),
                               True, triggered_by, meta_name, ''))
            if interp.atom_trace:
                if mode in ('fact', 'graph-attribute-fact'):
                    _update_rule_trace(rule_trace_atoms, [], [], prev_bnd,
                                       facts_to_be_applied_trace[idx])
                elif mode == 'rule':
                    qn, qe, name = rules_to_be_applied_trace[idx]
                    _update_rule_trace(rule_trace_atoms, qn, qe, prev_bnd, name)

    # Propagate to the IPL complement: p2's bound tightens to [1-u, 1-l] of p1
    if updated:
        ip_update_cnt = 0
        for p1, p2 in interp.ipl:
            if p1 == l:
                if p2 not in world.world:
                    world.world[p2] = interval.closed(0, 1)
                    if p2 in predicate_map:
                        predicate_map[p2].append(comp)
                    else:
                        predicate_map[p2] = [comp]
                if interp.atom_trace:
                    _update_rule_trace(rule_trace_atoms, [], [], world.world[p2],
                                       f'IPL: {l.get_value()}')
                lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
                upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
                world.world[p2].set_lower_upper(lower, upper)
                world.world[p2].set_static(static)
                ip_update_cnt += 1
                updated_bnds.append(world.world[p2])
                if interp.store_interpretation_changes:
                    rule_trace.append((t_cnt, fp_cnt, comp, p2,
                                       interval.closed(lower, upper), True, 'IPL',
                                       f'IPL: {l.get_value()}', ''))
            if p2 == l:
                if p1 not in world.world:
                    world.world[p1] = interval.closed(0, 1)
                    if p1 in predicate_map:
                        predicate_map[p1].append(comp)
                    else:
                        predicate_map[p1] = [comp]
                if interp.atom_trace:
                    _update_rule_trace(rule_trace_atoms, [], [], world.world[p1],
                                       f'IPL: {l.get_value()}')
                lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
                upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
                world.world[p1].set_lower_upper(lower, upper)
                world.world[p1].set_static(static)
                ip_update_cnt += 1
                updated_bnds.append(world.world[p1])
                if interp.store_interpretation_changes:
                    rule_trace.append((t_cnt, fp_cnt, comp, p1,
                                       interval.closed(lower, upper), True, 'IPL',
                                       f'IPL: {l.get_value()}', ''))

    # Convergence contribution: only a bound that differs from its own
    # previous-timestep value counts
    change = 0
    if updated:
        current_bnd = world.world[l]
        prev_t_bnd = interval.closed(world.world[l].prev_lower, world.world[l].prev_upper)
        if current_bnd != prev_t_bnd:
            if interp._convergence_mode == 'delta_bound':
                for i in updated_bnds:
                    lower_delta = abs(i.lower - i.prev_lower)
                    upper_delta = abs(i.upper - i.prev_upper)
                    change = max(change, max(lower_delta, upper_delta))
            else:
                change = 1 + ip_update_cnt

    return (updated, change)


def _update_node(interp, interpretations, predicate_map, comp, na, rule_trace,
                 fp_cnt, t_cnt, static, rules_to_be_applied_trace, idx,
                 facts_to_be_applied_trace, rule_trace_atoms, mode, override=False):
    return _update_component(interp, interpretations, predicate_map, comp, na,
                             rule_trace, fp_cnt, t_cnt, static,
                             rules_to_be_applied_trace, idx,
                             facts_to_be_applied_trace, rule_trace_atoms,
                             mode, override)


def _update_edge(interp, interpretations, predicate_map, comp, na, rule_trace,
                 fp_cnt, t_cnt, static, rules_to_be_applied_trace, idx,
                 facts_to_be_applied_trace, rule_trace_atoms, mode, override=False):
    return _update_component(interp, interpretations, predicate_map, comp, na,
                             rule_trace, fp_cnt, t_cnt, static,
                             rules_to_be_applied_trace, idx,
                             facts_to_be_applied_trace, rule_trace_atoms,
                             mode, override)


def _resolve_inconsistency(interp, interpretations, comp, na, t_cnt, fp_cnt, idx,
                           rule_trace, rule_trace_atoms, rules_to_be_applied_trace,
                           facts_to_be_applied_trace, mode, comp_str):
    """An inconsistent update pins the bound to static [0,1] (and its IPL
    complements with it), banking an inconsistency row instead of the update
    (interpretation.py:1960-2083)."""
    world = interpretations[comp]

    triggered_by = 'Fact' if mode in ('fact', 'graph-attribute-fact') else 'Rule'
    actual_name = ''
    if interp.atom_trace:
        if mode in ('fact', 'graph-attribute-fact'):
            actual_name = facts_to_be_applied_trace[idx]
        elif mode == 'rule':
            actual_name = rules_to_be_applied_trace[idx][2]

    msg = ''
    if interp.atom_trace:
        comp_label_value = ''
        for _p1, _p2 in interp.ipl:
            if _p1 == na[0]:
                comp_label_value = _p2.get_value()
                break
            if _p2 == na[0]:
                comp_label_value = _p1.get_value()
                break
        if comp_label_value != '':
            msg = (f'Inconsistency occurred. Grounding {na[0].get_value()}({comp_str}) '
                   f'conflicts with grounding {comp_label_value}({comp_str}). '
                   f'Setting bounds to [0,1] and static=True for this timestep.')
        else:
            msg = (f'Inconsistency occurred. Conflicting bounds for '
                   f'{na[0].get_value()}({comp_str}). Update from '
                   f'[{float_to_str(world.world[na[0]].lower)}, {float_to_str(world.world[na[0]].upper)}] to '
                   f'[{float_to_str(na[1].lower)}, {float_to_str(na[1].upper)}] is not allowed. '
                   f'Setting bounds to [0,1] and static=True for this timestep.')

    if interp.store_interpretation_changes:
        rule_trace.append((t_cnt, fp_cnt, comp, na[0], interval.closed(0, 1),
                           False, triggered_by, actual_name, msg))
        if interp.atom_trace:
            if mode == 'rule':
                qn, qe, _ = rules_to_be_applied_trace[idx]
            else:
                qn, qe = [], []
            _update_rule_trace(rule_trace_atoms, qn, qe, world.world[na[0]], actual_name)

    world.world[na[0]].set_lower_upper(0, 1)
    world.world[na[0]].set_static(True)
    for p1, p2 in interp.ipl:
        if p1 == na[0]:
            if interp.atom_trace:
                _update_rule_trace(rule_trace_atoms, [], [], world.world[p2], actual_name)
            world.world[p2].set_lower_upper(0, 1)
            world.world[p2].set_static(True)
            if interp.store_interpretation_changes:
                rule_trace.append((t_cnt, fp_cnt, comp, p2, interval.closed(0, 1),
                                   False, 'IPL', actual_name, msg))
        if p2 == na[0]:
            if interp.atom_trace:
                _update_rule_trace(rule_trace_atoms, [], [], world.world[p1], actual_name)
            world.world[p1].set_lower_upper(0, 1)
            world.world[p1].set_static(True)
            if interp.store_interpretation_changes:
                rule_trace.append((t_cnt, fp_cnt, comp, p1, interval.closed(0, 1),
                                   False, 'IPL', actual_name, msg))


def resolve_inconsistency_node(interp, interpretations, comp, na, t_cnt, fp_cnt,
                               idx, rule_trace, rule_trace_atoms,
                               rules_to_be_applied_trace, facts_to_be_applied_trace,
                               mode):
    _resolve_inconsistency(interp, interpretations, comp, na, t_cnt, fp_cnt, idx,
                           rule_trace, rule_trace_atoms, rules_to_be_applied_trace,
                           facts_to_be_applied_trace, mode, comp_str=f'{comp}')


def resolve_inconsistency_edge(interp, interpretations, comp, na, t_cnt, fp_cnt,
                               idx, rule_trace, rule_trace_atoms,
                               rules_to_be_applied_trace, facts_to_be_applied_trace,
                               mode):
    _resolve_inconsistency(interp, interpretations, comp, na, t_cnt, fp_cnt, idx,
                           rule_trace, rule_trace_atoms, rules_to_be_applied_trace,
                           facts_to_be_applied_trace, mode,
                           comp_str=f'{comp[0]},{comp[1]}')


def _add_node(interp, node, interpretations_node):
    """Add one node to the shared graph state, its world into the CALLER'S
    world dict — the whole dict on the default schedule, the current
    timestep's on the fp schedule. The presence guard is the fp variant's
    (interpretation_fp.py:2197-2203); on the default schedule a node absent
    from `nodes` is never in the dict, so the guard changes nothing there."""
    interp.nodes.append(node)
    interp.neighbors[node] = []
    interp.reverse_neighbors[node] = []
    if node not in interpretations_node:
        interpretations_node[node] = World([])


def _add_edge(interp, source, target, l, t, interpretations_node,
              interpretations_edge):
    """interpretation.py:2095-2134 / interpretation_fp.py:2216-2254 — the
    bodies differ only in the fp variant's presence guard and its dropped
    ground-atom counting (gated on interp.fp_mode here)."""
    if source not in interp.nodes:
        _add_node(interp, source, interpretations_node)
    if target not in interp.nodes:
        _add_node(interp, target, interpretations_node)

    edge = (source, target)
    new_edge = False
    if edge not in interp.edges:
        new_edge = True
        interp.edges.append(edge)
        interp.neighbors[source].append(target)
        interp.reverse_neighbors[target].append(source)
        if l.get_value() != '':
            if edge not in interpretations_edge:
                interpretations_edge[edge] = World([l])
            if not interp.fp_mode:
                interp.num_ga[t] += 1
            if l in interp.predicate_map_edge:
                interp.predicate_map_edge[l].append(edge)
            else:
                interp.predicate_map_edge[l] = [edge]
        else:
            interpretations_edge[edge] = World([])
    else:
        if l not in interpretations_edge[edge].world and l.get_value() != '':
            new_edge = True
            interpretations_edge[edge].world[l] = interval.closed(0, 1)
            if not interp.fp_mode:
                interp.num_ga[t] += 1
            if l in interp.predicate_map_edge:
                interp.predicate_map_edge[l].append(edge)
            else:
                interp.predicate_map_edge[l] = [edge]

    return edge, new_edge


def _add_edges(interp, sources, targets, l, t, interpretations_node,
               interpretations_edge):
    changes = 0
    edges_added = []
    for source in sources:
        for target in targets:
            edge, new_edge = _add_edge(interp, source, target, l, t,
                                       interpretations_node, interpretations_edge)
            edges_added.append(edge)
            changes = changes + 1 if new_edge else changes
    return edges_added, changes


def float_to_str(value):
    """The pinned manual float formatter (interpretation.py:2181-2200) —
    three-decimal fixed point, used in inconsistency messages and the
    delta-bound convergence print."""
    number = int(value)
    decimal = int(round(abs(value) % 1 * 1000))
    if decimal < 10:
        decimal_str = f'00{decimal}'
    elif decimal < 100:
        decimal_str = f'0{decimal}'
    else:
        decimal_str = f'{decimal}'
    if value < 0 and number == 0:
        return f'-{number}.{decimal_str}'
    return f'{number}.{decimal_str}'
