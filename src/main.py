"""CLI entry point for the dependency graph tool."""

import argparse
import csv
import sys

from .config import load_config
from .repository import get_dependencies

EXIT_SUCCESS = 0
EXIT_ERROR = 1


def print_dependencies(dependencies: list[str]) -> None:
    """Print one declared dependency per line or an empty-list message."""
    if not dependencies:
        print("No direct dependencies declared.")
        return
    for dependency in dependencies:
        print(dependency)


def main() -> int:
    """Load the config, fetch release metadata and print dependencies."""
    parser = argparse.ArgumentParser(
        description="Direct package dependencies, variant 21, stage 2"
    )
    parser.add_argument(
        "--config",
        default="configs/pypi.csv",
        help="Path to the CSV configuration file"
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        dependencies = get_dependencies(config)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR

    print_dependencies(dependencies)
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
