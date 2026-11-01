# AMOS External Audit G0 — field classification and owner decision matrix

Status: **DRAFT, all real-project external export DENIED until owner approval**.
Date: 2026-11-01 UTC. Derived from exact source contracts:
`schemas/amos-evidence-envelope.v0.2.schema.json`,
`src/aimeton_memory_os/collector.py`,
`src/aimeton_memory_os/live_shadow.py`,
`src/aimeton_memory_os/activity_context.py`,
`docs/architecture/SOVEREIGN_SECURITY_EXTENSIBILITY.md`.
This is a classification proposal, **not** a finding that any actual
project content is already public-safe.

## Field classification for external audit

| Source family | Fields or content | Default | Why / required action |
|---|---|---|---|
| E0 envelope | `evidence_id`, `source_ref`, `source_object_id` | DENY | Names, issue IDs and private URLs can reveal protected project structure; export opaque release-scoped aliases only after policy |
| E0 envelope | `payload` and nested GitHub `body`, `user`, `actor`, artifacts, workflow inputs | DENY | Free text, PII, command strings, credentials, private paths and unpublished research may be present |
| E0 envelope | `digest` | ESCALATE | Raw digests are correlators; in public pack prefer separately salted/release-specific opaque references or explicitly approved public digest |
| E0 envelope | `partition` | DENY | `holdout_candidate` / `frozen_holdout` reveals private eval design and can contaminate tests |
| E0 envelope | `observed_at`, `source_type` | REDACT | Only coarse/allowed times and category after owner-approved disclosure; sensitive event frequency must not leak |
| E1 | observation `value` / `subject` | DENY | May contain full copies of raw GitHub comment bodies |
| E2 | claim text, speaker, provenance IDs | DENY | External opinions and unvalidated claims must not become validated statements |
| E3 | accepted decisions and authority | ESCALATE | Exact scope, authority chain and decision payload need explicit owner approval and source-level checks |
| E4 | derived knowledge and summaries | DENY | Inherit strictest restrictions of all E0/E1/E2/E3 dependencies, including implicit references |
| V/R/O/A | `scope`, `actor`, `entity_id`, `evidence_refs`, `derived_refs` | DENY | May disclose project identity, people and private evidence graph |
| Compatibility | CR-01…CR-06 state and reason codes | REDACT | Only high-level aggregated approved results; no protected references or private reason messages |
| Activity ContextBundle | mission objective, critical path, next action, blockers | DENY | May be internal operational instructions, security data or unreleased research |
| C02 dispatch trace | exact command IDs, SHA, run IDs, bot receipt, GitHub URLs | DENY | Even verified provenance is not automatically public authorization |
| Runtime | paths, hostnames, tokens, log/error details, cursors, runner placement | DENY | Privileged infrastructure, internal cadence and operational details |
| Synthetic G1 | fixed project ID, controlled enum labels, synthetic digests | ALLOW *locally only* | Never use a synthetic permit as approval for C02 or other real projects |

**DENY** means excluded from all exported bytes including file names, manifest,
counts, cursors, nested attributes, embeddings and error strings.
**REDACT** / **ESCALATE** are not grants; before separate approval they also
resolve to DENY. No generic regex-based secret scrub is sufficient for
publishing raw data.

## Required project-owner decisions (G0 fail-closed)

Before a real-data G1 extension or a public URL exists, owner must approve
a **specific export profile**, not a universal AMOS-wide publishing grant:

1. Canonical `project_id` and exact source-repository scope.
2. Audience and purpose: named human/AI auditor vs genuinely anonymous public.
3. Allowlisted record categories and owner-reviewed text/spans; explicit
   handling for source URLs, authorship, timing and security labels.
4. Whether approved snapshots may include original primary evidence or
   only curated redacted abstracts and release-specific opaque references.
5. Fixed vs continuing scope, maximum content bytes, retention, expiry,
   revocation rules, offline-copy warning and permitted audit findings channel.
6. Explicit holdout exclusions and protection against inference of counts,
   links, deltas and relations to denied E0.
7. Human approval receipt referencing exact policy version, source snapshot
   watermark, object digests and permitted destination/audience.

No direct approval is implied by a GitHub repository being public.
An existing token's API read permission is not an authorization to export
its data to a third party. Derived artifacts inherit the most restrictive
source label. Export may only be declassified via an authorized auditable
policy event, not via a model-generated summary.

## Proposed G0 -> G1 integration boundary

A future real-data exporter should consume **signed or otherwise authoritative
approved release descriptors**, already filtered to spans, and independently
validate those authorizations. It must never read an arbitrary private E0
record and assume an input field `export_rule=allow` is sufficient.
Mandatory independent checks: deliberate restrictive-label tests, nested
secret contamination, disguised private URLs and identities, protected
existence/count leakage, ACL drift, revoked approval, cross-project
references, prompt-injection content and output integrity.

The existing G1 exporter is synthetically restricted at source-code level:
`project_id=amos-synthetic-audit-demo`,
`source_profile=synthetic_fixture`,
`authorization=synthetic-test-only`. It cannot be switched to a real
project by changing a CLI flag or JSON fixture.

## Acceptance state

- Inventory/proposed field defaults: **prepared**.
- Synthetic G1 exporter and CI: **accepted** by AMOS PR #43.
- Named real-project policy, object-label audit, owner approval receipt:
  **not approved / not implemented**.
- Real AMOS export: **prohibited**.
- Public read-only gateway and one-time/continuing links: **not deployed**.

Next safe engineering work: build a synthetic-only G2 local grant state machine
with atomic one-use redemption, expiry, revocation and bound immutable
snapshot hash; test under concurrent redemption and refuse any real project.
