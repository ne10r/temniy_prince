"""CLI tests using a separate Python process."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ARGUMENT_ERROR_EXIT_CODE = 2


def run_app(*args):
    """Run the CLI from the repository root."""
    return subprocess.run(
        [sys.executable, "-m", "src.main", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=10
    )


def test_successful_output():
    """Print exactly four key-value settings."""
    result = run_app()
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "package=requests",
        "repository=https://pypi.org/pypi",
        "test_mode=false",
        "version=2.32.3",
    ]


@pytest.mark.parametrize("field,value", [
    ("package", "bad name"),
    ("repository", "ftp://example.org"),
    ("test_mode", "yes"),
    ("version", "latest"),
])
def test_parameter_errors(config_file, field, value):
    """Return an error for each invalid setting, without a traceback."""
    result = run_app("--config", str(config_file(**{field: value})))
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("Error:")
    assert "Traceback" not in result.stderr


def test_missing_config_error(tmp_path):
    """Return a useful error if the CSV file is missing."""
    result = run_app("--config", str(tmp_path / "missing.csv"))
    assert result.returncode == 1
    assert "Error:" in result.stderr


def test_unknown_argument():
    """Do not accept package settings outside the CSV file."""
    result = run_app("--package", "requests")
    assert result.returncode == ARGUMENT_ERROR_EXIT_CODE


def test_help():
    """Show the configuration file option in help."""
    result = run_app("--help")
    assert result.returncode == 0
    assert "--config" in result.stdout
