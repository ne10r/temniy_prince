"""Show graph traversal examples when explicitly started by the user."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ["test", "cycle", "self_cycle", "leaf", "disconnected", "missing"]


def main() -> int:
    """Run the sample CSV configurations and display their graphs."""
    success = True
    for name in EXAMPLES:
        print(f"\nExample: {name}", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--config",
             str(ROOT / "configs" / f"{name}.csv")],
            cwd=ROOT, timeout=20
        )
        expected = 1 if name == "missing" else 0
        if result.returncode != expected:
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
