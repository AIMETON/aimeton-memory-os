"""AMOS G1 synthetic-only, fail-closed offline external audit pack exporter.

No raw E0 ingestion, user text, production project identifiers, or live access.
An owner-approved real data exporter requires separate security admission.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "amos.audit-pack.synthetic.v0.1"
DEMO_PROJECT = "amos-synthetic-audit-demo"
ALLOWED_KINDS = frozenset({"scope", "observation", "decision", "blocker"})
ALLOWED_RESULTS = frozenset({"PASS", "FAIL", "UNRESOLVED"})
ALLOWED_STATES = frozenset({"VERIFIED", "UNRESOLVED"})
ALLOWED_TITLES = frozenset({
    "Synthetic scope", "Synthetic validation", "Synthetic decision",
    "Synthetic blocker",
})


def canonical_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha256(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def _strict_keys(obj: Any, expected: set[str]) -> None:
    if not isinstance(obj, dict) or set(obj) != expected:
        raise ValueError("audit export contract rejected: invalid field set")


def _timestamp(value: Any) -> bool:
    # Frozen UTC only: no dependence on local clock or run time.
    return isinstance(value, str) and bool(re.fullmatch(
        r"20[0-9]{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
        r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z", value
    ))


def export_synthetic_audit_pack(source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Deterministically project an allowlisted synthetic release fixture.

    This function deliberately CANNOT export actual AMOS evidence or a
    private repository: real-project support is a future G0 policy gate.
    """
    _strict_keys(source, {
        "project_id", "source_profile", "export_policy_version", "as_of_utc",
        "authorization", "records",
    })
    if (source["project_id"] != DEMO_PROJECT
            or source["source_profile"] != "synthetic_fixture"
            or source["export_policy_version"] != "synthetic-v1"
            or source["authorization"] != "synthetic-test-only"
            or not _timestamp(source["as_of_utc"])):
        raise ValueError("audit export contract rejected: not an authorized synthetic fixture")
    if not isinstance(source["records"], list) or len(source["records"]) > 32:
        raise ValueError("audit export contract rejected: record limit")

    permitted: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in source["records"]:
        # Denied records, including nested secret-containing payloads, have no
        # influence on output bytes, counts, object names or cursor positions.
        if not isinstance(item, dict):
            raise ValueError("audit export contract rejected: malformed record")
        if item.get("export_rule") == "deny":
            continue
        _strict_keys(item, {
            "record_id", "export_rule", "security_label", "kind", "title",
            "result", "provenance_status", "evidence_digest",
        })
        if item["export_rule"] != "allow" or item["security_label"] != "synthetic_public":
            raise ValueError("audit export contract rejected: record policy")
        rid = item["record_id"]
        if not isinstance(rid, str) or not re.fullmatch(r"SYN-[0-9]{3}", rid) or rid in ids:
            raise ValueError("audit export contract rejected: record identity")
        ids.add(rid)
        if (item["kind"] not in ALLOWED_KINDS
                or item["title"] not in ALLOWED_TITLES
                or item["result"] not in ALLOWED_RESULTS
                or item["provenance_status"] not in ALLOWED_STATES
                or not isinstance(item["evidence_digest"], str)
                or not re.fullmatch("[0-9a-f]{64}", item["evidence_digest"])):
            raise ValueError("audit export contract rejected: record value")
        permitted.append({
            "record_id": rid,
            "kind": item["kind"],
            "title": item["title"],
            "result": item["result"],
            "provenance_status": item["provenance_status"],
            "evidence_sha256": item["evidence_digest"],
        })
    if not permitted:
        raise ValueError("audit export contract rejected: no explicitly permitted records")
    permitted.sort(key=lambda row: row["record_id"])

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "project_id": DEMO_PROJECT,
        "as_of_utc": source["as_of_utc"],
        "release_status": "NON_PUBLIC_SYNTHETIC_TEST_ONLY",
        "audit_authority": "read_only_no_actions",
        "policy_version": "synthetic-v1",
        "records": permitted,
    }
    digest = sha256(snapshot)
    manifest = {
        "schema_version": "amos.audit-manifest.synthetic.v0.1",
        "project_id": DEMO_PROJECT,
        "snapshot_id": "sha256:" + digest,
        "snapshot_filename": "snapshot.json",
        "snapshot_sha256": digest,
        "snapshot_size_bytes": len(canonical_bytes(snapshot)),
        "as_of_utc": source["as_of_utc"],
        "policy_version": "synthetic-v1",
        "release_status": "NON_PUBLIC_SYNTHETIC_TEST_ONLY",
    }
    return snapshot, manifest


def verify_synthetic_audit_pack(snapshot: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Independent byte-contract check without trusting manifest's hash."""
    _strict_keys(manifest, {
        "schema_version", "project_id", "snapshot_id", "snapshot_filename",
        "snapshot_sha256", "snapshot_size_bytes", "as_of_utc",
        "policy_version", "release_status",
    })
    _strict_keys(snapshot, {
        "schema_version", "project_id", "as_of_utc", "release_status",
        "audit_authority", "policy_version", "records",
    })
    if (snapshot["schema_version"] != SCHEMA_VERSION
            or snapshot["project_id"] != DEMO_PROJECT
            or snapshot["release_status"] != "NON_PUBLIC_SYNTHETIC_TEST_ONLY"
            or snapshot["audit_authority"] != "read_only_no_actions"
            or snapshot["policy_version"] != "synthetic-v1"
            or manifest["schema_version"] != "amos.audit-manifest.synthetic.v0.1"
            or manifest["project_id"] != DEMO_PROJECT
            or manifest["policy_version"] != "synthetic-v1"
            or manifest["release_status"] != snapshot["release_status"]
            or manifest["as_of_utc"] != snapshot["as_of_utc"]
            or manifest["snapshot_filename"] != "snapshot.json"):
        raise ValueError("audit pack verification failed: contract mismatch")
    digest = sha256(snapshot)
    if (manifest["snapshot_sha256"] != digest
            or manifest["snapshot_id"] != "sha256:" + digest
            or manifest["snapshot_size_bytes"] != len(canonical_bytes(snapshot))):
        raise ValueError("audit pack verification failed: digest mismatch")
    # Reconstruct approved content through the same strict allowlist; never
    # blindly trust records when loading an exported snapshot.
    records = snapshot["records"]
    if not isinstance(records, list):
        raise ValueError("audit pack verification failed: records")
    synthetic_source = {
        "project_id": DEMO_PROJECT,
        "source_profile": "synthetic_fixture",
        "export_policy_version": "synthetic-v1",
        "authorization": "synthetic-test-only",
        "as_of_utc": snapshot["as_of_utc"],
        "records": [
            {
                "record_id": row["record_id"],
                "export_rule": "allow",
                "security_label": "synthetic_public",
                "kind": row["kind"],
                "title": row["title"],
                "result": row["result"],
                "provenance_status": row["provenance_status"],
                "evidence_digest": row["evidence_sha256"],
            } for row in records
        ],
    }
    reconstructed, expected_manifest = export_synthetic_audit_pack(synthetic_source)
    if reconstructed != snapshot or expected_manifest != manifest:
        raise ValueError("audit pack verification failed: unapproved record content")
