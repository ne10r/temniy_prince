"""Tests for release URLs, network failures and dependency metadata."""

import io
import json
from http.client import IncompleteRead
from urllib.error import HTTPError, URLError

import pytest

from src.config import Config
from src.repository import REQUEST_TIMEOUT, build_release_url, fetch_metadata
from src.repository import get_dependencies, parse_dependencies


@pytest.mark.parametrize("base,version,expected", [
    ("https://pypi.org/pypi", "2.32.3", "2.32.3"),
    ("https://example.org/custom/", "1!2.0", "1%212.0"),
    ("https://example.org/pypi", "1.0+cpu", "1.0%2Bcpu"),
])
def test_release_url(base, version, expected):
    """Include the specified release and escape version characters."""
    url = build_release_url(base, "my-package", version)
    assert url == f"{base.rstrip('/')}/my-package/{expected}/json"


def test_fetch_metadata(monkeypatch):
    """Use a bounded stdlib HTTP request accepting JSON."""
    metadata = {"info": {"requires_dist": ["dep>=1"]}}
    calls = []

    def open_response(request, timeout):
        """Return metadata in the same byte format as an HTTP response."""
        calls.append((request, timeout))
        return io.BytesIO(json.dumps(metadata).encode())

    monkeypatch.setattr("src.repository.urlopen", open_response)
    url = "https://example.org/pypi/demo/1.0/json"
    assert fetch_metadata(url) == metadata
    request, timeout = calls[0]
    assert request.full_url == url
    assert request.get_header("Accept") == "application/json"
    assert timeout == REQUEST_TIMEOUT


@pytest.mark.parametrize("error,message", [
    (HTTPError("url", 404, "missing", {}, None), "not found"),
    (HTTPError("url", 403, "denied", {}, None), "HTTP 403"),
    (HTTPError("url", 500, "failed", {}, None), "HTTP 500"),
    (URLError("DNS failed"), "Cannot reach repository: DNS failed"),
    (TimeoutError(), "timed out"),
    (IncompleteRead(b"{", 10), "incomplete response"),
], ids=["not-found", "forbidden", "server-error", "dns", "timeout", "body"])
def test_network_errors(monkeypatch, error, message):
    """Convert HTTP, DNS and timeout failures into readable errors."""
    def fail(*args, **kwargs):
        """Simulate a failed request."""
        raise error

    monkeypatch.setattr("src.repository.urlopen", fail)
    with pytest.raises(ValueError, match=message):
        fetch_metadata("https://example.org/pypi/demo/1.0/json")


@pytest.mark.parametrize("body", [b"not-json", b"{", b"\xff"])
def test_invalid_json(monkeypatch, body):
    """Reject malformed JSON and undecodable responses."""
    monkeypatch.setattr(
        "src.repository.urlopen", lambda *a, **kw: io.BytesIO(body)
    )
    with pytest.raises(ValueError, match="invalid JSON"):
        fetch_metadata("https://example.org/pypi/demo/1.0/json")


@pytest.mark.parametrize("metadata", [
    [], None, "text", {}, {"info": None}, {"info": []},
    {"info": {"requires_dist": "dep>=1"}},
    {"info": {"requires_dist": {"dep": "1"}}},
    {"info": {"requires_dist": [12]}},
    {"info": {"requires_dist": [""]}},
    {"info": {"requires_dist": ["  "]}},
    {"info": {"requires_dist": ["dep\nother"]}},
    {"info": {"requires_dist": ["dep\rother"]}},
])
def test_invalid_metadata(metadata):
    """Reject unexpected metadata structures and broken entries."""
    with pytest.raises(ValueError):
        parse_dependencies(metadata)


@pytest.mark.parametrize("info", [{}, {"requires_dist": None}, {
    "requires_dist": []
}])
def test_no_dependencies(info):
    """Missing, null and empty Requires-Dist fields declare no entries."""
    assert parse_dependencies({"info": info}) == []


def test_preserve_requirements():
    """Keep extras, version constraints, markers, order and direct URLs."""
    dependencies = [
        "dep[fast]>=1,<2",
        'other; python_version < "3.12"',
        'extra-dep; extra == "test"',
        "linked @ https://example.org/linked.whl",
    ]
    assert parse_dependencies({"info": {
        "requires_dist": dependencies
    }}) == dependencies


def test_only_requested_version(monkeypatch):
    """Use release-specific metadata without querying child packages."""
    urls = []

    def fetch(url):
        """Return two direct dependencies without expanding them."""
        urls.append(url)
        return {"info": {"requires_dist": ["child>=1", "other"]}}

    monkeypatch.setattr("src.repository.fetch_metadata", fetch)
    config = Config("demo", "https://example.org/pypi", False, "1.2")
    assert get_dependencies(config) == ["child>=1", "other"]
    assert urls == ["https://example.org/pypi/demo/1.2/json"]
