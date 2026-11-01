"""Curated, manually approved external audit snapshot. No E0 access."""
import hashlib
import json
import re

def encode(obj):
    return (json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()

def digest(obj):
    return hashlib.sha256(encode(obj)).hexdigest()

KINDS={"objective","decision","test","limitation","next_action"}
STATUSES={"VERIFIED","UNRESOLVED","REJECTED"}
URL=re.compile(r"https://github\.com/AIMETON/(?:aimeton-memory-os|aimeton-site|aimeton-infrastructure)(?:/[A-Za-z0-9_./#-]+)?\Z")

def validate_record(r):
    if not isinstance(r,dict) or set(r)!={"id","kind","statement","status","evidence"}:
        raise ValueError("unknown record content")
    if not re.fullmatch(r"PUB-[0-9]{3}",str(r["id"])):
        raise ValueError("invalid record id")
    if r["kind"] not in KINDS or r["status"] not in STATUSES:
        raise ValueError("invalid kind/status")
    if not isinstance(r["statement"],str) or not 12<=len(r["statement"])<=1000:
        raise ValueError("invalid statement")
    if any(ord(c)<32 for c in r["statement"]):
        raise ValueError("control chars")
    if not isinstance(r["evidence"],list) or not 1<=len(r["evidence"])<=5:
        raise ValueError("missing evidence")
    if any(not isinstance(u,str) or not URL.fullmatch(u) for u in r["evidence"]):
        raise ValueError("unapproved source location")
    return r

def compile_release(source, approval):
    if not isinstance(source,dict) or set(source)!={"project_id","as_of_utc","records","policy_version"}:
        raise ValueError("source schema")
    if not isinstance(approval,dict) or set(approval)!={"source_sha256","record_digests","approval_id"}:
        raise ValueError("approval schema")
    if source["project_id"]!="AIMETON/aimeton-memory-os" or source["policy_version"]!="public-curated-v1":
        raise ValueError("project not admitted")
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",source["as_of_utc"]):
        raise ValueError("timestamp")
    items=source["records"]
    if not isinstance(items,list) or not 1<=len(items)<=100:
        raise ValueError("record count")
    for r in items: validate_record(r)
    if len({r["id"] for r in items})!=len(items):
        raise ValueError("duplicate record")
    expected={r["id"]:digest(r) for r in items}
    if approval["source_sha256"]!=digest(source) or approval["record_digests"]!=expected:
        raise ValueError("missing exact approval")
    if not re.fullmatch(r"RELEASE-[A-Z0-9]{8,20}",str(approval["approval_id"])):
        raise ValueError("invalid approval id")
    pack={"schema_version":"amos.audit-curated.v1","project_id":source["project_id"],
          "as_of_utc":source["as_of_utc"],"policy_version":source["policy_version"],
          "release_status":"OWNER_REVIEWED_PUBLIC_SOURCES",
          "audit_authority":"read_only_no_actions","approval_id":approval["approval_id"],
          "records":sorted(items,key=lambda x:x["id"])}
    h=digest(pack)
    manifest={"schema_version":"amos.audit-curated-manifest.v1","snapshot_id":"sha256:"+h,
              "snapshot_sha256":h,"snapshot_size_bytes":len(encode(pack)),
              "approval_id":approval["approval_id"],"project_id":pack["project_id"]}
    return pack,manifest

def verify_release(pack,manifest):
    if not isinstance(pack,dict) or not isinstance(manifest,dict):
        raise ValueError("bad pack")
    if pack.get("schema_version")!="amos.audit-curated.v1" or pack.get("audit_authority")!="read_only_no_actions":
        raise ValueError("wrong type")
    if pack.get("release_status")!="OWNER_REVIEWED_PUBLIC_SOURCES":
        raise ValueError("not approved")
    for r in pack["records"]: validate_record(r)
    if pack["records"]!=sorted(pack["records"],key=lambda r:r["id"]):
        raise ValueError("unstable ordering")
    h=digest(pack)
    if manifest!={"schema_version":"amos.audit-curated-manifest.v1","snapshot_id":"sha256:"+h,
                 "snapshot_sha256":h,"snapshot_size_bytes":len(encode(pack)),
                 "approval_id":pack["approval_id"],"project_id":pack["project_id"]}:
        raise ValueError("manifest mismatch")
