"""Read-only GitHub Shadow collector for AMOS LDC.

SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 AIMETON Project
"""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .ldc import make_evidence_envelope


@dataclass(frozen=True, order=True)
class Cursor:
    observed_at: str
    object_id: int


class SQLiteShadowStore:
    """Durable append-only E0 store plus resumable stream cursors."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                digest TEXT NOT NULL,
                partition_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                source_object_id TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS cursors (
                stream_key TEXT PRIMARY KEY,
                observed_at TEXT NOT NULL,
                object_id INTEGER NOT NULL
            )
        """)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def append(self, envelope: dict[str, Any]) -> bool:
        row = self.db.execute(
            "SELECT digest FROM evidence WHERE evidence_id = ?",
            (envelope["evidence_id"],),
        ).fetchone()
        if row:
            if row[0] != envelope["digest"]:
                raise ValueError(f"immutable evidence collision: {envelope['evidence_id']}")
            return False
        self.db.execute(
            """
            INSERT INTO evidence (
                evidence_id,digest,partition_name,source_type,source_ref,
                source_object_id,observed_at,payload_json
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                envelope["evidence_id"],
                envelope["digest"],
                envelope["partition"],
                envelope["source_type"],
                envelope["source_ref"],
                envelope["source_object_id"],
                envelope["observed_at"],
                json.dumps(envelope["payload"], ensure_ascii=False, sort_keys=True),
            ),
        )
        self.db.commit()
        return True

    def count(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0])

    def evidence_ids(self) -> list[str]:
        return [row[0] for row in self.db.execute(
            "SELECT evidence_id FROM evidence ORDER BY observed_at, source_object_id"
        ).fetchall()]

    def iter_envelopes(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            """
            SELECT evidence_id,digest,partition_name,source_type,source_ref,
                   source_object_id,observed_at,payload_json
            FROM evidence
            ORDER BY observed_at, source_object_id
            """
        ).fetchall()
        return [
            {
                "evidence_id": row[0],
                "layer": "E0",
                "digest": row[1],
                "partition": row[2],
                "source_type": row[3],
                "source_ref": row[4],
                "source_object_id": row[5],
                "observed_at": row[6],
                "payload": json.loads(row[7]),
            }
            for row in rows
        ]

    def get_cursor(self, stream_key: str) -> Cursor | None:
        row = self.db.execute(
            "SELECT observed_at, object_id FROM cursors WHERE stream_key = ?",
            (stream_key,),
        ).fetchone()
        return Cursor(row[0], int(row[1])) if row else None

    def advance_cursor(self, stream_key: str, cursor: Cursor) -> None:
        current = self.get_cursor(stream_key)
        if current is not None and cursor <= current:
            return
        self.db.execute(
            """
            INSERT INTO cursors(stream_key,observed_at,object_id)
            VALUES(?,?,?)
            ON CONFLICT(stream_key) DO UPDATE SET
              observed_at=excluded.observed_at,
              object_id=excluded.object_id
            """,
            (stream_key, cursor.observed_at, cursor.object_id),
        )
        self.db.commit()


class GitHubReadOnlyClient:
    """Minimal stdlib GitHub REST reader. No mutation methods exist by design."""

    def __init__(self, token: str | None = None, api_base: str = "https://api.github.com") -> None:
        self.token = token or os.environ.get("GH_TOKEN")
        self.api_base = api_base.rstrip("/")

    def get_page(self, path: str, page: int, per_page: int = 100) -> list[dict[str, Any]]:
        sep = "&" if "?" in path else "?"
        url = f"{self.api_base}{path}{sep}per_page={per_page}&page={page}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AIMETON-AMOS-Shadow-Collector",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if "/actions/runs" in path and isinstance(payload, dict):
            payload = payload.get("workflow_runs")
        if not isinstance(payload, list):
            raise ValueError(f"expected GitHub list response for {path}")
        return payload


def _iter_pages(client: Any, path: str, *, max_pages: int = 20) -> Iterable[dict[str, Any]]:
    for page in range(1, max_pages + 1):
        items = client.get_page(path, page, 100)
        for item in items:
            yield item
        if len(items) < 100:
            return
    raise RuntimeError(f"pagination limit reached for {path}")


def _cursor_for(item: dict[str, Any], timestamp_field: str = "created_at") -> Cursor:
    return Cursor(str(item[timestamp_field]), int(item["id"]))


def _after(cursor: Cursor | None, item: dict[str, Any], timestamp_field: str = "created_at") -> bool:
    return cursor is None or _cursor_for(item, timestamp_field) > cursor


def _event_envelope(repo: str, item: dict[str, Any], *, partition: str) -> dict[str, Any]:
    return make_evidence_envelope(
        evidence_id=f"github:issue-event:{repo}:{item['id']}",
        source_type="github.issue_event",
        source_ref=str(item.get("url") or f"https://api.github.com/repos/{repo}/issues/events/{item['id']}"),
        source_object_id=str(item["id"]),
        observed_at=str(item["created_at"]),
        payload=item,
        partition=partition,
    )


def _comment_envelope(repo: str, item: dict[str, Any], *, partition: str) -> dict[str, Any]:
    return make_evidence_envelope(
        evidence_id=f"github:issue-comment:{repo}:{item['id']}",
        source_type="github.issue_comment",
        source_ref=str(item.get("url") or f"https://api.github.com/repos/{repo}/issues/comments/{item['id']}"),
        source_object_id=str(item["id"]),
        observed_at=str(item["created_at"]),
        payload=item,
        partition=partition,
    )


def _pull_snapshot_envelope(repo: str, item: dict[str, Any], *, partition: str) -> dict[str, Any]:
    updated_at = str(item["updated_at"])
    return make_evidence_envelope(
        evidence_id=f"github:pull-snapshot:{repo}:{item['id']}:{updated_at}",
        source_type="github.pull_snapshot",
        source_ref=str(item.get("url") or f"https://api.github.com/repos/{repo}/pulls/{item['number']}"),
        source_object_id=f"{item['id']}@{updated_at}",
        observed_at=updated_at,
        payload=item,
        partition=partition,
    )


def _workflow_run_envelope(repo: str, item: dict[str, Any], *, partition: str) -> dict[str, Any]:
    updated_at = str(item["updated_at"])
    return make_evidence_envelope(
        evidence_id=f"github:workflow-run:{repo}:{item['id']}:{updated_at}",
        source_type="github.workflow_run",
        source_ref=str(item.get("url") or f"https://api.github.com/repos/{repo}/actions/runs/{item['id']}"),
        source_object_id=f"{item['id']}@{updated_at}",
        observed_at=updated_at,
        payload=item,
        partition=partition,
    )


def collect_repository(
    repo: str,
    store: SQLiteShadowStore,
    client: Any,
    *,
    partition: str = "development",
    source_mode: str = "issue_events_plus_comments",
) -> dict[str, Any]:
    if partition not in {"development", "holdout_candidate", "frozen_holdout"}:
        raise ValueError("invalid evaluation partition")
    if source_mode == "issue_events_plus_comments":
        streams = [
            ("issue_events", f"/repos/{repo}/issues/events", _event_envelope, "created_at"),
            ("issue_comments", f"/repos/{repo}/issues/comments?sort=created&direction=asc", _comment_envelope, "created_at"),
        ]
    elif source_mode == "versioned_pull_snapshots_plus_comments":
        streams = [
            ("pull_snapshots", f"/repos/{repo}/pulls?state=all&sort=updated&direction=asc", _pull_snapshot_envelope, "updated_at"),
            ("issue_comments", f"/repos/{repo}/issues/comments?sort=created&direction=asc", _comment_envelope, "created_at"),
        ]
    elif source_mode == "activity_stream":
        streams = [
            ("pull_snapshots", f"/repos/{repo}/pulls?state=all&sort=updated&direction=asc", _pull_snapshot_envelope, "updated_at"),
            ("issue_comments", f"/repos/{repo}/issues/comments?sort=created&direction=asc", _comment_envelope, "created_at"),
            ("issue_events", f"/repos/{repo}/issues/events", _event_envelope, "created_at"),
            ("workflow_runs", f"/repos/{repo}/actions/runs?exclude_pull_requests=false", _workflow_run_envelope, "updated_at"),
        ]
    elif source_mode == "versioned_pull_snapshots":
        streams = [
            ("pull_snapshots", f"/repos/{repo}/pulls?state=all&sort=updated&direction=asc", _pull_snapshot_envelope, "updated_at"),
        ]
    else:
        raise ValueError("invalid GitHub source mode")

    result: dict[str, Any] = {
        "repository": repo,
        "partition": partition,
        "source_mode": source_mode,
        "streams": {},
        "appended": 0,
    }
    for name, path, envelope_fn, timestamp_field in streams:
        stream_key = f"github:{repo}:{name}"
        cursor = store.get_cursor(stream_key)
        appended = 0
        newest = cursor
        for item in _iter_pages(client, path):
            candidate = _cursor_for(item, timestamp_field)
            if not _after(cursor, item, timestamp_field):
                continue
            envelope = envelope_fn(repo, item, partition=partition)
            if store.append(envelope):
                appended += 1
            if newest is None or candidate > newest:
                newest = candidate
        if newest is not None:
            store.advance_cursor(stream_key, newest)
        result["streams"][name] = {
            "appended": appended,
            "cursor": None if newest is None else {
                "observed_at": newest.observed_at,
                "object_id": newest.object_id,
            },
        }
        result["appended"] += appended
    return result
