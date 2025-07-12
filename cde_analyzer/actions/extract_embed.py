#
# File: actions/extract_embed.py
#
import argparse
import json
import pydantic
import sys
import logging
from typing import TypeVar
from pydantic import BaseModel
from CDE_Schema import CDEItem, CDEForm
from utils.helpers import extract_embed_project_fields_by_tinyid
from utils.tinyid_utils import load_tinyids
from logic.extract_embed import extract_path
from argparse import ArgumentParser, ArgumentError, BooleanOptionalAction

# from actions.count import run_action
logger = logging.getLogger(__name__)

MODEL_REGISTRY = {
    "CDE": CDEItem,
    "Form": CDEForm,
    # Add others here
}

help_text = "Extract subset of fields from model for embedding text"
description_text = "Extract a desired subset of fields and collapse repeated key:value pairs to key: 'value1;value2;value3,...'"

models_str = ", ".join(MODEL_REGISTRY.keys())


def register_subparser(subparser: ArgumentParser):
    subparser.add_argument("--input", help="Input JSON file.")
    ids = subparser.add_mutually_exclusive_group()
    ids.add_argument(
        "--id-list",
        nargs="+",
        # required=True,
        help="List of item IDs (tinyId) to exclude or extract.",
    )
    ids.add_argument(
        "--id-file",
        default=str,
        help="File containing list of item IDs (tinyId) to exclude or extract (requires --exclude / --no-exclude).",
    )
    subparser.add_argument(
        "--output-format",
        choices=["json", "csv", "tsv"],
        default="json",
        help="Choose output format. (default JSON)",
    )
    subparser.add_argument(
        "--id-type", default=str, help="The type of ID (default=tinyId)."
    )
    subparser.add_argument(
        "--output", default=str, help="Path, including filename, to store results."
    )
    subparser.add_argument(
        "-m",
        "--model",
        default=str,
        required=True,
        choices=MODEL_REGISTRY.keys(),
        help="pydantic model appropriate for input file. ",
    )
    subparser.add_argument(
        "--path-file",
        default=str,
        help="File with paths of interest and new name (as name:path) for extracted data.",
    )
    subparser.add_argument(
        "--exclude",
        action=BooleanOptionalAction,
        default=True,
        help="Exclude (--exclude) or include (--no-exclude) IDs in list.",
    )
    subparser.add_argument(
        "--collapse",
        action=BooleanOptionalAction,
        default=True,
        help='Collapse repeated "None;" in list items.',
    )
    subparser.set_defaults(func=run_action)


def run_action(args):
    if (args.id_list or args.id_file) and args.id_type is None:
        print(
            "error:--id_type is required when --id-list or --id-file is used.",
            file=sys.stderr,
        )
        sys.exit(2)

    if (args.id_list or args.id_file) and args.exclude is None:
        print(
            "error:--exclude / --no-exclude is required when --id-list or --id-file is used.",
            file=sys.stderr,
        )
        sys.exit(2)

    # paths = load_path_schema(args.path_file)
    if args.id_file:
        idlist = load_tinyids(args.id_file)
    else:
        idlist = args.id_list

    raw = json.load(open(args.input))
    # ModelType = TypeVar(MODEL_REGISTRY[args.model], bound=BaseModel)
    model_class = MODEL_REGISTRY[args.model]

    extract_path(
        model_class,
        raw,
        idlist,
        args.output,
        args.output_format,
        args.path_file,
        args.exclude,
        args.collapse,
    )
