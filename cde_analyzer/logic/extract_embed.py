import actions
import json
import csv
import pydantic
import re
import logging
from typing import List, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from utils.helpers import extract_embed_project_fields_by_tinyid
from utils.path_utils import (
    load_path_schema,
    get_path_value,
    permis_values_to_dict_list,
)
from utils.designation_parser import extract_name_and_question_from_designations
from utils.logger import log_if_verbose
from utils.analyzer_state import get_verbosity, set_verbosity
from utils.extract_embed import (
    simplify_permissible_values,
    normalize_extracted_value,
    strip_json_list,
    strip_embedded_nl,
    sanitize,
)

# from CDE_Schema.CDE_Item import CDEItem
# from CDE_Schema.CDE_Form import CDEForm

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
    simplify: bool = False,
):
    # model_class = MODEL_REGISTRY[args.model]
    items = [model_class.model_validate(obj) for obj in data]
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
                    and model_class.__name__ == "CDEItem"
                    and re.match("designations", path_expr)
                ):
                    result = extract_name_and_question_from_designations(
                        [
                            d.model_dump()
                            for d in getattr(item, "designations", []) or []
                        ]
                    )  # type: ignore
                    # qn += 1
                    if isinstance(result, dict):
                        result = {k: sanitize(v) for k, v in result.items()}
                    elif isinstance(result, list):
                        result = [
                            {k: sanitize(v) for k, v in d.items()} for d in result  # type: ignore
                        ]

                    row.update(result)  # type: ignore
                    # continue

                val = get_path_value(item.model_dump(), path_expr)
                log_if_verbose(f"[extract_embed logic] Check tinyId: {item.tinyId}", 2)  # type: ignore
                # Here the even more complex simplification of permissibleValueSets.
                #   The problem is that PVs can have permissibleValue (pv), valueMeaningDefinition (vmd) and
                #   valueMeanningName (vmn). If values present (non-empty set), pv is defined, but vmd may or may not
                #   be and vmn likewise. Heuristically, vmd is more valuable than vmn. Simplification should
                #   return only two sets pv and either pvd or pvn.
                if (
                    path_expr.endswith("permissibleValues")
                    and model_class.__name__ == "CDEItem"
                    and collapse
                    and simplify
                ):
                    log_if_verbose(
                        f"[simplify call] passed all tests and calling simplify_permissible_values",
                        3,
                    )
                    simplified = simplify_permissible_values(val, collapse)
                    for key, collapsed_val in simplified.items():  # type: ignore
                        row[f"{tag}.{key}"] = (  # type: ignore
                            collapsed_val if collapsed_val is not None else ""
                        )
                    continue
                else:
                    val = normalize_extracted_value(val, collapse=collapse)

                row[tag] = val if val is not None else ""  # type: ignore
            rows.append(row)
    else:
        rows = extract_embed_project_fields_by_tinyid(data, tinyids, exclude)

    if not output:
        print(json.dumps(rows, indent=2))
        return

    # clean up leading/trailing whitespace on some data values
    rows = strip_json_list(rows)
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
