import actions
import json
import csv
import pydantic
import re
import logging
from typing import List, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from CDE_Schema import CDEItem, PermissibleValue, CDEForm

from utils.helpers import extract_embed_project_fields_by_tinyid
from utils.path_utils import (
    load_path_schema,
    get_path_value,
    permis_values_to_dict_list,
)
from utils.designation_parser import extract_name_and_question_from_designations
from utils.logger import log_if_verbose
from utils.analyzer_state import get_verbosity, set_verbosity
from CDE_Schema import CDEItem, CDEForm

logger = logging.getLogger("cde_analyzer.extract_embed")
ModelType = TypeVar("ModelType", bound=BaseModel)


# This function can be generalized by changing data to a List[Basemodel]
# would need to check the schmema_path for validity
def extract_path(
    model_class: Type[ModelType],
    data: List[Dict],
    tinyids: List[str],
    output: Optional[str] = None,
    format: str = "json",
    schema_path: Optional[str] = None,
    exclude: bool = False,
    collapse: bool = False,
):
    # model_class = MODEL_REGISTRY[args.model]
    items = [model_class.model_validate(obj) for obj in data]
    if collapse:
        none_pat = re.compile(r"(?:None, )*None")
    log_if_verbose(f"[DEBUG] The list of tinyIds is: {tinyids}", 1)
    qn = 0  # counter to skip subsequent designations in path
    if schema_path:
        schema = load_path_schema(schema_path)
        rows = []
        for item in items:
            if exclude:
                if item.tinyId in tinyids:  # type: ignore
                    log_message = f"[extract_embed logic] Check tinyId: {item.tinyId}"  # type: ignore
                    log_if_verbose(log_message, 2)
                    continue
            row: Dict[str, str] = {"tinyId": item.tinyId}  # type: ignore

            # Here start iterating over the path_expr read in from file
            #   Must add dynamic_tag with designations.*.designation
            for tag, path_expr in schema.items():
                # Here we must test for "designations" in path, if yes, then check for existence of
                # "tags" Must check that we are parsing CDE not Form
                if (
                    qn == 0
                    and model_class == "CDE"
                    and re.match("designations", path_expr)
                ):
                    result = extract_name_and_question_from_designations(item.get("designations"))  # type: ignore validate item
                    qn += 1
                    rows.append(result)
                    continue

                val = get_path_value(item.model_dump(), path_expr)
                log_if_verbose(f"[extract_embed logic] Check tinyId: {item.tinyId}", 2)  # type: ignore

                if isinstance(val, list):
                    if all(isinstance(item, dict) for item in val):
                        val = permis_values_to_dict_list(val)  # type: ignore -- we have checked
                        log_message = (
                            f"[extract_embed logic]  permissible vals -- val is: {val}"
                        )
                        log_if_verbose(log_message, 3)
                        vdict = {}
                        for vtag, vdata in val.items():
                            if collapse:
                                log_message = f"[extract_embed logic]  collapsing permis vals -- vtag is: {vtag}, vdata is: {vdata}"
                                log_if_verbose(log_message, 3)
                                if isinstance(vdata, list):
                                    vdata = [item for item in vdata if item is not None]
                                    log_message = f"[extract_embed logic]  after collapsing -- vtag is: {vtag}, vdata is: {vdata}"
                                    log_if_verbose(log_message, 3)
                            if isinstance(vdata, list):
                                cstring = ";;".join(str(v) for v in vdata)
                                vdict[vtag] = cstring
                        val = vdict
                    else:
                        val = ";".join(str(v) for v in val)
                        log_message = (
                            f"[extract_embed logic] Flattened [list] -- val is: {val}"
                        )
                        log_if_verbose(log_message, 3)
                        # None is introduced during data dump
                        # if collapse:
                        #     val = re.sub(none_pat, "", val)
                        #     log_message = f"[extract_embed logic] Flattened [list] after collapse -- val is: {val}"
                        #     log_if_verbose(log_message, 3)

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
        with open(output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    elif format == "tsv":
        with open(output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    else:
        raise ValueError(f"Unsupported output format: {format}")
