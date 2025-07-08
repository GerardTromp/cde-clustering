#
# File: actions/extract.py
#
import argparse
import json
import textwrap
import logging
from typing import List, Dict, Optional
from CDE_Schema import CDEItem
from utils.helpers import extract_embed_project_fields_by_tinyid
from utils.path_utils import load_path_schema, get_path_value
from CDE_Schema.CDE_Item import CDEItem
from utils.tinyid_utils import load_tinyids
from logic.extract_embed import extract_path

# from actions.count import run_action


def run_action(arglist):
    parser = argparse.ArgumentParser(prog="cde_analyzer extract_embed")
    parser.add_argument("input", help="Input JSON file")
    ids = parser.add_mutually_exclusive_group()
    ids.add_argument(
        "--id-list",
        nargs="+",
        required=False,
        help="List of identifiers to exclude/include (see --exclude)",
    )
    ids.add_argument(
        "--id-file", help="Path to file with list of identifiers (JSON, csv, or tsv)"
    )
    parser.add_argument(
        "--id-type",
        help=textwrap.dedent(
            """
            Pydantic path/tag for identifier, i.e., what type of identifier. \n
              Required if either --id-list or --id-file is provided.
            """
        ),
    )
    #    parser.add_argument(
    #        "--match-type",
    #        choices=["non_null", "null", "fixed", "regex"],
    #        default="non_null",
    #    )
    parser.add_argument(
        "--exclude",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Should provided tinyId's be excluded (--exclude) or included (--no-exclude)",
    )
    parser.add_argument(
        "--path-file",
        required=True,
        help="File with the key-value pairs defining the names (key) and paths (value) to be extracted",
    )
    parser.add_argument(
        "--outfile",
        required=True,
        help="Path and filename where to store extracted fields.",
    )
    parser.add_argument(
        "--output-format",
        required=False,
        choices=["json", "csv", "tsv"],
        default="json",
        help="Format for file with extracted data.",
    )

    logging.debug(f"[extract_embed action] Argument list arglist: {arglist}")

    args, state_dict = parser.parse_known_args(arglist)
    logging.debug(f"[extract_embed action] Parsed arguments are: {args}")

    if (args.id_list or args.id_file) and args.id_type is None:
        parser.error("--id_type is required when --id-list or --id-file is used.")

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
