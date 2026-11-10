"""Tests for CSV loading and configuration values."""

import csv

import pytest

from src.config import load_config


def test_load_pypi_config(config_file):
    """Read all four settings from CSV."""
    config = load_config(str(config_file()))
    assert config.get_info() == {
        "package": "requests",
        "repository": "https://pypi.org/pypi",
        "test_mode": False,
        "version": "2.32.3",
    }


def test_test_repository_path(config_file, tmp_path, monkeypatch):
    """Resolve the repository relative to CSV, not the current directory."""
    repo = tmp_path / "repo, example.csv"
    repo.write_text("package,dependencies\nA,B\nB,\n", encoding="utf-8")
    path = config_file(
        package="A", repository=repo.name, test_mode="true"
    )
    another_dir = tmp_path / "other"
    another_dir.mkdir()
    monkeypatch.chdir(another_dir)
    config = load_config(str(path))
    assert config.repository == str(repo.resolve())
    assert config.test_mode is True


def test_absolute_repository_path(config_file, tmp_path):
    """Accept an absolute test repository path."""
    repo = tmp_path / "repo.csv"
    repo.write_text("package,dependencies\nA,\n", encoding="utf-8")
    path = config_file(
        package="A", repository=str(repo), test_mode="true"
    )
    assert load_config(str(path)).repository == str(repo)


def test_missing_repository_file(config_file):
    """Reject a test repository that does not exist."""
    path = config_file(
        package="A", repository="missing.csv", test_mode="true"
    )
    with pytest.raises(ValueError, match="not found"):
        load_config(str(path))


def test_repository_is_directory(config_file, tmp_path):
    """Reject a directory instead of a test repository file."""
    path = config_file(
        package="A", repository=str(tmp_path), test_mode="true"
    )
    with pytest.raises(ValueError, match="not found"):
        load_config(str(path))


def test_trim_values(config_file):
    """Ignore surrounding spaces in CSV values."""
    config = load_config(str(config_file(package=" requests ")))
    assert config.package == "requests"


def test_bom_and_reordered_columns(tmp_path):
    """Accept UTF-8 BOM and a different column order."""
    path = tmp_path / "config.csv"
    path.write_text(
        "version,package,test_mode,repository\n"
        "1.0,requests,false,https://pypi.org/pypi\n",
        encoding="utf-8-sig",
    )
    assert load_config(str(path)).version == "1.0"


@pytest.mark.parametrize("text", [
    "",
    "package,repository,test_mode\nA,https://pypi.org,false\n",
    "package,repository,test_mode,unknown\nA,https://pypi.org,false,1\n",
    "package,repository,test_mode,test_mode\nA,https://pypi.org,false,1\n",
    "package,repository,test_mode,version\n",
    "package,repository,test_mode,version\nA,https://pypi.org,false\n",
    "package,repository,test_mode,version\nA,https://pypi.org,false,1,x\n",
    "package,repository,test_mode,version\n"
    "A,https://pypi.org,false,1\nB,https://pypi.org,false,1\n",
])
def test_invalid_csv_shape(tmp_path, text):
    """Reject invalid headers and incomplete or extra data rows."""
    path = tmp_path / "config.csv"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(str(path))


def test_broken_quotes(tmp_path):
    """Reject an unterminated quoted CSV value."""
    path = tmp_path / "config.csv"
    path.write_text(
        'package,repository,test_mode,version\n"unfinished',
        encoding="utf-8",
    )
    with pytest.raises(csv.Error):
        load_config(str(path))


def test_invalid_utf8(tmp_path):
    """Report invalid text encoding."""
    path = tmp_path / "config.csv"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(UnicodeError):
        load_config(str(path))


def test_missing_config(tmp_path):
    """Report an absent configuration file."""
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "absent.csv"))


@pytest.mark.parametrize("field", [
    "package", "repository", "test_mode", "version"
])
def test_empty_parameter(config_file, field):
    """Reject an empty value for each configurable parameter."""
    path = config_file(**{field: ""})
    with pytest.raises(ValueError):
        load_config(str(path))
