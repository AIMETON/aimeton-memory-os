# AMOS G3 — loopback-only synthetic HTTP prototype

Status: **LOCAL TEST CANDIDATE**. No public route, no staging deployment,
no actual AMOS data access, no real audit link publication.

## Purpose and constraints

The prototype binds to `127.0.0.1` only and preloads exactly one validated
synthetic G1 package. It reads **only** the separate G2 synthetic-grants SQLite;
the authoritative AMOS E0 store is not mounted or opened.

Endpoints:
- `GET /health`: fixed synthetic-only status.
- `GET /v1/shares/<uuid>/preview`: only non-secret synthetic metadata; never
  consumes a one-time grant, even for repeated preview attempts.
- `POST /v1/redeem` with `Content-Type: application/json` and a short body
  `{"capability":"..."}`: atomic redemption and immediate return of the
  pinned synthetic `manifest` + `snapshot` in the same response. No
  reusable artifact endpoint, no credential-bearing URL, no admin API.

All other paths/methods fail closed. Unrecognized Host/Origin, encoded paths,
query strings, missing/oversize body, invalid content types, unknown or
revoked grants are rejected. There is no CORS authorization. Response security
headers disable caching and referer leakage. The server suppresses request
logging to avoid leaking capabilities. A one-time redemption response can
not be retrieved a second time; callers must preserve their first result.

## Local demonstration

This is **not** a deployment instruction. To run locally in a private dev
environment, produce the synthetic G1 package and issue a grant using the
G2 local admin Python function, then start:

```bash
python3 scripts/serve_synthetic_audit_gateway.py \
  --db /tmp/amos-g3-local-grants.sqlite \
  --fixture tests/fixtures/audit_synthetic_policy_input.json --port 0
```

The server prints the ephemeral loopback port only, never any token.

Tests:
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_audit_http_g3.py' -v
```

## Not accepted or provided

- No HTTPS termination, reverse proxy, public domain or site integration.
- No verified auditor identity, production-grade authentication, quotas,
  logging/audit receipts, network-zone isolation or independent security audit.
- No HTTP grant issuance, revocation or snapshot updates: those stay local
  administrative functions and MUST require authentication before exposure.
- No unrestricted real AMOS exports. G0 has not approved any source span or
  project profile, so C02/BIS/private information remains inaccessible.
- No authorisation for Caddy routing or a public URL.

G3 staging deployment remains a separate security/infrastructure step:
[Infrastructure #846](https://github.com/AIMETON/aimeton-infrastructure/issues/846).
The actual online gateway requires an appropriately hardened network server,
a separate content store and signed owner-approved export policy, verified
in a synthetic-only staging environment first.
