#! /usr/bin/python3
import sys
import argparse
from actions import (
    phrase,
    count,
    extract_embed,
    fix_underscores,
    strip_html,
    strip_phrases,
)
from utils.logger import configure_logging
from utils.helpers import which_r, get_state, set_state
from utils.analyzer_state import get_verbosity, set_verbosity


ACTIONS = {
    "phrase": phrase,
    "count": count,
    "strip_html": strip_html,
    "extract_embed": extract_embed,
    "fix_underscores": fix_underscores,
    "strip_phrases": strip_phrases,
    #    "depth": depth.run_action,
    #    "quality": quality.run_action,
}


def main():
    parser = argparse.ArgumentParser(
        description="Utilities to work with the NLM CDE repository data modeled as pydantic classes"
    )
    parser.add_argument(
        "--verbosity",
        "-v",
        action="count",
        default=1,
        help="Increase verbosity level (-vv for debug)",
    )
    parser.add_argument("--logfile", help="Optional log file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register each action as a subparser
    for name, module in ACTIONS.items():
        action_parser = subparsers.add_parser(
            name,
            help=getattr(module, "help_text", ""),
            description=getattr(module, "description_text", ""),
        )
        module.register_subparser(action_parser)

    args = parser.parse_args()
    configure_logging(args.verbosity, args.logfile)
    set_verbosity(args.verbosity)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
