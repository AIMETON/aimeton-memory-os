# AMOS MVP-1 Shadow LDC — acceptance evidence

**Status:** ACCEPTED for bounded Shadow LDC semantics  
**Date:** 2026-10-30  
**Parent:** https://github.com/AIMETON/aimeton-memory-os/issues/4

## Proven slice

A real AIMETON GitHub lifecycle was converted into an append-only AMOS Shadow path:

```text
GitHub lifecycle receipts
→ E0 immutable envelopes
→ E1 observations
→ E2 claims
→ E3 decisions
→ E4 derived knowledge
→ V/R/O/A
→ CR-01..CR-06
→ SHADOW ContextBundle
→ replay trace
```

The source case is Issue #6:
- opened on 2026-08-27;
- P0 acceptance comment by a project member on 2026-10-30;
- GitHub closed event three seconds later.

Replay at `2026-10-30T14:11:06Z` reconstructs the historical issue state as `open`.
Replay at `2026-10-30T14:11:09Z` reconstructs the later state as `closed`.
Earlier E0 evidence is preserved and is not rewritten by the later transition.

## Safety boundary

The compiled bundle is explicitly `SHADOW`.
Its authority envelope forbids:
- GitHub mutation;
- production mutation.

No paid model call or new infrastructure is required.

## Implementation evidence

PR:
```text
#18 AMOS MVP-1: Shadow LDC over real GitHub lifecycle
```

PR exact-SHA acceptance:
```text
run 41070389951
head 234c440fbb9fd3a4cca3e6a0bdaf24cb641ad7e6
conclusion success
```

Merged main:
```text
9ce960dbc7723733fa2b0ca1158888631b3191dc
```

Post-merge acceptance:
```text
run 41070665048
head 9ce960dbc7723733fa2b0ca1158888631b3191dc
conclusion success
```

## Implemented surface

- `schemas/amos-evidence-envelope.v0.1.schema.json`
- `src/aimeton_memory_os/ldc.py`
- `scripts/replay_shadow_ldc.py`
- `tests/fixtures/ldc/github_issue6_lifecycle.json`
- `tests/test_ldc_shadow.py`

## Claim boundary

This is development/dogfooding evidence. It does not count as frozen holdout, F1, cross-domain replication or production persistence evidence.

## Next critical path

Move from one replayable real case to a continuous read-only Shadow collector for selected AIMETON GitHub repositories. The collector must append source receipts, preserve object IDs/digests, maintain cursors/checkpoints, never mutate source repositories, and feed the accepted LDC/Continuity pipeline.
