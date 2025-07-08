# ------------------------------
# File: utils/helpers.py
# ------------------------------
from typing import Any, Dict, List
import csv
import json
import logging


def safe_nested_increment(d: Dict[str, Any], *keys: str, v: int = 1):
    """
    Safely increment a nested dictionary by arbitrary depth using keys.
    Usage:
        safe_nested_increment(results, k1, k2, k3, v=1)
        --> results[k1][k2][k3] += 1
    """
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    last_key = keys[-1]
    current[last_key] = current.get(last_key, 0) + v


def flatten_nested_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, int]:
    """
    Flattens a nested dictionary to a flat dict with joined keys.
    {"a": {"b": {"c": 1}}} -> {"a.b.c": 1}
    """
    flat = {}
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(flatten_nested_dict(v, prefix=full_key))
        else:
            flat[full_key] = v
    return flat


def export_results_csv(results: Dict[str, Any], output_path: str, group_by_field: str):
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "datatype", f"groupby_{group_by_field}", "count"])
        for field, type_dict in results.items():
            if isinstance(type_dict, dict):
                for dtype, group_dict in type_dict.items():
                    if isinstance(group_dict, dict):
                        for group_key, count in group_dict.items():
                            writer.writerow([field, dtype, group_key, count])


def export_results_tsv(results: Dict[str, Any], output_path: str, group_by_field: str):
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["field", "datatype", f"groupby_{group_by_field}", "count"])
        for field, type_dict in results.items():
            if isinstance(type_dict, dict):
                for dtype, group_dict in type_dict.items():
                    if isinstance(group_dict, dict):
                        for group_key, count in group_dict.items():
                            writer.writerow([field, dtype, group_key, count])


def safe_nested_append(d: Dict[str, Any], *keys: str, value: Any):
    """
    Appends a value into a nested list, building structure if needed.
    """
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    last_key = keys[-1]
    if last_key not in current or not isinstance(current[last_key], list):
        current[last_key] = []
    if value not in current[last_key]:
        current[last_key].append(value)


def extract_embed_project_fields_by_tinyid(
    items: List[Any], tinyids: List[str], logic: bool
) -> List[Dict[str, Any]]:
    """
    Extracts fields from a list of CDEItems given a list of target tinyIds.
    """

    def process_record(item):
        element_name = (
            item.designations[0].designation if len(item.designations) > 0 else ""
        )
        question = (
            item.designations[1].designation if len(item.designations) > 1 else ""
        )
        description = item.definitions[0].definition if item.definitions else ""

        perm_vals = []
        val_defs = []
        val_names = []

        if item.valueDomain and item.valueDomain.permissibleValues:
            for pv in item.valueDomain.permissibleValues:
                perm_vals.append(pv.permissibleValue or "")
                val_defs.append(pv.valueMeaningDefinition or "")
                val_names.append(pv.valueMeaningName or "")

        rows.append(
            {
                "tinyId": item.tinyId,
                "element_name": element_name,
                "question": question,
                "description": description,
                "permissible_values": ";".join(perm_vals),
                "value_meaning_definitions": ";".join(val_defs),
                "value_meaning_names": ";".join(val_names),
            }
        )

    rows = []
    for item in items:
        if item.tinyId in tinyids:
            if logic:
                process_record(item)
            else:
                continue

    return rows


def which_r(boolean_list):
    """
    Finds the indices of True values in a boolean list.

    Args:
        boolean_list: A list of boolean values (True or False).

    Returns:
        A list of indices where the boolean values are True.
    """
    return [i for i, x in enumerate(boolean_list) if x]


def create_state_verbosity(initial_state):
    """
    Intention was to share the variable across modules, but the
    assessor functions are seen as variables.
    """
    state_variable = initial_state  # The shared state variable

    def modify_state(new_value):  # An "assessor" function
        nonlocal state_variable  # Declare intent to modify the variable in the enclosing scope
        state_variable = new_value

    def access_state():  # Another "assessor" function
        return state_variable

    return modify_state, access_state  # Return the assessor functions


# Generalized versions of the create_state_verbosity above.
# Requires construction of the state dictionary in cde_analyzer main function
# Then
def get_state(state_dict, key):
    """Accesses a state variable from the dictionary."""
    return state_dict.get(key)  # Use .get() for safe access


# 3. Define a mutator function (optional)
def set_state(state_dict, key, value):
    """Sets a state variable in the dictionary."""
    state_dict[key] = value


def log_info(message: str, level: int = 2):
    """
    Custom logging that logs or discards base
    on global verbosity.
    Avoids so many conditionals.
    """
    from utils.analyzer_state import get_verbosity

    if get_verbosity() >= level:
        logging.info(message)
