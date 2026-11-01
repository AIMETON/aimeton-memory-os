# AMOS MVP-4 C02 exact dispatch provenance — independent live acceptance

Date: 2026-11-01 (UTC). Scope: `AIMETON/Choke_ring_antenna` issue #2 command routing and AMOS Shadow memory. Status: **ACCEPTED for exact source-to-dispatch evidence**, not for whole mission reconstruction, scientific modelling or Webhook activation.

## Contract and exact revisions

- C02 source PR [#191](https://github.com/AIMETON/Choke_ring_antenna/pull/191), accepted `c1f32c13d2fcbe5cc91761c3bf771a315d0ab9c5`: the existing owner-only router invokes GitHub `workflow_dispatch` with `return_run_details=true` and records a GitHub Actions bot-authored receipt in control issue #2. No RF/EM or scientific workflow logic was changed. Receipt includes exact source comment ID and command SHA-256, router run ID, target workflow filename and run ID, and pinned source SHA. The raw command is omitted from the receipt.
- AMOS verifier PR [#38](https://github.com/AIMETON/aimeton-memory-os/pull/38), accepted `de729a641454d632742a99f4603e5eb5cc0dc2a8`: require FOUR separately preserved E0 records and exact identity/content corroboration (owner command, trusted GitHub Actions bot receipt, router run, child run). False/ambiguous links are not accepted.
- AMOS post-persistence automatic projection PR [#39](https://github.com/AIMETON/aimeton-memory-os/pull/39), accepted `80e7cadc634271221e7d7f2998ef5026dbfed6c1`: emit `amos.live-dispatch-provenance` immutable trace only from exact authenticated E0 links and terminal source run versions. Checkpoint schema v2; idle fast path retained, no additional GitHub API requests.
- Infra independent readback PR [#845](https://github.com/AIMETON/aimeton-infrastructure/pull/845), accepted `ac326719a6b939113a104290e3e6eee3dea26c33`. Live production application via [run 41281384309](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41281384309), SUCCESS, installed AMOS exact SHA `80e7cadc634271221e7d7f2998ef5026dbfed6c1`.

## Real source events

1. [C02 command comment #6554410040](https://github.com/AIMETON/Choke_ring_antenna/issues/2#issuecomment-6554410040): limited `/probe-antenna-c02` at pinned C02 SHA.
2. [C02 Command Router run #41280730833](https://github.com/AIMETON/Choke_ring_antenna/actions/runs/41280730833): **SUCCESS** (the routing operation completed).
3. [GitHub Actions bot receipt #6554412402](https://github.com/AIMETON/Choke_ring_antenna/issues/2#issuecomment-6554412402): explicit source comment `6554410040`, router `41280730833`, child `41280746107`, command SHA-256 and workflow identity.
4. [C02 downstream route-probe run #41280746107](https://github.com/AIMETON/Choke_ring_antenna/actions/runs/41280746107): **FAILURE** on its own runtime gate. Router success must never be converted into downstream/scientific success.

The first read-only VPS check [41280964720](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41280964720) **failed closed** while E0 still held a pre-terminal workflow version. After normal five-minute reconciliation updated the immutable E0 stream, follow-up [41281118859](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41281118859) **PASSED**, proving the exact chain and retaining terminal `failure`. This is evidence of correct version handling, not grounds to ignore collector freshness latency.

## Independent immutable trace acceptance

[Infrastructure readback #41281559880](https://github.com/AIMETON/aimeton-infrastructure/actions/runs/41281559880) **SUCCESS**:

- All FOUR source E0 refs are digest-verified; exactly one accepted trace corresponding to the authoritative terminal source combination was independently read by its SHA-256 filename.
- `causal_status=VERIFIED` for **dispatch provenance only**; `downstream_conclusion=failure`.
- CR-01…CR-06: **6/6 satisfied**. Recomputed ContextBundle equals the persisted JSON trace.
- Immutable trace filename digest: `57df0ea05ba502b54194bb22a65d253be1f2ba9a65544a9738b56b755a4fce06`.
- Server at acceptance: **1,298 E0**, **1,301 traces**, checkpoint `schema_version=2`, `dispatch_chain_traces=1`; collector service healthy.
- Readback did not invoke the collector and performed **no GitHub/source/provider mutation**.

## Limits and next preregistered gates

- A completed downstream `workflow_dispatch` with conclusion `failure` proves an attempted execution and a failed result, **not** a successful engineering operation.
- An exact command-to-run link alone is **not** a proven C02 scientific decision, geometry validity, impedance/S4p acceptance, or permission to launch full FDTD. It does not authorize a next scientific action.
- Historical comment `6537145047` on 2026-10-31 remains **UNRESOLVED** as an exact causal link: no contemporary bot receipt exists. Never backfill an asserted link based on temporal proximity.
- The current idle-fast-path avoids full E0 replay if nothing changed, but non-idle cycles still replay all E0 in the existing processor. **Incremental E0-rowid/affected-mission projection and measured CPU/SQLite/network cost remain outstanding**.
- Authenticated HTTPS Webhooks and six-hour backup reconciliation are not accepted; five-minute polling remains.

Next: [AMOS Issue #36](https://github.com/AIMETON/aimeton-memory-os/issues/36) for incremental activity/mission graph, source-authorized decision extraction and fresh-agent ContextBundle reconstruction. [Issue #30](https://github.com/AIMETON/aimeton-memory-os/issues/30) separately tracks Webhook transition. No closure of either issue is implied by this narrower acceptance.
