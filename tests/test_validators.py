"""Tests for individual parameter checks."""

import pytest

from src.validators import check_package, check_url, check_version
from src.validators import parse_test_mode


@pytest.mark.parametrize("name", [
    "requests", "my-package", "my_package", "my.package", "A", "7zip"
])
def test_package_names(name):
    """Accept Python distribution names."""
    check_package(name, False)


@pytest.mark.parametrize("name", [
    "", "bad name", "-requests", "requests_", "../requests", "foo/bar"
])
def test_invalid_package_names(name):
    """Reject invalid package names."""
    with pytest.raises(ValueError):
        check_package(name, False)


@pytest.mark.parametrize("name", ["A", "ABC", "Z"])
def test_uppercase_test_names(name):
    """Accept uppercase test graph node names."""
    check_package(name, True)


@pytest.mark.parametrize("name", ["a", "A1", "A-B", "А", ""])
def test_invalid_test_names(name):
    """Reject non-Latin and non-uppercase test graph names."""
    with pytest.raises(ValueError):
        check_package(name, True)


@pytest.mark.parametrize("value,expected", [
    ("true", True), ("false", False), ("TRUE", True), ("False", False)
])
def test_boolean_values(value, expected):
    """Read true and false without using bool on a string."""
    assert parse_test_mode(value) is expected


@pytest.mark.parametrize("value", ["", "yes", "no", "1", "0", "maybe"])
def test_invalid_boolean_values(value):
    """Reject unsupported boolean spellings."""
    with pytest.raises(ValueError):
        parse_test_mode(value)


@pytest.mark.parametrize("version", [
    "1", "1.2.3", "2.0rc1", "1!2.0+cpu", "v1.0", "1.0.post1",
    "1.0.dev2", "1.0-1", "1.0b1.post2.dev3+linux_x86",
])
def test_python_versions(version):
    """Accept release, prerelease and development version forms."""
    check_version(version)


@pytest.mark.parametrize("version", [
    "", "latest", "1..2", "1.", "-1", "1 2", "../1", "1.0+"
])
def test_invalid_versions(version):
    """Reject malformed versions."""
    with pytest.raises(ValueError):
        check_version(version)


@pytest.mark.parametrize("url", [
    "https://pypi.org/pypi", "http://localhost:8080/pypi",
    "https://example.org/simple/",
])
def test_repository_urls(url):
    """Accept repository URLs without accessing them."""
    check_url(url)


@pytest.mark.parametrize("url", [
    "", "pypi.org", "ftp://pypi.org", "https://", "https://[bad",
    "https://example.org:bad", "https://example.org:65536",
    "https://example.org:0", "https://example.org:",
    "https://user:password@example.org", "https://example.org?a=b",
    "https://example.org/#fragment", "https://example.org/bad path",
    "https://example.org/\tpath",
])
def test_invalid_repository_urls(url):
    """Reject invalid URL schemes, hosts, ports and extra fields."""
    with pytest.raises(ValueError):
        check_url(url)
