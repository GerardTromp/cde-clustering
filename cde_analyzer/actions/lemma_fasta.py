#
# File: actions/lemma_fasta.py
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
from logic.lemma_fasta import make_pfasta
from argparse import ArgumentParser, ArgumentError, BooleanOptionalAction


# from actions.count import run_action
logger = logging.getLogger(__name__)

MODEL_REGISTRY = {
    "CDE": CDEItem,
    "Form": CDEForm,
    # Add others here
}

help_text = "Extract fields as pseudo FASTA format"
description_text = """Extract a desired subset of fields as for embedding 
(extract_embed), but encode the "words" as uint16_t tokens to be used by 
genomic repeat finder tools.

The subset of fields is specified in a file (--path-file) as a set of 
   key-value pairs. Output "flattens" nested dict to simple dict with
   new keys.
The encoded uint16_t tokens are written to a fasta file encoding the 
   binary values in base85. The genomic tools need to be modified to
   de-/en- code the base85 data and work with uint16 tokens. 
Multiple files are generated so that the output name must be a stem/prefix. 
   1. JSON with keys:
      a. lemmatized -- JSON of simplified model, text lemmatized
      b. verbatim   -- JSON of simplified model, text original
      c. b85        -- JSON with base85 concatenated strings for each value
      d. b85_concat -- JSON base 85 of single `fasta_uint16` key (in addtion to tinyId)
      d. vocab      -- Vocab dict of lemmatized words and corresponding
                       uint16 encoding
   2. Pseudo fasta:
      a. FASTA representaiton of 1.b. > tinyid and base85 string as 
         payload
"""

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
    # subparser.add_argument(
    #     "--output-format",
    #     choices=["json", "csv", "tsv", "pfasta"],
    #     default="json",
    #     help="Choose output format. (default JSON)\n  - pfasta: pseudo FASTA encoding words in base85",
    # )
    subparser.add_argument(
        "--id-type", default=str, help="The type of ID (default=tinyId)."
    )
    subparser.add_argument(
        "-o",
        "--output",
        default=str,
        help="Path, with a prefix/stem name for results. Multiple files will be generated",
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
        "-c",
        "--collapse",
        action=BooleanOptionalAction,
        default=True,
        help='Collapse repeated "None;" in list items.',
    )
    subparser.add_argument(
        "-s",
        "--simplify-permissible",
        action=BooleanOptionalAction,
        default=True,
        help="Process limited set of permissibleValues fields using heuristic.",
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
    
    format = "pfasta"

    ### 
    # Need a wrapper function here that calls extract path and then processes the data
    # for the pseudo fasta
    make_pfasta(
        model_class,
        raw,
        idlist,
        args.output,
        format,
        args.path_file,
        args.exclude,
        args.collapse,
        args.simplify_permissible,
    )
