from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.collector import SQLiteShadowStore, collect_repository


class FakeClient:
    def __init__(self, events, comments, pulls=None):
        self.events = events
        self.comments = comments
        self.pulls = pulls or []

    def get_page(self, path, page, per_page=100):
        if page > 1:
            return []
        if "/pulls" in path:
            return list(self.pulls)
        return list(self.comments if "comments" in path else self.events)


class ShadowCollectorTest(unittest.TestCase):
    def _events(self):
        return [
            {
                "id": 1001,
                "url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/events/1001",
                "event": "closed",
                "created_at": "2026-10-30T14:11:08Z",
            }
        ]

    def _comments(self):
        return [
            {
                "id": 2001,
                "url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/comments/2001",
                "body": "P0 accepted",
                "created_at": "2026-10-30T14:11:05Z",
            }
        ]

    def test_restart_is_idempotent_and_cursor_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shadow.db"
            store = SQLiteShadowStore(path)
            first = collect_repository(
                "AIMETON/aimeton-memory-os",
                store,
                FakeClient(self._events(), self._comments()),
            )
            self.assertEqual(first["appended"], 2)
            self.assertEqual(store.count(), 2)
            store.close()

            restarted = SQLiteShadowStore(path)
            second = collect_repository(
                "AIMETON/aimeton-memory-os",
                restarted,
                FakeClient(self._events(), self._comments()),
            )
            self.assertEqual(second["appended"], 0)
            self.assertEqual(restarted.count(), 2)
            self.assertIsNotNone(restarted.get_cursor("github:AIMETON/aimeton-memory-os:issue_events"))
            restarted.close()

    def test_new_transition_is_appended_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shadow.db"
            store = SQLiteShadowStore(path)
            collect_repository(
                "AIMETON/aimeton-memory-os",
                store,
                FakeClient(self._events(), self._comments()),
            )
            events = self._events() + [{
                "id": 1002,
                "url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/events/1002",
                "event": "reopened",
                "created_at": "2026-10-30T14:20:00Z",
            }]
            result = collect_repository(
                "AIMETON/aimeton-memory-os",
                store,
                FakeClient(events, self._comments()),
            )
            self.assertEqual(result["appended"], 1)
            self.assertEqual(store.count(), 3)
            again = collect_repository(
                "AIMETON/aimeton-memory-os",
                store,
                FakeClient(events, self._comments()),
            )
            self.assertEqual(again["appended"], 0)
            self.assertEqual(store.count(), 3)
            store.close()

    def test_partition_is_persisted_at_ingestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteShadowStore(Path(tmp) / "shadow.db")
            collect_repository(
                "AIMETON/aimeton-memory-os",
                store,
                FakeClient(self._events(), self._comments()),
                partition="holdout_candidate",
            )
            partitions = {
                row[0] for row in store.db.execute(
                    "SELECT partition_name FROM evidence"
                ).fetchall()
            }
            self.assertEqual(partitions, {"holdout_candidate"})
            store.close()


    def test_private_source_mode_uses_pull_snapshots_and_independent_cursors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shadow.db"
            store = SQLiteShadowStore(path)
            collect_repository(
                "AIMETON/aimeton-memory-os",
                store,
                FakeClient(self._events(), self._comments()),
            )
            memory_ids = set(store.evidence_ids())
            choke_comment = {
                "id": 3001,
                "url": "https://api.github.com/repos/AIMETON/Choke_ring_antenna/issues/comments/3001",
                "issue_url": "https://api.github.com/repos/AIMETON/Choke_ring_antenna/issues/2",
                "body": "read-only engineering observation",
                "created_at": "2026-10-30T15:20:00Z",
                "author_association": "MEMBER",
                "user": {"login": "Dimar4713"},
            }
            pull = {
                "id": 4001,
                "number": 64,
                "url": "https://api.github.com/repos/AIMETON/Choke_ring_antenna/pulls/64",
                "state": "open",
                "updated_at": "2026-10-30T15:19:00Z",
                "user": {"login": "Dimar4713"},
            }
            result = collect_repository(
                "AIMETON/Choke_ring_antenna",
                store,
                FakeClient([], [choke_comment], [pull]),
                source_mode="versioned_pull_snapshots_plus_comments",
            )
            self.assertEqual(result["source_mode"], "versioned_pull_snapshots_plus_comments")
            self.assertEqual(result["appended"], 2)
            self.assertTrue(memory_ids <= set(store.evidence_ids()))
            self.assertIsNotNone(store.get_cursor("github:AIMETON/aimeton-memory-os:issue_events"))
            self.assertIsNotNone(store.get_cursor("github:AIMETON/Choke_ring_antenna:pull_snapshots"))
            self.assertIsNotNone(store.get_cursor("github:AIMETON/Choke_ring_antenna:issue_comments"))
            choke = [
                e for e in store.iter_envelopes()
                if "AIMETON/Choke_ring_antenna" in e["evidence_id"]
            ]
            self.assertEqual({e["source_type"] for e in choke}, {"github.pull_snapshot", "github.issue_comment"})
            self.assertEqual(
                next(e for e in choke if e["source_type"] == "github.pull_snapshot")["observed_at"],
                pull["updated_at"],
            )
            again = collect_repository(
                "AIMETON/Choke_ring_antenna",
                store,
                FakeClient([], [choke_comment], [pull]),
                source_mode="versioned_pull_snapshots_plus_comments",
            )
            self.assertEqual(again["appended"], 0)
            store.close()

    def test_pull_snapshot_state_change_appends_new_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteShadowStore(Path(tmp) / "shadow.db")
            opened = {
                "id": 4001,
                "number": 64,
                "url": "https://api.github.com/repos/AIMETON/Choke_ring_antenna/pulls/64",
                "state": "open",
                "updated_at": "2026-10-30T15:19:00Z",
                "user": {"login": "Dimar4713"},
            }
            collect_repository(
                "AIMETON/Choke_ring_antenna",
                store,
                FakeClient([], [], [opened]),
                source_mode="versioned_pull_snapshots_plus_comments",
            )
            closed = dict(opened)
            closed["state"] = "closed"
            closed["updated_at"] = "2026-10-30T15:29:00Z"
            result = collect_repository(
                "AIMETON/Choke_ring_antenna",
                store,
                FakeClient([], [], [closed]),
                source_mode="versioned_pull_snapshots_plus_comments",
            )
            snapshots = [
                e for e in store.iter_envelopes()
                if e["source_type"] == "github.pull_snapshot"
            ]
            self.assertEqual(result["appended"], 1)
            self.assertEqual(len(snapshots), 2)
            self.assertEqual([e["payload"]["state"] for e in snapshots], ["open", "closed"])
            store.close()


if __name__ == "__main__":
    unittest.main()
