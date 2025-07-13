import CDE_Schema
import argparse
import json
from argparse import ArgumentParser, Namespace
from utils.logger import configure_logging, logging
from pydantic import BaseModel, ValidationError
from typing import Any, Type, List, Optional, Dict, Union
from logic.phrase_stripper import load_phrase_map, strip_phrases
from utils.diff_utils import print_json_diff

from CDE_Schema import CDEItem, CDEForm
from actions.count import register_subparser, run_action

MODEL_REGISTRY: dict[str, Type[BaseModel]] = {
    "CDE": CDEItem,
    "Form": CDEForm,
}

logger = logging.getLogger(__name__)


def register_subparser(subparser: ArgumentParser):
    # parser = subparsers.add_parser(
    #     "strip_phrases",
    #     help="Remove curated phrases from specific paths in a JSON document.",
    # )
    subparser.add_argument(
        "-i", "--input", required=True, help="Path to input JSON file."
    )
    subparser.add_argument(
        "-m",
        "--model",
        choices=MODEL_REGISTRY.keys(),
        required=True,
        help="Top-level Pydantic model name for parsing the input JSON.",
    )
    subparser.add_argument(
        "-p",
        "--phrases",
        required=True,
        help="Path to phrases file (JSON, CSV, or TSV).",
    )
    subparser.add_argument(
        "-o", "--output", required=True, help="Path to output JSON file."
    )
    # This should be moved to post-processing. Inefficient and memory hungry
    subparser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="Show diff between original and cleaned JSON",
    )
    subparser.add_argument(
        "--diff-output", type=str, help="Path to file for writing diff information."
    )
    subparser.add_argument(
        "-c", "--color", action="store_true", help="Colorize diff output."
    )
    subparser.add_argument(
        "--summary", action="store_true", help="Show a summary of lines changed lines."
    )
    subparser.add_argument(
        "-C",
        "--context",
        type=int,
        default=3,
        help="Number of context lines before and after changes.",
    )
    subparser.set_defaults(func=run_action)


def run_action(args: Namespace):
    model_class = MODEL_REGISTRY[args.model]

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    # Parse into model if needed
    # items = [CDEItem.model_validate(obj) for obj in raw]
    try:
        parsed = [model_class.model_validate(obj) for obj in data]  # or other model
    # Some verbose error output. Appropriate for STDERR
    except ValidationError as e:
        for error in e.errors():
            print(f"Error Type: {error['type']}")
            print(f"Message: {error['msg']}")
            print(f"Location: {error['loc']}")
            if "input" in error:
                print(f"Input: {error['input']}")
            if "ctx" in error:
                print(f"Context: {error['ctx']}")
            print("-" * 20)
    else:
        phrase_map = load_phrase_map(args.phrases)
        cleaned = strip_phrases(parsed, phrase_map)

        with open(args.output, "w", encoding="utf-8", newline="") as f:
            cleaned_json = [item.model_dump(mode="json") for item in cleaned]
            f.write(json.dumps(cleaned_json, indent=2))

        if args.diff or args.diff_output or args.summary:
            original_json = [item.model_dump(mode="json") for item in parsed]
            cleaned_json = [item.model_dump(mode="json") for item in cleaned]
            original_json = json.dumps(original_json, indent=2)
            cleaned_json = json.dumps(cleaned_json, indent=2)

            print_json_diff(
                original=original_json,
                cleaned=cleaned_json,
                context=args.context,
                color=args.color,
                summary=args.summary,
                output_file=args.diff_output,
            )
