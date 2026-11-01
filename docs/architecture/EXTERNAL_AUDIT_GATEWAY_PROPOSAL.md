# AMOS External Audit Gateway — architecture proposal v0.1

Status: **PROPOSED / NON-DEPLOYED**, 2026-11-01. Owner authorization required to expose any real project data.

## Purpose

Allow external human or AI auditors to inspect an explicitly permitted, evidence-grounded
AMOS project snapshot through AIMETON's website, either for a **one-time audit** or
through a **revocable project-scoped continuing access link**. The public gateway MUST NOT
give direct connectivity to AMOS SQLite, GitHub credentials, raw Evidence Vault, private
repos, all project history or production operations.

This is a read-only external export and feedback interface. It is not an agent-execution
platform and it is not a replacement for AMOS provenance, CR-01…CR-06 or security policy.

## External routes (proposed; DO NOT expose until independent security acceptance)

- `https://aimeton.ru/audit/<public-share-id>` — human-oriented landing page: purpose,
  scope, expiry, restrictions, snapshot digest, available formats and instructions for agents.
- `GET /api/audit/v1/shares/<id>/manifest` — machine-readable manifest, versioned
  API contract; no session secrets in audit artifact content.
- `GET /api/audit/v1/shares/<id>/snapshots/<snapshot-id>` — frozen, filtered project
  audit pack (JSON with typed records; optionally bounded HTML/Markdown and ZIP export).
- `GET /api/audit/v1/shares/<id>/changes?after=<cursor>` — permitted delta stream
  for continuing audit links; only approved revisions.
- `POST /api/audit/v1/shares/<id>/findings` — future explicitly authorized,
  rate-limited external findings intake. Disabled in read-only MVP. Findings are
  external **claims**, never automatic E3/E4 truth or production changes.

Routes are logical API proposals, not a claim that the current static
`aimeton-site` already has a backend. A separate small scoped read-only Gateway
behind the existing Caddy and authenticated export storage is the likely
deployment, subject to infrastructure review. No new DNS, paid provider or server
is assumed.

## Share models

1. **one_time**: random unguessable capability, explicit `expires_at`, one successful
   redemption for protected content. Beware HEAD/previews/link scanners: a GET preview
   must not consume one-time entitlement unintentionally. Prefer a human-opened landing
   page followed by an explicit redeem action. The redeemed access is bound to a
   short-lived session or one export, not indefinitely reusable.
2. **project_continuous**: stable revocable landing URL and policy; each actual audit
   uses an immutable pinned `snapshot_id`/manifest digest. A new version is
   published only after a fresh export policy check; permissions can be narrowed
   or revoked without modifying earlier immutable AMOS evidence.
3. **public_demo** (future separate mode): owner-approved genuinely public subset,
   suitable for anonymous browsing; must never be inferred from repository
   public/private status alone.

For sensitive projects **link possession alone is not sufficient authorization**:
use separately verified auditor identity or exchange an out-of-band access code
for a scoped bearer credential. Shared links must not leak auth tokens through
Referer, redirects, third-party JS, browser history, server logs or analytics.
Tokens should be hashed at rest, with rotation, revocation and per-link
limits. No credentials in query parameters for API access.

## Export contract (fail closed)

Input:
`owner + project_scope + source_snapshot_watermark + requested_fields + sensitivity_profile + audience + purpose + policy_version`.

Processing:
`project ACL -> policy decision -> field/span-level export filter -> provenance scrub/redaction -> deterministic bundle -> manifest digest -> immutable publication`.

The current AMOS sovereign-security contract applies: security labels for
classification/compartment/tenant/handling/retention/export/processing/policy version,
separate ContentAccess and DescriptorAccess, derived data inherit most restrictive
source label, deny/redact/escalate before any public cache or summary.

No silent access to private comments, PII, secrets, license-restricted media,
API credentials, source code or discussion text, even when they appear inside
derived traces/ContextBundles. Redaction must cover nested JSON, relations,
embeddings, filenames, error messages and citations. Denied sources must not
be inferable through counts or cursor gaps when disclosure itself is restricted.

An export pack includes:
- `schema_version`, `project_id`, `snapshot_id`, `as_of_utc`, export policy
  and permitted taxonomy/scope, digest and source-manifest references;
- permitted mission objective/state, proven decisions, failed/blocked/open work,
  next-safe-action **as a historical observation** (not authority to run it);
- E0 references/digests and V/R/O/A projections with sensitivity-filtered
  human-readable evidence summaries; explicit `VERIFIED` vs `UNRESOLVED`;
- accepted validation/CR outcomes, known limitations, contested claims;
- clear timestamps, snapshot freshness and evaluation partition treatment.

Exported artifacts carry no write credentials and no private infrastructure
locators. External auditor text/findings are untrusted input and must never
be interpreted as policies, system prompts or project-owner authorization.

## Operational and audit constraints

- Keep the authoritative AMOS E0 store and private GitHub token inaccessible
  to the gateway's public process; export snapshots offline/read-only into
  a separate constrained storage and serve only approved bytes.
- Rate limit, content-size cap, request timeout, quota, abuse controls and
  concurrency cap. No external-agent-triggered LLM inference or expensive
  live project replay in the HTTP request path.
- Record export-policy decision and share lifecycle (created, redeemed,
  denied, expired, revoked, accessed, versioned) without logging secret URLs.
- Revocation blocks future fetches of all protected snapshots and deltas;
  it cannot retract already downloaded evidence. Explicitly warn owner.
- Immutable `snapshot_id` ensures reproducibility; continuing share URL
  points to latest permitted immutable snapshot with explicit `as_of`.
- Consider ETag/If-None-Match and delta cursors to avoid recurrent full downloads.
- Independent security audit includes URL guessing, SSRF/path traversal, token
  leakage, re-identification, nested secret contamination, replay/race in
  one-time redemption, link previews, cross-tenant access and stale ACL.
- Do not claim end-to-end encryption, sovereign/GOST processing or privileged
  source visibility without separately verified runtime evidence.

## Proposed milestone gates

**G0 — policy/data inventory**: classify actual AMOS fields across public/private C02
and AMOS; owner signs exact export policy; decide whether anonymous public demo
is permissible. No public deployment.

**G1 — offline minimal exporter**: deterministic redacted frozen snapshot + JSON
schema/manifest/digest and golden tests. Denied E0 never appears in exported
projections or summaries; verify independent reconstruction from allowed sources.

**G2 — local link authority service**: capability issuance, one-time redemption
atomicity, expiry/revocation, continuous-link versioning, immutable share manifests,
access audit and negative security cases. Unit/integration tests offline.

**G3 — site + gateway staging**: guarded `/audit/` UI and read-only machine endpoints
on staging through existing Caddy/infrastructure. No real private project data;
synthetic fixtures only. Exact-SHA CI and external independent unauthenticated test.

**G4 — limited live pilot**: owner-approved public-only AMOS demonstration and
one named auditor; verify 403 after revocation, stability after restart, data
minimization, bounded CPU/RAM/bytes and no writes to AMOS E0. Repeat for continuous
link only after one-time mode acceptance.

**G5 — findings loop** (separate authorization): accept external audit findings into
quarantine as E2 external assertions with provenance and human review. Never
promote to project decisions without independent evidence and authorized approval.

## Repository boundaries

- `aimeton-memory-os`: export schema, field/label policy, deterministic redacted
  ContextBundle compiler, tests and manifest/provenance rules.
- `aimeton-site`: public audit landing page and presentation, no raw evidence,
  no credentials and no direct private AMOS API.
- `aimeton-infrastructure`: edge routing, service placement, network isolation,
  secrets policy, audit logs and deploy/readback; no unsanctioned new VPS.
- `aimeton-architecture`: cross-product normative security/publishing policy
  if the contract becomes platform-wide.

## Decision boundary

This document defines an architecture candidate, not approval to publish
any C02, GNSS, BIS, AMOS or other private/project material. Production endpoint
and external public share creation remain unimplemented and require explicit
owner approval of scope and data classification.
