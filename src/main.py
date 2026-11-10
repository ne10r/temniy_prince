"""CLI entry point for the dependency graph tool."""

import argparse
import csv
import sys

from .config import Config, load_config

EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1


def print_config(config: Config) -> None:
    """Print the four settings as key-value pairs."""
    for key, value in config.get_info().items():
        if isinstance(value, bool):
            value = str(value).lower()
        print(f"{key}={value}")


def main() -> int:
    """Read the configuration and report invalid settings."""
    parser = argparse.ArgumentParser(
        description="Dependency graph tool, variant 21, stage 1"
    )
    parser.add_argument(
        "--config",
        default="configs/pypi.csv",
        help="Path to the CSV configuration file"
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    print_config(config)
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
