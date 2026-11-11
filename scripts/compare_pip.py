"""Save an actual pip installation order for comparison with stage 4."""

import argparse
import csv
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_config
from src.graph import load_graph
from src.order import get_load_order
from .pip_tools import compare_orders, install_reference, read_install_order


def collect_comparison(config_path: str) -> dict:
    """Build our order first, then collect a separate pip reference."""
    config = load_config(config_path)
    if config.test_mode:
        raise ValueError("pip comparison requires a real Python package")
    graph, cycles = load_graph(config)
    order = get_load_order(graph, next(iter(graph)))
    with tempfile.TemporaryDirectory(prefix="package-reference-") as temp:
        output = install_reference(config, Path(temp) / "packages")
    comparison = compare_orders(graph, order, read_install_order(output))
    comparison.update({
        "package": config.package, "version": config.version,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(), "graph": graph,
        "pip_stdout": output,
        "notes": [
            "Graph includes conditional and optional declarations.",
            "Child versions in the graph use latest release metadata.",
            "pip evaluates markers and resolves compatible versions.",
            "Independent packages may have different valid orders.",
        ],
    })
    return comparison


def main() -> int:
    """Write the comparison as JSON without running any test suite."""
    parser = argparse.ArgumentParser(description="Compare order with pip")
    parser.add_argument("--config", default="configs/dateutil.csv")
    parser.add_argument("--output", default="reports/stage4/dateutil.json")
    args = parser.parse_args()
    try:
        comparison = collect_comparison(args.config)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
    except (OSError, ValueError, csv.Error,
            subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Comparison saved: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
