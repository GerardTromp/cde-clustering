from difflib import unified_diff
from rich.console import Console
from rich.syntax import Syntax


def print_json_diff(
    original: str,
    cleaned: str,
    context: int = 3,
    color: bool = False,
    summary: bool = False,
    output_file: str | None = None,
):
    """
    Print or save a unified diff between two JSON strings.

    Parameters:
        original: Original formatted JSON string.
        cleaned: Cleaned formatted JSON string.
        context: Lines of context to show before/after changes.
        color: Whether to colorize output using Rich.
        summary: Whether to print a summary line count.
        output_file: Optional path to write the diff to.
    """
    original_lines = original.splitlines()
    cleaned_lines = cleaned.splitlines()

    diff = list(
        unified_diff(
            original_lines,
            cleaned_lines,
            fromfile="original.json",
            tofile="cleaned.json",
            n=context,
            lineterm="",
        )
    )

    if summary:
        adds = sum(
            1 for line in diff if line.startswith("+") and not line.startswith("+++")
        )
        subs = sum(
            1 for line in diff if line.startswith("-") and not line.startswith("---")
        )
        print(f"\nSummary: +{adds} additions, -{subs} deletions\n")

    if color:
        console = Console()
        syntax = Syntax("\n".join(diff), "diff", theme="ansi_dark", line_numbers=False)
        console.print(syntax)
    else:
        print("\n".join(diff))

    if output_file:
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(diff))
