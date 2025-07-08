import json
import csv
from pathlib import Path
from CDE_Schema.CDE_Item import CDEItem
from typing import Any, Type, List, Optional, Dict, Union


def save_raw_json(model, base_filename, idx):
    raw_filename = f"{base_filename}_raw_{idx+1}.json"
    with open(raw_filename, "w") as raw_file:
        json.dump(model.dict(), raw_file, indent=2)
    print(f"Raw JSON saved to {raw_filename}")


def export_results(results, output_format, filename):
    if output_format == "csv":
        export_to_csv(
            [
                {
                    "path": r["path"],
                    "value": (
                        concatenate_values(r["value"])
                        if isinstance(r["value"], list)
                        else r["value"]
                    ),
                }
                for r in results
            ],
            filename,
        )
        print(f"Results exported to {filename} in CSV format.")
    elif output_format == "json":
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results exported to {filename} in JSON format.")
    else:
        print("Unsupported export format.")


def export_to_csv(data_list: list, file_path: str):
    if not data_list:
        return
    with open(file_path, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data_list[0].keys())
        for row in data_list:
            writer.writerow(row.values())


def concatenate_values(data_list: list, delimiter: str = ", ") -> str:
    return delimiter.join(str(item) for item in data_list if item is not None)


## This is not quite right
def load_json_model(file_path: str) -> List[CDEItem]:
    with open(file_path, "r") as f:
        data = json.load(f)
    return list(CDEItem)  # type: ignore


def load_json(filepath: Path) -> Union[list, dict]:
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)
