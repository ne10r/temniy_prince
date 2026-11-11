"""Read a graph of uppercase package names from a test CSV file."""

import csv

from .validators import check_package


def read_test_repository(path: str) -> dict[str, list[str]]:
    """Read all rows and reject duplicate or missing package names."""
    packages = {}
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if reader.fieldnames != ["package", "dependencies"]:
            raise ValueError("Test CSV columns: package,dependencies")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError("Invalid test repository row")
            name = row["package"].strip()
            check_package(name, True)
            if name in packages:
                raise ValueError(f"Duplicate test package: {name}")
            dependencies = row["dependencies"].split()
            for dependency in dependencies:
                check_package(dependency, True)
            packages[name] = dependencies
    for name, dependencies in packages.items():
        for dependency in dependencies:
            if dependency not in packages:
                raise ValueError(f"Missing test package: {dependency} ({name})")
    return packages


def read_test_dependencies(path: str, package: str) -> list[str]:
    """Return the direct neighbours of one package."""
    packages = read_test_repository(path)
    if package not in packages:
        raise ValueError(f"Test package not found: {package}")
    return packages[package]
