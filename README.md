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

**MVP-1 Shadow LDC under acceptance.** MVP-0 Continuity Kernel is accepted. The immediate P0 is Issue #4: prove real AIMETON development-stream ingestion/replay in Shadow mode. Architectural effectiveness claims remain hypotheses until frozen holdout and preregistered F1.

## License and trademarks

Apache-2.0. See LICENSE and NOTICE. AIMETON names and marks are governed separately by TRADEMARKS.md.

SPDX-License-Identifier: Apache-2.0
