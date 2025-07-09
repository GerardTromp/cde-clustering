#
# File: actions/extract_embed.py
#
import argparse
import json
import sys
import textwrap
import logging
from typing import List, Dict, Optional
from CDE_Schema import CDEItem
from utils.helpers import extract_embed_project_fields_by_tinyid
from utils.path_utils import load_path_schema, get_path_value
from utils.tinyid_utils import load_tinyids
from logic.extract_embed import extract_path
from argparse import ArgumentParser, ArgumentError

# from actions.count import run_action
logger = logging.getLogger(__name__)

help_text = "Extract subset of fields from model for embedding text"
description_text = "Extract a desired subset of fields and collapse repeated key:value pairs to key: 'value1;value2;value3,...'"


def register_subparser(subparser: ArgumentParser):
    subparser.add_argument("--input", help="Input JSON file.")
    subparser.add_argument(
        "--fields", nargs="+", required=True, help="Field names from pydantic classes."
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


def run_action(args):
    if (args.id_list or args.id_file) and args.id_type is None:
        print(
            "error:--id_type is required when --id-list or --id-file is used.",
            file=sys.stderr,
        )
        sys.exit(2)

    # paths = load_path_schema(args.path_file)
    if args.id_file:
        idlist = load_tinyids(args.id_file)
    else:
        idlist = args.id_list

    raw = json.load(open(args.input))
    items = [CDEItem.model_validate(obj) for obj in raw]

    extract_path(
        items, idlist, args.outfile, args.output_format, args.path_file, args.exclude
    )
