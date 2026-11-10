"""Demonstrate stage 2 against a local PyPI-like JSON API."""

import csv
import json
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parent.parent
RELEASES = {
    "/pypi/demo/1.0/json": {"info": {
        "requires_dist": ["core>=1,<2", 'legacy; python_version < "3.10"']
    }},
    "/pypi/demo/2.0/json": {"info": {
        "requires_dist": ["core>=2", 'fast; extra == "speed"']
    }},
    "/pypi/demo/3.0/json": {"info": {"requires_dist": []}},
}


class RepositoryHandler(BaseHTTPRequestHandler):
    """Serve several releases and two deliberately broken responses."""

    def do_GET(self) -> None:
        """Return release JSON, invalid JSON or an HTTP error."""
        data = RELEASES.get(self.path)
        status = 200 if data is not None else 404
        body = json.dumps(data).encode()
        if self.path == "/pypi/demo/4.0/json":
            status, body = 200, b"not-json"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        """Hide routine HTTP access logs during the demonstration."""


def run_example(
    directory: Path, base: str, version: str, expected_code: int
) -> bool:
    """Write a CSV config and run the real CLI for one release."""
    path = directory / f"release_{version}.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["package", "repository", "test_mode", "version"])
        writer.writerow(["demo", base, "false", version])
    print(f"\nRelease demo {version}", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--config", str(path)],
        cwd=ROOT, capture_output=True, text=True, timeout=20
    )
    print(result.stdout + result.stderr, end="", flush=True)
    return result.returncode == expected_code


def main() -> int:
    """Show different versions, an empty list, bad JSON and HTTP 404."""
    cases = [("1.0", 0), ("2.0", 0), ("3.0", 0), ("4.0", 1), ("9.0", 1)]
    with tempfile.TemporaryDirectory() as directory:
        with ThreadingHTTPServer(("127.0.0.1", 0), RepositoryHandler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            base = f"http://{host}:{port}/pypi"
            try:
                results = [run_example(Path(directory), base, version, code)
                           for version, code in cases]
            finally:
                server.shutdown()
                thread.join(timeout=5)
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
