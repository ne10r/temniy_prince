"""Load package neighbours from PyPI-compatible JSON metadata."""

import re
from urllib.parse import quote

from .config import Config
from .repository import fetch_metadata, get_dependencies, parse_dependencies
from .validators import PACKAGE_PATTERN


def normalize_name(name: str) -> str:
    """Use the same graph vertex for case and separator variants."""
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(declaration: str) -> str:
    """Read a declared package name without resolving environment markers."""
    requirement = declaration.split(";", 1)[0].strip()
    pattern = rf"({PACKAGE_PATTERN})(?:\s*\[[\w.,\s-]+\])?\s*(.*)"
    match = re.fullmatch(pattern, requirement)
    if match is None:
        raise ValueError(f"Invalid dependency declaration: {declaration}")
    name, constraint = match.groups()
    if constraint.startswith("@"):
        raise ValueError(f"Direct URL dependency is not supported: {name}")
    if constraint and constraint[0] not in "<>=!~(":
        raise ValueError(f"Invalid dependency declaration: {declaration}")
    return normalize_name(name)


class PyPIRepository:
    """Keep the root release fixed and read current child metadata."""

    def __init__(self, config: Config) -> None:
        """Save the repository settings and normalized root name."""
        self.config = config
        self.root = normalize_name(config.package)

    def get_children(self, package: str) -> list[str]:
        """Return all declared neighbours of one graph vertex."""
        if package == self.root:
            declarations = get_dependencies(self.config)
        else:
            base = self.config.repository.rstrip("/")
            url = f"{base}/{quote(package, safe='')}/json"
            declarations = parse_dependencies(fetch_metadata(url))
        return [requirement_name(value) for value in declarations]
