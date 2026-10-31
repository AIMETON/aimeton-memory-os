# AMOS MVP-3 — natural Choke Ring activity accepted

Date of readback: 2026-10-31 02:04–02:05 UTC.
Classification: **development / dogfooding**, NOT holdout, F1 or full Memory OS effectiveness.

## Source activity

The existing private source `AIMETON/Choke_ring_antenna` produced PRs #75–#86
with source `updated_at` from 2026-10-30 21:22:45Z to 23:02:37Z,
all after the corrected multi-repository collector activation at ~16:10Z.
Activity includes recovery from G2.5 postprocessing, G2.5 spatial PASS,
and G3 configuration/admission engineering. AMOS did not create or edit those
source PRs to produce test events.

## Independent persistent readback

- Infrastructure exact main: `47f2d391b2d61d56e41afde8dcfeca5f960d0f96`.
- Installed AMOS exact product: `966133589e881f8a2d81e3f41a9fc023d334e59a`.
- Source marker: PR #86, GitHub source object ID `5092157619`,
  source updated at `2026-10-30T23:02:37Z`.
- Immutable E0 ID:
  `github:pull-snapshot:AIMETON/Choke_ring_antenna:5092157619:2026-10-30T23:02:37Z`.
- Independent readback workflow run
  [#41158318969](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41158318969):
  **SUCCESS**; read-only, `collector_invoked_by_readback=false`.
- Repeated independent readback run
  [#41158380394](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41158380394):
  **SUCCESS** after a fresh bounded timer opportunity. The source marker
  remained exactly **1 E0 / 1 trace** (no duplicates).
- Persistent totals unchanged between two reads:
  **147 E0, 149 real immutable traces**; 65 memory-os E0;
  82 Choke Ring E0; 4 physical cursors (3 required complete-source cursors,
  one retained legacy partial comment cursor). Two decision-chain traces.
- All six `CR-01…CR-06` satisfied for marker; `V.scope`
  is the expected private repo, PR number=86, E1 populated,
  E2 legitimately empty for plain PR snapshot, no source/provider mutation.
- Choke PR cursor: `5092157619 @ 2026-10-30T23:02:37Z`.
- Live installer/readback reports healthy service.
- Source count advanced from 69 Choke E0 at the earlier accepted v0.5.1
  deployment to 82 E0 at this readback; this is **13 additional
  versioned E0 receipts**, not a claim that 13 unique PRs were created.

## Interpretation

The formerly missing post-activation natural-event acceptance criterion
for `aimeton-memory-os#24` has been observed and independently tested.
Source-to-E0-to-immutable-trace continuity and idempotency on this
private GitHub stream are now accepted for the **bounded Shadow MVP-3**.

Not proven by this acceptance: completeness of private issue comments
(known partial visibility, explicitly excluded), meaningful full-project
decision extraction, memory effectiveness on agent task completion,
webhook live delivery or six-hour fallback. The accepted runtime
still collects via the 5-minute periodic source reconciliation.
Event-driven ingress remains separately tracked by issue #30.
