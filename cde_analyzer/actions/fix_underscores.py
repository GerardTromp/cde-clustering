# actions/fix_underscores.py

import json
import logging
import argparse
import textwrap
from argparse import ArgumentParser, BooleanOptionalAction, Namespace

logger = logging.getLogger(__name__)

help_text = "Prepend a character to JSON keys starting with an underscore"
description_text = "Pydantic reserves keys beginning with an underscore as private. Convert to start with another character"


def register_subparser(subparser: ArgumentParser):
    subparser.add_argument("input", help="Input JSON file")
    ids = subparser.add_mutually_exclusive_group()
    ids.add_argument(
        "--id-list",
        nargs="+",
        required=False,
        help="List of identifiers to exclude/include (see --exclude)",
    )
    ids.add_argument(
        "--id-file", help="Path to file with list of identifiers (JSON, csv, or tsv)"
    )
    subparser.add_argument(
        "--id-type",
        help=textwrap.dedent(
            """
            Pydantic path/tag for identifier, i.e., what type of identifier. \n
              Required if either --id-list or --id-file is provided.
            """
        ),
    )
    subparser.add_argument(
        "--exclude",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Should provided tinyId's be excluded (--exclude) or included (--no-exclude)",
    )
    subparser.add_argument(
        "--path-file",
        required=True,
        help="File with the key-value pairs defining the names (key) and paths (value) to be extracted",
    )
    subparser.add_argument(
        "--output",
        required=True,
        help="Path, including filename, where to store extracted fields.",
    )
    subparser.add_argument(
        "--output-format",
        required=False,
        choices=["json", "csv", "tsv"],
        default="json",
        help="Format for file with extracted data.",
    )
    subparser.set_defaults(func=run_action)


def fix_keys(data, prefix, max_depth=None, current_depth=0):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = key
            if key.startswith("_") and (
                max_depth is None or current_depth <= max_depth
            ):
                new_key = prefix + key
                logger.debug(
                    f"Renaming key: {key} -> {new_key} at depth {current_depth}"
                )
            new_dict[new_key] = fix_keys(value, prefix, max_depth, current_depth + 1)
        return new_dict
    elif isinstance(data, list):
        return [fix_keys(item, prefix, max_depth, current_depth) for item in data]
    else:
        return data


def run_action(args: Namespace):
    logger.info(f"Reading input JSON from {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Fixing underscore-prefixed keys with prefix '{args.prefix}'")
    fixed = fix_keys(data, args.prefix, args.depth)

    if args.output:
        logger.info(f"Writing output to {args.output}")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(fixed, f, indent=2)
    else:
        print(json.dumps(fixed, indent=2))
