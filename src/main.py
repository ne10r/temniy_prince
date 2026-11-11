"""CLI entry point for the dependency graph tool."""

import argparse
import csv
import sys

from .config import load_config
from .graph import load_graph
from .order import get_load_order

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
    """Read the CSV path and optional loading-order mode."""
    parser = argparse.ArgumentParser(
        description="Dependency graph and loading order, variant 21, stage 4"
    )
    parser.add_argument(
        "--config",
        default="configs/pypi.csv",
        help="Path to the CSV configuration file"
    )
    parser.add_argument(
        "--order", action="store_true",
        help="Print dependencies before the packages that require them"
    )
    return parser.parse_args()


def main() -> int:
    """Build the graph and print adjacency lists or loading order."""
    args = parse_args()

    try:
        config = load_config(args.config)
        graph, cycles = load_graph(config)
        if args.order:
            order = get_load_order(graph, next(iter(graph)))
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR

    if args.order:
        print(" -> ".join(order))
    else:
        print_graph(graph, cycles)
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
