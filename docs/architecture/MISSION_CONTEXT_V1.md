# Mission Context v1 — operator-side read-only interface

This is a **local AMOS Shadow context compiler** over durable SQLite E0. It is
not a public REST route, not a replacement for the authenticated controlling
agent, and not permission to run engineering actions.

## Invocation

```bash
PYTHONPATH=src python3 scripts/query_mission_context.py \
  --db /secure/amos/e0.sqlite \
  --project AIMETON/aimeton-memory-os \
  --allow-repo AIMETON/aimeton-memory-os \
  --limit 100 --offset 0
```

The trusted operator/agent adapter MUST supply `--allow-repo` from its already
verified server-side access policy. It MUST NOT pass a remote user's requested
repository list verbatim. E0 database and JSON output remain private.
No browser or external-auditor grant integration is enabled.

Result: `amos.mission-context.v1` JSON containing project, indexed snapshot,
paginated source history, latest observed PR experiments, latest failed Actions,
unverified decision assertions, explicit unresolved canonical objective and
contradictions, restrictions, a non-executable next-step proposal, E0 evidence
references and stored digests. Full history retrieval is via `next_offset`.

## Semantic limits

E0 GitHub events are real observations, but GitHub comment text is **not** a
verified engineering decision. A workflow dispatch is **not** scientific PASS.
Mission objective, decisions, semantic contradictions and experimental
acceptance remain UNRESOLVED unless governed canonical E3/E4 evidence is
incorporated in a later version. The index hash fingerprints **stored digests**;
it does not independently attest raw E0 integrity. `--as-of` filters by
persisted observed_at; no guarantee of completeness against GitHub source.

The output contains summaries and metadata, not all raw evidence payloads.
The redactor mitigates common secrets but is not a security boundary; internal
scope enforcement and authenticated hosting are mandatory.

## Acceptance

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mission_context.py' -v
```

This gate verifies deterministic recovery, source isolation, no E0 mutation,
explicitly unresolved E3 decisions, pagination, deny-by-default scope and
basic secret redaction. Before production acceptance implement a trusted
authenticated adapter, verified E0 integrity, canonical E3/E4 mission-state
projection, contradiction derivation, complete cross-source replay and live
access-control smoke on a self-hosted runner. Track in Issue #53.
