"""The rule-text DSL parser — validating entry point for `pyreason.Rule`.

Behavior target: the pinned oracle's rule parser (oracle
scripts/utils/rule_parser.py), whose rejection behavior and exact message
text are banked by the rule-text-malformed case. The control flow mirrors
the pin statement-for-statement; the numba containers become plain lists,
the weights ndarray becomes a plain float list (np.array conversion
semantics mimicked on list input — the arm the public constructor exposes —
including rectangular nested lists and None-to-NaN, see _weights_to_floats),
and delta is a plain int wrapped modulo 2**16 (the pinned uint16 cast).

Pinned quirks kept on purpose (equivalence first, per AC-6):
- every leading digit of the body is consumed as one integer, so '<-10'
  means delta_t=10, not a malformed arrow;
- an empty body is a valid always-fires rule;
- bound-shaped-but-malformed head suffixes re-raise with the trailing
  "Note: Annotation function names cannot contain brackets" sentence;
- a node rule silently forces infer_edges off.
"""

import math
import re

from . import interval
from ._rule_ir import RuleIR
from .label import Label
from .threshold import Threshold


def parse_rule(rule_text, name, custom_thresholds, infer_edges=False,
               set_static=False, weights=None) -> RuleIR:
    # --- Entry-point validation ---
    if not isinstance(rule_text, str):
        raise TypeError(f"rule_text must be a string, got {type(rule_text).__name__}")

    if not rule_text.strip():
        raise ValueError("rule_text cannot be empty or whitespace only")

    arrow_count = rule_text.count('<-')
    if arrow_count != 1:
        raise ValueError(
            f"Rule must contain exactly one '<-' separator, found {arrow_count}. "
            "Use the format: 'head(X) <- body(X)'"
        )

    # First remove all spaces from line
    rule_str = rule_text.replace(' ', '')

    # Separate into head and body
    head, body = rule_str.split('<-')

    if not head:
        raise ValueError("Rule head cannot be empty")

    # Handle empty body (valid rule - always fires unconditionally)
    if not body:
        delta_t = 0
        body_clauses = []
        body_bounds = []
    else:
        # Extract delta_t of rule if it exists else set it to 0 — every
        # leading digit is consumed as one integer (the pinned behavior)
        delta_t = ''
        is_digit = True
        while is_digit:
            if body[0].isdigit():
                delta_t += body[0]
                body = body[1:]
            else:
                is_digit = False

        if delta_t == '':
            delta_t = 0
        else:
            # The pinned constructor casts through numba.types.uint16
            # (rule_parser.py:243 at the pin), so the stored delta wraps
            # modulo 2**16: '<-65536' means delta_t=0 and '<-70000' means
            # 4464 — banked by the rule-delta-variants case fingerprints.
            delta_t = int(delta_t) % 65536

        # Split the body into clauses and their bounds
        body_clauses, body_bounds = _split_body_into_clauses(body)

    # Handle forall quantifier in body clauses
    for i, clause_str in enumerate(body_clauses.copy()):
        if 'forall(' in clause_str:
            if not clause_str.endswith(')'):
                raise ValueError(f"Malformed forall expression: '{clause_str}'. Expected 'forall(pred(vars))'")
            inner = clause_str[:-1].replace('forall(', '', 1)
            if '(' not in inner or ')' not in inner:
                raise ValueError(f"forall expression must contain an inner predicate with variables, got 'forall({inner})'")
            if not custom_thresholds:
                custom_thresholds = {}
            custom_thresholds[i] = Threshold("greater_equal", ("percent", "total"), 100)
            body_clauses[i] = inner

    # Parse the head: target predicate, bound, annotation function, and head-negation flag
    head, target_bound, ann_fn, head_negated = _parse_head(head)

    idx = head.find('(')
    target = head[:idx]
    _validate_predicate_name(target, "Head")
    target = Label(target)

    # Variable(s) in the head of the rule — supports functions like f(X, Y);
    # the last ')' bounds the argument string so nested calls survive
    end_idx = head.rfind(')')
    head_args_str = head[idx + 1:end_idx]

    head_variables, head_fns, head_fns_vars = _parse_head_arguments(head_args_str)

    if len(head_variables) < 1:
        raise ValueError("Rule head must contain at least one argument inside parentheses")

    for var in head_variables:
        _validate_component_name(var, "Head")

    # Assign type of rule
    rule_type = 'node' if len(head_variables) == 1 else 'edge'

    # Get the predicates and variables in the body. If there's an operator in
    # a clause, anything after the operator is discarded but its variables kept.
    body_predicates = []
    body_variables = []
    for clause_str in body_clauses:
        start_idx = clause_str.find('(')
        if start_idx == -1:
            raise ValueError(f"Body clause '{clause_str}' must contain parentheses around argument")

        end_idx = clause_str.find(')')
        if end_idx == -1:
            raise ValueError(f"Body clause '{clause_str}' is missing closing parenthesis")
        pred_name = clause_str[:start_idx]
        _validate_predicate_name(pred_name, "Body")
        body_predicates.append(pred_name)

        variables = clause_str[start_idx+1:end_idx].split(',')
        start_idx = clause_str.find('(', start_idx+1)
        end_idx = clause_str.find(')', end_idx+1)
        if start_idx != -1 and end_idx != -1:
            variables += clause_str[start_idx+1:end_idx].split(',')
        for var in variables:
            _validate_component_name(var, "Body")
        body_variables.append(variables)

    # A node rule never infers edges (pinned silent override)
    if rule_type == 'node':
        infer_edges = False

    # Thresholds: one (comparison, (number|percent, total|available), thresh)
    # tuple per clause
    thresholds = []

    num_clauses = len(body_clauses)

    if isinstance(custom_thresholds, list):
        if len(custom_thresholds) != num_clauses:
            raise ValueError(f'The length of custom thresholds {len(custom_thresholds)} is not equal to number of clauses {num_clauses}')
        for threshold in custom_thresholds:
            thresholds.append(threshold.to_tuple())
    elif isinstance(custom_thresholds, dict):
        if len(custom_thresholds) == 0:
            raise ValueError("custom_thresholds dict cannot be empty. Use None for default thresholds")
        if any(k < 0 for k in custom_thresholds.keys()):
            raise ValueError("custom_thresholds dict keys must be non-negative integers")
        if max(custom_thresholds.keys()) >= num_clauses:
            raise ValueError(f'The max clause index in the custom thresholds map {max(custom_thresholds.keys())} is greater than number of clauses {num_clauses}')
        for i in range(num_clauses):
            if i in custom_thresholds:
                thresholds.append(custom_thresholds[i].to_tuple())
            else:
                thresholds.append(('greater_equal', ('number', 'total'), 1.0))
    elif not custom_thresholds:
        for _ in range(num_clauses):
            thresholds.append(('greater_equal', ('number', 'total'), 1.0))

    # Clauses: (node|edge|comparison, label, [variables], interval, operator)
    clauses = []
    for body_clause, predicate, variables, bounds in zip(body_clauses, body_predicates, body_variables, body_bounds):
        clause_type = 'node' if len(variables) == 1 else 'edge'
        op = _get_operator_from_clause(body_clause)
        if op:
            clause_type = 'comparison'

        clauses.append((clause_type, Label(predicate), list(variables),
                        interval.closed(bounds[0], bounds[1]), op))

    # Edges between head variables when inferring
    if infer_edges:
        edges = (head_variables[0], head_variables[1], target)
    else:
        edges = ('', '', Label(''))

    if weights is None:
        weights = [1.0] * len(body_predicates)
    else:
        # The pinned parser converts through np.array(weights, dtype=float64)
        # (rule_parser.py:208-212 at the pin), which accepts more than a flat
        # float list: rectangular NESTED numeric lists convert to a 2-D array
        # whose len() is its top-level row count (so [[1,2]] passes a
        # one-clause length check — banked by rule-json-weights-dtypes'
        # weights-nested probe), and None converts to NaN (taking the
        # finiteness raise, not the conversion raise). _weights_to_floats
        # mimics exactly those observable arms; every conversion fault takes
        # the pinned TypeError below, and the length/finiteness/sign checks
        # run over top-level length and flattened leaves the way the pinned
        # ndarray checks do.
        try:
            weights = _weights_to_floats(weights)
        except (ValueError, TypeError):
            raise TypeError(f"weights must be a numpy array or convertible to one, got {type(weights).__name__}")

        if len(weights) != len(body_predicates):
            raise ValueError(f'Number of weights {len(weights)} is not equal to number of clauses {len(body_predicates)}')

        leaves = list(_flat_weights(weights))
        if not all(math.isfinite(w) for w in leaves):
            raise ValueError("weights must contain only finite values (no NaN or Inf)")

        if any(w < 0 for w in leaves):
            raise ValueError("weights must be non-negative")

    return RuleIR(name, rule_type, target, list(head_variables), delta_t,
                  clauses, target_bound, thresholds, ann_fn, weights,
                  list(head_fns), [list(v) for v in head_fns_vars], edges,
                  set_static, head_negated)


def _weights_to_floats(w):
    """Convert one weights list the way np.array(w, dtype=float64) does,
    for the leaf types JSON input can carry (the arm the public constructor
    and the JSON rule loader expose): numbers, numeric strings, and booleans
    convert through float(); None converts to NaN (np fills nan, so a [None]
    weight takes the FINITENESS raise, not the conversion raise — verified
    against the pinned numpy 2026-07-12); nested lists must be rectangular
    (np raises ValueError on ragged input) and keep their structure, so
    len() of the result is the top-level row count exactly as len(ndarray)
    is shape[0]. Any other leaf (dict, non-numeric string) raises — the
    caller re-wraps every conversion fault as the pinned TypeError."""
    if isinstance(w, list):
        converted = [_weights_to_floats(x) for x in w]
        shapes = {_weights_shape(x) for x in converted}
        if len(shapes) > 1:
            raise ValueError("setting an array element with a sequence")
        return converted
    if w is None:
        return float("nan")
    return float(w)


def _weights_shape(w):
    """The nested-list shape of an already-converted weights entry — leaves
    are (), lists are (len, *inner) — rectangularity was enforced during
    conversion, so the first element's shape stands for all."""
    if isinstance(w, list):
        return (len(w),) + (_weights_shape(w[0]) if w else ())
    return ()


def _flat_weights(w):
    """Every leaf float of a (possibly nested) converted weights list — the
    iteration order np's elementwise isfinite/sign checks reduce over."""
    if isinstance(w, list):
        for x in w:
            yield from _flat_weights(x)
    else:
        yield w


def _split_body_into_clauses(body):
    """Split the body string into (body_clauses, body_bounds) lists.

    Uses the pinned double-character trick to split on clause boundaries
    without destroying closing delimiters that are part of clause content:
      1. Double-up ')' and ']' so that splitting on '),' or '],' always
         leaves one copy of the delimiter inside the clause string.
      2. Split first on '),' then on '],' to handle both unbracketed and
         bracketed clause endings.
      3. Restore the original single characters.
      4. Attach default bounds :[1,1] (or :[0,0] for negated clauses).
      5. Split each clause on ':' to separate predicate from bound.
    """
    # Convert :True/:False shorthand to numeric bounds before splitting
    # (case-insensitive) — must happen before delimiter doubling so clauses
    # end with ']' for correct splitting
    body_lower = body.lower()
    new_body = []
    i = 0
    while i < len(body):
        if body_lower[i:i + 5] == ':true' and (i + 5 >= len(body) or body[i + 5] in ',)'):
            new_body.append(':[1,1]')
            i += 5
        elif body_lower[i:i + 6] == ':false' and (i + 6 >= len(body) or body[i + 6] in ',)'):
            new_body.append(':[0,0]')
            i += 6
        else:
            new_body.append(body[i])
            i += 1
    body = ''.join(new_body)

    # Double-up closing delimiters so splitting on ")," / "]," is safe
    body = body.replace(')', '))')
    body = body.replace(']', ']]')

    # Split on clause boundaries: first '),' then '],'
    body = body.split('),')
    split_body = []
    for part in body:
        split_body.extend(part.split('],'))

    # Restore original single delimiters
    for i in range(len(split_body)):
        split_body[i] = split_body[i].replace('))', ')')
        split_body[i] = split_body[i].replace(']]', ']')

    # Check for empty or malformed clauses (trailing commas, double commas)
    for i, part in enumerate(split_body):
        stripped = part.lstrip(',')
        if not stripped:
            raise ValueError(f"Body clause {i} is empty. Check for trailing commas or double commas in the rule body")
        # Leading comma indicates consecutive commas in the original rule
        if stripped != part:
            raise ValueError(f"Body clause {i} is empty. Check for trailing commas or double commas in the rule body")

    # Check for double negation in body clauses
    for part in split_body:
        if part.startswith('~~'):
            raise ValueError(f"Double negation '~~' is not allowed in body clause '{part}'")

    # Attach default bounds: negated clauses get [0,0], others get [1,1];
    # negated clauses with explicit bounds are flagged for [1-u, 1-l]
    negate_body_flags = [False] * len(split_body)
    for i in range(len(split_body)):
        if split_body[i][0] == '~':
            if split_body[i][-1] == ']':
                split_body[i] = split_body[i][1:]
                negate_body_flags[i] = True
            else:
                split_body[i] = split_body[i][1:] + ':[0,0]'
        elif split_body[i][-1] != ']':
            split_body[i] += ':[1,1]'

    # Separate each clause into predicate and bound string
    body_clauses = []
    body_bounds = []
    for part in split_body:
        parts = part.split(':')
        if len(parts) != 2:
            raise ValueError(f"Body clause '{part}' has invalid format: expected exactly one ':' separating predicate from bound")
        clause_str, bound_str = parts
        body_clauses.append(clause_str)
        body_bounds.append(bound_str)

    # Convert bound strings to [lower, upper] float pairs
    for i in range(len(body_bounds)):
        bound_str = body_bounds[i]
        lower, upper = _str_bound_to_bound(bound_str)
        # Apply negation inversion: ~[l,u] = [1-u, 1-l]
        if negate_body_flags[i]:
            lower, upper = round(1 - upper, 10), round(1 - lower, 10)
        body_bounds[i] = [lower, upper]

    return body_clauses, body_bounds


def _parse_head(head):
    """Parse the head string into (head_str, target_bound, ann_fn, negated).

    Possible head formats:
      - pred(x)            → default bound [1,1], no annotation
      - ~pred(x)           → negated bound [0,0]
      - pred(x):[l,u]      → explicit bound
      - ~pred(x):[l,u]     → negated explicit bound
      - pred(x):fn_name    → annotation function with default bound [0,1]
    """
    # Check for double negation in head
    if head.startswith('~~'):
        raise ValueError(f"Double negation '~~' is not allowed in rule head '{head}'")

    if '(' not in head:
        raise ValueError(f"Rule head '{head}' must contain parentheses around variables")
    if ')' not in head:
        raise ValueError(f"Rule head '{head}' is missing closing parenthesis")

    # At most one colon allowed in head
    colon_count = head.count(':')
    if colon_count > 1:
        raise ValueError(f"Rule head contains {colon_count} colons, expected at most 1")

    # Strip a leading '~' up front so the suffix handling is uniform across
    # all forms; the [1-u, 1-l] inversion applies to the resolved bound below
    negate_head_interval = False
    if head[0] == '~':
        head = head[1:]
        negate_head_interval = True

    # Convert :True/:False shorthand to numeric bounds (case-insensitive)
    if colon_count == 1:
        colon_idx = head.index(':')
        suffix = head[colon_idx + 1:]
        if suffix.lower() == 'true':
            head = head[:colon_idx] + ':[1,1]'
        elif suffix.lower() == 'false':
            head = head[:colon_idx] + ':[0,0]'

    # If no colon present, attach default bound [1,1] (negation flips to [0,0])
    if head[-1] == ')':
        head += ':[1,1]'

    head_str, head_bound_str = head.split(':')

    # Determine if head_bound_str is a numeric bound or an annotation function name
    if _is_bound(head_bound_str):
        target_bound = list(_str_bound_to_bound(head_bound_str))
        if negate_head_interval:
            target_bound = [round(1 - target_bound[1], 10), round(1 - target_bound[0], 10)]
        target_bound = interval.closed(target_bound[0], target_bound[1])
        ann_fn = ''
    else:
        # If it looks like a bound (has brackets) but failed _is_bound, it's malformed
        if '[' in head_bound_str and ']' in head_bound_str:
            try:
                _str_bound_to_bound(head_bound_str)
            except ValueError as e:
                raise ValueError(
                    f"{e}. Note: Annotation function names cannot contain brackets '[' or ']'"
                )
        # Annotation function: default bound is [0,1]; ~[0,1] = [0,1] is a
        # no-op at parse time — the head_negated flag carries the negation
        target_bound = interval.closed(0, 1)
        ann_fn = head_bound_str

    return head_str, target_bound, ann_fn, negate_head_interval


def _parse_head_arguments(head_args_str):
    """Parse head arguments — simple variables or function calls.

    Examples:
        "X"            → (['X'], [''], [[]])
        "X, Y"         → (['X', 'Y'], ['', ''], [[], []])
        "f(X, Y)"      → (['__temp_var_0'], ['f'], [['X', 'Y']])
        "f(X, Y), Z"   → (['__temp_var_0', 'Z'], ['f', ''], [['X', 'Y'], []])
    """
    head_variables = []
    head_fns = []
    head_fns_vars = []

    if not head_args_str:
        return head_variables, head_fns, head_fns_vars

    # Split arguments by comma, respecting nested parentheses
    args_list = []
    current_arg = ''
    paren_count = 0

    for char in head_args_str:
        if char == '(':
            paren_count += 1
            current_arg += char
        elif char == ')':
            paren_count -= 1
            current_arg += char
        elif char == ',' and paren_count == 0:
            args_list.append(current_arg.strip())
            current_arg = ''
        else:
            current_arg += char

    if current_arg.strip():
        args_list.append(current_arg.strip())

    for arg in args_list:
        arg = arg.strip()

        if '(' in arg and ')' in arg:
            # Function call: extract name and arguments
            paren_idx = arg.find('(')
            fn_name = arg[:paren_idx]

            fn_args_str = arg[paren_idx + 1:arg.rfind(')')]
            fn_args = [a.strip() for a in fn_args_str.split(',') if a.strip()]

            temp_var = f'__temp_var_{len(head_variables)}'

            head_variables.append(temp_var)
            head_fns.append(fn_name)
            head_fns_vars.append(fn_args)
        else:
            head_variables.append(arg)
            head_fns.append('')
            head_fns_vars.append([])

    return head_variables, head_fns, head_fns_vars


_PREDICATE_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.\-]*$')
_COMPONENT_RE = re.compile(r'^[a-zA-Z0-9_][a-zA-Z0-9_.@\-]*$')


def _validate_predicate_name(pred, context):
    """Validate that a predicate name matches ^[a-zA-Z_][a-zA-Z0-9_.\\-]*$."""
    if not _PREDICATE_RE.match(pred):
        if pred and pred[0].isdigit():
            raise ValueError(f"{context} predicate name '{pred}' cannot start with a digit")
        raise ValueError(f"{context} predicate name '{pred}' contains invalid characters. Must match [a-zA-Z_][a-zA-Z0-9_.\\-]*")


def _validate_component_name(var, context):
    """Validate that a component name matches ^[a-zA-Z0-9_][a-zA-Z0-9_.@\\-]*$."""
    if not _COMPONENT_RE.match(var):
        raise ValueError(f"{context} component name '{var}' contains invalid characters. Must match [a-zA-Z0-9_][a-zA-Z0-9_.@\\-]*")


def _str_bound_to_bound(str_bound):
    """Convert a string bound like '[0.5,0.8]' to (float, float).

    Validates exactly 2 comma-separated numeric finite values in [0, 1]
    with lower <= upper.
    """
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    parts = str_bound.split(',')

    if len(parts) != 2:
        raise ValueError(f"Bound must contain exactly 2 values, got {len(parts)}: '{str_bound}'")

    lower_str, upper_str = parts

    try:
        lower = float(lower_str)
    except ValueError:
        raise ValueError(f"Bound lower value must be numeric, got '{lower_str}'")
    try:
        upper = float(upper_str)
    except ValueError:
        raise ValueError(f"Bound upper value must be numeric, got '{upper_str}'")

    if math.isnan(lower):
        raise ValueError(f"Bound lower value must be a number, got '{lower_str}'")
    if math.isnan(upper):
        raise ValueError(f"Bound upper value must be a number, got '{upper_str}'")

    if lower < 0 or lower > 1:
        raise ValueError(f"Bound lower value {lower} is out of range [0, 1]")
    if upper < 0 or upper > 1:
        raise ValueError(f"Bound upper value {upper} is out of range [0, 1]")

    if lower > upper:
        raise ValueError(f"Bound lower value {lower} is greater than upper value {upper}")

    return lower, upper


def _is_bound(str_bound):
    """Whether str_bound looks like a numeric bound (e.g. '[0.5,0.8]')
    rather than an annotation function name — float() parsing, so negative
    numbers and scientific notation count as numeric."""
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    try:
        lower, upper = str_bound.split(',')
        float(lower)
        float(upper)
        result = True
    except (ValueError, AttributeError):
        result = False

    return result


def _get_operator_from_clause(clause):
    operators = ['<=', '>=', '<', '>', '==', '!=']
    for op in operators:
        if op in clause:
            return op

    # No operator found in clause
    return ''
