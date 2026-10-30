#!/usr/bin/env python3
"""Localhost-only AMOS GitHub Webhook receiver. External Caddy route is separate."""
from __future__ import annotations

import argparse
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aimeton_memory_os.webhook_inbox import MAX_SIZE, InvalidWebhook, insert_receipt, validate


def handler_factory(database: Path, wake_file: Path, key: bytes):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/hooks/amos/github":
                self.send_error(404)
                return
            try:
                size = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                size = -1
            if size < 0 or size > MAX_SIZE:
                self.send_error(413)
                return
            try:
                receipt = validate(
                    {name: self.headers.get(name, "") for name in
                     ("X-GitHub-Delivery", "X-GitHub-Event", "X-Hub-Signature-256")},
                    self.rfile.read(size),
                    key,
                )
            except InvalidWebhook:
                self.send_error(403)
                return
            try:
                insert_receipt(database, receipt)
                # A repeated signed delivery is allowed to retry a failed wake.
                wake_file.parent.mkdir(parents=True, exist_ok=True)
                with wake_file.open("ab") as output:
                    output.write(b"1")
            except OSError:
                self.send_error(503)
                return
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, fmt, *args):
            # Never log untrusted request headers or bodies.
            return
    return Handler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8769)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--wake-file", required=True)
    args = parser.parse_args()
    # Deny public bind; use an authenticated HTTPS reverse proxy.
    if args.listen not in ("127.0.0.1", "::1"):
        parser.error("receiver must bind to loopback")
    key = Path(args.key_file).read_bytes().strip()
    if len(key) < 32:
        parser.error("shared key must have at least 32 bytes")
    server = ThreadingHTTPServer((args.listen, args.port), handler_factory(
        Path(args.db), Path(args.wake_file), key
    ))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
