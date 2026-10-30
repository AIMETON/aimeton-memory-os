# AMOS MVP-2 Continuous Shadow Path — live acceptance evidence

**Status:** ACCEPTED for the bounded single-repository continuous Shadow path  
**Date:** 2026-10-30  
**Parent:** https://github.com/AIMETON/aimeton-memory-os/issues/20

## Accepted capability

AMOS now continuously observes the selected AIMETON GitHub development stream and executes the bounded Life-and-Activity Learning path:

```text
GitHub read-only source
→ durable immutable E0
→ E1/E2/E3/E4 derivation
→ V/R/O/A
→ CR-01..CR-06
→ immutable Shadow ContextBundle/trace
→ replay
```

The runtime is deployed on the existing AIMETON persistent main server. No dedicated AMOS server, new provider resource, paid LLM call, or autonomous source mutation is used.

## Product evidence

AMOS v0.4 implementation:

```text
AIMETON/aimeton-memory-os
main SHA 974016eab74dd7062c4b0cd8d4633f032ecd10c6
```

PR #22 exact-SHA CI:

```text
run 41075397684
conclusion success
```

Post-merge main CI:

```text
run 41075493018
conclusion success
```

## Runtime evidence

Infrastructure runtime:

```text
AIMETON/aimeton-infrastructure
main SHA afb60adde8bdc424260868a724a0e0d57a7380b8
```

Live apply run:

```text
run 41076640392
conclusion success
installed AMOS SHA 974016eab74dd7062c4b0cd8d4633f032ecd10c6
E0 evidence 43
stream cursors 2
immutable traces 44
decision-chain traces 1
```

The post-persistence compiler receives no GitHub/provider credential. It opens the durable E0 SQLite store read-only and writes derived immutable traces separately.

## Independent read-only acceptance

A previously created post-start operator marker was used:

```text
GitHub comment id 6525522492
E0 evidence id github:issue-comment:AIMETON/aimeton-memory-os:6525522492
```

Read-only acceptance run:

```text
run 41076813777
conclusion success
```

Observed result:

```text
marker E0 count = 1
marker live-evidence trace count = 1
Issue #6 decision-chain trace count = 1
evidence total = 43
trace total = 44
collector invoked by readback = false
repository mutation by collector = false
provider write = false
```

The marker trace contains E1/E2, V/R/O/A and six satisfied compatibility checks.

The Issue #6 decision-chain trace contains non-empty E2, E3 and E4 with provenance and six satisfied compatibility checks.

## Temporal / idempotency evidence

Before the marker, the accepted continuous collector had 39 E0 records. After the marker was observed by the systemd timer, the store had 40 E0 records and the marker count remained exactly one. Later normal project activity increased the durable set to 43 E0 records; the marker remained exactly one and its derived trace remained exactly one.

The processor uses immutable trace paths. A replay must either match the existing trace byte-for-byte or fail closed.

## Claim boundary

This acceptance proves the bounded continuous Shadow path for one AIMETON repository.

It does **not** yet prove:

- F1 superiority over C/A/B baselines;
- cross-domain effectiveness;
- organization-wide collection;
- autonomous action authority;
- semantic-relation research benefit;
- production readiness for arbitrary multi-writer memory;
- model-weight learning.

## Next critical path

Replicate the same accepted read-only Shadow path on one active AIMETON application repository without changing the AMOS compatibility semantics. Keep the first repository as development/dogfooding evidence and preserve holdout separation for later F1.
