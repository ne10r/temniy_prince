"""Temporary configuration files used by tests."""

import csv

import pytest

from src.config import CONFIG_FIELDS


@pytest.fixture
def config_file(tmp_path):
    """Create a CSV config with optional replacement values."""
    def create(**changes):
        """Write one configuration row into the temporary directory."""
        values = {
            "package": "requests",
            "repository": "https://pypi.org/pypi",
            "test_mode": "false",
            "version": "2.32.3",
        }
        values.update(changes)
        path = tmp_path / "config.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CONFIG_FIELDS)
            writer.writeheader()
            writer.writerow(values)
        return path

    return create
