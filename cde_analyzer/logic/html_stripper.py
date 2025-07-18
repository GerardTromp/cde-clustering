import unicodedata
import yaml  # pip install pyyaml
import csv
import warnings
import json
from pathlib import Path
from typing import Any, Type, List, Optional, Dict, Union
from pydantic import BaseModel
from CDE_Schema import CDEForm, CDEItem
from utils.html import clean_text_values
from utils.output_writer import save_data
from utils.cde_impexport import load_json
from utils.logger import logging


logger = logging.getLogger("cde_analyzer.strip")

# === MODEL REGISTRY ===
MODEL_REGISTRY: dict[str, Type[BaseModel]] = {
    "CDE": CDEItem,
    "Form": CDEForm,
}


def process_data(
    data: Union[list, dict], model_class: Type[BaseModel], set_keys, tables, colnames
) -> List[Dict]:
    logger.debug(f"Raw input type: {type(data).__name__}")
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("Input must be a dict or list of dicts.")

    models = [model_class(**item) for item in data]
    cleaned = [clean_text_values(model, set_keys, tables, colnames) for model in models]
    return [model.model_dump(by_alias=True) for model in cleaned]


def process_file(
    filepath: Path,
    outdir: Path,
    model_class: Type[BaseModel],
    fmt: str,
    dry_run: bool,
    set_keys: bool,
    pretty: bool,
    tables: bool,
    colnames: bool,
):
    logger.info(f"Processing: {filepath}")
    try:
        raw_data = load_json(filepath)
        cleaned_data = process_data(raw_data, model_class, set_keys, tables, colnames)

        output_path = outdir / f"{filepath.stem}_nohtml.{fmt}"

        if dry_run:
            logger.info(f"[Dry-run] Would write: {output_path}")
        else:
            save_data(cleaned_data, output_path, fmt, pretty)
            logger.info(f"Saved cleaned data to: {output_path}")

    except Exception as e:
        logger.error(f"Error processing {filepath.name}: {e}")
