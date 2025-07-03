#! /usr/bin/python3
import sys
from actions import phrase, count, strip


ACTIONS = {
    "phrase": phrase.run_action,
    "count": count.run_action,
    "strip": strip.run_action,
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

    ACTIONS[action](sys.argv[2:])


if __name__ == "__main__":
    main()
