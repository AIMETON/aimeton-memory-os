from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.collector import SQLiteShadowStore, collect_repository


class FakeClient:
    def __init__(self, events, comments):
        self.events = events
        self.comments = comments

    def get_page(self, path, page, per_page=100):
        if page > 1:
            return []
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


if __name__ == "__main__":
    unittest.main()
