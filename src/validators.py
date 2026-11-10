"""Validation of package and repository settings."""

import re
from pathlib import Path
from urllib.parse import SplitResult, urlsplit

PACKAGE_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
TEST_PACKAGE_PATTERN = r"[A-Z]+"
VERSION_PATTERN = (
    r"v?(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*"
    r"(?:[-_.]?(?:a|b|c|rc|alpha|beta|pre|preview)[-_.]?[0-9]*)?"
    r"(?:(?:-[0-9]+)|(?:[-_.]?(?:post|rev|r)[-_.]?[0-9]*))?"
    r"(?:[-_.]?dev[-_.]?[0-9]*)?"
    r"(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?"
)
ALLOWED_SCHEMES = ("http", "https")


def parse_test_mode(value: str) -> bool:
    """Convert true or false from the config into a boolean."""
    if value.lower() not in ("true", "false"):
        raise ValueError("test_mode must be true or false")
    return value.lower() == "true"


def check_package(package: str, test_mode: bool) -> None:
    """Check a Python package name or an uppercase test name."""
    pattern = TEST_PACKAGE_PATTERN if test_mode else PACKAGE_PATTERN
    if not re.fullmatch(pattern, package):
        if test_mode:
            raise ValueError("Test package must use uppercase Latin letters")
        raise ValueError("Invalid Python package name")


def check_version(version: str) -> None:
    """Check the syntax of a Python package version."""
    if not re.fullmatch(VERSION_PATTERN, version, re.IGNORECASE):
        raise ValueError("Invalid version; use e.g. 1.2.3 or 2.0rc1")


def check_url(repository: str) -> None:
    """Check a repository URL without sending a network request."""
    if any(char.isspace() or not char.isprintable() for char in repository):
        raise ValueError("Repository URL contains whitespace or controls")
    try:
        url = urlsplit(repository)
        port = url.port
    except ValueError as error:
        raise ValueError("Invalid repository URL") from error
    check_url_fields(url)
    if url.netloc.endswith(":"):
        raise ValueError("Repository URL has an empty port")
    if port is not None and not port:
        raise ValueError("Repository URL port must be positive")


def check_url_fields(url: SplitResult) -> None:
    """Check the scheme, host and optional URL parts."""
    if url.scheme not in ALLOWED_SCHEMES or not url.hostname:
        raise ValueError("Repository must be an HTTP or HTTPS URL")
    if url.username is not None or url.password is not None:
        raise ValueError("Repository URL must not contain credentials")
    if url.query or url.fragment:
        raise ValueError("Repository URL must not have query or fragment")


def check_repository(
    repository: str, test_mode: bool, config_dir: Path
) -> str:
    """Check the URL or resolve a test file relative to its config."""
    if not repository:
        raise ValueError("repository must not be empty")
    if not test_mode:
        check_url(repository)
        return repository

    path = Path(repository)
    if not path.is_absolute():
        path = config_dir / path
    if not path.is_file():
        raise ValueError(f"Test repository file not found: {path}")
    with path.open("rb") as file:
        file.read(1)
    return str(path.resolve())
