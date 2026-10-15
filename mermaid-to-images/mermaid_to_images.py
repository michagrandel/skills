#!/usr/bin/env python3
"""Render Markdown Mermaid blocks using one of the bundled visual styles."""

from pathlib import Path
import subprocess
import sys


USAGE = """Usage: mermaid_to_images.py [--style diagram|sketch] <markdown-file-or-folder>... [--out <folder>]

  --style diagram  Professional dark style (default)
  --style sketch   Hand-drawn pastel style
"""


def parse_style(argv):
    style = "diagram"
    remaining = []
    index = 0

    while index < len(argv):
        argument = argv[index]
        if argument == "--style":
            if index + 1 >= len(argv):
                raise ValueError("--style requires a value: diagram or sketch.")
            style = argv[index + 1].lower()
            index += 2
        elif argument.startswith("--style="):
            style = argument.split("=", 1)[1].lower()
            index += 1
        else:
            remaining.append(argument)
            index += 1

    if style not in {"diagram", "sketch"}:
        raise ValueError(f"Unsupported style {style!r}; choose 'diagram' or 'sketch'.")
    return style, remaining


def main(argv):
    if not argv or any(argument in {"-h", "--help"} for argument in argv):
        print(USAGE, end="")
        return 0 if argv else 1

    try:
        style, renderer_args = parse_style(argv)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        print(USAGE, file=sys.stderr, end="")
        return 2

    if not renderer_args:
        print("Error: provide at least one Markdown file or folder.", file=sys.stderr)
        print(USAGE, file=sys.stderr, end="")
        return 2

    skill_dir = Path(__file__).resolve().parent
    renderer = skill_dir / "renderers" / style / "renderer.py"
    command = [sys.executable, str(renderer), *renderer_args]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
