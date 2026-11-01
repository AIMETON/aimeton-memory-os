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
EVIDENCE_URL = re.compile(r"https://github[.]com/AIMETON/(?:aimeton-memory-os|aimeton-site|aimeton-infrastructure)(?:/[A-Za-z0-9_./#-]+)?\Z")
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
    required = {"category","severity","referenced_item","observation","recommendation"}
    allowed = required | {"evidence_urls"}
    if not isinstance(finding,dict) or not required <= set(finding) or not set(finding) <= allowed:
        raise ValueError("finding schema")
    evidence_urls = finding.get("evidence_urls", [])
    if (not isinstance(evidence_urls,list) or len(evidence_urls)>5
            or any(not isinstance(url,str) or not EVIDENCE_URL.fullmatch(url) for url in evidence_urls)
            or len(set(evidence_urls)) != len(evidence_urls)):
        raise ValueError("unapproved evidence URL")
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


def ingest_curated_finding(db, pack, manifest, finding, now=None):
    """Check exact snapshot and referent before writing untrusted quarantine E2.

    This verifies technical integrity ONLY. The pack's release approval ID
    remains unauthenticated; calling this function never publishes the pack,
    authorizes a real project, or promotes findings into AMOS E0/E3/E4.
    """
    from .curated_audit import verify_release
    verify_release(pack, manifest)
    if not isinstance(finding, dict) or finding.get("referenced_item") not in {
            record["id"] for record in pack["records"]}:
        raise ValueError("finding references unknown project record")
    return ingest_finding(db, manifest, finding, now=now)
