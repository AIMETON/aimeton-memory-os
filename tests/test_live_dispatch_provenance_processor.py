from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aimeton_memory_os.collector import SQLiteShadowStore
from aimeton_memory_os.ldc import make_evidence_envelope
from aimeton_memory_os.live_shadow import process_shadow_store
from test_dispatch_receipt import fixture, REPO


class LiveDispatchProvenanceProcessorTest(unittest.TestCase):
    def _traces(self, root):
        return [json.loads(p.read_text(encoding="utf-8")) for p in root.glob("*.json")]

    def test_proof_written_once_and_late_failure_appends_new_immutable_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); db=root/"shadow.db"; traces=root/"traces"
            original=fixture()
            store=SQLiteShadowStore(db)
            for x in original: self.assertTrue(store.append(x))
            store.close()

            first=process_shadow_store(db,traces)
            self.assertEqual(first["evidence_count"],4)
            self.assertEqual(first["dispatch_chain_traces"],1)
            self.assertEqual(first["created"],5)
            found=[x for x in self._traces(traces) if x.get("trace",{}).get("trace_type")=="amos.live-dispatch-provenance"]
            self.assertEqual(len(found),1)
            self.assertEqual(found[0]["causal_link"]["status"],"VERIFIED")
            self.assertEqual(found[0]["workflow_observation"]["conclusion"],"success")
            self.assertEqual(len(found[0]["exact_references"]),4)

            with patch("aimeton_memory_os.live_shadow._read_envelopes_ro",
                       side_effect=AssertionError("unchanged E0 must not be scanned")):
                idle=process_shadow_store(db,traces)
            self.assertTrue(idle["idle_fast_path"])
            self.assertEqual(idle["dispatch_chain_traces"],1)

            old_run=original[3]["payload"]
            changed=copy.deepcopy(old_run)
            changed["conclusion"]="failure"
            changed["updated_at"]="2026-11-01T10:01:00Z"
            target_id=int(changed["id"])
            version=make_evidence_envelope(
                evidence_id=f"github:workflow-run:{REPO}:{target_id}:{changed['updated_at']}",
                source_type="github.workflow_run",
                source_ref=changed["url"],
                source_object_id=f"{target_id}@{changed['updated_at']}",
                observed_at=changed["updated_at"],
                payload=changed,partition="development",
            )
            store=SQLiteShadowStore(db)
            self.assertTrue(store.append(version))
            self.assertEqual(store.count(),5)
            store.close()

            second=process_shadow_store(db,traces)
            self.assertEqual(second["created"],2)
            self.assertEqual(second["dispatch_chain_traces"],2)
            found=[x for x in self._traces(traces) if x.get("trace",{}).get("trace_type")=="amos.live-dispatch-provenance"]
            self.assertEqual(len(found),2)
            self.assertEqual({x["workflow_observation"]["conclusion"] for x in found},{"success","failure"})
            self.assertEqual(process_shadow_store(db,traces)["idle_fast_path"],True)
            self.assertEqual(process_shadow_store(db,traces,verify_all=True)["created"],0)

    def test_forged_bot_comment_never_creates_dispatch_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);db=root/"shadow.db";traces=root/"traces"
            items=list(fixture())
            receipt=copy.deepcopy(items[1]["payload"])
            receipt["user"]={"login":"Dimar4713","type":"User"}
            old=items[1]
            items[1]=make_evidence_envelope(
                evidence_id=old["evidence_id"],source_type=old["source_type"],
                source_ref=old["source_ref"],source_object_id=old["source_object_id"],
                observed_at=old["observed_at"],payload=receipt,partition="development",
            )
            store=SQLiteShadowStore(db)
            for x in items: store.append(x)
            store.close()
            result=process_shadow_store(db,traces)
            self.assertEqual(result["dispatch_chain_traces"],0)
            self.assertEqual(result["created"],4)


if __name__=="__main__":
    unittest.main()
