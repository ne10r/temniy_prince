"""Show dependency-first order for the local example graphs."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ["test", "leaf", "disconnected", "cycle", "self_cycle", "missing"]


def main() -> int:
    """Display orders and report cycles as ordering errors."""
    success = True
    for name in EXAMPLES:
        print(f"\nExample: {name}", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--config",
             str(ROOT / "configs" / f"{name}.csv"), "--order"],
            cwd=ROOT, timeout=20
        )
        expected = 1 if name in ("cycle", "self_cycle", "missing") else 0
        if result.returncode != expected:
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
