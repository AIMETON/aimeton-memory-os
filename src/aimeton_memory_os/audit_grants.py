"""G2 local synthetic-only audit grant state machine, no HTTP API.

Strictly separate from AMOS source data. Secret link token is returned once,
stored as SHA256 digest only, and must not be placed in URLs/logs by callers.
"""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit_export import verify_synthetic_audit_pack, DEMO_PROJECT


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("grant time must be UTC Z")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("invalid UTC grant time") from exc
    if dt.utcoffset().total_seconds() != 0:
        raise ValueError("grant timezone mismatch")
    return dt


def _now(now: str | None) -> str:
    stamp = now if now is not None else datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    _utc(stamp)
    return stamp


def _hash_token(token: str) -> str:
    if not isinstance(token, str) or len(token) < 32 or len(token) > 256:
        raise ValueError("invalid grant capability")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), timeout=15, isolation_level=None)
    connection.execute("PRAGMA busy_timeout=15000")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS synthetic_audit_grants (
          grant_id TEXT PRIMARY KEY,
          token_digest TEXT NOT NULL UNIQUE,
          project_id TEXT NOT NULL CHECK(project_id='amos-synthetic-audit-demo'),
          mode TEXT NOT NULL CHECK(mode IN ('one_time','project_continuous')),
          snapshot_id TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          redeemed_at TEXT,
          revoked_at TEXT
        )
    """)
    return connection


def issue_synthetic_grant(
    db_path: str | Path, snapshot: dict[str, Any], manifest: dict[str, Any],
    *, mode: str, expires_at: str, now: str | None = None,
) -> dict[str, str]:
    """Issue an offline capability for a validated *synthetic* snapshot only.

    IMPORTANT: this is a local admin-facing primitive; no authentication or
    public request handler is implemented or implied.
    """
    verify_synthetic_audit_pack(snapshot, manifest)
    if manifest["project_id"] != DEMO_PROJECT or mode not in {"one_time", "project_continuous"}:
        raise ValueError("grant issuance refused")
    if _utc(expires_at) <= _utc(_now(now)):
        raise ValueError("grant already expired")
    token = secrets.token_urlsafe(48)
    grant_id = str(uuid.uuid4())
    with _connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                """INSERT INTO synthetic_audit_grants
                   (grant_id,token_digest,project_id,mode,snapshot_id,expires_at)
                   VALUES (?,?,?,?,?,?)""",
                (grant_id, _hash_token(token), DEMO_PROJECT, mode,
                 manifest["snapshot_id"], expires_at),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"grant_id": grant_id, "capability": token, "mode": mode}


def preview_synthetic_grant(db_path: str | Path, grant_id: str, *, now: str | None = None) -> dict[str, str]:
    """Public-safe synthetic metadata; never consumes the capability."""
    clock = _now(now)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT mode,expires_at,revoked_at,redeemed_at FROM synthetic_audit_grants WHERE grant_id=?",
            (grant_id,),
        ).fetchone()
    if row is None or row[2] is not None or _utc(row[1]) <= _utc(clock) or (row[0] == "one_time" and row[3]):
        raise PermissionError("audit grant unavailable")
    return {"project_id": DEMO_PROJECT, "mode": row[0], "release_status": "NON_PUBLIC_SYNTHETIC_TEST_ONLY"}


def redeem_synthetic_grant(db_path: str | Path, capability: str, *, now: str | None = None) -> dict[str, str]:
    """Atomic one-use redemption, safe against concurrent requests."""
    clock = _now(now)
    digest = _hash_token(capability)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """SELECT grant_id,mode,snapshot_id,expires_at,redeemed_at,revoked_at
               FROM synthetic_audit_grants WHERE token_digest=?""", (digest,),
        ).fetchone()
        if (row is None or row[5] is not None or _utc(row[3]) <= _utc(clock)
                or (row[1] == "one_time" and row[4] is not None)):
            conn.execute("ROLLBACK")
            raise PermissionError("audit grant unavailable")
        if row[1] == "one_time":
            changed = conn.execute(
                """UPDATE synthetic_audit_grants SET redeemed_at=?
                   WHERE grant_id=? AND redeemed_at IS NULL AND revoked_at IS NULL""",
                (clock, row[0]),
            ).rowcount
            if changed != 1:
                conn.execute("ROLLBACK")
                raise PermissionError("audit grant unavailable")
        conn.execute("COMMIT")
        return {
            "project_id": DEMO_PROJECT, "mode": row[1],
            "snapshot_id": row[2], "release_status": "NON_PUBLIC_SYNTHETIC_TEST_ONLY"
        }
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def revoke_synthetic_grant(db_path: str | Path, grant_id: str, *, now: str | None = None) -> bool:
    """Local owner-operation placeholder. Do NOT expose without real admin auth."""
    stamp = _now(now)
    with _connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            changed = conn.execute(
                """UPDATE synthetic_audit_grants SET revoked_at=?
                   WHERE grant_id=? AND revoked_at IS NULL""",
                (stamp, grant_id),
            ).rowcount
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return changed == 1


def update_continuous_synthetic_snapshot(
    db_path: str | Path, grant_id: str,
    old_snapshot_id: str, snapshot: dict[str, Any], manifest: dict[str, Any],
    *, now: str | None = None,
) -> bool:
    """Optimistic, revocation-aware continuous-link version switch; no content writes."""
    verify_synthetic_audit_pack(snapshot, manifest)
    clock = _now(now)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT mode,expires_at,revoked_at FROM synthetic_audit_grants WHERE grant_id=?",
            (grant_id,),
        ).fetchone()
        if row is None or row[0] != "project_continuous" or row[2] or _utc(row[1]) <= _utc(clock):
            conn.execute("ROLLBACK")
            return False
        result = conn.execute(
            """UPDATE synthetic_audit_grants SET snapshot_id=?
               WHERE grant_id=? AND snapshot_id=? AND revoked_at IS NULL""",
            (manifest["snapshot_id"], grant_id, old_snapshot_id),
        ).rowcount
        conn.execute("COMMIT")
        return result == 1
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
