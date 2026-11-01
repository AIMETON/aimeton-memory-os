# AMOS External Audit Gateway — G1 offline synthetic exporter

Status: **prototype, synthetic-only, no public data, no server route**.

## Implemented

`src/aimeton_memory_os/audit_export.py` creates a versioned, deterministic
`snapshot.json` and `manifest.json` from an exact synthetic input contract.
The CLI is `scripts/export_synthetic_audit_pack.py`. All approved statements
come from a fixed vocabulary; project name is a single fixed synthetic ID.
Unknown keys, unauthorized profile, actual repository name, private labels,
freeform body/source URL, duplicate record IDs, malformed digests and
unknown values fail closed.

Denied records are excluded **before inspecting their nested data**; they
cannot affect the output, IDs, counts, order or manifest. The result contains
only explicitly approved record descriptors and 64-hex synthetic evidence
digests. No raw E0, code, comments, hidden private paths, cursor gaps,
embedded credentials, agent instructions or arbitrary text are exported.

The snapshot uses canonical UTF-8 JSON (sorted keys, compact separators,
trailing LF). The manifest binds the exact snapshot bytes using SHA-256,
size and `snapshot_id`. An independent verifier checks hashes, field sets,
version and reconstructs from the whitelist. CLI refuses to overwrite an
existing output directory and never publishes to the website.

## Run (local, offline)

```bash
python3 scripts/export_synthetic_audit_pack.py \
  --fixture tests/fixtures/audit_synthetic_policy_input.json \
  --out /tmp/amos-synthetic-audit-pack
python3 -m unittest tests.test_audit_export_g1 -v
```

`/tmp/amos-synthetic-audit-pack` is a local synthetic test artifact, **not**
a link or production distribution. Only files `manifest.json` and
`snapshot.json` are generated, no raw input is copied.

## Critical boundaries and prerequisites

This intentionally implements **only a safe slice of G1**. It is not a
general exporter from AMOS. G0 authorization and per-field SecurityLabel
classification have not been completed for private real project evidence.
Do not remove the exact synthetic profile gate or convert the fixture flag
into an owner-approval bypass. Real data require a separate policy decision,
explicitly approved field/span filtering, restrictive inheritance across
derived projections, content/descriptor separation and independent
exfiltration tests.

No audit link issuance, redemption, revocation, public gateway, OAuth,
Caddy route, database or site change exists yet. This code cannot
unilaterally make private AMOS content public.

## Next safe stage

Independently verify the fixture bytes and SHA-256, run broader negative
tests, then define the G0 classification matrix and a distinct, owner-gated
real-data export extension. The first gateway staging test must use
**synthetic content exclusively** and remain closed to unauthenticated
external requests until its own security acceptance.
