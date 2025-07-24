# file utils/extrac_embed.py
from typing import Union, Dict, Any
from utils.path_utils import permis_values_to_dict_list
from utils.logger import log_if_verbose


def simplify_permissible_values(
    pv_list: Any, collapse: bool = False
) -> Union[Dict[str, str], str]:
    """
    Applies heuristics to simplify a list of permissible values.

    If collapse is True:
        Returns {"permissibleValue": "1;;2;;3", "secondary": "Yes;;No;;"}
    Else:
        Returns {"1": "Yes", "2": "No", "3": ""}
    """
    if not isinstance(pv_list, list) or not all(isinstance(pv, dict) for pv in pv_list):
        log_if_verbose(
            f"[simplify permissible value] pv_list is neither list nor dict: {pv_list}",
            3,
        )
        return pv_list  # type: ignore # Fallback to raw

    collapsed_primary = []
    collapsed_secondary = []
    expanded = {}

    for entry in pv_list:
        log_if_verbose(
            f"[simplify permissible value] simplifying one of three: {entry}", 3
        )
        primary = str(entry.get("permissibleValue", "")).strip()
        defn = str(entry.get("valueMeaningDefinition", "")).strip()
        altname = str(entry.get("valueMeaningName", "")).strip()

        secondary = defn if defn else altname
        if not secondary or secondary == primary:
            secondary = ""

        if collapse:
            collapsed_primary.append(primary)
            collapsed_secondary.append(secondary)
        else:
            expanded[primary] = secondary

    if collapse:
        return {
            "permissibleValue": ";;".join(collapsed_primary),
            "secondary": ";;".join(collapsed_secondary),
        }

    return expanded


def normalize_extracted_value(val: Any, collapse: bool = False) -> Any:
    """
    Handles flattening of lists or cleaning of values post-extraction.
    """
    if isinstance(val, list):
        if all(isinstance(item, dict) for item in val):
            val = permis_values_to_dict_list(val)
            log_if_verbose(f"[normalize] permis_values_to_dict_list result: {val}", 3)

            result = {}
            for vtag, vdata in val.items():
                if collapse:
                    if isinstance(vdata, list):
                        vdata = [item for item in vdata if item is not None]
                if isinstance(vdata, list):
                    vdata = ";;".join(str(v) for v in vdata)
                result[vtag] = vdata
            return result
        else:
            flat = [str(v) for v in val if v is not None]
            val = ";".join(flat)
            log_if_verbose(f"[normalize] Flattened simple list: {val}", 3)
    return val
