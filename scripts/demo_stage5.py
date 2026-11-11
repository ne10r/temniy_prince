"""Render three package graphs and compare them with pipdeptree."""

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_config
from src.graph import load_graph
from src.pypi_repository import normalize_name
from src.visualization import render_graph, show_image
from .pip_tools import install_reference, run_command

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ["dateutil", "dotenv", "six"]


def collect_reference(config, python: str) -> dict:
    """Ask pipdeptree about a separately installed reference package."""
    command = [python, "-m", "pipdeptree", "--packages", config.package]
    with tempfile.TemporaryDirectory(prefix="tree-reference-") as directory:
        target = Path(directory) / "packages"
        install_log = install_reference(config, target)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(target)
        tree = json.loads(run_command(command + ["--json-tree"], env))
        text = run_command(command, env)
    return {
        "tree": tree, "text": text, "pip_stdout": install_log,
        "pipdeptree_version": run_command(
            [python, "-m", "pipdeptree", "--version"]
        ).strip(),
    }


def flatten_tree(tree: list) -> dict:
    """Convert the reference tree to adjacency lists iteratively."""
    graph = {}
    stack = list(reversed(tree))
    while stack:
        node = stack.pop()
        name = normalize_name(node["key"])
        children = node["dependencies"]
        graph[name] = [normalize_name(child["key"]) for child in children]
        stack.extend(reversed(children))
    return graph


def compare_graphs(graph: dict, reference: dict) -> dict:
    """Report differences in nodes and directed dependency edges."""
    edges = {(name, child) for name, children in graph.items()
             for child in children}
    reference_edges = {(name, child) for name, children in reference.items()
                       for child in children}
    return {
        "same_graph": set(graph) == set(reference) and edges == reference_edges,
        "only_in_graph": sorted(set(graph) - set(reference)),
        "only_in_reference": sorted(set(reference) - set(graph)),
        "extra_edges": sorted(edges - reference_edges),
        "missing_edges": sorted(reference_edges - edges),
    }


def save_json(path: Path, value) -> None:
    """Save a readable UTF-8 reference result."""
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def create_example(name: str, args: argparse.Namespace) -> Path:
    """Save the D2 image, reference tree and comparison for one package."""
    config = load_config(str(ROOT / "configs" / f"{name}.csv"))
    graph, cycles = load_graph(config)
    root = next(iter(graph))
    image_path = Path(args.output_dir) / f"{name}.svg"
    source, image = render_graph(graph, cycles, root, image_path, args.d2)
    reference = collect_reference(config, args.reference_python)
    reference_graph = flatten_tree(reference["tree"])
    if root not in reference_graph:
        raise ValueError(f"pipdeptree did not return the root: {root}")
    report = compare_graphs(graph, reference_graph)
    report.update({
        "package": config.package, "version": config.version,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "graph": graph,
        "reference_graph": reference_graph, "d2_source": str(source),
        "image": str(image), "reference": reference,
    })
    reports = Path(args.report_dir)
    reports.mkdir(parents=True, exist_ok=True)
    save_json(reports / f"{name}.json", report)
    (reports / f"{name}-pipdeptree.txt").write_text(
        reference["text"], encoding="utf-8"
    )
    return image


def parse_args() -> argparse.Namespace:
    """Read renderer, output and isolated reference-tool options."""
    parser = argparse.ArgumentParser(description="Three D2 package examples")
    parser.add_argument("--d2", help="Path to the D2 executable")
    parser.add_argument("--output-dir", default="examples/visualizations")
    parser.add_argument("--report-dir", default="reports/stage5")
    folder = "Scripts" if os.name == "nt" else "bin"
    executable = "python.exe" if os.name == "nt" else "python"
    reference = ROOT / ".tools" / "reference" / folder / executable
    parser.add_argument("--reference-python", default=str(reference))
    parser.add_argument("--no-open", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Create three visualizations and their actual reference comparisons."""
    args = parse_args()
    try:
        for name in EXAMPLES:
            image = create_example(name, args)
            print(f"Saved example: {image}")
            if not args.no_open:
                show_image(image)
    except (OSError, ValueError, csv.Error,
            subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
