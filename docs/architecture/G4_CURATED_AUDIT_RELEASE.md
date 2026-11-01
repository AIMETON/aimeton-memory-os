# G4 curated project audit release

Status: development candidate. Real AMOS E0 export remains denied. For AIMETON/aimeton-memory-os, a first real-project pilot may contain exclusively manually reviewed public-repository assertions, each with explicit approved source URLs, fixed source version and immutable manifest digest. Approval is per release and never inferred from repository visibility. Findings from auditors stay quarantined and cannot mutate AMOS E0 or decisions. No public release is authorized by this document.

## Authentication boundary (mandatory)

This module compares explicit content digests and a structured release
identifier, but **does not authenticate an owner**. A caller can construct
matching digests for arbitrary input. Such a self-consistent descriptor is a
**release candidate**, NOT proof of owner authorization or declassification.
There is no issuance endpoint, no public link, and no deployment of the G4
exporter. The runtime must reject all curated candidates until a separate
authenticated, auditable, exact-snapshot release approval is implemented,
including grant scope, source provenance, content moderation, retention,
reviewer identity, and revocation policy.

For this first pilot only the project name AIMETON/aimeton-memory-os is
accepted by the prototype, and every evidence URI must match the explicitly
limited public GitHub source allowlist. Repository visibility alone is not
owner approval; private E0 and derived internal knowledge remain denied.
External findings are untrusted and remain QUARANTINED in an isolated
database, with no automatic promotion to AMOS semantic layers or actions.

## Implementation and verification

- Compiler: `src/aimeton_memory_os/curated_audit.py`.
- Quarantined findings: `src/aimeton_memory_os/audit_findings.py`.
- Negative tests: `tests/test_curated_release_v1.py`.
- G4 is **not** wired to the existing G3 HTTP Gateway or website.
