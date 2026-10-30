"""Deterministic AMOS MVP-0 continuity kernel.

SPDX-License-Identifier: Apache-2.0
Copyright (c) 2026 AIMETON Project
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


CR_IDS = tuple(f"CR-{n:02d}" for n in range(1, 7))
REQUIRED_STATE_FIELDS = {
    "mission_id", "objective", "status", "scope", "active_critical_path",
    "decisions", "constraints", "invariants", "attempted", "rejected",
    "failed", "completed", "open", "blockers", "next_safe_action",
    "next_after_next", "authority_envelope", "budget_envelope",
    "exact_references", "expected_evidence_digests", "snapshot_id",
    "state_as_of", "termination_criteria",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_mission_state(state: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_STATE_FIELDS - set(state))
    if missing:
        raise ValueError(f"mission state missing fields: {', '.join(missing)}")
    if state["status"] not in {"ACTIVE", "BLOCKED", "COMPLETED"}:
        raise ValueError("mission status must be ACTIVE, BLOCKED or COMPLETED")
    if not isinstance(state["exact_references"], list) or not state["exact_references"]:
        raise ValueError("exact_references must be a non-empty list")
    if not isinstance(state["authority_envelope"], dict):
        raise ValueError("authority_envelope must be an object")
    if not isinstance(state["budget_envelope"], dict):
        raise ValueError("budget_envelope must be an object")


def validate_evidence(evidence: dict[str, Any]) -> None:
    for key in ("evidence_id", "source_type", "source_ref", "observed_at", "digest", "payload"):
        if key not in evidence:
            raise ValueError(f"evidence missing field: {key}")
    actual = payload_digest(evidence["payload"])
    if actual != evidence["digest"]:
        raise ValueError(
            f"evidence digest mismatch for {evidence['evidence_id']}: "
            f"expected={evidence['digest']} actual={actual}"
        )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _result(check_id: str, ok: bool, reason_ok: str, reason_bad: str, refs: list[str]) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "state": "satisfied" if ok else "blocked",
        "reason_code": reason_ok if ok else reason_bad,
        "refs": refs,
    }


def evaluate_compatibility(
    state: dict[str, Any], evidence_items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    validate_mission_state(state)
    evidence_by_id: dict[str, dict[str, Any]] = {}
    invalid_evidence: set[str] = set()
    for item in evidence_items:
        try:
            validate_evidence(item)
        except ValueError:
            invalid_evidence.add(str(item.get("evidence_id", "<unknown>")))
        else:
            evidence_by_id[item["evidence_id"]] = item

    next_action = state["next_safe_action"]
    refs = list(state["exact_references"])
    checks: list[dict[str, Any]] = []

    checks.append(_result(
        "CR-01",
        next_action.get("scope") == state["scope"],
        "scope_aligned",
        "scope_mismatch",
        refs,
    ))

    allowed = set(state["authority_envelope"].get("allowed_actions", []))
    checks.append(_result(
        "CR-02",
        next_action.get("action_id") in allowed,
        "authority_bound",
        "action_not_authorized",
        refs,
    ))

    completed_ids = {item.get("action_id") for item in state["completed"]}
    checks.append(_result(
        "CR-03",
        state["status"] == "ACTIVE" and next_action.get("action_id") not in completed_ids,
        "active_state_valid",
        "inactive_or_duplicate_action",
        refs,
    ))

    missing_refs = [ref for ref in refs if ref not in evidence_by_id]
    checks.append(_result(
        "CR-04",
        not missing_refs and not invalid_evidence,
        "primary_evidence_present",
        "primary_evidence_missing_or_invalid",
        refs,
    ))

    temporal_ok = True
    if not missing_refs:
        state_time = _dt(state["state_as_of"])
        temporal_ok = all(_dt(evidence_by_id[ref]["observed_at"]) <= state_time for ref in refs)
    checks.append(_result(
        "CR-05",
        temporal_ok and not missing_refs,
        "temporal_coherence",
        "evidence_after_state_or_missing",
        refs,
    ))

    expected = state["expected_evidence_digests"]
    snapshot_ok = (
        set(expected) == set(refs)
        and all(
            ref in evidence_by_id and expected[ref] == evidence_by_id[ref]["digest"]
            for ref in refs
        )
    )
    checks.append(_result(
        "CR-06",
        snapshot_ok,
        "snapshot_coherent",
        "source_version_changed_or_unreconstructable",
        refs,
    ))
    return checks


def compile_context_bundle(
    state: dict[str, Any], evidence_items: list[dict[str, Any]]
) -> dict[str, Any]:
    checks = evaluate_compatibility(state, evidence_items)
    outcome = "admit" if all(c["state"] == "satisfied" for c in checks) else "escalate"
    return {
        "bundle_version": "0.1",
        "mission": {"mission_id": state["mission_id"], "objective": state["objective"]},
        "current_state": state["status"],
        "active_critical_path": state["active_critical_path"],
        "decisions": state["decisions"],
        "constraints": state["constraints"],
        "invariants": state["invariants"],
        "attempted": state["attempted"],
        "rejected": state["rejected"],
        "failed": state["failed"],
        "completed": state["completed"],
        "open": state["open"],
        "blocked": state["blockers"],
        "next_safe_action": state["next_safe_action"],
        "next_after_next": state["next_after_next"],
        "authority_envelope": state["authority_envelope"],
        "budget_envelope": state["budget_envelope"],
        "exact_references": state["exact_references"],
        "snapshot_id": state["snapshot_id"],
        "state_as_of": state["state_as_of"],
        "compatibility": checks,
        "outcome": outcome,
    }


def recovery_assertions(bundle: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    completed_ids = {item["action_id"] for item in bundle["completed"]}
    next_id = bundle["next_safe_action"]["action_id"]
    return {
        "mission_id_match": bundle["mission"]["mission_id"] == expected["mission_id"],
        "state_match": bundle["current_state"] == expected["status"],
        "next_match": next_id == expected["next_action_id"],
        "next_after_next_match": (
            bundle["next_after_next"]["action_id"] == expected["next_after_next_action_id"]
        ),
        "duplicate_mutation_count": 1 if next_id in completed_ids else 0,
        "authority_preserved": (
            next_id in set(bundle["authority_envelope"].get("allowed_actions", []))
        ),
        "evidence_refs_match": set(bundle["exact_references"]) == set(expected["exact_references"]),
        "outcome": bundle["outcome"],
    }
