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
    *, evidence_id: str, source_type: str, source_ref: str,
    observed_at: str, payload: dict[str, Any], source_object_id: str,
    partition: str = "development",
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "layer": "E0",
        "partition": partition,
        "source_type": source_type,
        "source_ref": source_ref,
        "source_object_id": source_object_id,
        "observed_at": observed_at,
        "digest": payload_digest(payload),
        "payload": payload,
    }


class AppendOnlyEvidenceLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

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
    """Turn source-grounded GitHub lifecycle receipts into immutable E0 envelopes."""
    opened = raw["opened_event"]
    comment = raw["decision_comment"]
    closed = raw["closed_event"]
    return [
        make_evidence_envelope(
            evidence_id=f"github:issue-opened:{opened['issue_id']}",
            source_type="github.issue_opened",
            source_ref=opened["source_ref"],
            source_object_id=str(opened["issue_id"]),
            observed_at=opened["created_at"],
            payload=opened,
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
            evidence_id=f"github:issue-event:{closed['id']}",
            source_type="github.issue_event",
            source_ref=closed["url"],
            source_object_id=str(closed["id"]),
            observed_at=closed["created_at"],
            payload=closed,
        ),
    ]


def project_semantic_layers(
    envelopes: Iterable[dict[str, Any]], *, as_of: str
) -> dict[str, list[dict[str, Any]]]:
    items = list(envelopes)
    cutoff = _dt(as_of)
    opened_env = next(x for x in items if x["source_type"] == "github.issue_opened")
    comment_env = next(x for x in items if x["source_type"] == "github.issue_comment")
    close_env = next(x for x in items if x["source_type"] == "github.issue_event")
    opened, comment, closed = opened_env["payload"], comment_env["payload"], close_env["payload"]

    e1 = [{
        "record_id": f"obs:issue:{opened['issue_id']}:opened",
        "layer": "E1",
        "kind": "issue_state",
        "subject": f"{opened['repository']}#{opened['number']}",
        "value": "open",
        "observed_at": opened["created_at"],
        "provenance": [opened_env["evidence_id"]],
    }]
    if _dt(comment["created_at"]) <= cutoff:
        e1.append({
            "record_id": f"obs:comment:{comment['id']}",
            "layer": "E1",
            "kind": "comment_observed",
            "subject": f"{opened['repository']}#{opened['number']}",
            "value": comment["body"],
            "observed_at": comment["created_at"],
            "provenance": [comment_env["evidence_id"]],
        })
    if closed["event"] == "closed" and _dt(closed["created_at"]) <= cutoff:
        e1.append({
            "record_id": f"obs:event:{closed['id']}",
            "layer": "E1",
            "kind": "issue_state",
            "subject": f"{opened['repository']}#{opened['number']}",
            "value": "closed",
            "observed_at": closed["created_at"],
            "provenance": [close_env["evidence_id"]],
        })

    e2, e3, e4 = [], [], []
    if comment["body"].startswith("P0 accepted") and _dt(comment["created_at"]) <= cutoff:
        claim_id = f"claim:comment:{comment['id']}:p0-accepted"
        e2.append({
            "record_id": claim_id, "layer": "E2", "kind": "claim",
            "claim": "P0 acceptance was asserted", "speaker": comment["author"],
            "asserted_at": comment["created_at"], "provenance": [comment_env["evidence_id"]],
        })
        if comment.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}:
            e3.append({
                "record_id": f"decision:comment:{comment['id']}:accept-p0",
                "layer": "E3", "kind": "decision", "decision": "accept_p0",
                "authority": comment["author_association"], "effective_at": comment["created_at"],
                "supersedes": [], "provenance": [comment_env["evidence_id"], claim_id],
            })

    closed_obs = next((x for x in e1 if x["kind"] == "issue_state" and x["value"] == "closed"), None)
    if e3 and closed_obs:
        e4.append({
            "record_id": f"knowledge:issue:{opened['issue_id']}:accepted-closed",
            "layer": "E4", "kind": "derived_knowledge",
            "knowledge": "P0 was accepted by an authorized project member and the issue was then closed",
            "valid_from": closed["created_at"],
            "provenance": [e3[0]["record_id"], closed_obs["record_id"]],
        })
    return {"E1": e1, "E2": e2, "E3": e3, "E4": e4}


def project_vroa(
    envelopes: Iterable[dict[str, Any]], semantic: dict[str, list[dict[str, Any]]], *, as_of: str
) -> dict[str, dict[str, Any]]:
    items = list(envelopes)
    opened = next(x for x in items if x["source_type"] == "github.issue_opened")["payload"]
    state_obs = [x for x in semantic["E1"] if x["kind"] == "issue_state"]
    current_state = state_obs[-1]["value"]
    return {
        "V": {"scope": opened["repository"], "purpose": "shadow_observe_issue_lifecycle", "issue_number": opened["number"]},
        "R": {
            "actor": semantic["E2"][0]["speaker"] if semantic["E2"] else None,
            "authority": semantic["E3"][0]["authority"] if semantic["E3"] else "UNRESOLVED",
            "mode": "SHADOW",
        },
        "O": {"entity_type": "GitHubIssue", "entity_id": str(opened["issue_id"]), "state": current_state, "valid_at": as_of},
        "A": {
            "evidence_refs": [x["evidence_id"] for x in items if _dt(x["observed_at"]) <= _dt(as_of)],
            "derived_refs": [x["record_id"] for layer in ("E1","E2","E3","E4") for x in semantic[layer]],
        },
    }


def compile_shadow_case(envelopes: list[dict[str, Any]], *, as_of: str) -> dict[str, Any]:
    semantic = project_semantic_layers(envelopes, as_of=as_of)
    vroa = project_vroa(envelopes, semantic, as_of=as_of)
    active = [x for x in envelopes if _dt(x["observed_at"]) <= _dt(as_of)]
    refs = [x["evidence_id"] for x in active]
    expected = {x["evidence_id"]: x["digest"] for x in active}
    state = {
        "mission_id": "AMOS-LDC-SHADOW-0001",
        "objective": "Observe and replay one real AIMETON GitHub issue lifecycle without operational mutation",
        "status": "ACTIVE",
        "scope": vroa["V"]["scope"],
        "active_critical_path": "GitHub receipt -> E0 -> E1/E2/E3/E4 -> V/R/O/A -> CR -> Shadow ContextBundle",
        "decisions": semantic["E3"],
        "constraints": ["shadow_mode_only", "no_operational_mutation"],
        "invariants": ["E0_is_immutable", "derived_layers_do_not_rewrite_E0"],
        "attempted": [], "rejected": [], "failed": [], "completed": [],
        "open": ["observe_issue_state"], "blockers": [],
        "next_safe_action": {
            "action_id": "shadow_observe_issue_state", "scope": vroa["V"]["scope"],
            "description": "Observe source state only; do not mutate GitHub",
        },
        "next_after_next": {
            "action_id": "shadow_replay_issue_state", "scope": vroa["V"]["scope"],
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
    bundle = compile_context_bundle(state, active)
    bundle["mode"] = "SHADOW"
    bundle["semantic_layers"] = semantic
    bundle["projections"] = vroa
    bundle["trace"] = {
        "snapshot_id": state["snapshot_id"],
        "as_of": as_of,
        "evidence": [{"id": x["evidence_id"], "digest": x["digest"]} for x in active],
        "compatibility": [{"check_id": x["check_id"], "state": x["state"], "reason_code": x["reason_code"]} for x in bundle["compatibility"]],
    }
    return bundle
