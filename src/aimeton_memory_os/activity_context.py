"""MVP-4 bounded, read-only source-provenance mission reconstruction.

Do not infer GitHub issue_comment -> workflow_run causality from timing.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .continuity import compile_context_bundle, validate_evidence


def _one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> dict[str, Any]:
    rows = conn.execute(sql, params).fetchall()
    if len(rows) != 1:
        raise ValueError(f"expected exactly one authoritative E0 record, found {len(rows)}")
    row = rows[0]
    item = {
        "evidence_id": row[0],
        "digest": row[1],
        "partition": row[2],
        "source_type": row[3],
        "source_ref": row[4],
        "source_object_id": row[5],
        "observed_at": row[6],
        "payload": json.loads(row[7]),
    }
    validate_evidence(item)
    return item


def read_activity_pair(
    db_path: str | Path, repo: str, comment_id: int, run_id: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Two indexed E0 lookups; no full table scan or network calls."""
    if repo != "AIMETON/Choke_ring_antenna":
        raise ValueError("MVP-4 pilot is scoped to the C02 repository")
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        comment = _one(
            conn,
            """SELECT evidence_id,digest,partition_name,source_type,source_ref,
                      source_object_id,observed_at,payload_json
               FROM evidence WHERE evidence_id=? AND source_type='github.issue_comment'""",
            (f"github:issue-comment:{repo}:{comment_id}",),
        )
        run = _one(
            conn,
            """SELECT evidence_id,digest,partition_name,source_type,source_ref,
                      source_object_id,observed_at,payload_json
               FROM evidence
               WHERE evidence_id LIKE ? AND source_type='github.workflow_run'
               ORDER BY observed_at DESC LIMIT 1""",
            (f"github:workflow-run:{repo}:{run_id}:%",),
        )
    if not run["evidence_id"].startswith(f"github:workflow-run:{repo}:{run_id}:"):
        raise ValueError("workflow id mismatch")
    return comment, run


def _explicit_trigger_id(payload: dict[str, Any]) -> int | None:
    # Standard workflow_run REST objects generally contain no originating comment id.
    # Only accept a source-provided exact id, not run title, time or actor proximity.
    candidate = payload.get("triggering_comment_id")
    event_payload = payload.get("event_payload")
    if candidate is None and isinstance(event_payload, dict):
        nested = event_payload.get("comment")
        if isinstance(nested, dict):
            candidate = nested.get("id")
    if candidate is None:
        return None
    try:
        return int(candidate)
    except (ValueError, TypeError):
        return None


def compile_activity_context(
    comment: dict[str, Any], run: dict[str, Any],
    *, repo: str = "AIMETON/Choke_ring_antenna"
) -> dict[str, Any]:
    """Produce a Shadow mission bundle, preserving epistemic uncertainty."""
    for evidence in (comment, run):
        validate_evidence(evidence)
        if f":{repo}:" not in evidence["evidence_id"]:
            raise ValueError("cross-repository evidence is not admissible")
    if comment["source_type"] != "github.issue_comment" or run["source_type"] != "github.workflow_run":
        raise ValueError("unexpected evidence types")
    comment_id = int(comment["payload"]["id"])
    run_id = int(run["payload"]["id"])
    if comment["evidence_id"] != f"github:issue-comment:{repo}:{comment_id}":
        raise ValueError("comment identity mismatch")
    if not run["evidence_id"].startswith(f"github:workflow-run:{repo}:{run_id}:"):
        raise ValueError("run identity mismatch")
    if comment["partition"] != run["partition"]:
        raise ValueError("evaluation partition mismatch")

    triggered = _explicit_trigger_id(run["payload"])
    causal_proven = (
        triggered == comment_id
        and run["payload"].get("event") == "issue_comment"
        and run["observed_at"] >= comment["observed_at"]
    )
    status = "VERIFIED" if causal_proven else "UNRESOLVED"
    refs = [comment["evidence_id"], run["evidence_id"]]
    run_result = {
        "status": run["payload"].get("status"),
        "conclusion": run["payload"].get("conclusion"),
        "observed_at": run["observed_at"],
        "evidence_id": run["evidence_id"],
    }
    as_of = max(comment["observed_at"], run["observed_at"])
    next_action = "shadow_review_verified_link" if causal_proven else "shadow_verify_trigger_provenance"
    state = {
        "mission_id": f"AMOS-C02-ACTIVITY-{comment_id}-{run_id}",
        "objective": "Reconstruct C02 activity without unsupported causal claims",
        "status": "ACTIVE",
        "scope": repo,
        "active_critical_path": "E0 comment + E0 workflow -> exact-source trigger proof -> decision review",
        "decisions": [],
        "constraints": ["shadow_mode_only", "read_only", "exact_source_link_required"],
        "invariants": ["E0_is_authoritative", "temporal_proximity_is_not_causal_proof"],
        "attempted": [],
        "rejected": [],
        "failed": [],
        "completed": [{"action_id": "shadow_inspect_evidence_pair", "evidence_refs": refs}],
        "open": [next_action],
        "blockers": [] if causal_proven else ["missing_source_authoritative_trigger_comment_id"],
        "next_safe_action": {
            "action_id": next_action,
            "scope": repo,
            "description": "Review verified evidence only" if causal_proven
                           else "Obtain an authoritative trigger comment id or retain UNRESOLVED",
        },
        "next_after_next": {
            "action_id": "shadow_replay_activity_context",
            "scope": repo,
            "description": "Replay mission context without mutating sources",
        },
        "authority_envelope": {
            "allowed_actions": [next_action, "shadow_replay_activity_context"],
            "forbidden_actions": ["github_mutation", "production_mutation", "automatic_fdtd_admission"],
        },
        "budget_envelope": {"paid_llm_calls": 0, "new_infrastructure_spend": 0},
        "exact_references": refs,
        "expected_evidence_digests": {item["evidence_id"]: item["digest"] for item in (comment, run)},
        "snapshot_id": f"amos:c02:activity:{comment['digest']}:{run['digest']}",
        "state_as_of": as_of,
        "termination_criteria": ["all assertions replayable from E0"],
    }
    bundle = compile_context_bundle(state, [comment, run])
    bundle.update({
        "mode": "SHADOW",
        "partition": comment["partition"],
        "causal_link": {
            "status": status,
            "basis": "exact_trigger_comment_id" if causal_proven else "no_exact_trigger_provenance",
            "comment_id": comment_id,
            "workflow_run_id": run_id,
            "evidence_refs": refs,
        },
        "workflow_observation": run_result,
        "issue_observation": {
            "issue_url": comment["payload"].get("issue_url"),
            "comment_evidence_id": comment["evidence_id"],
            "observed_at": comment["observed_at"],
        },
        "trace": {
            "trace_type": "amos.live-activity-context",
            "source_evidence_ids": refs,
            "causal_status": status,
            "source_mutation_performed": False,
        },
    })
    return bundle
