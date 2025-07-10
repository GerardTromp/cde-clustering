#!/usr/bin/env python3
"""
Export CLI help documentation for all registered actions.

Supports multiple formats (e.g., 'man', 'markdown') and writes
one file per action into a target output directory.
"""

import os
import sys
import argparse
from io import StringIO

# Insert project root manually if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("→ Added project root to sys.path manually.")

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cde_analyzer import (
    ACTIONS,
)  # assumes cde_analyzer.py exposes these


def get_main_help(topparser: argparse.ArgumentParser) -> str:
    buf = StringIO()
    topparser.print_help(file=buf)
    return buf.getvalue()


def extract_action_help(subparser: argparse.ArgumentParser) -> str:
    buf = StringIO()
    subparser.print_help(file=buf)
    return buf.getvalue()


def format_help(name: str, help_text: str, format: str) -> str:
    if format == "man":
        return help_text
    elif format == "markdown":
        return f"# `{name}` Command\n\n```\n{help_text.strip()}\n```"
    elif format == "plaintext":
        return f"{name.upper()} COMMAND HELP\n\n{help_text}"
    else:
        raise ValueError(f"Unsupported help format: {format}")


def get_write_help(name, parser: argparse.ArgumentParser, format, output_dir):
    help_text = extract_action_help(parser)
    formatted = format_help(name, help_text, format)
    filename = os.path.join(output_dir, f"{name}.{format}")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(formatted)
    return formatted, filename


def export_all_help_docs(
    output_dir: str = "docs/help", format: str = "man", combine: bool = True
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    top_parser = argparse.ArgumentParser(description="CDE Analyzer CLI")
    subparsers = top_parser.add_subparsers(dest="command")

    combined_sections = []

    name = "cde_analyzer"
    main_text, filename = get_write_help(name, top_parser, format, output_dir)
    print(f"✅ Wrote help for '{name}' to {filename}")
    combined_sections.append(main_text)

    for name, module in ACTIONS.items():
        help_text = getattr(module, "__help__", f"{name} command")
        description = getattr(module, "__description__", help_text)
        epilog = getattr(module, "__epilog__", None)
        subparser = subparsers.add_parser(
            name, help=help_text, description=description, epilog=epilog
        )
        module.register_subparser(subparser)

        formatted, filename = get_write_help(name, subparser, format, output_dir)
        print(f"✅ Wrote help for '{name}' to {filename}")
        combined_sections.append(formatted)

    if combine and format == "markdown":
        cheat_file = os.path.join(output_dir, "all-commands.md")
        with open(cheat_file, "w", encoding="utf-8") as f:
            f.write("# CDE Analyzer CLI Cheat Sheet\n\n")
            f.write("\n\n---\n\n".join(combined_sections))
        print(f"📚 Wrote combined cheat sheet to {cheat_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Export help documentation for cde_analyzer actions."
    )
    parser.add_argument(
        "--format",
        choices=["man", "markdown", "plaintext"],
        default="man",
        help="Output format for help files",
    )
    parser.add_argument(
        "--output-dir", default="docs/help", help="Directory to store help files"
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="If using markdown, also produce a combined all-commands.md cheat sheet",
    )
    args = parser.parse_args()

    export_all_help_docs(
        output_dir=args.output_dir, format=args.format, combine=args.combine
    )


if __name__ == "__main__":
    main()
