"""Read direct dependencies from a Python package repository."""

import json
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .config import Config
from .test_repository import read_test_dependencies

REQUEST_TIMEOUT = 10


def build_release_url(repository: str, package: str, version: str) -> str:
    """Build the JSON API URL for one specific package release."""
    package = quote(package, safe="")
    version = quote(version, safe="")
    return f"{repository.rstrip('/')}/{package}/{version}/json"


def fetch_metadata(url: str) -> dict:
    """Request release metadata without invoking a package manager."""
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            raise ValueError("Package or version not found") from error
        raise ValueError(f"Repository returned HTTP {error.code}") from error
    except URLError as error:
        raise ValueError(f"Cannot reach repository: {error.reason}") from error
    except TimeoutError as error:
        raise ValueError("Repository request timed out") from error
    except HTTPException as error:
        raise ValueError(
            "Repository returned an incomplete response"
        ) from error
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("Repository returned invalid JSON") from error


def parse_dependencies(metadata: dict) -> list[str]:
    """Read Requires-Dist entries, preserving constraints and markers."""
    if not isinstance(metadata, dict):
        raise ValueError("Release metadata must be a JSON object")
    info = metadata.get("info")
    if not isinstance(info, dict):
        raise ValueError("Release metadata must contain an info object")
    dependencies = info.get("requires_dist")
    if dependencies is None:
        return []
    if not isinstance(dependencies, list):
        raise ValueError("requires_dist must be a list or null")
    for dependency in dependencies:
        if not isinstance(dependency, str) or not dependency.strip():
            raise ValueError("Dependency must be a non-empty string")
        if any(char in dependency for char in "\r\n"):
            raise ValueError("Dependency must fit on one line")
    return dependencies


def get_dependencies(config: Config) -> list[str]:
    """Return only the configured package's direct dependencies."""
    if config.test_mode:
        return read_test_dependencies(config.repository, config.package)
    url = build_release_url(
        config.repository, config.package, config.version
    )
    return parse_dependencies(fetch_metadata(url))
