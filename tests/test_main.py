"""CLI tests using a separate Python process."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def run_app(*args):
    """Run the CLI from the repository root."""
    return subprocess.run(
        [sys.executable, "-m", "src.main", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=10
    )


def test_successful_output(config_file, repository_server):
    """Print direct dependencies from the configured release URL."""
    base, routes, requested = repository_server
    dependencies = ["urllib3<3,>=1.21.1", 'extra-lib; extra == "test"']
    routes["/pypi/requests/2.32.3/json"] = (
        200, {"info": {"requires_dist": dependencies}}
    )
    path = config_file(repository=base)
    result = run_app("--config", str(path))
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == dependencies
    assert requested == ["/pypi/requests/2.32.3/json"]


def test_empty_release(config_file, repository_server):
    """Explain when the release declares no dependencies."""
    base, routes, _ = repository_server
    routes["/pypi/requests/2.32.3/json"] = (200, {"info": {}})
    result = run_app("--config", str(config_file(repository=base)))
    assert result.returncode == 0
    assert result.stdout == "No direct dependencies declared.\n"
    assert result.stderr == ""


@pytest.mark.parametrize("status,data,message", [
    (404, {}, "Package or version not found"),
    (503, {}, "Repository returned HTTP 503"),
    (200, b"not-json", "Repository returned invalid JSON"),
    (200, {"info": []}, "info object"),
])
def test_repository_error(
    config_file, repository_server, status, data, message
):
    """Report repository errors without partial output or tracebacks."""
    base, routes, _ = repository_server
    routes["/pypi/requests/2.32.3/json"] = (status, data)
    result = run_app("--config", str(config_file(repository=base)))
    assert result.returncode == 1
    assert result.stdout == ""
    assert message in result.stderr
    assert "Traceback" not in result.stderr


def test_local_repository():
    """Print only the direct test neighbours, without following B or C."""
    result = run_app("--config", "configs/test.csv")
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["B", "C"]
    assert result.stderr == ""


@pytest.mark.parametrize("version,dependency", [
    ("1.0", "core<2"), ("2.0", "core>=2"),
])
def test_version_changes_dependencies(
    config_file, repository_server, version, dependency
):
    """Select the requested release rather than the latest release."""
    base, routes, requested = repository_server
    for release, requirement in [("1.0", "core<2"), ("2.0", "core>=2")]:
        routes[f"/pypi/requests/{release}/json"] = (
            200, {"info": {"requires_dist": [requirement]}}
        )
    path = config_file(repository=base, version=version)
    result = run_app("--config", str(path))
    assert result.returncode == 0
    assert result.stdout.splitlines() == [dependency]
    assert result.stderr == ""
    assert requested == [f"/pypi/requests/{version}/json"]


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
    assert result.returncode == 2


def test_help():
    """Show the configuration file option in help."""
    result = run_app("--help")
    assert result.returncode == 0
    assert "--config" in result.stdout
