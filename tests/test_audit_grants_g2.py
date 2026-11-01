from __future__ import annotations

import concurrent.futures
import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from aimeton_memory_os.audit_export import export_synthetic_audit_pack
from aimeton_memory_os.audit_grants import (
    issue_synthetic_grant,preview_synthetic_grant,redeem_synthetic_grant,
    revoke_synthetic_grant,update_continuous_synthetic_snapshot
)

FIXTURE=json.loads((ROOT/"tests/fixtures/audit_synthetic_policy_input.json").read_text())
NOW="2026-11-01T08:00:00Z"
EXP="2026-11-02T08:00:00Z"


class SyntheticGrantG2Test(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/"grants.sqlite"
        self.snapshot,self.manifest=export_synthetic_audit_pack(FIXTURE)

    def issue(self, mode="one_time", expires_at=EXP):
        return issue_synthetic_grant(
            self.db,self.snapshot,self.manifest,mode=mode,expires_at=expires_at,now=NOW)

    def test_one_time_preview_does_not_consume_and_double_redeem_denied(self):
        grant=self.issue()
        self.assertEqual(preview_synthetic_grant(self.db,grant["grant_id"],now=NOW)["mode"],"one_time")
        self.assertEqual(preview_synthetic_grant(self.db,grant["grant_id"],now=NOW)["mode"],"one_time")
        redeemed=redeem_synthetic_grant(self.db,grant["capability"],now=NOW)
        self.assertEqual(redeemed["snapshot_id"],self.manifest["snapshot_id"])
        for fn,arg in [(redeem_synthetic_grant,grant["capability"]),
                       (preview_synthetic_grant,grant["grant_id"])]:
            with self.assertRaises(PermissionError):
                fn(self.db,arg,now=NOW)

    def test_parallel_one_time_redemption_exactly_once(self):
        grant=self.issue()
        def worker(_):
            try:
                redeem_synthetic_grant(self.db,grant["capability"],now=NOW)
                return "ok"
            except PermissionError:
                return "denied"
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(worker,range(16)))
        self.assertEqual(results.count("ok"),1)
        self.assertEqual(results.count("denied"),15)

    def test_expiration_revocation_unknown_capability(self):
        with self.assertRaises(ValueError):
            self.issue(expires_at=NOW)
        grant=self.issue()
        with self.assertRaises(PermissionError):
            redeem_synthetic_grant(self.db,grant["capability"],now=EXP)
        with self.assertRaises(PermissionError):
            redeem_synthetic_grant(self.db,"x"*64,now=NOW)
        self.assertTrue(revoke_synthetic_grant(self.db,grant["grant_id"],now=NOW))
        self.assertFalse(revoke_synthetic_grant(self.db,grant["grant_id"],now=NOW))
        with self.assertRaises(PermissionError):
            redeem_synthetic_grant(self.db,grant["capability"],now=NOW)

    def test_continuous_version_switch_is_conditional(self):
        grant=self.issue(mode="project_continuous")
        first=redeem_synthetic_grant(self.db,grant["capability"],now=NOW)
        self.assertEqual(redeem_synthetic_grant(self.db,grant["capability"],now=NOW),first)
        source=copy.deepcopy(FIXTURE)
        source["as_of_utc"]="2026-11-01T09:00:00Z"
        updated,updated_manifest=export_synthetic_audit_pack(source)
        self.assertFalse(update_continuous_synthetic_snapshot(
            self.db,grant["grant_id"],"sha256:"+("0"*64),updated,updated_manifest,now=NOW))
        self.assertTrue(update_continuous_synthetic_snapshot(
            self.db,grant["grant_id"],first["snapshot_id"],updated,updated_manifest,now=NOW))
        second=redeem_synthetic_grant(self.db,grant["capability"],now=NOW)
        self.assertEqual(second["snapshot_id"],updated_manifest["snapshot_id"])
        self.assertTrue(revoke_synthetic_grant(self.db,grant["grant_id"],now=NOW))
        self.assertFalse(update_continuous_synthetic_snapshot(
            self.db,grant["grant_id"],second["snapshot_id"],self.snapshot,self.manifest,now=NOW))

    def test_never_store_raw_capability_or_allow_real_export(self):
        grant=self.issue()
        raw=self.db.read_bytes()
        self.assertNotIn(grant["capability"].encode(),raw)
        with sqlite3.connect(self.db) as conn:
            row=conn.execute("SELECT token_digest,project_id,mode FROM synthetic_audit_grants").fetchone()
        self.assertEqual(len(row[0]),64)
        self.assertEqual(row[1],"amos-synthetic-audit-demo")
        bad=copy.deepcopy(self.snapshot)
        bad["project_id"]="AIMETON/Choke_ring_antenna"
        with self.assertRaises(ValueError):
            issue_synthetic_grant(self.db,bad,self.manifest,mode="one_time",expires_at=EXP,now=NOW)


if __name__=="__main__":
    unittest.main()
