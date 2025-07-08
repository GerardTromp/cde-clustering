#! /usr/bin/python3
import sys
import argparse
from actions import phrase, count, strip, extract_embed
from utils.logger import configure_logging
from utils.helpers import which_r, get_state, set_state
from utils.analyzer_state import get_verbosity, set_verbosity


ACTIONS = {
    "phrase": phrase.run_action,
    "count": count.run_action,
    "strip": strip.run_action,
    "extract_embed": extract_embed.run_action,
    #    "depth": depth.run_action,
    #    "quality": quality.run_action,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: cde_analyzer <action> [options]")
        print("Available actions:", ", ".join(ACTIONS))
        sys.exit(1)

    action = sys.argv[1]
    if action not in ACTIONS:
        print(f"Unknown action: {action}")
        print("Available actions:", ", ".join(ACTIONS))
        sys.exit(1)

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
    args, other = parser.parse_known_args(sys.argv)
    configure_logging(args.verbosity, args.logfile)
    set_verbosity(args.verbosity)

    ACTIONS[action](other[2:])


if __name__ == "__main__":
    main()
