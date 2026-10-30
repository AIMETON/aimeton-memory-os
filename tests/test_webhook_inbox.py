from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.webhook_inbox import InvalidWebhook, insert_receipt, validate, begin_batch, finish_batch, pending_count

KEY = b"x" * 40
DELIVERY = "8d9cdf8b-aaaa-4c1e-9f8b-333333333333"


def signed(repo="AIMETON/Choke_ring_antenna", kind="pull_request", action="synchronize"):
    body = json.dumps({"repository": {"full_name": repo}, "action": action}).encode()
    headers = {
        "X-GitHub-Delivery": DELIVERY,
        "X-GitHub-Event": kind,
        "X-Hub-Signature-256": "sha256=" + hmac.new(KEY, body, hashlib.sha256).hexdigest(),
    }
    return headers, body


class WebhookInboxTests(unittest.TestCase):
    def test_hmac_and_source_allowlist(self):
        headers, body = signed()
        self.assertEqual(validate(headers, body, KEY), (DELIVERY, "AIMETON/Choke_ring_antenna", "pull_request"))
        for altered in [
            {**headers, "X-Hub-Signature-256": "sha256=" + "0" * 64},
            {**headers, "X-GitHub-Delivery": "bad-id"},
        ]:
            with self.assertRaises(InvalidWebhook):
                validate(altered, body, KEY)
        with self.assertRaises(InvalidWebhook):
            validate(headers, body + b" ", KEY)
        for repo, kind in [
            ("AIMETON/Choke_ring_antenna", "issue_comment"),
            ("AIMETON/untrusted", "pull_request"),
            ("AIMETON/aimeton-memory-os", "pull_request"),
        ]:
            h, payload = signed(repo, kind)
            with self.assertRaises(InvalidWebhook):
                validate(h, payload, KEY)

    def test_durable_receipt_idempotent_and_restart_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "inbox.db"
            receipt = validate(*signed(), KEY)
            self.assertTrue(insert_receipt(db, receipt))
            self.assertFalse(insert_receipt(db, receipt))
            conn = sqlite3.connect(db)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT status FROM deliveries").fetchone()[0], "pending")
            conn.close()
            self.assertFalse(insert_receipt(db, receipt))
            self.assertEqual(sqlite3.connect(db).execute("SELECT COUNT(*) FROM deliveries").fetchone()[0], 1)

    def test_batch_ack_does_not_lose_deliveries_arriving_during_processing(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "inbox.db"
            first = (DELIVERY, "AIMETON/Choke_ring_antenna", "pull_request")
            second = ("8d9cdf8b-bbbb-4c1e-9f8b-444444444444", "AIMETON/aimeton-memory-os", "issues")
            insert_receipt(db, first)
            claimed = begin_batch(db)
            self.assertEqual(claimed, [DELIVERY])
            insert_receipt(db, second)
            self.assertEqual(pending_count(db), 1)
            self.assertEqual(finish_batch(db, claimed, success=True), 1)
            self.assertEqual(pending_count(db), 1)
            self.assertEqual(begin_batch(db), [second[0]])
            self.assertEqual(finish_batch(db, [second[0]], success=False), 1)
            self.assertEqual(pending_count(db), 1)
            # A crashed processing batch is re-claimed by the next exclusive worker.
            self.assertEqual(begin_batch(db), [second[0]])
            self.assertEqual(begin_batch(db), [second[0]])
            self.assertEqual(finish_batch(db, [second[0]], success=True), 1)
            self.assertEqual(pending_count(db), 0)

    def test_reject_oversize_and_malformed_signed_body(self):
        headers, body = signed()
        with self.assertRaises(InvalidWebhook):
            validate(headers, b"x" * 262145, KEY)
        broken = b"{"
        h = {**headers, "X-Hub-Signature-256": "sha256=" + hmac.new(KEY, broken, hashlib.sha256).hexdigest()}
        with self.assertRaises(InvalidWebhook):
            validate(h, broken, KEY)


if __name__ == "__main__":
    unittest.main()
