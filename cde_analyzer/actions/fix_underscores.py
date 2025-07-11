# actions/fix_underscores.py

import json
import logging
import argparse
import textwrap
from argparse import ArgumentParser, BooleanOptionalAction, Namespace

logger = logging.getLogger(__name__)

help_text = "Prepend a character to JSON keys starting with an underscore."
description_text = "Pydantic reserves keys beginning with an underscore as private. Convert to start with another character."


def register_subparser(subparser: ArgumentParser):
    subparser.add_argument(
        "--input", help="Full path, including name, of input JSON file."
    )
    subparser.add_argument(
        "--output", help="Full path, including name, of output JSON file."
    )
    subparser.add_argument(
        "--prefix",
        required=True,
        help="Character to prepend on fields starting with an underscore.",
    )
    subparser.add_argument(
        "--depth",
        type=int,
        help="Maximum depth (JSON nesting) to process. (type integer)",
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
