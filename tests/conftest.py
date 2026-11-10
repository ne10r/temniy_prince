"""Temporary configuration files used by tests."""

import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from src.config import CONFIG_FIELDS


@pytest.fixture
def config_file(tmp_path):
    """Create a CSV config with optional replacement values."""
    def create(**changes):
        """Write one configuration row into the temporary directory."""
        values = {
            "package": "requests",
            "repository": "https://pypi.org/pypi",
            "test_mode": "false",
            "version": "2.32.3",
        }
        values.update(changes)
        path = tmp_path / "config.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CONFIG_FIELDS)
            writer.writeheader()
            writer.writerow(values)
        return path

    return create


@pytest.fixture
def repository_server():
    """Serve configurable release responses on a local HTTP server."""
    routes = {}
    requested = []

    class Handler(BaseHTTPRequestHandler):
        """Return a configured status and JSON body for each path."""

        def do_GET(self):
            """Serve one metadata request."""
            requested.append(self.path)
            status, data = routes.get(self.path, (404, {}))
            body = data if isinstance(data, bytes) else json.dumps(data)
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            """Keep test output free of HTTP access logs."""

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            yield f"http://{host}:{port}/pypi", routes, requested
        finally:
            server.shutdown()
            thread.join(timeout=5)
