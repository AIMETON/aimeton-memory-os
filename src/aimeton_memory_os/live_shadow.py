"""Post-persistence Shadow derivation for the AMOS Living Development Corpus.

This module never reads GitHub directly. It derives bounded semantic layers,
V/R/O/A projections, Compatibility Registry results and immutable traces from
E0 evidence already persisted by the collector.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .continuity import compile_context_bundle


_REPO_RE = re.compile(r"https://api\.github\.com/repos/([^/]+/[^/]+)/")


def _repo(envelope: dict[str, Any]) -> str:
    match = _REPO_RE.match(str(envelope["source_ref"]))
    if not match:
        raise ValueError(f"unsupported GitHub source_ref: {envelope['source_ref']}")
    return match.group(1)


def _actor(payload: dict[str, Any]) -> tuple[str | None, str]:
    user = payload.get("user") or payload.get("actor") or {}
    if isinstance(user, dict):
        login = user.get("login")
    else:
        login = str(user) if user else None
    authority = str(payload.get("author_association") or "SOURCE")
    return login, authority


def _issue_number(envelope: dict[str, Any]) -> int | None:
    payload = envelope["payload"]
    if envelope["source_type"] == "github.pull_snapshot" and payload.get("number") is not None:
        return int(payload["number"])
    issue = payload.get("issue")
    if isinstance(issue, dict) and issue.get("number") is not None:
        return int(issue["number"])
    issue_url = payload.get("issue_url")
    if issue_url:
        try:
            return int(str(issue_url).rstrip("/").split("/")[-1])
        except ValueError:
            return None
    return None


def semantic_layers_for_envelope(envelope: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    payload = envelope["payload"]
    actor, authority = _actor(payload)
    e1 = [{
        "record_id": f"obs:{envelope['evidence_id']}",
        "layer": "E1",
        "kind": "source_observed",
        "source_type": envelope["source_type"],
        "observed_at": envelope["observed_at"],
        "provenance": [envelope["evidence_id"]],
    }]
    e2: list[dict[str, Any]] = []
    if envelope["source_type"] == "github.issue_comment" and str(payload.get("body") or "").strip():
        e2.append({
            "record_id": f"claim:{envelope['evidence_id']}",
            "layer": "E2",
            "kind": "source_assertion",
            "speaker": actor,
            "authority_hint": authority,
            "text": str(payload["body"]),
            "asserted_at": envelope["observed_at"],
            "provenance": [envelope["evidence_id"]],
        })
    return {"E1": e1, "E2": e2, "E3": [], "E4": []}


def compile_envelope_bundle(envelope: dict[str, Any]) -> dict[str, Any]:
    repo = _repo(envelope)
    payload = envelope["payload"]
    actor, authority = _actor(payload)
    semantic = semantic_layers_for_envelope(envelope)
    issue_number = _issue_number(envelope)
    vroa = {
        "V": {
            "scope": repo,
            "purpose": "shadow_observe_persisted_evidence",
            "issue_number": issue_number,
        },
        "R": {"actor": actor, "authority": authority, "mode": "SHADOW"},
        "O": {
            "entity_type": envelope["source_type"],
            "entity_id": envelope["source_object_id"],
            "state": str(payload.get("event") or payload.get("state") or "observed"),
            "valid_at": envelope["observed_at"],
        },
        "A": {
            "evidence_refs": [envelope["evidence_id"]],
            "derived_refs": [
                record["record_id"]
                for layer in ("E1", "E2", "E3", "E4")
                for record in semantic[layer]
            ],
        },
    }
    state = {
        "mission_id": f"AMOS-LIVE-EVIDENCE-{envelope['source_object_id']}",
        "objective": "Derive a Shadow ContextBundle from already persisted E0 evidence",
        "status": "ACTIVE",
        "scope": repo,
        "active_critical_path": "durable E0 -> semantic layers -> V/R/O/A -> CR -> immutable Shadow trace",
        "decisions": [],
        "constraints": ["post_persistence_only", "shadow_mode_only", "no_source_mutation"],
        "invariants": ["E0_is_authoritative", "derived_trace_is_not_source_of_truth"],
        "attempted": [], "rejected": [], "failed": [], "completed": [],
        "open": ["record_shadow_trace"], "blockers": [],
        "next_safe_action": {
            "action_id": "shadow_record_trace",
            "scope": repo,
            "description": "Record derived Shadow trace only",
        },
        "next_after_next": {
            "action_id": "shadow_replay_trace",
            "scope": repo,
            "description": "Replay derived trace against immutable E0",
        },
        "authority_envelope": {
            "allowed_actions": ["shadow_record_trace", "shadow_replay_trace"],
            "forbidden_actions": ["github_mutation", "production_mutation"],
        },
        "budget_envelope": {"paid_llm_calls": 0, "new_infrastructure_spend": 0},
        "exact_references": [envelope["evidence_id"]],
        "expected_evidence_digests": {envelope["evidence_id"]: envelope["digest"]},
        "snapshot_id": f"amos:live:evidence:{envelope['digest']}",
        "state_as_of": envelope["observed_at"],
        "termination_criteria": ["trace is deterministic and replayable from E0"],
    }
    bundle = compile_context_bundle(state, [envelope])
    bundle["mode"] = "SHADOW"
    bundle["partition"] = envelope["partition"]
    bundle["semantic_layers"] = semantic
    bundle["projections"] = vroa
    bundle["trace"] = {
        "trace_type": "amos.live-evidence",
        "source_evidence_id": envelope["evidence_id"],
        "source_digest": envelope["digest"],
        "compatibility": [
            {
                "check_id": item["check_id"],
                "state": item["state"],
                "reason_code": item["reason_code"],
            }
            for item in bundle["compatibility"]
        ],
        "source_mutation_performed": False,
    }
    return bundle


def _decision_chains(envelopes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for envelope in envelopes:
        number = _issue_number(envelope)
        if number is not None:
            grouped.setdefault((_repo(envelope), number), []).append(envelope)

    traces: list[dict[str, Any]] = []
    for (repo, number), group in grouped.items():
        comments = [
            e for e in group
            if e["source_type"] == "github.issue_comment"
            and str(e["payload"].get("body") or "").startswith("P0 accepted")
            and str(e["payload"].get("author_association") or "") in {"OWNER", "MEMBER", "COLLABORATOR"}
        ]
        closed = [
            e for e in group
            if e["source_type"] == "github.issue_event"
            and e["payload"].get("event") == "closed"
        ]
        for comment in comments:
            later = [event for event in closed if event["observed_at"] >= comment["observed_at"]]
            if not later:
                continue
            event = sorted(later, key=lambda x: (x["observed_at"], x["source_object_id"]))[0]
            actor, authority = _actor(comment["payload"])
            claim_id = f"claim:{comment['evidence_id']}:p0-accepted"
            decision_id = f"decision:{comment['evidence_id']}:accept-p0"
            closed_obs = f"obs:{event['evidence_id']}:closed"
            knowledge_id = f"knowledge:{repo}:{number}:accepted-closed"
            semantic = {
                "E1": [
                    {
                        "record_id": f"obs:{comment['evidence_id']}",
                        "layer": "E1",
                        "kind": "comment_observed",
                        "observed_at": comment["observed_at"],
                        "provenance": [comment["evidence_id"]],
                    },
                    {
                        "record_id": closed_obs,
                        "layer": "E1",
                        "kind": "issue_state",
                        "value": "closed",
                        "observed_at": event["observed_at"],
                        "provenance": [event["evidence_id"]],
                    },
                ],
                "E2": [{
                    "record_id": claim_id,
                    "layer": "E2",
                    "kind": "claim",
                    "claim": "P0 acceptance was asserted",
                    "speaker": actor,
                    "asserted_at": comment["observed_at"],
                    "provenance": [comment["evidence_id"]],
                }],
                "E3": [{
                    "record_id": decision_id,
                    "layer": "E3",
                    "kind": "decision",
                    "decision": "accept_p0",
                    "authority": authority,
                    "effective_at": comment["observed_at"],
                    "provenance": [comment["evidence_id"], claim_id],
                }],
                "E4": [{
                    "record_id": knowledge_id,
                    "layer": "E4",
                    "kind": "derived_knowledge",
                    "knowledge": "P0 was accepted by an authorized project member and the issue was then closed",
                    "valid_from": event["observed_at"],
                    "provenance": [decision_id, closed_obs],
                }],
            }
            refs = [comment["evidence_id"], event["evidence_id"]]
            state = {
                "mission_id": f"AMOS-LIVE-ISSUE-{number}-DECISION",
                "objective": "Derive decision lineage from persisted GitHub evidence",
                "status": "ACTIVE",
                "scope": repo,
                "active_critical_path": "persisted comment + persisted close event -> E2/E3/E4 -> CR -> trace",
                "decisions": semantic["E3"],
                "constraints": ["post_persistence_only", "shadow_mode_only"],
                "invariants": ["E0_is_authoritative", "decision_lineage_preserves_provenance"],
                "attempted": [], "rejected": [], "failed": [], "completed": [],
                "open": ["record_decision_lineage"], "blockers": [],
                "next_safe_action": {
                    "action_id": "shadow_record_decision_lineage",
                    "scope": repo,
                    "description": "Record derived decision lineage only",
                },
                "next_after_next": {
                    "action_id": "shadow_replay_decision_lineage",
                    "scope": repo,
                    "description": "Replay decision lineage from E0",
                },
                "authority_envelope": {
                    "allowed_actions": ["shadow_record_decision_lineage", "shadow_replay_decision_lineage"],
                    "forbidden_actions": ["github_mutation", "production_mutation"],
                },
                "budget_envelope": {"paid_llm_calls": 0, "new_infrastructure_spend": 0},
                "exact_references": refs,
                "expected_evidence_digests": {
                    comment["evidence_id"]: comment["digest"],
                    event["evidence_id"]: event["digest"],
                },
                "snapshot_id": f"amos:live:issue:{number}:{event['digest']}",
                "state_as_of": event["observed_at"],
                "termination_criteria": ["E2/E3/E4 lineage is reproducible from two E0 records"],
            }
            bundle = compile_context_bundle(state, [comment, event])
            bundle["mode"] = "SHADOW"
            bundle["partition"] = comment["partition"]
            bundle["semantic_layers"] = semantic
            bundle["projections"] = {
                "V": {"scope": repo, "purpose": "shadow_decision_lineage", "issue_number": number},
                "R": {"actor": actor, "authority": authority, "mode": "SHADOW"},
                "O": {"entity_type": "GitHubIssue", "entity_id": str(number), "state": "closed", "valid_at": event["observed_at"]},
                "A": {
                    "evidence_refs": refs,
                    "derived_refs": [
                        record["record_id"]
                        for layer in ("E1", "E2", "E3", "E4")
                        for record in semantic[layer]
                    ],
                },
            }
            bundle["trace"] = {
                "trace_type": "amos.live-decision-chain",
                "issue": number,
                "source_evidence_ids": refs,
                "compatibility": [
                    {"check_id": x["check_id"], "state": x["state"], "reason_code": x["reason_code"]}
                    for x in bundle["compatibility"]
                ],
                "source_mutation_performed": False,
            }
            traces.append(bundle)
    return traces


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _trace_path(root: Path, trace_id: str) -> Path:
    digest = hashlib.sha256(trace_id.encode("utf-8")).hexdigest()
    return root / f"{digest}.json"


def _write_immutable(path: Path, payload: dict[str, Any]) -> bool:
    rendered = _canonical(payload)
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise ValueError(f"immutable trace collision: {path.name}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(rendered, encoding="utf-8")
    tmp.replace(path)
    return True


def _read_envelopes_ro(db_path: str | Path) -> tuple[list[dict[str, Any]], int]:
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        rows = conn.execute(
            """
            SELECT evidence_id,digest,partition_name,source_type,source_ref,
                   source_object_id,observed_at,payload_json
            FROM evidence
            ORDER BY observed_at, source_object_id
            """
        ).fetchall()
        count = int(conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0])
    finally:
        conn.close()
    envelopes = [
        {
            "evidence_id": row[0],
            "layer": "E0",
            "digest": row[1],
            "partition": row[2],
            "source_type": row[3],
            "source_ref": row[4],
            "source_object_id": row[5],
            "observed_at": row[6],
            "payload": json.loads(row[7]),
        }
        for row in rows
    ]
    return envelopes, count


def _store_signature(db_path: str | Path) -> tuple[int, int]:
    """Cheap append-only E0 watermark; no E0 content is modified."""
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        count, max_rowid = conn.execute(
            "SELECT COUNT(*), COALESCE(MAX(rowid), 0) FROM evidence"
        ).fetchone()
        return int(count), int(max_rowid)
    finally:
        conn.close()


def process_shadow_store(
    db_path: str | Path, output_dir: str | Path, *, verify_all: bool = False
) -> dict[str, Any]:
    root = Path(output_dir)
    checkpoint = root / ".shadow-processor-checkpoint.json"
    before_signature = _store_signature(db_path)
    if not verify_all and checkpoint.is_file():
        try:
            previous = json.loads(checkpoint.read_text(encoding="utf-8"))
            if (
                previous.get("schema_version") == 1
                and previous.get("signature") == list(before_signature)
                and previous.get("traces") == sum(1 for path in root.glob("*.json") if path.name != checkpoint.name)
            ):
                return {
                    "schema_version": "1.0",
                    "evidence_count": before_signature[0],
                    "envelope_traces": previous["envelope_traces"],
                    "decision_chain_traces": previous["decision_chain_traces"],
                    "created": 0,
                    "existing": previous["traces"],
                    "idle_fast_path": True,
                    "e0_mutation_performed": False,
                    "source_mutation_performed": False,
                }
        except (ValueError, TypeError, KeyError, OSError):
            # Invalid checkpoint is never authoritative; derive from E0.
            pass
    envelopes, evidence_count_before = _read_envelopes_ro(db_path)
    created = 0
    existing = 0
    envelope_traces = 0
    chain_traces = 0

    for envelope in envelopes:
        bundle = compile_envelope_bundle(envelope)
        path = _trace_path(root, f"evidence:{envelope['evidence_id']}")
        if _write_immutable(path, bundle):
            created += 1
        else:
            existing += 1
        envelope_traces += 1

    for bundle in _decision_chains(envelopes):
        trace_id = f"decision:{bundle['mission']['mission_id']}:{bundle['snapshot_id']}"
        path = _trace_path(root, trace_id)
        if _write_immutable(path, bundle):
            created += 1
        else:
            existing += 1
        chain_traces += 1

    after_signature = _store_signature(db_path)
    if after_signature != before_signature:
        raise RuntimeError("E0 changed during Shadow derivation; retry on next cycle")

    # Commit after every immutable trace succeeded. Crash before this write
    # falls back to deterministic replay; no partial checkpoint is admitted.
    state = {
        "schema_version": 1,
        "signature": list(after_signature),
        "traces": envelope_traces + chain_traces,
        "envelope_traces": envelope_traces,
        "decision_chain_traces": chain_traces,
    }
    root.mkdir(parents=True, exist_ok=True)
    staged = checkpoint.with_suffix(".tmp")
    staged.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    staged.replace(checkpoint)

    return {
        "schema_version": "1.0",
        "idle_fast_path": False,
        "evidence_count": evidence_count_before,
        "envelope_traces": envelope_traces,
        "decision_chain_traces": chain_traces,
        "created": created,
        "existing": existing,
        "e0_mutation_performed": False,
        "source_mutation_performed": False,
    }
