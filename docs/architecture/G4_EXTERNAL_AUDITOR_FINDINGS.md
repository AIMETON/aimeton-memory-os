# AMOS G4 external auditor finding contract — quarantined only

Status: **offline acceptance candidate**; no externally callable POST route or
permission to publish a real AMOS project snapshot.

## Auditor input

The independent auditor is given only a separately owner-authorized immutable
curated public-source snapshot and its SHA-256 manifest. The auditor MUST not
receive raw E0, internal AMOS traces, access tokens, live URLs requiring
private GitHub permissions, or direct write privileges.

Findings are JSON objects with:

| Field | Constraint |
|---|---|
| `category` | `missing_evidence`, `contradiction`, `methodology`, `risk`, `recommendation` |
| `severity` | `low`, `medium`, `high` |
| `referenced_item` | One of the immutable `PUB-NNN` IDs in the exact released snapshot |
| `observation` | Nonempty independent statement, 12–2000 characters |
| `recommendation` | Proposed follow-up, 12–2000 characters; NOT an executable command |
| `evidence_urls` | Optional 0–5 distinct public AIMETON GitHub URLs; no query, credentials or local paths |

The offline `ingest_curated_finding` first verifies curated snapshot integrity
against the supplied manifest and the referenced item's membership. It then
stores the untrusted observation in a **separate SQLite table** with immutable
`snapshot_sha256`, body SHA-256 and status `QUARANTINED`. Unknown fields,
unknown references, corrupted manifests and unapproved URLs fail closed before
a SQLite file is created. Raw reviewer prose may include adversarial
instructions and MUST never be interpreted as agent commands.

**A valid digest or a self-declared release ID is not proof of project-owner
approval.** Authentication, owner release receipts, per-auditor quotas,
rate limits, anti-replay and online findings ingestion remain future gates.
A finding has no automatic E0/E3/E4 mutation or approval authority.

## Independent reviewer acceptance

The first pilot should use project
`AIMETON/aimeton-memory-os` and the source-pinned non-public candidate
`tests/fixtures/g4_first_public_project_candidate.json`.
Before any external model call:

1. Owner explicitly approves the exact immutable curated snapshot, audience
   and retention policy, and no private E0 source or hidden relations leak.
2. Grant lifecycle is independently tested, including revocation, one-time
   access and stale source version denial.
3. Only the approved release snapshot, not source private project context,
   is supplied to an independent reviewer.
4. Reviewer findings are imported through quarantine with explicit source
   snapshot binding and reviewed by an authorized human before any
   engineering decision.

No independent external LLM has been called by this change. System tests of
the findings contract must not be presented as independent scientific review.
