"""Quarantined external auditor findings, never E0 or accepted decisions."""
import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime,timezone

CATEGORIES={"missing_evidence","contradiction","methodology","risk","recommendation"}
SEVERITY={"low","medium","high"}
def _canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def _store(db):
    conn=sqlite3.connect(str(db),timeout=15,isolation_level=None)
    conn.execute("PRAGMA busy_timeout=15000")
    conn.execute("""CREATE TABLE IF NOT EXISTS external_audit_findings(
        id TEXT PRIMARY KEY,snapshot_sha256 TEXT NOT NULL,body_sha256 TEXT NOT NULL,
        submitted_at TEXT NOT NULL,category TEXT NOT NULL,severity TEXT NOT NULL,
        referenced_item TEXT NOT NULL,body_json TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status='QUARANTINED'))""")
    return conn

def ingest_finding(db,manifest,finding,now=None):
    if not isinstance(manifest,dict) or not re.fullmatch("[0-9a-f]{64}",str(manifest.get("snapshot_sha256",""))):
        raise ValueError("snapshot binding missing")
    if not isinstance(finding,dict) or set(finding)!={"category","severity","referenced_item","observation","recommendation"}:
        raise ValueError("finding schema")
    if finding["category"] not in CATEGORIES or finding["severity"] not in SEVERITY:
        raise ValueError("finding category")
    if not re.fullmatch(r"PUB-[0-9]{3}",str(finding["referenced_item"])):
        raise ValueError("finding reference")
    for key in ("observation","recommendation"):
        s=finding[key]
        if not isinstance(s,str) or not 12<=len(s)<=2000 or any(ord(x)<32 for x in s):
            raise ValueError("finding length/content")
    fid=str(uuid.uuid4())
    submitted_at=now or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    payload=_canonical(finding)
    with closing(_store(db)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("INSERT INTO external_audit_findings VALUES(?,?,?,?,?,?,?,?,?)",
                (fid,manifest["snapshot_sha256"],hashlib.sha256(payload).hexdigest(),
                 submitted_at,finding["category"],finding["severity"],
                 finding["referenced_item"],payload.decode(),"QUARANTINED"))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"finding_id":fid,"status":"QUARANTINED",
            "snapshot_sha256":manifest["snapshot_sha256"]}

def read_findings(db,snapshot_sha256):
    with closing(_store(db)) as conn:
        rows=conn.execute("""SELECT id,body_sha256,submitted_at,body_json,status
            FROM external_audit_findings WHERE snapshot_sha256=? ORDER BY submitted_at,id""",
            (snapshot_sha256,)).fetchall()
    return [{"finding_id":id,"body_sha256":h,"submitted_at":ts,
             "body":json.loads(body),"status":status} for id,h,ts,body,status in rows]
