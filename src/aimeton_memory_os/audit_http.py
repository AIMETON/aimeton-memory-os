"""G3 loopback-only synthetic audit HTTP transport.

No public edge, no admin issuance endpoint, no AMOS E0 database or GitHub access.
A one-time capability is redeemed and its synthetic pack delivered in ONE POST.
This handler is not a production network/security boundary.
"""
from __future__ import annotations

import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .audit_export import canonical_bytes, export_synthetic_audit_pack, verify_synthetic_audit_pack
from .audit_grants import preview_synthetic_grant, redeem_synthetic_grant

MAX_REQUEST_BYTES = 1024
MAX_RESPONSE_BYTES = 64 * 1024
SHARE_PATH = re.compile(r"^/v1/shares/([0-9a-f-]{36})/preview$")


class LoopbackAuditServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, db_path: str | Path, fixture_path: str | Path):
        host, port = address
        if host not in ("127.0.0.1", "::1"):
            raise ValueError("synthetic gateway must bind loopback only")
        source = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        snapshot, manifest = export_synthetic_audit_pack(source)
        verify_synthetic_audit_pack(snapshot, manifest)
        self.snapshot = snapshot
        self.manifest = manifest
        self.db_path = str(db_path)
        super().__init__(address, LoopbackAuditHandler)
        self.timeout = 2


class LoopbackAuditHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Never log user-controlled path, token, body or headers.
        return

    def _respond(self, status: int, obj: dict):
        body = canonical_bytes(obj)
        if len(body) > MAX_RESPONSE_BYTES:
            status, body = 500, canonical_bytes({"error": "internal"})
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, private")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _path(self):
        # Exact path parsing; no query tokens, encoded traversal or redirect.
        path = self.path
        if ("?" in path or "#" in path or "%" in path or ".." in path
                or len(path) > 120):
            return None
        return path

    def _host_ok(self):
        host = self.headers.get("Host", "")
        port = self.server.server_address[1]
        return host in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _request_safe(self):
        # Host checking also blocks DNS rebinding via arbitrary Host names.
        return self._host_ok() and not self.headers.get("Origin") and not self.headers.get("Transfer-Encoding")

    def do_HEAD(self):
        self._respond(405, {"error": "method_not_allowed"})

    def do_GET(self):
        if not self._request_safe():
            self._respond(403, {"error": "forbidden"})
            return
        path = self._path()
        if path == "/health":
            self._respond(200, {"status": "synthetic_loopback_only"})
            return
        match = SHARE_PATH.fullmatch(path or "")
        if match is None:
            self._respond(404, {"error": "not_found"})
            return
        try:
            key = str(uuid.UUID(match.group(1)))
            if key != match.group(1):
                raise ValueError("noncanonical grant id")
            value = preview_synthetic_grant(self.server.db_path, key)
        except (PermissionError, ValueError):
            self._respond(404, {"error": "not_found"})
            return
        self._respond(200, value)

    def do_POST(self):
        if not self._request_safe():
            self._respond(403, {"error": "forbidden"})
            return
        if self._path() != "/v1/redeem":
            self._respond(404, {"error": "not_found"})
            return
        if self.headers.get("Content-Type") != "application/json":
            self._respond(415, {"error": "unsupported_media_type"})
            return
        length = self.headers.get("Content-Length", "")
        if not length.isascii() or not length.isdecimal() or not (1 <= int(length) <= MAX_REQUEST_BYTES):
            self._respond(413, {"error": "invalid_content_length"})
            return
        raw = self.rfile.read(int(length))
        try:
            doc = json.loads(raw)
            if not isinstance(doc, dict) or set(doc) != {"capability"} or not isinstance(doc["capability"], str):
                raise ValueError("body contract")
            token = doc["capability"]
            receipt = redeem_synthetic_grant(self.server.db_path, token)
            if receipt["snapshot_id"] != self.server.manifest["snapshot_id"]:
                # In-memory demo publishes only one exact immutable snapshot.
                # Never serve different bytes under a mismatching version.
                self._respond(409, {"error": "snapshot_not_available"})
                return
            self._respond(200, {
                "mode": receipt["mode"],
                "manifest": self.server.manifest,
                "snapshot": self.server.snapshot,
            })
        except (ValueError, TypeError, UnicodeDecodeError, PermissionError):
            self._respond(403, {"error": "grant_unavailable"})

    def do_PUT(self):
        self._respond(405, {"error": "method_not_allowed"})

    def do_DELETE(self):
        self._respond(405, {"error": "method_not_allowed"})
