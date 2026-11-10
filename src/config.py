"""CSV configuration loading."""

import csv
from pathlib import Path

from .validators import check_package, check_repository, check_version
from .validators import parse_test_mode

CONFIG_FIELDS = ("package", "repository", "test_mode", "version")
CONFIG_ROW_COUNT = 1


class Config:
    """Store the four settings read from a CSV file."""

    def __init__(
        self, package: str, repository: str, test_mode: bool, version: str
    ) -> None:
        """Save the validated settings."""
        self.package = package
        self.repository = repository
        self.test_mode = test_mode
        self.version = version

    def get_info(self) -> dict:
        """Return settings in their output order."""
        return {
            "package": self.package,
            "repository": self.repository,
            "test_mode": self.test_mode,
            "version": self.version,
        }


def read_csv(path: Path) -> dict:
    """Read the header and a single configuration row."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        fields = reader.fieldnames
        if fields is None:
            raise ValueError("Config file is empty")
        if len(fields) != len(CONFIG_FIELDS):
            raise ValueError("Config must have exactly four columns")
        if set(fields) != set(CONFIG_FIELDS):
            names = ", ".join(CONFIG_FIELDS)
            raise ValueError(f"Expected CSV columns: {names}")
        rows = list(reader)

    if len(rows) != CONFIG_ROW_COUNT:
        raise ValueError("Config must contain exactly one data row")
    values = rows[0]
    if None in values or None in values.values():
        raise ValueError("The data row does not match the CSV header")
    return {key: value.strip() for key, value in values.items()}


def load_config(config_path: str) -> Config:
    """Load the CSV file and validate every setting."""
    path = Path(config_path)
    values = read_csv(path)
    test_mode = parse_test_mode(values["test_mode"])
    check_package(values["package"], test_mode)
    check_version(values["version"])
    repository = check_repository(
        values["repository"], test_mode, path.parent
    )
    return Config(
        values["package"], repository, test_mode, values["version"]
    )
