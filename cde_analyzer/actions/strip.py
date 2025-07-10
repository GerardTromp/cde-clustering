#
# File: actions/strip.py
#
import argparse
from argparse import ArgumentParser, Namespace
from typing import Any, Type, List, Optional, Dict, Union
from pathlib import Path
from logic.html_stripper import process_file
from utils.logger import configure_logging, logging
from pydantic import BaseModel
from CDE_Schema import CDEItem, CDEForm  # type: ignore

# === MODEL REGISTRY ===
MODEL_REGISTRY: dict[str, Type[BaseModel]] = {
    "CDE": CDEItem,
    "Form": CDEForm,
}

logger = logging.getLogger(__name__)

help_text = "Clean (strip) embedded HTML from JSON structure"
description_text = "Clean and normalize string fields containing HTML in structured JSON via Pydantic models"


def register_subparser(subparser: ArgumentParser):
    subparser.add_argument(
        "--input", help="Input JSON file that has underscore tags fixed."
    )
    subparser.add_argument(
        "--output", help="Path, including filename, to store results."
    )
    subparser.add_argument(
        "--model",
        "-m",
        required=True,
        choices=MODEL_REGISTRY.keys(),
        help="Model to use for validation",
    )
    subparser.add_argument(
        "--outdir",
        default=".",
        help="Directory for output files (default: current directory)",
    )
    subparser.add_argument(
        "--format",
        choices=["json", "yaml", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    subparser.add_argument(
        "--dry-run", action="store_true", help="Do not write output files"
    )
    subparser.add_argument(
        "--verbosity",
        "-v",
        action="count",
        default=1,
        help="Increase verbosity level (-vv for debug)",
    )
    subparser.add_argument("--logfile", help="Optional log file path")
    subparser.add_argument(
        "--pretty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Produce pretty (default: --pretty) or minified (--no-pretty) JSON (no whitespace)",
    )
    subparser.add_argument(
        "--set-keys",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save model with keys only represented if they are set (no null, None, or empty sets)",
    )
    subparser.add_argument(
        "--tables",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Convert html tables to JSON representation (default: --tables, i.e., true) or munged text (--no-tables)",
    )
    subparser.add_argument(
        "--colnames",
        action="store_false",
        help="Use first row of table as column names (default: false). Only relevant if --tables.",
    )
    subparser.set_defaults(func=run_action)


def run_action(args: Namespace):
    model_class = MODEL_REGISTRY[args.model]
    outdir = Path(args.outdir)

    for filename in args.filenames:
        filepath = Path(filename)
        if not filepath.is_file():
            logging.warning(f"Skipping: {filename} is not a valid file.")
            continue
        process_file(
            filepath,
            outdir,
            model_class,
            args.format,
            args.dry_run,
            args.set_keys,
            args.pretty,
            args.tables,
            args.colnames,
        )
