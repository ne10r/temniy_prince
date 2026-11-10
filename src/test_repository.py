"""Read the direct neighbours of a package from a test CSV file."""

import csv

from .validators import check_package


def read_test_dependencies(path: str, package: str) -> list[str]:
    """Find one test package without traversing its dependencies."""
    result = None
    names = set()
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if reader.fieldnames != ["package", "dependencies"]:
            raise ValueError("Test CSV columns: package,dependencies")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError("Invalid test repository row")
            name = row["package"].strip()
            check_package(name, True)
            if name in names:
                raise ValueError(f"Duplicate test package: {name}")
            names.add(name)
            dependencies = row["dependencies"].split()
            for dependency in dependencies:
                check_package(dependency, True)
            if name == package:
                result = dependencies
    if result is None:
        raise ValueError(f"Test package not found: {package}")
    return result
