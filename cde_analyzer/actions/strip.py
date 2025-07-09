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
        "--fields", nargs="+", required=True, help="Field names from pydantic classes"
    )
    subparser.add_argument(
        "--min-words",
        type=int,
        default=2,
        help="Minimum length of phrases, i.e., discard shorter phrases. (default: 2)",
    )
    subparser.add_argument(
        "--min-ids",
        type=int,
        default=2,
        help="Minimum number of objects that share a phrase. (default: 2)",
    )
    subparser.add_argument(
        "--remove-stopwords",
        action="store_true",
        default=False,
        help="Remove common English stop words (articles, prepositions, conjunctions)? (default: False)",
    )
    subparser.add_argument(
        "--lemmatize",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Convert the text to standardized (lemma) form so that similar phrases match?",
    )
    subparser.add_argument(
        "--prune-subphrases",
        action="store_true",
        help="Collect longest shared phrases? (default: False)",
    )
    subparser.add_argument(
        "--output-format",
        choices=["json", "csv", "tsv"],
        default="json",
        help="Choose output format. (default JSON)",
    )
    subparser.add_argument(
        "--output", help="Path, including filename, to store results."
    )
    subparser.add_argument(
        "--verbatim",
        action="store_true",
        help="Include verbatim (non-lemmatized) phrases alongside lemma phrases. (default: False)",
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
