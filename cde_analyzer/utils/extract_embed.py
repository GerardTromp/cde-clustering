# file utils/extrac_embed.py
import re
from typing import Union, Dict, Any, List
from utils.path_utils import permis_values_to_dict_list
from utils.logger import log_if_verbose


DOS_NL = re.compile(r"\r\n")
MAC_NL = re.compile(r"\r")
MULTI_NL = re.compile(r"\n\n*")
MULTI_SPACE = re.compile(r" {2,}")
NUM_LIST = re.compile(r"(?:\d+;; )+")


def strip_embedded_nl(text: str) -> Union[str, None]:
    if not isinstance(text, str):
        return text
    log_if_verbose(f"[EMBED-NL PRE] {repr(text)}", 3)

    # Normalize to LF only
    text = DOS_NL.sub("\n", text)
    text = MAC_NL.sub("\n", text)

    # Replace multiple newlines with space
    text = MULTI_NL.sub(" ", text)

    # Collapse multiple spaces
    text = MULTI_SPACE.sub(" ", text)

    result = text.strip()
    log_if_verbose(f"[EMBED-NL POST] {repr(result)}", 3)
    return result


def sanitize(s):
    """
    clean up strings
    """
    if s is None:
        return ""
    else:
        s = str(s).strip()
        s = strip_embedded_nl(s)
        return s


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

        # Filter out sets that have numerical listing
        # Heuristic since tabulaton shows only two sets that match the regex contain 
        # char strings, remainder are all variations of consecutive numbers
        #  1 - Not at all;; 2;; 3;; 4;; 5 - very well
        #  0 - absent;; 0.5;; 1 - mild;; 1.5;; 2 - moderate;; 2.5;; 3 - severe
        if NUM_LIST.search(str(pv_str)):
            pv_str = ""
        if NUM_LIST.search(str(secondary_str)):
           secondary_str = ""

        # secondary str sometimes becomes some multiple of double semi-colons
        # ';;;;;;'. Add filter to avoid multiple empty strings in list
        if pv_str and pv_str != "":
            result["permissibleValue"].append(pv_str)
        if secondary_str and secondary_str != "":
            result["secondary"].append(secondary_str)  # type: ignore

    if collapse:
        return {
            "permissibleValue": ";; ".join(result["permissibleValue"]),
            "secondary": ";; ".join(result["secondary"]),
        }

    return result


def normalize_extracted_value(val: Any, collapse: bool = False) -> Any:
    """
    Normalize extracted value by:
    - Removing Python `None` values
    - Collapsing lists into strings if collapse is True
    - Preserving string literals like "None"
    """

    # def sanitize(v):
    #     if v == None:
    #         return ""
    #     else:
    #         v = str(v).strip()
    #         return strip_embedded_nl(v)

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
                    vdata = ";; ".join(str(v) for v in vdata)
                result[vtag] = vdata
            return result
        else:
            flat = [sanitize(v) for v in val if v is not None]
            val = ";; ".join(flat)  # type: ignore
            log_if_verbose(f"[normalize] Flattened simple list: {val}", 3)
    return val


def strip_json(obj):
    """
    clean up the json to remove extra whitespace on values
       and also remove embedded newlines
    """
    stripped_obj = {
        key: sanitize(value) if isinstance(value, str) else value
        for key, value in obj.items()
    }
    return stripped_obj


def strip_json_list(json_list):
    json_list = [strip_json(item) for item in json_list]
    return json_list
