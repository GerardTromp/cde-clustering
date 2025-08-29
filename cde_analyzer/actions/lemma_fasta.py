import json
import logging
import argparse
from argparse import ArgumentParser, BooleanOptionalAction, Namespace
from logic.lemma_fasta import collect_all_phrase_occurrences
from utils.output_writer import phrase_write_output
from utils.analyzer_state import get_verbosity, set_verbosity

# from pydantic import parse_file_as
from pydantic import BaseModel
from CDE_Schema import CDEItem  # type: ignore with your actual model

help_text = "Extract common phrases from CDE CDs or Forms"
description_text = "Extract frequent phrases, verbatim or lemmatized, from designatted fields in CDE model classes"

logger = logging.getLogger(__name__)

def register_subparser(subparser: ArgumentParser):
    subparser.add_argument("--input", "-i", help="Input JSON file")
    subparser.add_argument(
        "--fields",
        "-f",
        nargs="+",
        required=True,
        help="Field names from pydantic classes",
    )
    subparser.add_argument(
        "--remove-stopwords",
        action="store_true",
        help="Remove common English stop words (articles, prepositions, conjunctions)?",
    )
    subparser.add_argument(
        "--lemmatize",
        "-l",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Convert the text to standardized (lemma) form so that similar phrases match?",
    )
    subparser.add_argument(
        "--output-format",
        choices=["json", "csv", "tsv"],
        default="json",
        help="Choose output format",
    )
    subparser.add_argument(
        "--output", "-o", help="Path, including filename, to store results."
    )
    subparser.add_argument(
        "--verbatim",
        action="store_true",
        help="Include verbatim (non-lemmatized) phrases alongside lemma phrases",
    )
    subparser.set_defaults(func=run_action)
    
def run_action(args: Namespace):
    verbosity = get_verbosity()
    raw = json.load(open(args.input))
    items = [CDEItem.model_validate(obj) for obj in raw]

    logger.info(f"arguments: {args}")

    results = collect_all_phrase_occurrences(
        items=items,
        field_names=args.fields,
        remove_stopwords=args.remove_stopwords,
        verbosity=verbosity,
        prune=args.prune,
        verbatim=args.verbatim,
    )