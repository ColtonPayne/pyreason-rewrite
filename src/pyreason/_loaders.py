"""The loader family — file-taking entry points over the explicit state.

Behavior target: the pinned oracle loaders (oracle pyreason.py:652-690 for
the rules text file, :753-866 CSV rules, :868-1077 JSON rules, :1168-1292
JSON facts, :1294-1412 CSV facts), whose raise/warn/skip arms and exact
message text are banked by the five loader-family malformed cases. Control
flow mirrors the pin per function: row/item-level ValueErrors re-wrap with
the doubled Row/Item prefix, raise_errors=False arms warn and skip, and
partial loads before a raise stay loaded (pinned state behavior, observed
through get_rules).

The pinned CSV loaders read through pandas
(read_csv(header=None, dtype=str, keep_default_na=False)); this package
reads through the stdlib csv module and reproduces the observable pandas
behaviors the banked artifacts pin: the wrapped 'CSV file not found' /
'Error reading CSV file' / empty-file-warn arms, blank-line skipping, and
the C-tokenizer message for a row with more fields than the first row
(hand-matched text, see _TOKENIZER_MSG; the message's line number is the
record ordinal, see _numbered_rows). A row with FEWER fields than the first
row is padded with '' here, matching the pinned pandas read
(keep_default_na=False reads missing trailing cells as '', not NaN —
verified empirically: a short row missing its name cell autonames rule_<n>
identically in both engines; session-16 review probe).
"""

import csv
import json
import warnings

from ._state import EngineState, add_fact, add_rule
from .fact import Fact
from .rule import Rule
from .threshold import Threshold

# The pinned pandas C-tokenizer text, trailing newline included
# (pandas.errors.ParserError str at the pin) — reproduced verbatim so the
# wrapped ValueError compares equal. Hand-matched against the banked
# rule-from-csv-malformed 'unquoted-comma' artifact.
_TOKENIZER_MSG = "Error tokenizing data. C error: Expected {expected} fields in line {line}, saw {saw}\n"


class _EmptyCsvError(Exception):
    """A CSV file with no parseable rows — the pinned pandas EmptyDataError
    equivalence class (zero-byte or blank-lines-only files)."""


class _TokenizeError(Exception):
    """A row wider than the first row — the pinned pandas ParserError
    equivalence class; str(exc) carries the pinned tokenizer text."""


def _read_csv_rows(csv_path):
    """Read a CSV the way the pinned loaders observe pandas' output: a list
    of string rows, blank lines skipped, the first row fixing the field
    count, every row padded to that count."""
    with open(csv_path, 'r', newline='') as f:
        raw_rows = [(f_line_num, row) for f_line_num, row
                    in _numbered_rows(csv.reader(f)) if row]
    if not raw_rows:
        raise _EmptyCsvError
    expected = len(raw_rows[0][1])
    rows = []
    for line_num, row in raw_rows:
        if len(row) > expected:
            raise _TokenizeError(_TOKENIZER_MSG.format(
                expected=expected, line=line_num, saw=len(row)))
        rows.append(row + [''] * (expected - len(row)))
    return rows


def _numbered_rows(reader):
    """Each parsed row with the line number the pinned tokenizer message
    reports: the record ordinal, NOT the physical line — a blank line counts
    one record, a quoted field spanning physical lines counts once (verified
    against the pinned pandas C tokenizer: 'line 2' for a wide row after a
    two-physical-line quoted record, 'line 5' after three blank lines;
    csv.reader.line_num counts physical lines and diverges on quoted
    multi-line records)."""
    for record_ordinal, row in enumerate(reader, start=1):
        yield record_ordinal, row


def _read_csv(csv_path, kind: str):
    """The shared read-and-wrap choke point for both CSV loaders: pinned
    outer messages, with `kind` filling the rules/facts wording. Returns the
    row list, or None for the pinned warn-and-return empty-file arm."""
    try:
        return _read_csv_rows(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    except _EmptyCsvError:
        warnings.warn(f"CSV file {csv_path} is empty, no {kind} loaded")
        return None
    except (_TokenizeError, csv.Error, OSError, UnicodeDecodeError) as e:
        # The pinned loader wraps any other read fault into ValueError
        # (pyreason.py:795-796/:1340-1341). UnicodeDecodeError must be named
        # here: it subclasses ValueError, so without it a non-UTF8 file's
        # decode fault would propagate raw instead of taking the pinned wrap
        # (the codec text itself matches the oracle's byte-for-byte —
        # session-16 review probe).
        raise ValueError(f"Error reading CSV file {csv_path}: {e}")


def _parse_bool_param(raw_value, param_name, idx, raise_errors, item_label="Item", default=False):
    """Parse a raw loader cell as a boolean — the pinned coercion table
    (oracle pyreason.py:692-724): true/1/yes/t/y and false/0/no/f/n
    case-insensitively, empty means default, numbers truthy-coerce, anything
    else raises (raise_errors) or warns and defaults."""
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        val_str = raw_value.strip().lower()
        if val_str in ('true', '1', 'yes', 't', 'y'):
            return True
        elif val_str in ('false', '0', 'no', 'f', 'n', ''):
            return default if val_str == '' else False
        else:
            if raise_errors:
                raise ValueError(f"{item_label} {idx}: Invalid {param_name} value '{raw_value}'")
            warnings.warn(f"{item_label} {idx}: Invalid {param_name} value '{raw_value}', using default value")
            return default
    if isinstance(raw_value, (int, float)):
        return bool(raw_value)
    if raise_errors:
        raise ValueError(f"{item_label} {idx}: Invalid {param_name} value type '{type(raw_value).__name__}'")
    warnings.warn(f"{item_label} {idx}: Invalid {param_name} value type '{type(raw_value).__name__}', using default value")
    return default


def _parse_and_validate_rule_params(idx, name_raw, infer_edges_raw, set_static_raw, raise_errors, item_label="Item"):
    """Parse one loader row/item's rule parameters — pinned semantics
    (oracle pyreason.py:727-750): empty/whitespace names become None, the
    two flags go through the shared boolean table."""
    name = None
    if name_raw is not None:
        name = str(name_raw).strip() if str(name_raw).strip() else None

    infer_edges = _parse_bool_param(infer_edges_raw, 'infer_edges', idx, raise_errors, item_label, default=False)
    set_static = _parse_bool_param(set_static_raw, 'set_static', idx, raise_errors, item_label, default=False)

    return name, infer_edges, set_static


def _parse_and_validate_fact_params(idx, name_raw, start_time_raw, end_time_raw, static_raw, raise_errors, item_label="Item"):
    """Parse one loader row/item's fact parameters — pinned semantics
    (oracle pyreason.py:1080-1119): empty names become None, times
    int-convert with 0 defaults (a failed end_time defaults to start_time
    on the warn path), static goes through the shared boolean table."""
    name = None
    if name_raw is not None:
        name = str(name_raw).strip() if str(name_raw).strip() else None

    try:
        start_time = int(start_time_raw) if start_time_raw is not None and str(start_time_raw).strip() else 0
    except (ValueError, TypeError, AttributeError):
        if raise_errors:
            raise ValueError(f"{item_label} {idx}: Invalid start_time '{start_time_raw}'")
        warnings.warn(f"{item_label} {idx}: Invalid start_time '{start_time_raw}', using default value")
        start_time = 0

    try:
        end_time = int(end_time_raw) if end_time_raw is not None and str(end_time_raw).strip() else 0
    except (ValueError, TypeError, AttributeError):
        if raise_errors:
            raise ValueError(f"{item_label} {idx}: Invalid end_time '{end_time_raw}'")
        warnings.warn(f"{item_label} {idx}: Invalid end_time '{end_time_raw}', using default value")
        end_time = start_time

    static = _parse_bool_param(static_raw, 'static', idx, raise_errors, item_label, default=False)

    return name, start_time, end_time, static


def _cell(row, k):
    """Column k of a padded row, None when the file has fewer columns — the
    shape the pinned loaders see from a narrow DataFrame."""
    return row[k] if len(row) > k else None


def add_rules_from_file(state: EngineState, file_path: str,
                        infer_edges: bool = False, raise_errors: bool = False) -> None:
    """Add rules from a text file: one rule per non-empty non-# line.

    Pinned semantics (oracle pyreason.py:652-690): names are
    rule_<line index + preexisting rule count>, where the index runs over
    the FILTERED line list and advances even for failed lines — the pinned
    name-gap behavior; raise_errors=True wraps the first failure as
    ValueError('Line <n>: ...') AFTER earlier lines loaded; the default
    warns and skips.
    """
    with open(file_path, 'r') as file:
        rules = [line.rstrip() for line in file if line.rstrip() != '' and line.rstrip()[0] != '#']

    loaded_count = 0
    error_count = 0

    rule_offset = 0 if state.rules is None else len(state.rules)
    for i, r in enumerate(rules):
        try:
            add_rule(state, Rule(r, f'rule_{i+rule_offset}', infer_edges))
            loaded_count += 1
        except Exception as e:
            if raise_errors:
                raise ValueError(f"Line {i + 1}: Failed to parse rule '{r}' - {e}") from e
            error_count += 1
            warnings.warn(f"Line {i + 1}: Failed to parse rule '{r}' - {e}")

    if state.settings.verbose:
        print(f"Loaded {loaded_count} rules from {file_path}")
        if error_count > 0:
            print(f"Failed to load {error_count} rules due to errors")


def add_rule_from_csv(state: EngineState, csv_path: str, raise_errors: bool = True) -> None:
    """Load rules from a CSV of rows `rule_text, name, infer_edges, set_static`
    (header row optional, matched exactly).

    Pinned semantics (oracle pyreason.py:753-866): row-level ValueErrors
    re-wrap as 'Row <n>: Failed to parse rule - <inner>' (doubled prefix);
    duplicate names within one file raise/warn AFTER earlier rows loaded;
    a missing file, an empty file, and an unreadable file take the three
    outer arms in _read_csv.
    """
    rows = _read_csv(csv_path, "rules")
    if rows is None:
        return

    expected_header = ['rule_text', 'name', 'infer_edges', 'set_static']
    first_row = [str(v).strip() for v in rows[0]]
    has_header = first_row == expected_header
    start_idx = 1 if has_header else 0

    loaded_count = 0
    error_count = 0
    loaded_name_set = set()

    for idx, row in enumerate(rows[start_idx:], start=start_idx):
        try:
            if len(row) < 1 or not str(row[0]).strip():
                if raise_errors:
                    raise ValueError(f"Row {idx + 1}: Missing required 'rule_text'")
                warnings.warn(f"Row {idx + 1}: Missing required 'rule_text', skipping row")
                error_count += 1
                continue

            rule_text = str(row[0]).strip()

            name, infer_edges, set_static = _parse_and_validate_rule_params(
                idx + 1, _cell(row, 1), _cell(row, 2), _cell(row, 3),
                raise_errors, "Row")

            if name and name in loaded_name_set:
                if raise_errors:
                    raise ValueError(f"Row {idx + 1}: Loaded name '{name}' is a duplicate - all rule names must be unique.")
                warnings.warn(f"Row {idx + 1}: Loaded name '{name}' is a duplicate - all rule names must be unique.")
                error_count += 1
                continue
            if name:
                loaded_name_set.add(name)

            r = Rule(rule_text=rule_text, name=name, infer_edges=infer_edges, set_static=set_static)
            add_rule(state, r)
            loaded_count += 1

        except ValueError as e:
            if raise_errors:
                raise ValueError(f"Row {idx + 1}: Failed to parse rule - {e}") from e
            error_count += 1
            warnings.warn(f"Row {idx + 1}: Failed to parse rule - {e}")
        except Exception as e:
            if raise_errors:
                raise Exception(f"Row {idx + 1}: Unexpected error - {e}") from e
            error_count += 1
            warnings.warn(f"Row {idx + 1}: Unexpected error - {e}")

    if state.settings.verbose:
        print(f"Loaded {loaded_count} rules from {csv_path}")
        if error_count > 0:
            print(f"Failed to load {error_count} rules due to errors")


def add_rule_from_json(state: EngineState, json_path: str, raise_errors: bool = True) -> None:
    """Load rules from a JSON array of rule objects (rule_text required;
    name, infer_edges, set_static, custom_thresholds, weights optional).

    Pinned semantics (oracle pyreason.py:868-1077): document-level faults
    (missing file, bad syntax, non-array) raise before any item loads;
    item-level ValueErrors re-wrap as 'Item <n>: Failed to parse rule -
    <inner>' (doubled prefix); threshold construction faults surface the
    inner KeyError/ValueError/TypeError text inside an
    'Item <n>, threshold <k>: Invalid threshold - <e>' wrap.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in file {json_path}: {e}")
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError(f"Error reading JSON file {json_path}: {e}")

    if not isinstance(data, list):
        raise ValueError(f"JSON file must contain an array of rule objects, got {type(data).__name__}")

    if len(data) == 0:
        warnings.warn(f"JSON file {json_path} contains an empty array, no rules loaded")
        return

    loaded_count = 0
    error_count = 0
    loaded_name_set = set()

    for idx, rule_obj in enumerate(data):
        try:
            if not isinstance(rule_obj, dict):
                if raise_errors:
                    raise ValueError(f"Item {idx}: Expected object, got {type(rule_obj).__name__}")
                warnings.warn(f"Item {idx}: Expected object, got {type(rule_obj).__name__}, skipping item")
                error_count += 1
                continue

            rule_text = rule_obj.get('rule_text')
            if not rule_text or not str(rule_text).strip():
                if raise_errors:
                    raise ValueError(f"Item {idx}: Missing required 'rule_text'")
                warnings.warn(f"Item {idx}: Missing required 'rule_text', skipping item")
                error_count += 1
                continue

            rule_text = str(rule_text).strip()

            name, infer_edges, set_static = _parse_and_validate_rule_params(
                idx, rule_obj.get('name'), rule_obj.get('infer_edges', False),
                rule_obj.get('set_static', False), raise_errors, "Item")

            custom_thresholds_raw = rule_obj.get('custom_thresholds')
            custom_thresholds = None
            found_threshold_error = False
            if custom_thresholds_raw is not None:
                if isinstance(custom_thresholds_raw, list):
                    custom_thresholds = []
                    for t_idx, t_obj in enumerate(custom_thresholds_raw):
                        if isinstance(t_obj, dict):
                            try:
                                custom_thresholds.append(Threshold(
                                    t_obj['quantifier'],
                                    tuple(t_obj['quantifier_type']),
                                    t_obj['thresh']
                                ))
                            except (KeyError, ValueError, TypeError) as te:
                                if raise_errors:
                                    raise ValueError(f"Item {idx}, threshold {t_idx}: Invalid threshold - {te}")
                                warnings.warn(f"Item {idx}, threshold {t_idx}: Invalid threshold - {te}, skipping rule")
                                found_threshold_error = True
                                break
                        else:
                            if raise_errors:
                                raise ValueError(f"Item {idx}, threshold {t_idx}: Expected object, got {type(t_obj).__name__}")
                            warnings.warn(f"Item {idx}, threshold {t_idx}: Expected object, got {type(t_obj).__name__}, skipping rule")
                            found_threshold_error = True
                            break
                elif isinstance(custom_thresholds_raw, dict):
                    custom_thresholds = {}
                    for key_str, t_obj in custom_thresholds_raw.items():
                        try:
                            clause_idx = int(key_str)
                        except (ValueError, TypeError):
                            if raise_errors:
                                raise ValueError(f"Item {idx}: custom_thresholds dict key '{key_str}' must be an integer clause index")
                            warnings.warn(f"Item {idx}: custom_thresholds dict key '{key_str}' must be an integer clause index, skipping rule")
                            found_threshold_error = True
                            break
                        if isinstance(t_obj, dict):
                            try:
                                custom_thresholds[clause_idx] = Threshold(
                                    t_obj['quantifier'],
                                    tuple(t_obj['quantifier_type']),
                                    t_obj['thresh']
                                )
                            except (KeyError, ValueError, TypeError) as te:
                                if raise_errors:
                                    raise ValueError(f"Item {idx}, threshold key '{key_str}': Invalid threshold - {te}")
                                warnings.warn(f"Item {idx}, threshold key '{key_str}': Invalid threshold - {te}, skipping rule")
                                found_threshold_error = True
                                break
                        else:
                            if raise_errors:
                                raise ValueError(f"Item {idx}, threshold key '{key_str}': Expected object, got {type(t_obj).__name__}")
                            warnings.warn(f"Item {idx}, threshold key '{key_str}': Expected object, got {type(t_obj).__name__}, skipping rule")
                            found_threshold_error = True
                            break
                else:
                    if raise_errors:
                        raise ValueError(f"Item {idx}: 'custom_thresholds' must be a list or dict of threshold objects")
                    warnings.warn(f"Item {idx}: 'custom_thresholds' must be a list or dict of threshold objects, skipping rule")
                    found_threshold_error = True
            if found_threshold_error:
                error_count += 1
                continue

            weights_raw = rule_obj.get('weights')
            weights = None
            if weights_raw is not None:
                if not isinstance(weights_raw, list):
                    if raise_errors:
                        raise ValueError(f"Item {idx}: 'weights' must be a list of numeric values")
                    warnings.warn(f"Item {idx}: 'weights' must be a list of numeric values, skipping rule")
                    error_count += 1
                    continue
                else:
                    weights = weights_raw

            if name and name in loaded_name_set:
                if raise_errors:
                    raise ValueError(f"Item {idx}: Loaded name '{name}' is a duplicate - all rule names must be unique.")
                warnings.warn(f"Item {idx}: Loaded name '{name}' is a duplicate - all rule names must be unique.")
                error_count += 1
                continue
            if name:
                loaded_name_set.add(name)

            r = Rule(rule_text=rule_text, name=name, infer_edges=infer_edges,
                     set_static=set_static, custom_thresholds=custom_thresholds,
                     weights=weights)
            add_rule(state, r)
            loaded_count += 1

        except ValueError as e:
            if raise_errors:
                raise ValueError(f"Item {idx}: Failed to parse rule - {e}") from e
            error_count += 1
            warnings.warn(f"Item {idx}: Failed to parse rule - {e}")
        except Exception as e:
            if raise_errors:
                raise Exception(f"Item {idx}: Unexpected error - {e}") from e
            error_count += 1
            warnings.warn(f"Item {idx}: Unexpected error - {e}")

    if state.settings.verbose:
        print(f"Loaded {loaded_count} rules from {json_path}")
        if error_count > 0:
            print(f"Failed to load {error_count} rules due to errors")


def add_fact_from_json(state: EngineState, json_path: str, raise_errors=True) -> None:
    """Load facts from a JSON array of fact objects (fact_text required;
    name, start_time, end_time, static optional).

    Pinned semantics (oracle pyreason.py:1168-1292): document-level faults
    raise before any item loads; item-level ValueErrors re-wrap as
    'Item <n>: Failed to parse fact - <inner>' (the fact parser's own
    ValueError carries no item tag, so its wrap is single-prefixed);
    duplicate names raise AFTER earlier items loaded. The closing loaded-
    count print is unconditional at the pin (pyreason.py:1290) — the one
    loader not gated on verbose — and stays so here.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in file {json_path}: {e}")
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError(f"Error reading JSON file {json_path}: {e}")

    if not isinstance(data, list):
        raise ValueError(f"JSON file must contain an array of fact objects, got {type(data).__name__}")

    if len(data) == 0:
        warnings.warn(f"JSON file {json_path} contains an empty array, no facts loaded")
        return

    loaded_count = 0
    error_count = 0
    loaded_name_set = set()

    for idx, fact_obj in enumerate(data):
        try:
            if not isinstance(fact_obj, dict):
                if raise_errors:
                    raise ValueError(f"Item {idx}: Expected object, got {type(fact_obj).__name__}")
                warnings.warn(f"Item {idx}: Expected object, got {type(fact_obj).__name__}, skipping item")
                error_count += 1
                continue

            fact_text = fact_obj.get('fact_text')
            if not fact_text or not str(fact_text).strip():
                if raise_errors:
                    raise ValueError(f"Item {idx}: Missing required 'fact_text'")
                warnings.warn(f"Item {idx}: Missing required 'fact_text', skipping item")
                error_count += 1
                continue

            fact_text = str(fact_text).strip()

            name, start_time, end_time, static = _parse_and_validate_fact_params(
                idx, fact_obj.get('name'), fact_obj.get('start_time', 0),
                fact_obj.get('end_time', 0), fact_obj.get('static', False),
                raise_errors, "Item")

            if name and name in loaded_name_set:
                if raise_errors:
                    raise ValueError(f"Item {idx}: Loaded name '{name}' is a duplicate - all fact names must be unique.")
                warnings.warn(f"Item {idx}: Loaded name '{name}' is a duplicate - all fact names must be unique.")
                error_count += 1
                continue
            if name:
                loaded_name_set.add(name)

            fact = Fact(fact_text=fact_text, name=name, start_time=start_time, end_time=end_time, static=static)
            add_fact(state, fact)
            loaded_count += 1

        except ValueError as e:
            if raise_errors:
                raise ValueError(f"Item {idx}: Failed to parse fact - {e}") from e
            error_count += 1
            warnings.warn(f"Item {idx}: Failed to parse fact - {e}")
        except Exception as e:
            if raise_errors:
                raise Exception(f"Item {idx}: Unexpected error - {e}") from e
            error_count += 1
            warnings.warn(f"Item {idx}: Unexpected error - {e}")

    print(f"Loaded {loaded_count} facts from {json_path}")
    if error_count > 0:
        print(f"Failed to load {error_count} facts due to errors")


def add_fact_from_csv(state: EngineState, csv_path: str, raise_errors=True) -> None:
    """Load facts from a CSV of rows
    `fact_text, name, start_time, end_time, static` (header row optional,
    matched exactly).

    Pinned semantics (oracle pyreason.py:1294-1412): row-level ValueErrors
    re-wrap as 'Row <n>: Failed to parse fact - <inner>' (doubled prefix);
    a missing file, an empty file, and an unreadable file take the three
    outer arms in _read_csv.
    """
    rows = _read_csv(csv_path, "facts")
    if rows is None:
        return

    expected_header = ['fact_text', 'name', 'start_time', 'end_time', 'static']
    first_row = [str(v).strip() for v in rows[0]]
    has_header = first_row == expected_header
    start_idx = 1 if has_header else 0

    loaded_count = 0
    error_count = 0
    loaded_name_set = set()

    for idx, row in enumerate(rows[start_idx:], start=start_idx):
        try:
            if len(row) < 1 or not str(row[0]).strip():
                if raise_errors:
                    raise ValueError(f"Row {idx + 1}: Missing required 'fact_text'")
                warnings.warn(f"Row {idx + 1}: Missing required 'fact_text', skipping row")
                error_count += 1
                continue

            fact_text = str(row[0]).strip()

            name, start_time, end_time, static = _parse_and_validate_fact_params(
                idx + 1, _cell(row, 1), _cell(row, 2), _cell(row, 3),
                _cell(row, 4), raise_errors, "Row")

            if name and name in loaded_name_set:
                if raise_errors:
                    raise ValueError(f"Row {idx + 1}: Loaded name '{name}' is a duplicate - all fact names must be unique.")
                warnings.warn(f"Row {idx + 1}: Loaded name '{name}' is a duplicate - all fact names must be unique.")
                error_count += 1
                continue
            if name:
                loaded_name_set.add(name)

            fact = Fact(fact_text=fact_text, name=name, start_time=start_time, end_time=end_time, static=static)
            add_fact(state, fact)
            loaded_count += 1

        except ValueError as e:
            if raise_errors:
                raise ValueError(f"Row {idx + 1}: Failed to parse fact - {e}") from e
            error_count += 1
            warnings.warn(f"Row {idx + 1}: Failed to parse fact - {e}")
        except Exception as e:
            if raise_errors:
                raise Exception(f"Row {idx + 1}: Unexpected error - {e}") from e
            error_count += 1
            warnings.warn(f"Row {idx + 1}: Unexpected error - {e}")

    if state.settings.verbose:
        print(f"Loaded {loaded_count} facts from {csv_path}")
        if error_count > 0:
            print(f"Failed to load {error_count} facts due to errors")
