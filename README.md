# aimeton-memory-os

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

Evidence-governed, four-axis memory core and context compiler for the AIMETON Cognitive Operations Complex (AIMETON.COGOPS).

## Scope

This repository implements the bounded AMOS MVP core:

- immutable evidence and descriptor-first access;
- policy-aware ContextBundle compilation;
- four projections: scope/purpose (V), role/authority (R), ontology/state (O), and evidence/associations (A);
- deterministic compatibility checks before operational context admission;
- governed writes, verifiable actions, and replayable traces.

It is not a general RAG framework, a full fractal runtime, a graph database, or an autonomous agent executor.

## MVP boundary

The first vertical slice proves:

raw evidence → projections → compatibility checks → ContextBundle → permitted action → deterministic verification → trace and recovery.

OpenRAG is an optional document/retrieval edge. It is not the source of truth, policy engine, or final ContextBundle builder.

## MVP-0 Continuity Kernel

Version 0.1.0 introduces the first executable AMOS vertical slice for cognitive continuity:

- canonical mission state and immutable evidence references;
- deterministic CR-01…CR-06 evaluation;
- derived ContextBundle compilation;
- duplicate-mutation prevention;
- source-version/snapshot drift blocking;
- fresh-process recovery without raw chat history.

The canonical fixture is deliberately small and uses a real AIMETON repository-identity drift incident. Passing it proves only the bounded continuity mechanism; it does not prove the broader AMOS hypothesis or F1 effectiveness.

## MVP-1 Shadow Living Development Corpus

Version 0.2.0 adds the first Life-and-Activity Learning execution path over a real AIMETON GitHub lifecycle:

- source-grounded GitHub lifecycle receipts are wrapped as immutable E0 Evidence Envelopes;
- the append-only log refuses destructive replacement under an existing evidence ID;
- bounded E1 observations, E2 claims, E3 decisions and E4 derived knowledge preserve provenance;
- the same evidence is projected into V/R/O/A and evaluated through CR-01…CR-06;
- the resulting ContextBundle is explicitly `SHADOW` and forbids GitHub/production mutation;
- event-sourced replay distinguishes historical `open` state from later `closed` state without rewriting earlier evidence;
- the trace records snapshot identity, evidence digests and CR reason codes.

The first real fixture is the lifecycle of Issue #6, whose accepted P0 decision was followed by a GitHub `closed` event. This is development/dogfooding evidence, not an unseen F1 benchmark.

## MVP-2 Read-only Shadow Collector

Version 0.3.0 adds resumable continuous intake for selected AIMETON GitHub repositories:

- authenticated GET-only GitHub REST reader with no mutation methods;
- durable SQLite E0 storage with append-only evidence IDs and digest collision checks;
- independent resumable cursors for issue events and issue comments;
- restart/idempotency: already ingested source objects are not duplicated;
- ingestion-time partition tagging: `development`, `holdout_candidate`, or `frozen_holdout`;
- no paid LLM dependency and no dedicated AMOS compute requirement.

This collector remains Shadow-only. Scheduling and persistent placement must follow AIMETON infrastructure contracts rather than repository-local ad hoc deployment.

## MVP-2 Post-persistence Shadow Processing

Version 0.4.0 completes the processing half of the continuous Shadow path:

- the processor opens the durable E0 SQLite store in read-only mode;
- every persisted evidence record gets a deterministic E1 observation, bounded V/R/O/A projection, CR-01…CR-06 evaluation and immutable Shadow trace;
- source comments may create E2 source-assertion candidates, never truth by frequency or similarity;
- source-grounded decision patterns can create E3 decisions and E4 derived knowledge only with preserved E0 lineage;
- trace files are immutable/idempotent: a replay either matches byte-for-byte or fails closed;
- processor runs never change E0 evidence count and perform no GitHub/provider mutations.

The initial live decision-lineage target is the already persisted Issue #6 acceptance comment followed by its closed event. The post-start Issue #20 marker is the live per-evidence trace acceptance target.

## MVP-3 Multi-repository Shadow replication candidate

Version 0.5.1 corrects the least-privilege second-source contract for active private AIMETON application repositories:

- the accepted public AMOS source keeps `issue_events_plus_comments`;
- repositories with a verified complete Issues view may use `versioned_pull_snapshots_plus_comments`;
- `AIMETON/Choke_ring_antenna` uses `versioned_pull_snapshots` because its runtime credential has a complete PR view but only a partial Issues-comment view; each pull-request state version is persisted as a distinct immutable E0 snapshot keyed by source object and `updated_at`;
- repositories keep independent durable stream cursors in the same SQLite store;
- post-persistence processing reuses the same E1-E4, V/R/O/A and CR-01…CR-06 semantics;
- pull snapshots preserve repository scope, pull/issue number and observed source state in the immutable Shadow trace.

The first replication target is private `AIMETON/Choke_ring_antenna`. Diagnostic run `41085827899` proved the runtime credential sees all 67 pull requests but only 2 of 52 repository issue comments, so issue comments are excluded from this source contract rather than silently treated as complete. This code remains a live-acceptance candidate until the corrected runtime is deployed and a post-start PR state is replayed exactly once.

## MVP-4 Provenance-governed C02 activity (bounded acceptance)

As of 2026-11-01, the live AMOS Shadow collector uses `activity_stream` for
`AIMETON/Choke_ring_antenna`: PR snapshots, complete Issues comments,
Issues events and versioned Actions workflow runs. The existing token now has
Issues read permission. The historical PR-only limitation documented above
is **superseded in runtime**, not a current source-coverage contract.

The C02 Command Router now records an exact downstream run ID returned by
GitHub workflow dispatch in a GitHub Actions bot-authored receipt. AMOS validates
FOUR immutable E0 sources (owner command, bot receipt, router run, downstream
run), SHA-256 of the command, source identity and workflow identity before
claiming a verified **dispatch** link. It does not equate dispatch success with
successful execution or a scientific admission.

The post-persistence processor emits an immutable
`amos.live-dispatch-provenance` trace from terminal run versions without
extra network calls. An independently replayed live example proved
`causal_status=VERIFIED` while retaining a downstream `failure`:
[full acceptance record](docs/evidence/MVP4_C02_DISPATCH_PROVENANCE_ACCEPTANCE_2026-11-01.md).
Historical C02 events without a trustworthy exact link remain UNRESOLVED.
Mission-state reconstruction and incremental affected-event processing remain
open [in Issue #36](https://github.com/AIMETON/aimeton-memory-os/issues/36).

## G3/G4 External Audit Gateway — bounded pilot

As of 2026-11-01, synthetic-only G3 staging is available at
[aimeton.ru/audit-demo](https://aimeton.ru/audit-demo/), with a fixed G1
synthetic package and G2 one-time/continuing grant engine. The web route is
separate from production AMOS E0 and private project data.

The existing AIMETON site administrator can manage synthetic audit grants at
`/admin/audit` using the existing authenticated session and CSRF gate.
[Site PR #47](https://github.com/AIMETON/aimeton-site/pull/47) was deployed
under exact SHA `5e970cc3b1754abfe9991f7568e70fa04ff4a151`.
Independent isolated server acceptance
[infra run #41306260445](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41306260445)
passed: login/session, CSRF, grant issue/list/revoke, 1-of-12 concurrent
one-time redemption, continuing redemption and no raw token in audit logs.
The smoke uses throwaway SQLite databases, not production admin or AMOS E0.

G4 real-project work is currently **not an authorized public release**:
- [PR #48](https://github.com/AIMETON/aimeton-memory-os/pull/48)
  adds a deterministic, digest-bound curated public-source package compiler
  and a separate QUARANTINED external findings store.
- [PR #49](https://github.com/AIMETON/aimeton-memory-os/pull/49)
  adds the source-pinned, six-record
  `tests/fixtures/g4_first_public_project_candidate.json` for the
  publicly documented `AIMETON/aimeton-memory-os` project. Explicit
  `publication_authorized=false`; no private E0 material is included.
- [PR #50](https://github.com/AIMETON/aimeton-memory-os/pull/50)
  binds quarantined external findings to the exact snapshot and known
  `PUB-NNN` reference, with negative tests for forged manifests,
  unknown project items and unapproved evidence URLs.

**Authority boundary:** digest equality and public GitHub visibility do
not constitute authenticated owner release approval. Real-project audit
links and an external model review remain blocked pending exact-snapshot
owner consent, identity/audience policy and independent external reviewer
admission. External findings must never automatically update E0, E3/E4 or
cause engineering operations. Current G3 remains synthetic only.

## Repository layout

- docs/architecture — contracts and architecture decisions
- schemas — machine-readable contracts
- src/aimeton_memory_os — implementation package
- tests — golden fixtures and deterministic validation
- scripts — local, dependency-controlled validation tools

## Automation and runner placement

AMOS follows the AIMETON runner-placement standard instead of owning a dedicated compute server.

- baseline governance, schema validation and deterministic unit tests are `PERSISTENT_CONTROL` workloads;
- the canonical repository-scoped runner identity is `aimeton-memory-os-ci` with label `memory-os-ci` on the persistent AIMETON main-server control plane;
- CI must use self-hosted AIMETON capacity and must not depend on GitHub-hosted runners or Marketplace Actions;
- heavy corpus replay, ablation, benchmark and large-regression workloads are future `SHARED_BURST` candidates and must not be silently moved onto the persistent control lane;
- shared-burst activation requires separate infrastructure placement and live acceptance before dispatch is enabled.

The baseline workflow materializes an exact commit SHA with Git directly, requires Python 3.12+, validates repository contracts and executes dependency-free tests.

## Status

**MVP-3 multi-source Shadow collection ACCEPTED; MVP-4 exact C02
command-to-dispatch provenance and immutable trace ACCEPTED as a bounded
vertical slice.** The live server uses the five-minute polling timer, durable
append-only E0 and source-independent cursors; run-specific immutable evidence
is independently verified. Neither full engineering mission recovery,
performance/ablation gates nor authenticated webhook delivery has yet passed
acceptance. Verified routing is not proof that downstream work succeeded.
Architectural effectiveness remains a hypothesis pending frozen-holdout evals.

## License and trademarks

Apache-2.0. See LICENSE and NOTICE. AIMETON names and marks are governed separately by TRADEMARKS.md.

SPDX-License-Identifier: Apache-2.0

## Shadow idle-cycle efficiency (candidate)

The Shadow processor uses an **append-only E0 watermark checkpoint** in the traces directory
(`.shadow-processor-checkpoint.json`). When the E0 row count, max rowid and trace
file count have not changed, the normal cycle performs only constant-size SQLite
metadata reads plus a trace-file count; it skips JSON parsing, ContextBundle
compilation and existing-trace replay. A new E0 receipt, a missing trace or
a missing/invalid checkpoint forces deterministic reconstruction. The checkpoint
is written atomically only after trace processing succeeds; it is not a source
of truth. Run `python3 scripts/compile_live_shadow.py --db ... --output-dir ... --verify-all`
for an explicit full integrity replay (the normal idle fast path does not validate
each existing trace byte-for-byte). Running with `--verify-all` also detects
immutable collision/tampering in existing traces.

This is **compute optimisation**, not webhook delivery: the currently deployed
five-minute GitHub polling timer continues until an independently
verified event receiver, authenticated delivery, durable queue and reconciliation
fallback are available. Do not reduce intake frequency before that deployment.
