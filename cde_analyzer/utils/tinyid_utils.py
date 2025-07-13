import csv
import json
import logging
from typing import Any, Dict, List, Union


id_columnname_mapping = {
    "ID": "tinyId",
    "Id": "tinyId",
    "tinyID": "tinyId",
    "IDs": "tinyId",
    "Ids": "tinyId",
    # ... and so on
}


def load_tinyids(path: str) -> List[str]:
    """
    Load a set of tinyIds for inclusion or exclusion during processing
    Supports JSON, TSV, or CSV.
    Expects
        1. JSON key:value (dictionary) where value is list of tinyId.
        2. CSV/TSV single column with header and cells are tinyId.
    C/TSV format can tolerate column names in ["ID, "Id", "tinyID", "IDs", "Ids"] in addition to "tinyId".

    Should extract a generic function from this and call a special version with the mapped
    identifiers. Then the function could work for an ID with any name and any set of mappings
    """
    if path.endswith(".json"):
        with open(path) as f:
            return json.load(f)["tinyId"]

    id_list = []
    with open(path) as f:
        reader = csv.DictReader(f, delimiter="\t" if path.endswith(".tsv") else ",")
        for row in reader:
            new_row = {}
            for col_orig, value in row.items():
                if col_orig in id_columnname_mapping:
                    new_row[id_columnname_mapping[col_orig]] = value
                else:
                    new_row[col_orig] = value
            id_list.append(new_row["tinyId"])
            logging.debug(f"The ID list is now: {id_list}")

    return id_list
