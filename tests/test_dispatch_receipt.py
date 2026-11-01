from __future__ import annotations
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from aimeton_memory_os.ldc import make_evidence_envelope
from aimeton_memory_os.collector import SQLiteShadowStore
from aimeton_memory_os.activity_context import (
    compile_receipted_dispatch_context,read_receipted_dispatch_e0
)

REPO="AIMETON/Choke_ring_antenna"
COMMAND="/probe-antenna-c02 "+"a"*40

def evidence(source_type, prefix, ident, stamp, payload):
    return make_evidence_envelope(
        evidence_id=f"github:{prefix}:{REPO}:{ident}" if source_type=="github.issue_comment" else f"github:{prefix}:{REPO}:{ident}:{stamp}",
        source_type=source_type,
        source_ref=payload["url"],source_object_id=str(ident),
        observed_at=stamp,payload=payload,partition="development"
    )

def fixture():
    c_id=73001
    receipt_id=73002
    router_id=83001
    target_id=83002
    c_url=f"https://api.github.com/repos/{REPO}/issues/comments/{c_id}"
    claim={
        "schema_version":"amos.c02.dispatch-provenance.v1",
        "source_repository":REPO,"source_issue_number":2,
        "source_comment_id":c_id,"source_comment_url":c_url,
        "source_comment_sha256":hashlib.sha256(COMMAND.encode()).hexdigest(),
        "router_run_id":router_id,"target_workflow":"c02-route-probe.yml",
        "target_workflow_run_id":target_id,
        "target_workflow_url":f"https://github.com/{REPO}/actions/runs/{target_id}",
        "source_main_sha":"a"*40,
    }
    c=evidence("github.issue_comment","issue-comment",c_id,"2026-11-01T10:00:00Z",{
        "id":c_id,"url":c_url,"issue_url":f"https://api.github.com/repos/{REPO}/issues/2",
        "body":COMMAND,"created_at":"2026-11-01T10:00:00Z",
        "user":{"login":"Dimar4713","type":"User"}
    })
    receipt=evidence("github.issue_comment","issue-comment",receipt_id,"2026-11-01T10:00:10Z",{
        "id":receipt_id,
        "url":f"https://api.github.com/repos/{REPO}/issues/comments/{receipt_id}",
        "issue_url":f"https://api.github.com/repos/{REPO}/issues/2",
        "body":"AMOS_C02_DISPATCH_PROVENANCE_V1\\n"+json.dumps(claim,sort_keys=True,separators=(",",":")),
        "created_at":"2026-11-01T10:00:10Z",
        "user":{"login":"github-actions[bot]","type":"Bot"}
    })
    router=evidence("github.workflow_run","workflow-run",router_id,"2026-11-01T10:00:16Z",{
        "id":router_id,
        "url":f"https://api.github.com/repos/{REPO}/actions/runs/{router_id}",
        "html_url":f"https://github.com/{REPO}/actions/runs/{router_id}",
        "event":"issue_comment","path":".github/workflows/c02-command-router.yml@main",
        "status":"completed","conclusion":"success","updated_at":"2026-11-01T10:00:16Z"
    })
    target=evidence("github.workflow_run","workflow-run",target_id,"2026-11-01T10:00:19Z",{
        "id":target_id,
        "url":f"https://api.github.com/repos/{REPO}/actions/runs/{target_id}",
        "html_url":f"https://github.com/{REPO}/actions/runs/{target_id}",
        "event":"workflow_dispatch","path":".github/workflows/c02-route-probe.yml@main",
        "status":"completed","conclusion":"success","updated_at":"2026-11-01T10:00:19Z"
    })
    return c,receipt,router,target

class DispatchReceiptTest(unittest.TestCase):
    def test_all_four_are_source_verified(self):
        context=compile_receipted_dispatch_context(*fixture())
        self.assertEqual(context["causal_link"]["status"],"VERIFIED")
        self.assertEqual(context["causal_link"]["dispatched_run_id"],83002)
        self.assertEqual(len(context["exact_references"]),4)
        self.assertEqual(len(context["compatibility"]),6)
        self.assertEqual(context["outcome"],"admit")
        self.assertTrue(all(x["state"]=="satisfied" for x in context["compatibility"]))
        self.assertEqual(context["decisions"],[])

    def test_forged_receipt_and_wrong_workflow_rejected(self):
        for mutation in ("author","id","sha","workflow","target","url"):
            items=list(fixture())
            p=copy.deepcopy(items[1]["payload"])
            if mutation=="author": p["user"]["login"]="Dimar4713"
            else:
                claim=json.loads(p["body"].split("\\n",1)[1])
                key={"id":"source_comment_id","sha":"source_comment_sha256",
                     "workflow":"target_workflow","target":"target_workflow_run_id",
                     "url":"target_workflow_url"}[mutation]
                claim[key]="incorrect" if mutation in ("sha","workflow","url") else 999999
                p["body"]="AMOS_C02_DISPATCH_PROVENANCE_V1\\n"+json.dumps(claim)
            items[1]=evidence("github.issue_comment","issue-comment",73002,
                "2026-11-01T10:00:10Z",p)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                compile_receipted_dispatch_context(*items)

    def test_source_changes_and_mismatched_router_rejected(self):
        for i,key,value in [(0,"body","/different"),
                            (2,"event","push"),(3,"event","issue_comment"),
                            (2,"path",".github/workflows/other.yml@main"),
                            (3,"path",".github/workflows/other.yml@main")]:
            items=list(fixture())
            p=copy.deepcopy(items[i]["payload"])
            p[key]=value
            typ=items[i]["source_type"]
            prefix="issue-comment" if typ.endswith("comment") else "workflow-run"
            ident=p["id"]
            items[i]=evidence(typ,prefix,ident,items[i]["observed_at"],p)
            with self.subTest(i=i,key=key),self.assertRaises(ValueError):
                compile_receipted_dispatch_context(*items)

    def test_indexed_sql_readback_and_restart_idempotence(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/"shadow.db"
            store=SQLiteShadowStore(db)
            for item in fixture(): self.assertTrue(store.append(item))
            store.close()
            items=read_receipted_dispatch_e0(db,REPO,73001,73002,83001,83002)
            first=compile_receipted_dispatch_context(*items)
            second=compile_receipted_dispatch_context(*read_receipted_dispatch_e0(db,REPO,73001,73002,83001,83002))
            self.assertEqual(json.dumps(first,sort_keys=True),json.dumps(second,sort_keys=True))
            with self.assertRaises(ValueError):
                read_receipted_dispatch_e0(db,REPO,73001,73002,83001,83003)

if __name__=="__main__":
    unittest.main()
