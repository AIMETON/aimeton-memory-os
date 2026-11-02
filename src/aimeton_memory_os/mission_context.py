"""Read-only, evidence-grounded engineering mission context over AMOS E0.

Local operator interface, not a public HTTP endpoint or a grant of authority.
Raw GitHub text remains untrusted; it never becomes an accepted E3 decision.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

_REPO = re.compile(r"^https://api\.github\.com/repos/([^/]+/[^/]+)/")
_SECRET = re.compile(
    r"(?i)(gh[pousr]_[a-z0-9_]{20,}|github_pat_[a-z0-9_]{20,}|"
    r"(?:password|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]{4,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
_MAX_LIMIT = 500
_TEXT_LIMIT = 12000


def _sanitize(value: object) -> str:
    """Defensive output redaction; not a substitute for source ACLs."""
    text = str(value or "")
    return _SECRET.sub("[REDACTED]", text[:_TEXT_LIMIT])


def _repository(source_ref: str) -> str | None:
    match = _REPO.match(source_ref)
    return match.group(1) if match else None


def _subject(payload: dict[str, Any], source_type: str) -> str:
    if source_type == "github.pull_snapshot":
        return "PR #" + str(payload.get("number", "?"))
    issue = payload.get("issue")
    if isinstance(issue, dict) and issue.get("number") is not None:
        return "Issue #" + str(issue["number"])
    if payload.get("issue_url"):
        return "Issue #" + str(payload["issue_url"]).rstrip("/").rsplit("/", 1)[-1]
    if payload.get("number") is not None:
        return "Item #" + str(payload["number"])
    return _sanitize(payload.get("name") or source_type)


def _description(payload: dict[str, Any], source_type: str) -> str:
    issue = payload.get("issue")
    if source_type == "github.issue_comment":
        return _sanitize(payload.get("body"))
    if isinstance(issue, dict):
        return _sanitize(issue.get("title") or payload.get("event") or "")
    return _sanitize(payload.get("title") or payload.get("name") or payload.get("event") or "")


def _state(payload: dict[str, Any], source_type: str) -> str:
    if source_type == "github.workflow_run":
        return str(payload.get("conclusion") or payload.get("status") or "unknown")
    return str(payload.get("event") or payload.get("state") or "observed")


def compile_mission_context(
    db_path: str | Path,
    *,
    project: str,
    authorized_repositories: list[str],
    limit: int = 100,
    offset: int = 0,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Build a bounded, reproducible mission view from a SQLite read transaction.

    Authorization MUST be established by the embedding controller before this
    call; the allowlist is trusted input, not an end-user-supplied bearer claim.
    Projects are exact repository IDs, no substring matching. Output has no
    action execution authority. Unverified prose remains SOURCE_ASSERTION.
    """
    if not isinstance(project, str) or not project or project not in authorized_repositories:
        raise PermissionError("project not in authenticated operator repository scope")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_LIMIT:
        raise ValueError("limit must be 1..500")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("offset must be non-negative")
    if as_of is not None and (not isinstance(as_of, str) or not as_of):
        raise ValueError("as_of must be a non-empty timestamp")

    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        # One consistent SQLite snapshot; NO writes to E0.
        conn.execute("BEGIN")
        rows = conn.execute(
            """SELECT evidence_id,digest,partition_name,source_type,source_ref,
                      source_object_id,observed_at,payload_json
               FROM evidence ORDER BY observed_at,source_object_id,evidence_id"""
        )
        entries: list[dict[str, Any]] = []
        for eid, digest, partition, typ, ref, oid, observed, raw in rows:
            if _repository(str(ref)) != project or (as_of is not None and str(observed) > as_of):
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("invalid E0 payload object")
            entries.append({
                "evidence_id": eid, "stored_digest": digest,
                "partition": partition, "source_type": typ,
                "source_ref": ref, "source_object_id": oid,
                "observed_at": observed, "subject": _subject(payload, typ),
                "description": _description(payload, typ),
                "state": _state(payload, typ),
                "claim_status": "SOURCE_ASSERTION" if typ == "github.issue_comment" else "SOURCE_OBSERVATION",
            })
        conn.commit()
    finally:
        conn.close()

    # Reconstruct current observed state by object, while preserving full history.
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (str(entry["source_type"]), str(entry["source_object_id"]))
        latest[key] = entry
    recent = sorted(latest.values(), key=lambda e: (e["observed_at"], e["evidence_id"]), reverse=True)
    open_items = [e for e in recent if e["source_type"] == "github.pull_snapshot"
                  and e["state"] == "open"]
    failures = [e for e in recent if e["source_type"] == "github.workflow_run"
                and e["state"] in {"failure", "cancelled", "timed_out"}]
    comments = [e for e in recent if e["source_type"] == "github.issue_comment"]
    evidence_fingerprint = hashlib.sha256(
        json.dumps([(x["evidence_id"], x["stored_digest"]) for x in entries],
                   ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    page = entries[offset:offset + limit]
    return {
        "schema_version": "amos.mission-context.v1",
        "project": project, "mode": "SHADOW_READ_ONLY",
        "snapshot_id": "amos:mission:e0-index:" + evidence_fingerprint,
        "snapshot_note": "Index hash over stored E0 digests; independent raw-payload verification is not asserted",
        "as_of": as_of or (entries[-1]["observed_at"] if entries else None),
        "objective": {"status": "UNRESOLVED", "reason": "E0 activity alone does not prove a canonical mission goal"},
        "history": page, "history_total": len(entries),
        "pagination": {"offset": offset, "limit": limit,
                       "next_offset": offset + limit if offset + limit < len(entries) else None},
        "decisions": {"status": "UNRESOLVED", "reason": "Source comments cannot automatically become authorized E3 decisions",
                      "source_assertions": comments[:20]},
        "current_experiments": {"status": "OBSERVED_CANDIDATES", "open_pull_requests": open_items[:30]},
        "contradictions": {"status": "NOT_EVALUATED",
                           "reason": "Conflicting source claims require E3/E4 and policy-aware verification"},
        "constraints": ["read_only", "no_source_mutation", "no_implicit_E3_E4_promotion",
                        "no_autonomous_action_from_source_text"],
        "blockers": {"observed_failed_runs": failures[:30], "status": "SOURCE_OBSERVATIONS_ONLY"},
        "next_safe_step": {
            "kind": "PROPOSAL_NOT_COMMAND",
            "description": ("Review the newest failed workflow with its exact evidence reference"
                            if failures else "Verify mission objective and decisions against authorized canonical records"),
            "evidence_refs": [failures[0]["evidence_id"]] if failures else [],
            "requires_operator_authorization": True,
        },
        "provenance": {"e0_count": len(entries), "indexed_evidence_ids": [e["evidence_id"] for e in entries],
                       "all_source_digests": [e["stored_digest"] for e in entries]},
        "authority": {"read_scope": [project], "permitted_mutations": []},
    }
