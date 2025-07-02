# File: actions/extract.py

import json
import csv
from typing import List, Dict, Optional
from CDE_Schema import CDEItem
from utils.helpers import extract_fields_by_tinyid
from utils.path_utils import load_path_schema, get_path_value
from CDE_Schema.CDE_Item import CDEItem


def run_extract_action(
    data: List[CDEItem],
    tinyids: List[str],
    output: Optional[str] = None,
    format: str = "json",
    schema_path: Optional[str] = None,
):
    if schema_path:
        schema = load_path_schema(schema_path)
        rows = []
        for item in data:
            if item.tinyId not in tinyids:
                continue
            row: Dict[str, str] = {"tinyId": item.tinyId}
            for tag, path_expr in schema.items():
                val = get_path_value(item.dict(), path_expr)
                if isinstance(val, list):
                    val = ";".join(str(v) for v in val)
                row[tag] = val if val is not None else ""
            rows.append(row)
    else:
        rows = extract_fields_by_tinyid(data, tinyids)

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
