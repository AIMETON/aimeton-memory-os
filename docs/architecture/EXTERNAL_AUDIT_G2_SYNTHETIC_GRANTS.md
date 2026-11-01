# AMOS External Audit Gateway — G2 local synthetic grant lifecycle

Status: **offline test candidate only** (no web server, no URL issuance, no
production data, no public authorization). Built on G1 fixed
`amos-synthetic-audit-demo` snapshot + SHA-256 manifest.

## Primitives

- `issue_synthetic_grant`: validates the exact synthetic pack, accepts
  `one_time` or `project_continuous`, generates an unpredictable capability
  with `secrets.token_urlsafe(48)`. Only SHA-256 of the token is persisted
  in local SQLite. Returns the capability once to trusted local caller.
- `preview_synthetic_grant`: by public non-secret `grant_id`, returns only
  fixed synthetic metadata; does not consume a one-time grant. No artifacts,
  source details, manifest bytes or tokens are returned.
- `redeem_synthetic_grant`: requires the separate secret token; atomic
  `BEGIN IMMEDIATE` transaction makes exactly one concurrent request win for
  `one_time`, with UTC expiry/revocation checks. A continuing grant can be
  redeemed more than once without mutating the snapshot.
- `revoke_synthetic_grant`: local-only owner-operation placeholder, denies
  subsequent redemptions; do **not** expose as unauthenticated HTTP endpoint.
- `update_continuous_synthetic_snapshot`: validates a new synthetic
  manifest/snapshot and changes the continuous grant's snapshot pointer
  only if its old ID still matches; revoked/expired grants cannot update.
  Old snapshots remain immutable and require separate retention rules.

Every public share must eventually use separate identity verification for
sensitive data, and explicit user-initiated redemption (not link preview).
This module does not currently implement that web-level contract.

## Security properties checked

- Expired, revoked, unknown or already-redeemed one-time capability fails.
- Concurrent redemption accepts exactly one request among multiple threads.
- Raw capability absent from SQLite; token digest is unique.
- A real project ID or modified/unauthorized synthetic pack cannot be issued.
- Continuing grant version switch fails on stale snapshot, then succeeds
  on exact snapshot ID and fails after revocation.
- Link preview does not consume one-time access.
- No external requests, no AMOS SQLite access, no export of real project
  E0, no site/infra production mutation.

## Limitations

This is a reusable local state-machine **prototype**, not an access service.
The SQLite file is itself private and must live behind a real authenticated
administrative boundary before production. There is currently no public
HTTP route, no auditor login, no email delivery, no token exchange, no
rate limiting, no per-user quota, no browser session, no signed audit trail
for admin operations and no external release authorization.
A process with local database write access could issue/revoke links;
never mount this database writable in an untrusted gateway.

Do not treat this as G2 production acceptance or permission to export
real AMOS projects. Next: independently review grant ledger and negative
tests, specify authenticated service separation and link preview/redeem
HTTP handling with synthetic fixtures before staging.
