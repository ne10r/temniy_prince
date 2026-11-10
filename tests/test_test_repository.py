"""Tests for direct lookups in the local CSV repository."""

import pytest

from src.config import Config
from src.repository import get_dependencies
from src.test_repository import read_test_dependencies


@pytest.mark.parametrize("package,expected", [
    ("A", ["B", "C"]), ("B", ["D"]), ("D", []),
])
def test_direct_neighbours(package, expected):
    """Read one row without computing transitive dependencies."""
    config = Config(package, "examples/repository.csv", True, "1.0")
    assert get_dependencies(config) == expected


@pytest.mark.parametrize("content,message", [
    ("", "columns"),
    ("name,dependencies\nA,B\n", "columns"),
    ("package,dependencies\nA\n", "row"),
    ("package,dependencies\nA,B,C\n", "row"),
    ("package,dependencies\nA,B\nA,C\n", "Duplicate"),
    ("package,dependencies\nA,lower\n", "uppercase"),
    ("package,dependencies\nB,\n", "not found"),
])
def test_bad_test_repository(tmp_path, content, message):
    """Report malformed files and missing root packages."""
    path = tmp_path / "repository.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        read_test_dependencies(str(path), "A")


def test_cycle_is_not_followed(tmp_path):
    """Return a self dependency without starting any graph traversal."""
    path = tmp_path / "repository.csv"
    path.write_text("package,dependencies\nA,A\n", encoding="utf-8")
    assert read_test_dependencies(str(path), "A") == ["A"]
