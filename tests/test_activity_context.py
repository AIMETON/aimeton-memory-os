from __future__ import annotations

import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aimeton_memory_os.activity_context import compile_activity_context, read_activity_pair
from aimeton_memory_os.collector import SQLiteShadowStore
from aimeton_memory_os.ldc import make_evidence_envelope


REPO = "AIMETON/Choke_ring_antenna"
COMMENT_ID = 6537145047
RUN_ID = 41155320060


def records(*, run_event="issue_comment", trigger=None, status="completed", conclusion="success"):
    comment = {
        "id": COMMENT_ID,
        "url": f"https://api.github.com/repos/{REPO}/issues/comments/{COMMENT_ID}",
        "issue_url": f"https://api.github.com/repos/{REPO}/issues/2",
        "body": "G3 PEC occupancy verified; FDTD not admitted",
        "created_at": "2026-10-31T01:25:53Z",
        "user": {"login": "Dimar4713"},
    }
    workflow = {
        "id": RUN_ID,
        "url": f"https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}",
        "event": run_event,
        "created_at": "2026-10-31T01:25:57Z",
        "updated_at": "2026-10-31T01:26:08Z",
        "status": status,
        "conclusion": conclusion,
        "triggering_actor": {"login": "Dimar4713"},
    }
    if trigger is not None:
        workflow["triggering_comment_id"] = trigger
    c = make_evidence_envelope(
        evidence_id=f"github:issue-comment:{REPO}:{COMMENT_ID}",
        source_type="github.issue_comment",
        source_ref=comment["url"], source_object_id=str(COMMENT_ID),
        observed_at=comment["created_at"], payload=comment,
        partition="development",
    )
    w = make_evidence_envelope(
        evidence_id=f"github:workflow-run:{REPO}:{RUN_ID}:2026-10-31T01:26:08Z",
        source_type="github.workflow_run",
        source_ref=workflow["url"],
        source_object_id=f"{RUN_ID}@2026-10-31T01:26:08Z",
        observed_at=workflow["updated_at"],
        payload=workflow, partition="development",
    )
    return c, w


class ActivityContextTest(unittest.TestCase):
    def test_standard_github_run_has_unresolved_causality(self):
        c, w = records()
        bundle = compile_activity_context(c, w)
        self.assertEqual(bundle["causal_link"]["status"], "UNRESOLVED")
        self.assertEqual(bundle["causal_link"]["basis"], "no_exact_trigger_provenance")
        self.assertEqual(bundle["workflow_observation"]["conclusion"], "success")
        self.assertEqual(bundle["next_safe_action"]["action_id"], "shadow_verify_trigger_provenance")
        self.assertEqual(bundle["decisions"], [])
        self.assertIn("automatic_fdtd_admission", bundle["authority_envelope"]["forbidden_actions"])
        self.assertEqual(bundle["outcome"], "admit")
        self.assertTrue(all(row["state"] == "satisfied" for row in bundle["compatibility"]))
        self.assertEqual(len(bundle["exact_references"]), 2)

    def test_explicit_exact_trigger_is_verified(self):
        c, w = records(trigger=COMMENT_ID)
        bundle = compile_activity_context(c, w)
        self.assertEqual(bundle["causal_link"]["status"], "VERIFIED")
        self.assertEqual(bundle["causal_link"]["basis"], "exact_trigger_comment_id")
        self.assertEqual(bundle["next_safe_action"]["action_id"], "shadow_review_verified_link")
        self.assertEqual(bundle["decisions"], [])

    def test_nearby_unrelated_run_never_links(self):
        c, w = records(trigger=COMMENT_ID + 1)
        self.assertEqual(compile_activity_context(c, w)["causal_link"]["status"], "UNRESOLVED")
        c, w = records(run_event="push", trigger=COMMENT_ID)
        self.assertEqual(compile_activity_context(c, w)["causal_link"]["status"], "UNRESOLVED")

    def test_failed_and_pending_runs_do_not_claim_successful_mission(self):
        for status, conclusion in (("completed", "failure"), ("in_progress", None)):
            c, w = records(status=status, conclusion=conclusion)
            result = compile_activity_context(c, w)
            self.assertEqual(result["causal_link"]["status"], "UNRESOLVED")
            self.assertEqual(result["workflow_observation"]["conclusion"], conclusion)
            self.assertEqual(result["decisions"], [])

    def test_no_cross_repo_and_no_modified_payload(self):
        c, w = records()
        bad = copy.deepcopy(w)
        bad["evidence_id"] = bad["evidence_id"].replace(REPO, "AIMETON/other")
        with self.assertRaises(ValueError):
            compile_activity_context(c, bad)
        bad = copy.deepcopy(w)
        bad["payload"]["conclusion"] = "failure"
        with self.assertRaises(ValueError):
            compile_activity_context(c, bad)

    def test_targeted_readback_no_e0_write_and_versioned_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "shadow.db"
            store = SQLiteShadowStore(db)
            c, w = records()
            store.append(c)
            store.append(w)
            count = store.count()
            store.close()
            a, b = read_activity_pair(db, REPO, COMMENT_ID, RUN_ID)
            self.assertEqual(a["evidence_id"], c["evidence_id"])
            self.assertEqual(b["evidence_id"], w["evidence_id"])
            self.assertEqual(compile_activity_context(a, b)["causal_link"]["status"], "UNRESOLVED")
            conn = sqlite3.connect(db)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0], count)
            conn.close()
            with self.assertRaises(ValueError):
                read_activity_pair(db, REPO, COMMENT_ID + 1, RUN_ID)
            with self.assertRaises(ValueError):
                read_activity_pair(db, "AIMETON/other", COMMENT_ID, RUN_ID)

    def test_replay_is_deterministic_and_not_upgrading_uncertainty(self):
        c, w = records()
        one = compile_activity_context(c, w)
        two = compile_activity_context(c, w)
        self.assertEqual(json.dumps(one, sort_keys=True), json.dumps(two, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
