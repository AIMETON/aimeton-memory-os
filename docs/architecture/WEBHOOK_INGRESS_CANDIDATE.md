# AMOS signed GitHub webhook inbox — candidate ingress, not yet deployed

Status: **implementation candidate**. Parent: issue #30. No operational GitHub hook,
public HTTPS route, secret provisioning, systemd activation or queue-to-collector
completion contract has been accepted. The production one-shot reconciler remains
read-only, with a five-minute fallback interval.

## Components

- `src/aimeton_memory_os/webhook_inbox.py`: stdlib SHA-256 HMAC validation,
  strict repository/event allowlist and SQLite WAL deduplicated receipts.
- `scripts/receive_github_webhook.py`: local-loopback-only HTTP interface,
  path `/hooks/amos/github`, size bound 256 KiB, accepted signed deliveries
  reply 202 only after the SQLite commit and a wake-file append.
- `tests/test_webhook_inbox.py`: bad signature/tampering, wrong repository or
  event, malformed signed payload, duplicate, exact-claim ACK and durable restart checks.
- `scripts/webhook_batch_cli.py`: exact claimed-delivery batch checkpoint
  for exclusive systemd worker; complete only after successful source GET/E0/trace cycle.

No raw webhook body is stored. The queue is a *delivery hint*, not E0 and not
a substitute for the source-authoritative GitHub GET and digest verification.
No webhook result directly grants action authorization.

## Remaining deployment and acceptance gates

1. Protect a unique 32-byte-or-longer shared secret on the main server; configure
   the GitHub webhook source with the same secret using approved admin access.
   No secret values in a repository, chat, CI logs or telemetry.
2. Add a verified HTTPS edge route to the loopback receiver on the canonical
   Caddy deployment, preserving the current public-site routing.
3. Add a guarded systemd unit and path activation tied to durable wake events,
   followed by a bounded GitHub GET-only collector cycle. The product now
   provides `webhook_batch_cli.py` and durable exact-ID begin/success/failure
   transitions; the infra wrapper still needs to wire them into the oneshot
   service. New receipts during a run remain pending, and failed/crashed
   claims are recovered by the next exclusive worker.
4. Verify a naturally occurring authorized GitHub event is received and
   produces exactly one immutable E0 and trace. Test spoofed requests,
   duplicate delivery, server restart, reordering and outage recovery.
5. Only after this evidence switch the fallback timer from 5 minutes to
   6 hours; retain exact-SHA deployment, periodic full integrity audit,
   and an immediate rollback to five-minute polling.

External exposure and production secret registration are intentionally absent
from this source-only PR.
