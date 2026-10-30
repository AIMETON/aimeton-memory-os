# AMOS MVP-0 Continuity Kernel — acceptance evidence

**Status:** ACCEPTED for bounded MVP-0 continuity semantics  
**Date:** 2026-10-30  
**Parent P0:** https://github.com/AIMETON/aimeton-memory-os/issues/6  
**Architecture signal:** https://github.com/AIMETON/aimeton-architecture/issues/147

## What was proven

A fresh process with no access to prior chat history can reconstruct a bounded AMOS `ContextBundle` from canonical mission/evidence files and recover:

- mission identity;
- current ACTIVE state;
- NEXT_SAFE_ACTION;
- NEXT_AFTER_NEXT;
- authority envelope;
- budget envelope;
- exact evidence references;
- compatibility outcome.

The deterministic recovery fixture also proves:

- a completed action cannot be reissued as the next safe mutation;
- a pinned evidence-version mismatch is blocked by CR-06 and escalates;
- the ContextBundle is a derived projection, while canonical mission/evidence JSON remains the source of reconstruction.

## Canonical implementation evidence

Merged implementation commit:

```text
c06df2b00644646750868e1b659eea6f27f10519
```

Implementation PR:

```text
https://github.com/AIMETON/aimeton-memory-os/pull/16
```

PR exact-SHA acceptance:

```text
run 41069336788
head 5e5b0326fd33e8c9bf49412001e884d43856ad96
conclusion success
```

Post-merge `main` acceptance:

```text
run 41069428898
head c06df2b00644646750868e1b659eea6f27f10519
conclusion success
```

Both runs completed the canonical self-hosted `AMOS Baseline CI` path:

1. verify `aimeton-memory-os-ci` runner and Python baseline;
2. materialize exact revision without Marketplace actions;
3. compile sources/tests;
4. validate repository contracts;
5. execute dependency-free tests.

## Implemented surface

- `schemas/amos-continuity-state.v0.1.schema.json`
- `src/aimeton_memory_os/continuity.py`
- `scripts/recover_context.py`
- `tests/fixtures/continuity/evidence.json`
- `tests/fixtures/continuity/mission_state.json`
- `tests/fixtures/continuity/expected_recovery.json`
- `tests/test_continuity_kernel.py`

The canonical incident used by the fixture is a real repository-reality drift:

```text
historical identity: Dimar4713/aimeton-memory-os
current canonical identity: AIMETON/aimeton-memory-os
```

The stale identity was present in `manifest.json` and in deterministic tests after the organization transfer. MVP-0 corrected the canonical repository identity and used the incident as recovery evidence.

## Claim boundary

This acceptance proves only a bounded provider-neutral continuity kernel.

It does **not** yet prove:

- AMOS F1 superiority over baselines;
- durable production persistence;
- broad Living Development Corpus ingestion;
- model-weight learning;
- autonomous execution authority;
- semantic relation layer benefit;
- cross-domain replication.

## Next critical path

The next operational step is Issue #4:

```text
MVP Shadow LDC: ingest real AIMETON development stream
```

Reuse the accepted Continuity Kernel unchanged as the recovery/context core, replace static fixture-only input with append-only Shadow evidence from real GitHub activity, then prove replay across a real state transition.

Research Issues #11/#13 remain parallel and non-blocking until the Shadow LDC vertical slice produces real ContextBundle evidence.
