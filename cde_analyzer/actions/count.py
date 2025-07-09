import argparse
import json
import logging
from logic.counter import count_matching_fields
from utils.output_writer import phrase_write_output
from utils.helpers import (
    safe_nested_increment,
    flatten_nested_dict,
    export_results_csv,
    export_results_tsv,
)
from argparse import ArgumentParser
from CDE_Schema import CDEItem

help_text = "Count occurrences of fields in JSON pydantic model."
description_text = "Count pydantic model fields that satisify certain conditions, including checking for numeric, integer, string and length of string."

logger = logging.getLogger(__name__)


def register_subparser(subparser: ArgumentParser):
    subparser.add_argument("--input", help="Input JSON file.")
    subparser.add_argument("--fields", nargs="+", required=True)
    subparser.add_argument(
        "--match-type",
        choices=["non_null", "null", "fixed", "regex"],
        default="non_null",
        help="Type of match, null type is empty string or list, or None.",
    )
    subparser.add_argument(
        "--value", help="Value to match if match-type is fixed or regex."
    )
    subparser.add_argument(
        "--output-format",
        choices=["json", "csv", "tsv"],
        default="json",
        help="Output format.",
    )
    subparser.add_argument(
        "--output", help="Path, including filename, to store results."
    )
    subparser.add_argument(
        "--group-by",
        help="Dotted path or key name to group by (e.g. tinyId or path.to.tinyId)",
    )
    subparser.add_argument(
        "--group-type",
        choices=["top", "path", "terminal"],
        default="top",
        help="Interpret group-by field as a top-level, full-path, or terminal (deepest) component of model",
    )
    subparser.add_argument("--logic", help="Logical expression (e.g. 'A and not B')")
    subparser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug output for group-by resolution",
    )
    subparser.add_argument(
        "--count-type",
        action="store_true",
        help="Classify and count field values by type (int, float, strN)",
    )
    subparser.add_argument(
        "--char-limit",
        type=int,
        default=10,
        help="Character limit for short string classification",
    )
    subparser.add_argument(
        "--output-flat",
        action="store_true",
        help="Flatten nested result keys for easier analysis",
    )

    subparser.set_defaults(func=run_action)


def run_action(args):
    raw = json.load(open(args.input))
    items = [CDEItem.model_validate(obj) for obj in raw]

    results = count_matching_fields(
        items=items,
        field_names=args.fields,
        match_type=args.match_type,
        value_match=args.value,
        logic_expr=args.logic,
        group_by=args.group_by,
        group_type=args.group_type,
        verbose=args.verbose,
        count_type=args.count_type,
        char_limit=args.char_limit,
    )
    # define shorter vars to avoid using arg.* in many places
    output_path = args.output_path
    output_flat = args.output_flat
    group_by = args.group_by

    if output_path:
        if output_flat:
            flattened = flatten_nested_dict(results)
            with open(output_path, "w") as f:
                json.dump(flattened, f, indent=2)
        elif output_path.endswith(".csv"):
            export_results_csv(results, output_path, group_by or "group")
        elif output_path.endswith(".tsv"):
            export_results_tsv(results, output_path, group_by or "group")
        else:
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

    phrase_write_output(results, format=args.output_format, out_path=args.output)
