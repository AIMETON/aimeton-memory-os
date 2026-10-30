"""Signed webhook receipt boundary for read-only AMOS Shadow collection."""
import hashlib
import hmac
import json
import re
import sqlite3
from pathlib import Path

ALLOWED = {
    "AIMETON/aimeton-memory-os": {"issues", "issue_comment"},
    "AIMETON/Choke_ring_antenna": {"pull_request"},
}
MAX_SIZE = 262144


class InvalidWebhook(ValueError):
    pass


def validate(headers, body, shared_key):
    if not shared_key or len(body) > MAX_SIZE:
        raise InvalidWebhook("invalid size or configuration")
    delivery = headers.get("X-GitHub-Delivery", "")
    event = headers.get("X-GitHub-Event", "")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", delivery):
        raise InvalidWebhook("invalid delivery")
    expected = "sha256=" + hmac.new(shared_key, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, headers.get("X-Hub-Signature-256", "")):
        raise InvalidWebhook("invalid signature")
    try:
        payload = json.loads(body)
        repo = payload["repository"]["full_name"]
        action = payload["action"]
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidWebhook("invalid payload") from exc
    if not isinstance(repo, str) or not isinstance(action, str) or event not in ALLOWED.get(repo, set()):
        raise InvalidWebhook("unsupported source")
    return delivery.lower(), repo, event


def insert_receipt(database, receipt):
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE IF NOT EXISTS deliveries (
            id TEXT PRIMARY KEY, repository TEXT NOT NULL,
            kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending'
        )""")
        cur = conn.execute("INSERT OR IGNORE INTO deliveries(id,repository,kind) VALUES(?,?,?)", receipt)
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()
