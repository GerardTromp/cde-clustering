import argparse
import json
import logging
from logic.phrase_extractor import collect_all_phrase_occurrences
from utils.output_writer import phrase_write_output

# from pydantic import parse_file_as
from pydantic import BaseModel
from CDE_Schema import CDEItem  # type: ignore with your actual model

# from your_model_import import CDEItem  # Replace with actual module


def run_action(arglist):
    parser = argparse.ArgumentParser(prog="cde_analyzer phrase")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("--fields", nargs="+", required=True)
    parser.add_argument("--min-words", type=int, default=2)
    parser.add_argument("--min-ids", type=int, default=2)
    parser.add_argument("--remove-stopwords", action="store_true")
    parser.add_argument(
        "--lemmatize", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument("--prune-subphrases", action="store_true")
    parser.add_argument(
        "--output-format", choices=["json", "csv", "tsv"], default="json"
    )
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument(
        "--verbatim",
        action="store_true",
        help="Include verbatim (non-lemmatized) phrases alongside lemma phrases",
    )

    args = parser.parse_args(arglist)

    raw = json.load(open(args.input))
    items = [CDEItem.model_validate(obj) for obj in raw]

    logging.info(f"arguments: {args}")

    results = collect_all_phrase_occurrences(
        items=items,
        field_names=args.fields,
        min_words=args.min_words,
        remove_stopwords=args.remove_stopwords,
        min_ids=args.min_ids,
        verbosity=args.verbose,
        prune_subphrases=args.prune_subphrases,
        lemmatize=args.lemmatize,
        verbatim=args.verbatim,
    )

    phrase_write_output(results, format=args.output_format, out_path=args.output)
