import re
import json
import logging
from collections import defaultdict
from core.recursor import recursive_descent
from typing import TypeAlias, Union, Dict, List
from utils.datatype_check import check_number_type, is_string_shorter
from utils.helpers import (
    safe_nested_increment,
)

IntDict: TypeAlias = Dict[str, int]
NestedDict: TypeAlias = Dict[str, Union[IntDict, "NestedDict"]]

logger = logging.getLogger("cde_analyzer.count")


def match_condition(value, match_type, pattern):
    if value is None or value == "" or value == []:
        return match_type == "null"
    if match_type == "fixed":
        return value == pattern
    if match_type == "regex":
        return bool(re.search(pattern, str(value)))
    return False


def find_group_value(
    data: dict, group_by: str, group_type: str = "top", verbose: bool = False
) -> str:
    if group_type == "top":
        value = str(data.get(group_by, "<unknown>"))
        if verbose:
            print(f"[GROUP-BY] top-level '{group_by}' = {value}")
        return value

    found = "<unknown>"

    def visitor(path, value, context):
        nonlocal found
        if group_type == "path" and group_by in path:
            found = str(value)
        elif group_type == "terminal" and path.split(".")[-1] == group_by:
            found = str(value)

    recursive_descent(data, path="", visitor=visitor)
    if verbose:
        print(f"[GROUP-BY] {group_type}-match '{group_by}' = {found}")
    return found


def classify_type(value, char_limit: int) -> str:
    if value is None:
        return "null"
    is_num, is_float = check_number_type(value)
    if is_num:
        return "float" if is_float else "int"
    elif isinstance(value, str) and is_string_shorter(value, char_limit):
        return f"str{char_limit}"
    return "str"


def count_matching_fields(
    items,
    field_names: List[str],
    match_type: str = "non_null",
    value_match: Union[str, None] = None,
    logic_expr: Union[str, None] = None,
    group_by: Union[str, None] = None,
    group_type: str = "top",
    verbose: bool = False,
    count_type: bool = False,
    char_limit: int = 10,
) -> NestedDict:

    results: NestedDict = {}
    for item in items:
        flat: Dict[str, int] = {}
        flat_types: Dict[str, str] = {}

        def visitor(path, value, context):
            base_name = path.split(".")[-1]
            matched = any(
                fn == path
                or fn == base_name
                or ("*" in fn and re.fullmatch(fn.replace("*", ".*"), path))
                for fn in field_names
            )
            if matched:
                key = path if path in field_names else base_name
                if match_type == "non_null" and value not in (None, "", [], "null"):
                    flat[key] = flat.get(key, 0) + 1
                elif match_type == "null" and value in (None, "", [], "null"):
                    flat[key] = flat.get(key, 0) + 1
                elif match_type in {"fixed", "regex"} and match_condition(
                    value, match_type, value_match
                ):
                    flat[key] = flat.get(key, 0) + 1

                if count_type:
                    flat_types[key] = classify_type(value, char_limit)

        recursive_descent(item.model_dump(), path="", visitor=visitor)

        if verbose:
            logger.debug(f"[DEBUG] flat keys: {flat}")
            logger.debug(f"[DEBUG] logic_expr: {logic_expr}")

        try:
            result = (
                eval(logic_expr, {}, {k: bool(v) for k, v in flat.items()})
                if logic_expr
                else any(flat.values())
            )
        except Exception as e:
            if verbose:
                logger.warning(f"[ERROR] Failed logic eval: {e}")
                logger.debug(f"[DEBUG] flat keys available: {list(flat.keys())}")
            result = False

        if result:
            group_value = (
                find_group_value(
                    item.model_dump(), group_by, group_type, verbose=verbose
                )
                if group_by
                else "<global>"
            )
            if verbose and count_type:
                logger.debug(f"[DEBUG] Typed keys: {flat_types}")
            group_value = str(group_value)  # ensure it's a string key
            for key, count in flat.items():
                if count_type:
                    val_type = flat_types.get(key, "unknown")
                    if verbose:
                        logger.debug(
                            f"[DEBUG] Incrementing {key} -> {val_type} -> {group_value} by {count}"
                        )
                    safe_nested_increment(results, key, val_type, group_value, v=count)  # type: ignore
                else:
                    safe_nested_increment(results, key, group_value, v=count)  # type: ignore

    return results
