import argparse
import json
from typing import Any, Type, List, Optional, Dict, Union
from pathlib import Path
from logic.extractor import collect_all_phrase_occurrences
from logic.htlm_stripper import process_file
from utils.output_writer import phrase_write_output
from utils.logger import configure_logging, logging


# from pydantic import parse_file_as
from pydantic import BaseModel
from CDE_Schema import CDEItem, CDEForm  # type: ignore with your actual model

# === MODEL REGISTRY ===
MODEL_REGISTRY: dict[str, Type[BaseModel]] = {
    "CDE": CDEItem,
    "Form": CDEForm,
}


def run_action(argv):
    parser = argparse.ArgumentParser(
        description="Clean and normalize string fields in structured JSON via Pydantic models."
    )
    parser.add_argument("filenames", nargs="+", help="Input JSON file(s)")
    parser.add_argument(
        "--model",
        "-m",
        required=True,
        choices=MODEL_REGISTRY.keys(),
        help="Model to use for validation",
    )
    parser.add_argument(
        "--outdir",
        default=".",
        help="Directory for output files (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not write output files"
    )
    parser.add_argument(
        "--verbosity",
        "-v",
        action="count",
        default=1,
        help="Increase verbosity level (-vv for debug)",
    )
    parser.add_argument("--logfile", help="Optional log file path")
    parser.add_argument(
        "--pretty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Produce pretty (default: --pretty) or minified (--no-pretty) JSON (no whitespace)",
    )
    parser.add_argument(
        "--set-keys",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save model with keys only represented if they are set (no null, None, or empty sets)",
    )

    args = parser.parse_args()
    configure_logging(args.verbosity, args.logfile)

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
        )


#    raw = json.load(open(args.input))
#    items = [CDEItem.model_validate(obj) for obj in raw]
#
#    results = collect_all_phrase_occurrences(
#        items=items,
#        field_names=args.fields,
#        min_words=args.min_words,
#        remove_stopwords=args.remove_stopwords,
#        min_ids=args.min_ids,
#        verbosity=args.verbose,
#        prune_subphrases=args.prune_subphrases,
#        lemmatize=args.lemmatize,
#    )
#
#    write_output(results, format=args.output_format, out_path=args.output)
#
