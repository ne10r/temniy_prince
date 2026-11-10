"""Run successful examples and errors for all four parameters."""

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_example(path: Path, expected_code: int) -> bool:
    """Run one example and check its exit code."""
    print(f"\nConfig: {path.name}", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--config", str(path)],
        cwd=ROOT, timeout=10
    )
    return result.returncode == expected_code


def write_config(path: Path, field: str, value: str) -> None:
    """Write a config with one deliberately invalid parameter."""
    values = {
        "package": "requests", "repository": "https://pypi.org/pypi",
        "test_mode": "false", "version": "2.32.3",
    }
    values[field] = value
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=values)
        writer.writeheader()
        writer.writerow(values)


def main() -> int:
    """Demonstrate valid configs and validation errors."""
    results = [
        run_example(ROOT / "configs/pypi.csv", 0),
        run_example(ROOT / "configs/test.csv", 0),
    ]
    invalid = {
        "package": "bad name", "repository": "ftp://example.org",
        "test_mode": "yes", "version": "latest",
    }
    with tempfile.TemporaryDirectory() as directory:
        for field, value in invalid.items():
            path = Path(directory) / f"invalid_{field}.csv"
            write_config(path, field, value)
            results.append(run_example(path, 1))
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
