# Cognitive Continuity Contract (CCC)

**Status:** MVP-0 implementation contract  
**Date:** 2026-09-04  
**Implementation started:** 2026-10-30  
**Parent:** AIMETON Cognitive Continuity research in `aimeton-architecture`

## Purpose

CCC is the deterministic handoff/checkpoint contract used when active context is compacted, reconstructed, transferred between models/agents, or recovered after cognitive drift.

CCC is not canonical truth storage. It is a derived, verifiable projection over AMOS evidence and state.

## Required sections

```text
MISSION
CURRENT_STATE
ACTIVE_CRITICAL_PATH

DECISIONS
CONSTRAINTS
INVARIANTS

ATTEMPTED
REJECTED + WHY
FAILED + WHY

COMPLETED
OPEN
BLOCKED + OBJECTIVE_BLOCKER

NEXT_SAFE_ACTION
NEXT_AFTER_NEXT

EXACT_REFERENCES
```

## Hard requirements

1. Preserve provenance for every state-bearing claim.
2. Preserve supersession/temporal validity rather than flattening old and current state.
3. Preserve rejected alternatives and failure reasons when they constrain future work.
4. Preserve exact identifiers that are expensive or unsafe to reconstruct from memory.
5. Do not mutate canonical history when generating a checkpoint.
6. Checkpoint generation must be replayable from authoritative AMOS state where possible.
7. Recovery must verify environment/tool/runtime state before resuming mutation.
8. Missing required fields fail closed for autonomous mutation paths.

## Event-history model

```text
immutable evidence/events
        |
        v
typed AMOS state
        |
        v
CCC checkpoint
        |
        v
bounded active ContextBundle
```

A new CCC checkpoint appends a new continuity artifact. It never rewrites prior history.

## Recovery admission

A recovered actor may re-enter ACTIVE mutation state only after:

- mission and critical path reconstructed;
- current canonical state read back;
- contradictions typed/resolved or explicitly bounded;
- objective blockers identified;
- authority and safety gates re-evaluated;
- NEXT_SAFE_ACTION derived from current evidence.

## MVP-0 executable mapping

The first implementation is intentionally dependency-free and bounded:

- `schemas/amos-continuity-state.v0.1.schema.json` — machine-readable mission-state contract;
- `src/aimeton_memory_os/continuity.py` — deterministic state/evidence validation, CR-01…CR-06 evaluation and ContextBundle compilation;
- `scripts/recover_context.py` — fresh-process reconstruction entry point;
- `tests/fixtures/continuity/` — canonical recovery evidence/state/expected result;
- `tests/test_continuity_kernel.py` — admit, duplicate-mutation and CR-06 drift assertions.

This mapping is not a full persistence layer. JSON fixtures stand in for canonical durable storage so that recovery semantics can be proven before a storage substrate is selected.

## External evidence history

The initial CCC seed was reinforced by Anthropic's Claude Fable 5.1 prompting guidance captured on 2026-09-04:
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1

Vendor-specific Claude mechanics are not part of the contract. Only the vendor-neutral continuity lessons are retained.

## Next implementation slice

After MVP-0 acceptance, move the same contracts onto the AMOS Living Development Corpus Shadow path and prove replay against a real source state transition without changing the compatibility semantics.
