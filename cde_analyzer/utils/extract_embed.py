# file utils/extrac_embed.py
from typing import Union, Dict, Any, List
from utils.path_utils import permis_values_to_dict_list
from utils.logger import log_if_verbose


def simplify_permissible_values(
    pv_list: Any, collapse: bool = False
) -> Union[Dict[str, str], Dict[str, List[str]]]:
    """
    Applies heuristics to simplify a list of permissible values.

    If collapse is True:
        Returns {"permissibleValue": "1;;2;;3", "secondary": "Yes;;No;;"}
    Else:
        Returns {"1": "Yes", "2": "No", "3": ""}
    """

    # Sanitize values — only collapse Python None, NOT string "None"
    def sanitize(v):
        return "" if v is None else str(v).strip()

    result: Dict[str, List[str]] = {"permissibleValue": [], "secondary": []}

    if not isinstance(pv_list, list):
        return {}

    for item in pv_list:
        if not isinstance(item, dict):
            continue

        pv = item.get("permissibleValue", "")
        vmd = item.get("valueMeaningDefinition", "")
        vmn = item.get("valueMeaningName", "")

        # Heuristic selection: prefer valueMeaningDefinition, then valueMeaningName
        secondary = vmd or vmn or ""

        pv_str = sanitize(pv)
        secondary_str = sanitize(secondary)

        # Drop secondary if it's equal to permissibleValue
        if pv_str == secondary_str:
            secondary_str = ""

        # secondary str sometimes becomes some multiple of double semi-colons
        # ';;;;;;'. Add filter to avoid multiple empty strings in list
        if pv_str != "":
            result["permissibleValue"].append(pv_str)
        if secondary_str != "":
            result["secondary"].append(secondary_str)

    if collapse:
        return {
            "permissibleValue": ";;".join(result["permissibleValue"]),
            "secondary": ";;".join(result["secondary"]),
        }

    return result


def normalize_extracted_value(val: Any, collapse: bool = False) -> Any:
    """
    Normalize extracted value by:
    - Removing Python `None` values
    - Collapsing lists into strings if collapse is True
    - Preserving string literals like "None"
    """

    def sanitize(v):
        return "" if v is None else str(v).strip()

    if isinstance(val, list):
        if all(isinstance(item, dict) for item in val):
            val = permis_values_to_dict_list(val)
            log_if_verbose(f"[normalize] permis_values_to_dict_list result: {val}", 3)

            result = {}
            for vtag, vdata in val.items():
                if collapse:
                    if isinstance(vdata, list):
                        vdata = [sanitize(v) for v in vdata if v is not None]
                if isinstance(vdata, list):
                    vdata = [sanitize(v) for v in vdata if v is not None]
                    vdata = ";;".join(str(v) for v in vdata)
                result[vtag] = vdata
            return result
        else:
            flat = [sanitize(v) for v in val if v is not None]
            val = ";;".join(flat)
            log_if_verbose(f"[normalize] Flattened simple list: {val}", 3)
    return val


def strip_json(obj):
    stripped_obj = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in obj.items()
    }
    return stripped_obj


def strip_json_list(json_list):
    json_list = [strip_json(item) for item in json_list]
    return json_list
