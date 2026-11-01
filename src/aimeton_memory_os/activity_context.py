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


RECEIPT_PREFIX = "AMOS_C02_DISPATCH_PROVENANCE_V1\\n"


def _receipt_claim(receipt: dict[str, Any]) -> dict[str, Any]:
    """An E0 GitHub comment authored by Actions bot, never unauthenticated prose."""
    validate_evidence(receipt)
    payload = receipt["payload"]
    user = payload.get("user") or {}
    if receipt["source_type"] != "github.issue_comment" or user.get("login") != "github-actions[bot]" or user.get("type") != "Bot":
        raise ValueError("receipt must be GitHub-authenticated Actions bot comment")
    if not str(payload.get("issue_url") or "").endswith("/issues/2"):
        raise ValueError("receipt must belong to C02 operator issue 2")
    body = payload.get("body") or ""
    if not isinstance(body, str) or not body.startswith(RECEIPT_PREFIX):
        raise ValueError("unrecognized dispatch provenance schema")
    claim = json.loads(body[len(RECEIPT_PREFIX):])
    if claim.get("schema_version") != "amos.c02.dispatch-provenance.v1":
        raise ValueError("unexpected receipt schema")
    return claim


def compile_receipted_dispatch_context(
    command: dict[str, Any],
    receipt: dict[str, Any],
    router_run: dict[str, Any],
    dispatched_run: dict[str, Any],
    *,
    repo: str = "AIMETON/Choke_ring_antenna",
) -> dict[str, Any]:
    """Confirm one exact authenticated router receipt with four immutable E0 objects."""
    import hashlib
    import re

    items = (command, receipt, router_run, dispatched_run)
    for item in items:
        validate_evidence(item)
        if f":{repo}:" not in item["evidence_id"]:
            raise ValueError("cross-repository evidence rejected")
    if [x["source_type"] for x in items] != [
        "github.issue_comment", "github.issue_comment", "github.workflow_run", "github.workflow_run"
    ]:
        raise ValueError("incorrect source types")
    claim = _receipt_claim(receipt)
    command_payload = command["payload"]
    r_payload = router_run["payload"]
    w_payload = dispatched_run["payload"]
    raw_command = command_payload.get("body")
    if not isinstance(raw_command, str) or not raw_command.strip().startswith("/"):
        raise ValueError("command is not a routed owner command")
    if (command_payload.get("user") or {}).get("login") != "Dimar4713":
        raise ValueError("command owner mismatch")
    if not str(command_payload.get("issue_url") or "").endswith("/issues/2"):
        raise ValueError("command must belong to C02 control issue")
    if claim.get("source_repository") != repo or claim.get("source_issue_number") != 2:
        raise ValueError("receipt source mismatch")
    if claim.get("source_comment_id") != command_payload.get("id"):
        raise ValueError("receipt command id mismatch")
    if claim.get("source_comment_url") != command_payload.get("url"):
        raise ValueError("receipt command url mismatch")
    if claim.get("source_comment_sha256") != hashlib.sha256(raw_command.strip().encode("utf-8")).hexdigest():
        raise ValueError("command body digest mismatch")
    if claim.get("router_run_id") != r_payload.get("id"):
        raise ValueError("router run id mismatch")
    if claim.get("target_workflow_run_id") != w_payload.get("id"):
        raise ValueError("downstream run id mismatch")
    target_workflow = claim.get("target_workflow")
    if not isinstance(target_workflow, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+\.ya?ml", target_workflow):
        raise ValueError("invalid target workflow")
    if claim.get("target_workflow_url") != w_payload.get("html_url"):
        raise ValueError("downstream url mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", str(claim.get("source_main_sha") or "")):
        raise ValueError("invalid pinned main")
    if r_payload.get("event") != "issue_comment" or w_payload.get("event") != "workflow_dispatch":
        raise ValueError("incorrect event types")
    router_path = str(r_payload.get("path") or "").split("@")[0]
    dispatched_path = str(w_payload.get("path") or "").split("@")[0]
    if router_path != ".github/workflows/c02-command-router.yml":
        raise ValueError("router workflow identity not proven")
    if dispatched_path != f".github/workflows/{target_workflow}":
        raise ValueError("dispatched workflow identity mismatch")
    refs = [x["evidence_id"] for x in items]
    if len(set(refs)) != 4 or len({x["partition"] for x in items}) != 1:
        raise ValueError("duplicate or cross-partition evidence")
    if receipt["observed_at"] < command["observed_at"]:
        raise ValueError("receipt predates original command")
    state_time = max(x["observed_at"] for x in items)
    state = {
        "mission_id": f"AMOS-C02-DISPATCH-{command_payload['id']}-{w_payload['id']}",
        "objective": "Preserve authoritative source-to-dispatch command lineage",
        "status": "ACTIVE",
        "scope": repo,
        "active_critical_path": "owner comment -> bot receipt -> exact router/workflow runs -> review output",
        "decisions": [],
        "constraints": ["shadow_mode_only", "read_only", "source_authentication_required"],
        "invariants": ["E0_is_authoritative", "no_time_proximity_inference", "receipt_requires_bot_identity"],
        "attempted": [],
        "rejected": [],
        "failed": [],
        "completed": [{"action_id": "shadow_verify_dispatch_causality", "evidence_refs": refs}],
        "open": ["shadow_review_dispatched_run_result"],
        "blockers": [],
        "next_safe_action": {
            "action_id": "shadow_review_dispatched_run_result", "scope": repo,
            "description": "Review run outcome and project admission gates; do not execute commands",
        },
        "next_after_next": {
            "action_id": "shadow_replay_dispatch_lineage", "scope": repo,
            "description": "Verify the same four E0 references after restart",
        },
        "authority_envelope": {
            "allowed_actions": ["shadow_review_dispatched_run_result", "shadow_replay_dispatch_lineage"],
            "forbidden_actions": ["github_mutation", "production_mutation", "automatic_fdtd_admission"],
        },
        "budget_envelope": {"paid_llm_calls": 0, "new_infrastructure_spend": 0},
        "exact_references": refs,
        "expected_evidence_digests": {x["evidence_id"]: x["digest"] for x in items},
        "snapshot_id": "amos:c02:dispatch:" + ":".join(x["digest"] for x in items),
        "state_as_of": state_time,
        "termination_criteria": ["source-run link independently replayable from four E0"],
    }
    bundle = compile_context_bundle(state, list(items))
    bundle.update({
        "mode": "SHADOW",
        "partition": command["partition"],
        "causal_link": {
            "status": "VERIFIED",
            "basis": "github_actions_bot_dispatch_receipt_exact_run_ids",
            "source_comment_id": command_payload["id"],
            "router_run_id": r_payload["id"],
            "dispatched_run_id": w_payload["id"],
            "evidence_refs": refs,
        },
        "workflow_observation": {
            "status": w_payload.get("status"),
            "conclusion": w_payload.get("conclusion"),
            "evidence_id": dispatched_run["evidence_id"],
        },
        "trace": {"trace_type": "amos.live-dispatch-provenance",
                  "source_evidence_ids": refs, "causal_status": "VERIFIED",
                  "source_mutation_performed": False},
    })
    return bundle


def read_receipted_dispatch_e0(
    db_path: str | Path, repo: str, source_comment_id: int, receipt_comment_id: int,
    router_run_id: int, dispatched_run_id: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Four bounded indexed lookups, immutable E0 only, no GitHub requests."""
    if repo != "AIMETON/Choke_ring_antenna":
        raise ValueError("unsupported C02 pilot scope")
    columns = """SELECT evidence_id,digest,partition_name,source_type,source_ref,
                        source_object_id,observed_at,payload_json FROM evidence"""
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        comments = [
            _one(conn, columns + " WHERE evidence_id=?",
                 (f"github:issue-comment:{repo}:{ident}",))
            for ident in (source_comment_id, receipt_comment_id)
        ]
        runs = [
            _one(conn, columns +
                 " WHERE evidence_id LIKE ? AND source_type='github.workflow_run'"
                 " ORDER BY observed_at DESC LIMIT 1",
                 (f"github:workflow-run:{repo}:{ident}:%",))
            for ident in (router_run_id, dispatched_run_id)
        ]
    return comments[0], comments[1], runs[0], runs[1]
