from __future__ import annotations

import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from aimeton_memory_os.collector import SQLiteShadowStore
from aimeton_memory_os.ldc import make_evidence_envelope
from aimeton_memory_os.live_shadow import process_shadow_store


class LiveShadowProcessorTest(unittest.TestCase):
    def _seed(self, db_path: Path) -> tuple[str, int]:
        store = SQLiteShadowStore(db_path)
        comment_id = 6524862947
        comment = {
            "id": comment_id,
            "url": f"https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/comments/{comment_id}",
            "issue_url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/6",
            "body": "P0 accepted on 2026-10-30. Evidence passed.",
            "created_at": "2026-10-30T14:11:05Z",
            "author_association": "MEMBER",
            "user": {"login": "Dimar4713"},
        }
        closed_id = 34698426892
        closed = {
            "id": closed_id,
            "url": f"https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/events/{closed_id}",
            "event": "closed",
            "created_at": "2026-10-30T14:11:08Z",
            "actor": {"login": "Dimar4713"},
            "issue": {
                "number": 6,
                "repository_url": "https://api.github.com/repos/AIMETON/aimeton-memory-os",
            },
        }
        marker_id = 6525522492
        marker = {
            "id": marker_id,
            "url": f"https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/comments/{marker_id}",
            "issue_url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/20",
            "body": "AMOS-LDC-LIVE-ACCEPTANCE marker",
            "created_at": "2026-10-30T14:43:42Z",
            "author_association": "MEMBER",
            "user": {"login": "Dimar4713"},
        }
        for kind, payload, observed in [
            ("github.issue_comment", comment, comment["created_at"]),
            ("github.issue_event", closed, closed["created_at"]),
            ("github.issue_comment", marker, marker["created_at"]),
        ]:
            ident = payload["id"]
            source = payload["url"]
            prefix = "issue-comment" if kind.endswith("comment") else "issue-event"
            store.append(make_evidence_envelope(
                evidence_id=f"github:{prefix}:AIMETON/aimeton-memory-os:{ident}",
                source_type=kind,
                source_ref=source,
                source_object_id=str(ident),
                observed_at=observed,
                payload=payload,
                partition="development",
            ))
        count = store.count()
        store.close()
        return f"github:issue-comment:AIMETON/aimeton-memory-os:{marker_id}", count

    def _traces(self, root: Path):
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]

    def test_post_persistence_processor_builds_shadow_cr_traces_without_e0_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "shadow.db"
            traces = root / "traces"
            marker_evidence_id, before = self._seed(db)
            first = process_shadow_store(db, traces)
            store = SQLiteShadowStore(db)
            after = store.count()
            store.close()

            self.assertEqual(before, 3)
            self.assertEqual(after, before)
            self.assertEqual(first["evidence_count"], 3)
            self.assertEqual(first["envelope_traces"], 3)
            self.assertEqual(first["decision_chain_traces"], 1)
            self.assertEqual(first["created"], 4)
            self.assertFalse(first["e0_mutation_performed"])
            self.assertFalse(first["source_mutation_performed"])

            payloads = self._traces(traces)
            marker = next(
                x for x in payloads
                if x.get("trace", {}).get("source_evidence_id") == marker_evidence_id
            )
            self.assertEqual(marker["mode"], "SHADOW")
            self.assertEqual(marker["partition"], "development")
            self.assertEqual(marker["semantic_layers"]["E1"][0]["layer"], "E1")
            self.assertEqual(marker["semantic_layers"]["E2"][0]["layer"], "E2")
            self.assertEqual(marker["projections"]["V"]["scope"], "AIMETON/aimeton-memory-os")
            self.assertEqual([c["check_id"] for c in marker["compatibility"]], [f"CR-{n:02d}" for n in range(1, 7)])
            self.assertTrue(all(c["state"] == "satisfied" for c in marker["compatibility"]))
            self.assertIn("github_mutation", marker["authority_envelope"]["forbidden_actions"])

    def test_idle_fast_path_skips_full_e0_scan_and_new_evidence_invalidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "shadow.db"
            traces = root / "traces"
            self._seed(db)
            first = process_shadow_store(db, traces)
            self.assertEqual(first["created"], 4)
            with patch("aimeton_memory_os.live_shadow._read_envelopes_ro",
                       side_effect=AssertionError("idle must not scan E0")):
                second = process_shadow_store(db, traces)
            self.assertTrue(second["idle_fast_path"])
            self.assertEqual(second["created"], 0)
            store = SQLiteShadowStore(db)
            payload = {
                "id": 999999, "url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/comments/999999",
                "issue_url": "https://api.github.com/repos/AIMETON/aimeton-memory-os/issues/25",
                "body": "new source evidence",
                "created_at": "2026-10-31T01:00:00Z",
            }
            store.append(make_evidence_envelope(
                evidence_id="github:issue-comment:AIMETON/aimeton-memory-os:999999",
                source_type="github.issue_comment",
                source_ref=payload["url"],
                source_object_id="999999",
                observed_at=payload["created_at"],
                payload=payload,
                partition="development",
            ))
            store.close()
            third = process_shadow_store(db, traces)
            self.assertFalse(third["idle_fast_path"])
            self.assertEqual(third["evidence_count"], 4)
            self.assertEqual(third["created"], 1)
            self.assertEqual(process_shadow_store(db, traces, verify_all=True)["created"], 0)
            # Missing trace must invalidate idle checkpoint and be regenerated.
            candidate = next(p for p in traces.glob("*.json") if '"source_evidence_id": "github:issue-comment:AIMETON/aimeton-memory-os:999999"' in p.read_text())
            candidate.unlink()
            rebuilt = process_shadow_store(db, traces)
            self.assertEqual(rebuilt["created"], 1)
            self.assertFalse(rebuilt["idle_fast_path"])

    def test_live_decision_chain_has_e2_e3_e4_lineage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "shadow.db"
            traces = root / "traces"
            self._seed(db)
            result = process_shadow_store(db, traces)
            self.assertEqual(result["decision_chain_traces"], 1)
            chain = next(
                x for x in self._traces(traces)
                if x.get("trace", {}).get("trace_type") == "amos.live-decision-chain"
            )
            self.assertEqual(chain["projections"]["O"]["state"], "closed")
            self.assertEqual(len(chain["semantic_layers"]["E2"]), 1)
            self.assertEqual(len(chain["semantic_layers"]["E3"]), 1)
            self.assertEqual(len(chain["semantic_layers"]["E4"]), 1)
            self.assertEqual(chain["semantic_layers"]["E3"][0]["authority"], "MEMBER")
            self.assertEqual(chain["semantic_layers"]["E4"][0]["provenance"], [
                chain["semantic_layers"]["E3"][0]["record_id"],
                chain["semantic_layers"]["E1"][1]["record_id"],
            ])

    def test_processor_is_idempotent_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "shadow.db"
            traces = root / "traces"
            self._seed(db)
            first = process_shadow_store(db, traces)
            snapshot = {p.name: p.read_bytes() for p in traces.glob("*.json")}
            second = process_shadow_store(db, traces)
            self.assertEqual(second["created"], 0)
            self.assertEqual(second["existing"], first["created"])
            self.assertEqual({p.name: p.read_bytes() for p in traces.glob("*.json")}, snapshot)


    def test_pull_snapshot_trace_preserves_private_repo_scope_and_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "shadow.db"
            traces = root / "traces"
            store = SQLiteShadowStore(db)
            payload = {
                "id": 4001,
                "number": 64,
                "url": "https://api.github.com/repos/AIMETON/Choke_ring_antenna/pulls/64",
                "state": "open",
                "updated_at": "2026-10-30T15:19:00Z",
                "user": {"login": "Dimar4713"},
            }
            evidence_id = "github:pull-snapshot:AIMETON/Choke_ring_antenna:4001:2026-10-30T15:19:00Z"
            store.append(make_evidence_envelope(
                evidence_id=evidence_id,
                source_type="github.pull_snapshot",
                source_ref=payload["url"],
                source_object_id="4001@2026-10-30T15:19:00Z",
                observed_at=payload["updated_at"],
                payload=payload,
                partition="development",
            ))
            store.close()
            result = process_shadow_store(db, traces)
            self.assertEqual(result["evidence_count"], 1)
            pull_trace = next(
                x for x in self._traces(traces)
                if x.get("trace", {}).get("source_evidence_id") == evidence_id
            )
            self.assertEqual(pull_trace["projections"]["V"]["scope"], "AIMETON/Choke_ring_antenna")
            self.assertEqual(pull_trace["projections"]["V"]["issue_number"], 64)
            self.assertEqual(pull_trace["projections"]["O"]["state"], "open")
            self.assertEqual(len(pull_trace["compatibility"]), 6)
            self.assertTrue(all(c["state"] == "satisfied" for c in pull_trace["compatibility"]))
            self.assertFalse(pull_trace["trace"]["source_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
