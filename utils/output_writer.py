# ------------------------------
# File: utils/output_writer.py
# ------------------------------
import yaml  # pip install pyyaml
import csv
import json
from typing import Any, Dict
from pathlib import Path


def write_output(data, format="json", out_path=None):
    if format == "json":
        output = json.dumps(data, indent=2)
    elif format in {"csv", "tsv"}:
        sep = "," if format == "csv" else "\t"
        lines = []
        for path, phrases in data.items():
            for phrase, tids in phrases.items():
                lines.append([path, phrase, ";".join(tids)])
        output = "\n".join(
            [sep.join(["path", "phrase", "tinyIDs"])] + [sep.join(row) for row in lines]
        )
    else:
        raise ValueError("Unsupported output format")

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


def save_data(data: Any, output_path: Path, fmt: str, pretty: bool):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2 if pretty else None, ensure_ascii=False)

    elif fmt == "yaml":
        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    elif fmt == "csv":
        if isinstance(data, list) and all(isinstance(row, dict) for row in data):
            fieldnames = sorted(set().union(*(row.keys() for row in data)))
            with output_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        else:
            raise ValueError("CSV format only supports list of dicts.")
    else:
        raise ValueError(f"Unsupported format: {fmt}")
