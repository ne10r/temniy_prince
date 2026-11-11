"""CLI entry point for the dependency graph tool."""

import argparse
import csv
import subprocess
import sys
from pathlib import Path

from .config import load_config
from .graph import load_graph
from .order import get_load_order
from .visualization import render_graph, show_image

EXIT_SUCCESS = 0
EXIT_ERROR = 1


def print_graph(graph: dict, cycles: list) -> None:
    """Print adjacency lists and the cycles found during the walk."""
    for package, dependencies in graph.items():
        neighbours = ", ".join(dependencies) or "(none)"
        print(f"{package} -> {neighbours}")
    for cycle in cycles:
        print("Cycle: " + " -> ".join(cycle))


def parse_args() -> argparse.Namespace:
    """Read the CSV path, output mode and renderer options."""
    parser = argparse.ArgumentParser(
        description="D2 dependency graph visualization, variant 21, stage 5"
    )
    parser.add_argument(
        "--config",
        default="configs/dateutil.csv",
        help="Path to the CSV configuration file"
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--order", action="store_true",
        help="Print dependencies before the packages that require them"
    )
    modes.add_argument(
        "--graph", action="store_true", help="Print adjacency lists"
    )
    parser.add_argument("--output", default="build/dependencies.svg")
    parser.add_argument("--d2", help="Path to the D2 executable")
    parser.add_argument(
        "--no-open", action="store_true", help="Save the image without opening"
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    """Build the graph and display the selected result."""
    config = load_config(args.config)
    graph, cycles = load_graph(config)
    root = next(iter(graph))
    if args.order:
        print(" -> ".join(get_load_order(graph, root)))
    elif args.graph:
        print_graph(graph, cycles)
    else:
        source, image = render_graph(
            graph, cycles, root, Path(args.output), args.d2
        )
        print(f"D2 source: {source}")
        print(f"Image: {image}")
        if not args.no_open:
            show_image(image)


def main() -> int:
    """Render the image by default and report file or renderer errors."""
    args = parse_args()
    try:
        run(args)
    except (OSError, ValueError, csv.Error,
            subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
