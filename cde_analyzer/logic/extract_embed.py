import actions
import json
import csv
import logging
from typing import List, Dict, Optional
from CDE_Schema import CDEItem, PermissibleValue
from utils.helpers import extract_embed_project_fields_by_tinyid, get_state
from utils.path_utils import (
    load_path_schema,
    get_path_value,
    permis_values_to_dict_list,
)
from utils.analyzer_state import get_verbosity, set_verbosity
from CDE_Schema.CDE_Item import CDEItem

logger = logging.getLogger("cde_analyzer.extract_embed")


# This function can be generalized by changing data to a List[Basemodel]
# would need to check the schmema_path for validity
def extract_path(
    data: List[CDEItem],
    tinyids: List[str],
    output: Optional[str] = None,
    format: str = "json",
    schema_path: Optional[str] = None,
    exclude: bool = False,
):
    verbosity = get_verbosity()
    if verbosity > 1:
        logger.debug(f"[DEBUG] The list of tinyIds is: {tinyids}")
    if schema_path:
        schema = load_path_schema(schema_path)
        rows = []
        for item in data:
            if exclude:
                if item.tinyId in tinyids:
                    if verbosity > 2:
                        logger.debug(
                            f"[extract_embed logic] Check tinyId: {item.tinyId}"
                        )
                    continue
            row: Dict[str, str] = {"tinyId": item.tinyId}  # type: ignore
            for tag, path_expr in schema.items():
                val = get_path_value(item.model_dump(), path_expr)
                #                logger.debug(f"Processing: {tag}\t{path_expr}:\t{val}")
                if isinstance(val, list):
                    if all(isinstance(item, dict) for item in val):
                        val = permis_values_to_dict_list(val)  # type: ignore -- we have checked
                        if verbosity > 3:
                            logger.debug(
                                f"[extract_embed logic] Simplified _dictionary_ -- val is: {val}"
                            )
                        vdict = {}
                        for vtag, vdata in val.items():
                            if verbosity > 2:
                                logger.debug(
                                    f"[extract_embed logic]  collapsing permis vals -- vtag is: {vtag}, vdata is: {vdata}"
                                )
                            if isinstance(vdata, list):
                                cstring = ";".join(str(v) for v in vdata)
                                vdict[vtag] = cstring
                        val = vdict
                    else:
                        val = ";".join(str(v) for v in val)
                        if verbosity > 3:
                            logger.debug(
                                f"[extract_embed logic] Flattened [list] -- val is: {val}"
                            )
                row[tag] = val if val is not None else ""  # type: ignore
            rows.append(row)
    else:
        rows = extract_embed_project_fields_by_tinyid(data, tinyids, exclude)

    if not output:
        print(json.dumps(rows, indent=2))
        return

    if format == "json":
        with open(output, "w") as f:
            json.dump(rows, f, indent=2)
    elif format == "csv":
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    elif format == "tsv":
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    else:
        raise ValueError(f"Unsupported output format: {format}")
