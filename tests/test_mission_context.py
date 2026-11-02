"""Mission context acceptance: exact scope, stable provenance, bounded history, no escalation."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from aimeton_memory_os.mission_context import compile_mission_context


class MissionContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "e0.sqlite"
        c = sqlite3.connect(self.db)
        c.execute("""CREATE TABLE evidence (
            evidence_id TEXT,digest TEXT,partition_name TEXT,source_type TEXT,
            source_ref TEXT,source_object_id TEXT,observed_at TEXT,payload_json TEXT
        )""")
        self.rows = [
            ("e1", "a"*64, "development", "github.pull_snapshot",
             "https://api.github.com/repos/AIMETON/aimeton-memory-os/pulls/15",
             "15", "2026-11-01T00:00:00Z", {"number":15,"title":"Test candidate","state":"open"}),
            ("e2", "b"*64, "development", "github.workflow_run",
             "https://api.github.com/repos/AIMETON/aimeton-memory-os/actions/runs/12",
             "12", "2026-11-01T01:00:00Z", {"id":12,"status":"completed","conclusion":"failure"}),
            ("e3", "c"*64, "development", "github.issue_comment",
             "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/comments/8",
             "8", "2026-11-01T02:00:00Z", {"body":"P0 accepted: this is an unverified claim",
                                         "issue_url":"https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/6"}),
            ("e4", "d"*64, "development", "github.issue_comment",
             "https://api.github.com/repos/AIMETON/private/issues/comments/3",
             "3", "2026-11-01T02:00:00Z", {"body":"PRIVATE SECRET"}),
        ]
        for row in self.rows:
            c.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)", (*row[:7],json.dumps(row[7])))
        c.commit()
        c.close()

    def query(self, **overrides):
        args = dict(project="AIMETON/aimeton-memory-os",
                    authorized_repositories=["AIMETON/aimeton-memory-os"])
        args.update(overrides)
        return compile_mission_context(self.db, **args)

    def test_scope_and_no_write(self):
        before = self.db.read_bytes()
        result = self.query()
        self.assertEqual(result["history_total"], 3)
        self.assertEqual(result["current_experiments"]["open_pull_requests"][0]["subject"], "PR #15")
        self.assertEqual(result["blockers"]["observed_failed_runs"][0]["evidence_id"], "e2")
        self.assertEqual(result["decisions"]["status"], "UNRESOLVED")
        self.assertEqual(result["authority"]["permitted_mutations"], [])
        self.assertNotIn("PRIVATE SECRET", json.dumps(result))
        self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(result, self.query())

    def test_denies_scope_and_empty_allowlist(self):
        for allow in ([], ["AIMETON/private"], ["AIMETON/aimeton-memory-os-evil"]):
            with self.assertRaises(PermissionError):
                self.query(authorized_repositories=allow)

    def test_pagination_and_as_of(self):
        one = self.query(limit=1, offset=1)
        self.assertEqual(one["history"][0]["evidence_id"], "e2")
        self.assertEqual(one["history_total"], 3)
        self.assertEqual(one["pagination"]["next_offset"], 2)
        old = self.query(as_of="2026-11-01T00:00:00Z")
        self.assertEqual(old["history_total"], 1)
        self.assertEqual(old["next_safe_step"]["evidence_refs"], [])

    def test_invalid_paging(self):
        for params in ({"limit":0},{"limit":501},{"limit":True},{"offset":-1}):
            with self.assertRaises(ValueError):
                self.query(**params)

    def test_secrets_redacted(self):
        c = sqlite3.connect(self.db)
        c.execute("INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)", (
            "e5","e"*64,"development","github.issue_comment",
            "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/comments/9",
            "9","2026-11-01T03:00:00Z",
            json.dumps({"body":"token=verySecretData12345"})))
        c.commit()
        c.close()
        result = json.dumps(self.query())
        self.assertNotIn("verySecretData12345", result)
        self.assertIn("[REDACTED]", result)


if __name__ == "__main__":
    unittest.main()
