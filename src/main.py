"""CLI entry point for the dependency graph tool."""

import argparse
import csv
import sys

from .config import load_config
from .graph import load_graph

EXIT_SUCCESS = 0
EXIT_ERROR = 1


def print_graph(graph: dict, cycles: list) -> None:
    """Print adjacency lists and the cycles found during the walk."""
    for package, dependencies in graph.items():
        neighbours = ", ".join(dependencies) or "(none)"
        print(f"{package} -> {neighbours}")
    for cycle in cycles:
        print("Cycle: " + " -> ".join(cycle))


def main() -> int:
    """Load the config, build the dependency graph and print it."""
    parser = argparse.ArgumentParser(
        description="Dependency graph with iterative DFS, variant 21, stage 3"
    )
    parser.add_argument(
        "--config",
        default="configs/pypi.csv",
        help="Path to the CSV configuration file"
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        graph, cycles = load_graph(config)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR

    print_graph(graph, cycles)
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
