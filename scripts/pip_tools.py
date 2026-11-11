"""Use pip only to collect reference results outside the analyzer."""

import subprocess
import sys
from pathlib import Path

from src.config import Config
from src.pypi_repository import normalize_name

INDEX_URLS = {
    "https://pypi.org/pypi": "https://pypi.org/simple",
    "https://test.pypi.org/pypi": "https://test.pypi.org/simple",
}


def run_command(command: list[str], env=None) -> str:
    """Capture a reference command and report its failure as an error."""
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=240, env=env
    )
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"Reference command failed: {message}")
    return result.stdout


def install_reference(config: Config, target: Path) -> str:
    """Install wheels into a temporary target, keeping this env intact."""
    if config.test_mode:
        raise ValueError("pip comparison requires a real Python package")
    index = INDEX_URLS.get(config.repository.rstrip("/"))
    if index is None:
        raise ValueError("pip comparison supports PyPI and TestPyPI URLs")
    command = [
        sys.executable, "-m", "pip", "--isolated",
        "--disable-pip-version-check", "--no-input", "--no-color",
        "install", "--progress-bar", "off", "--only-binary=:all:",
        "--ignore-installed", "--no-compile", "--target", str(target),
        "--index-url", index, f"{config.package}=={config.version}",
    ]
    return run_command(command)


def read_install_order(output: str) -> list[str]:
    """Read pip's installation sequence rather than its sorted summary."""
    prefix = "Installing collected packages: "
    for line in output.splitlines():
        if line.startswith(prefix):
            return [normalize_name(value.strip())
                    for value in line[len(prefix):].split(",")]
    raise ValueError("pip did not report its installation order")


def compare_orders(graph: dict, order: list, pip_order: list) -> dict:
    """Compare package sets and relative order of shared dependencies."""
    positions = {name: i for i, name in enumerate(pip_order)}
    violations = []
    for package, children in graph.items():
        for child in children:
            if package not in positions or child not in positions:
                continue
            if positions[child] > positions[package]:
                violations.append([package, child])
    return {
        "our_order": order,
        "pip_order": pip_order,
        "same_order": order == pip_order,
        "only_in_graph": sorted(set(order) - set(pip_order)),
        "only_in_pip": sorted(set(pip_order) - set(order)),
        "reversed_shared_edges": violations,
    }
