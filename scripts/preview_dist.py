#!/usr/bin/env python3
"""Server locale della build con lo stesso fallback 404 di GitHub Pages."""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class PreviewHandler(SimpleHTTPRequestHandler):
    """Serve 404.html mantenendo status 404 anche per route annidate inesistenti."""

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        if code != 404:
            super().send_error(code, message, explain)
            return
        not_found = Path(self.directory) / "404.html"
        if not not_found.is_file():
            super().send_error(code, message, explain)
            return
        payload = not_found.read_bytes()
        self.send_response(404, "Not Found")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("dist"))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    directory = args.directory.resolve()
    if not (directory / "404.html").is_file():
        raise SystemExit(f"Build non valida: 404.html assente in {directory}")
    handler = partial(PreviewHandler, directory=str(directory))
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print(f"Preview OV: http://{args.bind}:{args.port}/ (root {directory})")
        server.serve_forever()


if __name__ == "__main__":
    main()
