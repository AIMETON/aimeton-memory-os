from __future__ import annotations

import concurrent.futures
import http.client
import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aimeton_memory_os.audit_export import export_synthetic_audit_pack
from aimeton_memory_os.audit_grants import (
    issue_synthetic_grant, revoke_synthetic_grant, update_continuous_synthetic_snapshot,
)
from aimeton_memory_os.audit_http import LoopbackAuditServer

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/audit_synthetic_policy_input.json"


class AuditHTTPG3Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "grants.sqlite"
        source = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.snapshot, self.manifest = export_synthetic_audit_pack(source)
        self.expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(
            timespec="seconds").replace("+00:00", "Z")
        self.server = LoopbackAuditServer(("127.0.0.1", 0), self.db, FIXTURE)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._shutdown)

    def _shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            status = response.status
            data = response.read()
            return status, dict(response.getheaders()), (json.loads(data) if data else {})
        finally:
            conn.close()

    def grant(self, mode="one_time"):
        return issue_synthetic_grant(
            self.db, self.snapshot, self.manifest, mode=mode, expires_at=self.expiry
        )

    def redeem(self, capability, headers=None):
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        return self.request("POST", "/v1/redeem",
                            json.dumps({"capability": capability}), h)

    def test_loopback_only_and_preview_does_not_redeem(self):
        with self.assertRaises(ValueError):
            LoopbackAuditServer(("0.0.0.0", 0), self.db, FIXTURE)
        grant = self.grant()
        p = "/v1/shares/" + grant["grant_id"] + "/preview"
        for _ in range(2):
            status, headers, obj = self.request("GET", p)
            self.assertEqual(status, 200)
            self.assertEqual(obj["release_status"], "NON_PUBLIC_SYNTHETIC_TEST_ONLY")
            self.assertEqual(headers["Cache-Control"], "no-store, private")
            self.assertNotIn("capability", str(obj))
        status, headers, value = self.redeem(grant["capability"])
        self.assertEqual(status, 200)
        self.assertEqual(value["manifest"], self.manifest)
        self.assertEqual(value["snapshot"], self.snapshot)
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(self.redeem(grant["capability"])[0], 403)

    def test_concurrent_redemption_single_winner(self):
        grant = self.grant()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(
                lambda _: self.redeem(grant["capability"])[0], range(16)
            ))
        self.assertEqual(statuses.count(200), 1)
        self.assertEqual(statuses.count(403), 15)

    def test_revocation_and_continuing_grant(self):
        grant = self.grant("project_continuous")
        self.assertEqual(self.redeem(grant["capability"])[0], 200)
        self.assertEqual(self.redeem(grant["capability"])[0], 200)
        self.assertTrue(revoke_synthetic_grant(self.db, grant["grant_id"]))
        self.assertEqual(self.redeem(grant["capability"])[0], 403)
        self.assertEqual(self.request(
            "GET", "/v1/shares/" + grant["grant_id"] + "/preview")[0], 404)

    def test_fail_closed_requests_and_no_token_or_raw_data_in_errors(self):
        grant = self.grant()
        tests = [
            ("GET", "/v1/shares/" + grant["grant_id"] + "/preview?token=secret", None, {}, 404),
            ("GET", "/../../etc/passwd", None, {}, 404),
            ("GET", "/v1/%2e%2e/redeem", None, {}, 404),
            ("GET", "/v1/redeem", None, {}, 404),
            ("HEAD", "/v1/shares/" + grant["grant_id"] + "/preview", None, {}, 405),
            ("POST", "/v1/redeem", "{}", {"Content-Type": "text/plain"}, 415),
            ("POST", "/v1/redeem", "{", {"Content-Type": "application/json"}, 403),
            ("POST", "/v1/redeem", json.dumps({"capability": grant["capability"], "admin": True}),
             {"Content-Type": "application/json"}, 403),
            ("PUT", "/v1/redeem", "{}", {}, 405),
            ("GET", "/health", None, {"Origin": "https://attacker.invalid"}, 403),
            ("POST", "/v1/redeem", json.dumps({"capability": grant["capability"]}),
             {"Content-Type": "application/json", "Origin": "https://attacker.invalid"}, 403),
            ("GET", "/health", None, {"Host": "hostile.invalid"}, 403),
        ]
        for method, path, body, headers, expected in tests:
            with self.subTest(method=method, path=path, headers=headers):
                status, received_headers, obj = self.request(method, path, body, headers)
                self.assertEqual(status, expected)
                self.assertNotIn(grant["capability"], str(obj))
                self.assertNotIn("NEVER_EXPORT_THIS_SECRET", str(obj))
                self.assertNotIn("Access-Control-Allow-Origin", received_headers)
        self.assertEqual(self.redeem(grant["capability"])[0], 200)

    def test_head_returns_no_body_and_does_not_redeem(self):
        grant = self.grant()
        path = "/v1/shares/" + grant["grant_id"] + "/preview"
        status, headers, body = self.request("HEAD", path)
        self.assertEqual(status, 405)
        self.assertEqual(headers["Content-Length"], "0")
        self.assertEqual(body, {})
        self.assertEqual(self.redeem(grant["capability"])[0], 200)

    def test_no_http_admin_and_unknown_capability(self):
        self.assertEqual(self.request("POST", "/v1/admin/grants", "{}",
                                      {"Content-Type": "application/json"})[0], 404)
        self.assertEqual(self.redeem("x" * 64)[0], 403)
        self.assertEqual(self.request("GET", "/health")[2], {"status": "synthetic_loopback_only"})

    def test_snapshot_version_change_blocks_mismatched_publication(self):
        grant = self.grant(mode="project_continuous")
        source = json.loads(FIXTURE.read_text())
        source["as_of_utc"] = "2026-11-02T00:00:00Z"
        updated, updated_manifest = export_synthetic_audit_pack(source)
        self.assertTrue(update_continuous_synthetic_snapshot(
            self.db, grant["grant_id"], self.manifest["snapshot_id"],
            updated, updated_manifest
        ))
        self.assertEqual(self.redeem(grant["capability"])[0], 409)


if __name__ == "__main__":
    unittest.main()
