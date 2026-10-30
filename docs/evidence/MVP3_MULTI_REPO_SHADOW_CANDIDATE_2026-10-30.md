# MVP-3 Multi-repository Shadow replication — candidate evidence

Date: 2026-10-30

Status: **CANDIDATE / NOT YET ACCEPTED**

Tracking issue: `AIMETON/aimeton-memory-os#24`

## Objective

Replicate the accepted continuous AMOS Shadow path from `AIMETON/aimeton-memory-os` onto the active private engineering repository `AIMETON/Choke_ring_antenna` without changing CR-01..CR-06 semantics, without mutating the source repository, and without expanding credentials merely to satisfy an endpoint shape.

## Product revision

Corrected AMOS candidate:

- version: `0.5.1`
- main SHA: `81a4dc3bb2773bc3fc3a89770821126ab61befcf`
- exact PR CI: `41086203246` — SUCCESS
- post-merge CI: `41086281791` — SUCCESS
- Choke source mode: `versioned_pull_snapshots`

The source mode stores immutable pull-request snapshots keyed by source object plus `updated_at`. It reuses the accepted E0 v0.2 envelope, post-persistence E1-E4 schema, V/R/O/A projections, CR-01..CR-06 evaluation and immutable Shadow trace compiler.

## Source-completeness incident

The first v0.5 runtime treated HTTP 200 on the private repository issue-comments endpoint as evidence of source completeness. Live evidence disproved that assumption.

Diagnostic run `41085827899` using the exact runtime credential reported:

- repository metadata: HTTP 200;
- pull requests: HTTP 200, 67 objects, newest object id `5086043627`, newest source version `2026-10-30T14:35:16Z`;
- issue comments: HTTP 200, only 2 objects, newest id `6525340582`, newest timestamp `2026-10-30T14:35:12Z`;
- repo-wide issue events: HTTP 403.

The authoritative connected GitHub view contained 52 issue comments, including later comment `6525345934` at `2026-10-30T14:35:28Z`.

Independent negative readback run `41085412599` queried that authoritative later comment and correctly failed with E0 count 0. This established that the private Issues-comment channel was partial rather than merely cursor-lagged.

Decision:

- do not expand the credential;
- accept only the complete pull-request snapshot view for `Choke_ring_antenna`;
- treat issue comments and repo-wide issue events as diagnostic-only for this source;
- preserve the two previously persisted visible comments and their legacy cursor append-only as historical candidate evidence, but exclude them from the accepted source contract.

## Corrected infrastructure runtime

Infrastructure source-contract correction:

- PR #829
- merge SHA: `fd1100ac9c64f9a10db5f3464adb8eadf1c9a72c`
- corrected post-merge capability run: `41087214439` — SUCCESS
- runtime deploy run: `41087302258` — SUCCESS
- installed AMOS SHA: `81a4dc3bb2773bc3fc3a89770821126ab61befcf`

The runtime uses one existing persistent systemd timer/service and one durable append-only SQLite evidence store. The complete-source admission cursors are:

1. `github:AIMETON/aimeton-memory-os:issue_events`
2. `github:AIMETON/aimeton-memory-os:issue_comments`
3. `github:AIMETON/Choke_ring_antenna:pull_snapshots`

The legacy `Choke_ring_antenna:issue_comments` cursor may still exist physically and is intentionally not deleted.

The deploy readback reported:

- 121 E0 records;
- 52 memory-os E0 records;
- 69 Choke candidate E0 records;
- 123 immutable traces;
- service healthy;
- repository mutation: false;
- provider write: false.

## Sparse semantic-layer acceptance incident

The first corrected PR-snapshot readback, run `41087499791`, failed on a generic requirement that E2 be non-empty.

That predicate was inconsistent with the product contract. A plain `github.pull_snapshot` is an observed source-state object and therefore always contributes E1; E2 is intentionally empty unless the source object contains a textual assertion.

Infrastructure PR #830 corrected the acceptance predicate:

- always require E1;
- require non-empty E2 for memory-os issue-comment markers;
- require `E2 == []` for Choke pull snapshots;
- retain exact repository scope, PR number/state, six CR checks and no-mutation assertions.

PR #830 merge SHA: `09cea1d01eb430c4faec82cd15916a48e9e8b390`.

## Baseline private-source readback

Independent corrected readback:

- run: `41088108448` — SUCCESS
- source repository: `AIMETON/Choke_ring_antenna`
- marker kind: `pull_snapshot`
- PR number: 74
- marker evidence id: `github:pull-snapshot:AIMETON/Choke_ring_antenna:5086043627:2026-10-30T14:35:16Z`
- marker observed_at: `2026-10-30T14:35:16Z`
- marker E0 count: 1
- marker trace count: 1
- `V.scope=AIMETON/Choke_ring_antenna`
- PR number preserved in V
- six CR checks satisfied
- readback invoked collector: false
- repository mutation by collector: false
- provider write: false

This proves that the corrected second-source path can read an existing immutable private PR snapshot and recover its deterministic Shadow trace without source mutation.

## Remaining acceptance criterion

MVP-3 is deliberately **not accepted yet**.

A single strict criterion remains: observe a naturally occurring `Choke_ring_antenna` PR state/version whose source `updated_at` is later than the corrected runtime activation, ingest it by the persistent timer exactly once, and independently read back exactly one E0 plus exactly one immutable trace with six satisfied CR checks and zero source/provider mutations.

AMOS must not manufacture that source event. The source repository remains read-only from the AMOS mission.

After that evidence exists, this candidate record must be superseded by an acceptance record and issue #24 may be closed. No F1 or architectural-effectiveness claim follows from MVP-3 alone.
