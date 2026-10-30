"""Shadow Living Development Corpus primitives for AMOS MVP-1.

SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 AIMETON Project
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .continuity import compile_context_bundle, payload_digest


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def make_evidence_envelope(
    *,
    evidence_id: str,
    source_type: str,
    source_ref: str,
    observed_at: str,
    payload: dict[str, Any],
    source_object_id: str,
) -> dict[str, Any]:
    """Create canonical E0 envelope without interpreting source truth."""
    return {
        "evidence_id": evidence_id,
        "layer": "E0",
        "source_type": source_type,
        "source_ref": source_ref,
        "source_object_id": source_object_id,
        "observed_at": observed_at,
        "digest": payload_digest(payload),
        "payload": payload,
    }


class AppendOnlyEvidenceLog:
    """Tiny JSONL append-only store used to prove LDC semantics before DB selection."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def append(self, envelope: dict[str, Any]) -> bool:
        existing = {row["evidence_id"]: row for row in self.read_all()}
        evidence_id = envelope["evidence_id"]
        if evidence_id in existing:
            if existing[evidence_id]["digest"] != envelope["digest"]:
                raise ValueError(f"immutable evidence collision: {evidence_id}")
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n")
        return True


def ingest_github_issue_fixture(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn raw GitHub receipts into E0 envelopes; no semantic promotion here."""
    issue = raw["issue"]
    comment = raw["decision_comment"]
    closed_event = raw["closed_event"]
    return [
        make_evidence_envelope(
            evidence_id=f"github:issue:{issue['id']}:resource",
            source_type="github.issue",
            source_ref=issue["url"],
            source_object_id=str(issue["id"]),
            observed_at=raw["observed_at"],
            payload=issue,
        ),
        make_evidence_envelope(
            evidence_id=f"github:issue-comment:{comment['id']}",
            source_type="github.issue_comment",
            source_ref=comment["url"],
            source_object_id=str(comment["id"]),
            observed_at=comment["created_at"],
            payload=comment,
        ),
        make_evidence_envelope(
            evidence_id=f"github:issue-event:{closed_event['id']}",
            source_type="github.issue_event",
            source_ref=closed_event["url"],
            source_object_id=str(closed_event["id"]),
            observed_at=closed_event["created_at"],
            payload=closed_event,
        ),
    ]


def project_semantic_layers(
    envelopes: Iterable[dict[str, Any]], *, as_of: str
) -> dict[str, list[dict[str, Any]]]:
    """Deterministically derive bounded E1..E4 records for the issue lifecycle fixture."""
    items = list(envelopes)
    cutoff = _dt(as_of)
    issue_env = next(x for x in items if x["source_type"] == "github.issue")
    comment_env = next(x for x in items if x["source_type"] == "github.issue_comment")
    close_env = next(x for x in items if x["source_type"] == "github.issue_event")

    issue = issue_env["payload"]
    comment = comment_env["payload"]
    close_event = close_env["payload"]

    e1: list[dict[str, Any]] = [
        {
            "record_id": f"obs:issue:{issue['id']}:created",
            "layer": "E1",
            "kind": "issue_created",
            "subject": f"{issue['repository']}#{issue['number']}",
            "value": "open",
            "observed_at": issue["created_at"],
            "provenance": [issue_env["evidence_id"]],
        }
    ]
    if _dt(comment["created_at"]) <= cutoff:
        e1.append({
            "record_id": f"obs:comment:{comment['id']}",
            "layer": "E1",
            "kind": "comment_observed",
            "subject": f"{issue['repository']}#{issue['number']}",
            "value": comment["body"],
            "observed_at": comment["created_at"],
            "provenance": [comment_env["evidence_id"]],
        })
    if close_event["event"] == "closed" and _dt(close_event["created_at"]) <= cutoff:
        e1.append({
            "record_id": f"obs:event:{close_event['id']}",
            "layer": "E1",
            "kind": "issue_state",
            "subject": f"{issue['repository']}#{issue['number']}",
            "value": "closed",
            "observed_at": close_event["created_at"],
            "provenance": [close_env["evidence_id"]],
        })

    e2: list[dict[str, Any]] = []
    e3: list[dict[str, Any]] = []
    e4: list[dict[str, Any]] = []
    accepted = comment["body"].startswith("P0 accepted")
    if accepted and _dt(comment["created_at"]) <= cutoff:
        claim_id = f"claim:comment:{comment['id']}:p0-accepted"
        e2.append({
            "record_id": claim_id,
            "layer": "E2",
            "kind": "claim",
            "claim": "P0 acceptance was asserted",
            "speaker": comment["author"],
            "asserted_at": comment["created_at"],
            "provenance": [comment_env["evidence_id"]],
        })
        if comment.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}:
            e3.append({
                "record_id": f"decision:comment:{comment['id']}:accept-p0",
                "layer": "E3",
                "kind": "decision",
                "decision": "accept_p0",
                "authority": comment["author_association"],
                "effective_at": comment["created_at"],
                "supersedes": [],
                "provenance": [comment_env["evidence_id"], claim_id],
            })

    closed_obs = next((x for x in e1 if x["kind"] == "issue_state" and x["value"] == "closed"), None)
    if e3 and closed_obs:
        e4.append({
            "record_id": f"knowledge:issue:{issue['id']}:accepted-closed",
            "layer": "E4",
            "kind": "derived_knowledge",
            "knowledge": "P0 was accepted by an authorized project member and the issue was then closed",
            "valid_from": close_event["created_at"],
            "provenance": [e3[0]["record_id"], closed_obs["record_id"]],
        })
    return {"E1": e1, "E2": e2, "E3": e3, "E4": e4}


def project_vroa(
    envelopes: Iterable[dict[str, Any]], semantic: dict[str, list[dict[str, Any]]], *, as_of: str
) -> dict[str, dict[str, Any]]:
    items = list(envelopes)
    issue_env = next(x for x in items if x["source_type"] == "github.issue")
    issue = issue_env["payload"]
    state_obs = [x for x in semantic["E1"] if x["kind"] in {"issue_created", "issue_state"}]
    current_state = state_obs[-1]["value"]
    authority = semantic["E3"][0]["authority"] if semantic["E3"] else "UNRESOLVED"
    return {
        "V": {
            "scope": issue["repository"],
            "purpose": "shadow_observe_issue_lifecycle",
            "issue_number": issue["number"],
        },
        "R": {
            "actor": semantic["E2"][0]["speaker"] if semantic["E2"] else None,
            "authority": authority,
            "mode": "SHADOW",
        },
        "O": {
            "entity_type": "GitHubIssue",
            "entity_id": str(issue["id"]),
            "state": current_state,
            "valid_at": as_of,
        },
        "A": {
            "evidence_refs": [x["evidence_id"] for x in items],
            "derived_refs": [x["record_id"] for layer in ("E1", "E2", "E3", "E4") for x in semantic[layer]],
        },
    }


def compile_shadow_case(envelopes: list[dict[str, Any]], *, as_of: str) -> dict[str, Any]:
    """Compile a non-mutating ContextBundle from a real GitHub lifecycle."""
    semantic = project_semantic_layers(envelopes, as_of=as_of)
    vroa = project_vroa(envelopes, semantic, as_of=as_of)
    refs = [x["evidence_id"] for x in envelopes if _dt(x["observed_at"]) <= _dt(as_of)]
    expected = {x["evidence_id"]: x["digest"] for x in envelopes if x["evidence_id"] in refs}
    state = {
        "mission_id": "AMOS-LDC-SHADOW-0001",
        "objective": "Observe and replay one real AIMETON GitHub issue lifecycle without operational mutation",
        "status": "ACTIVE",
        "scope": vroa["V"]["scope"],
        "active_critical_path": "GitHub receipt -> E0 -> E1/E2/E3/E4 -> V/R/O/A -> CR -> Shadow ContextBundle",
        "decisions": semantic["E3"],
        "constraints": ["shadow_mode_only", "no_operational_mutation"],
        "invariants": ["E0_is_immutable", "derived_layers_do_not_rewrite_E0"],
        "attempted": [],
        "rejected": [],
        "failed": [],
        "completed": [],
        "open": ["observe_issue_state"],
        "blockers": [],
        "next_safe_action": {
            "action_id": "shadow_observe_issue_state",
            "scope": vroa["V"]["scope"],
            "description": "Observe source state only; do not mutate GitHub",
        },
        "next_after_next": {
            "action_id": "shadow_replay_issue_state",
            "scope": vroa["V"]["scope"],
            "description": "Replay the same evidence at a later boundary",
        },
        "authority_envelope": {
            "allowed_actions": ["shadow_observe_issue_state", "shadow_replay_issue_state"],
            "forbidden_actions": ["github_mutation", "production_mutation"],
        },
        "budget_envelope": {"paid_llm_calls": 0, "new_infrastructure_spend": 0},
        "exact_references": refs,
        "expected_evidence_digests": expected,
        "snapshot_id": f"amos:ldc:shadow:{as_of}",
        "state_as_of": as_of,
        "termination_criteria": ["replay distinguishes historical open state from later closed state"],
    }
    bundle = compile_context_bundle(state, [x for x in envelopes if x["evidence_id"] in refs])
    bundle["mode"] = "SHADOW"
    bundle["semantic_layers"] = semantic
    bundle["projections"] = vroa
    return bundle
