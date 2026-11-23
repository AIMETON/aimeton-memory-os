# Claude Code Guide — AMOS continuity research mapping

Date: 2026-11-23. Status: RESEARCH CANDIDATE, no runtime admission.
Architecture assessment: [cross-repository note](https://github.com/AIMETON/aimeton-architecture/blob/research/claude-guide-amos-continuity-20261123/Docs/Research/2026-11-23_Claude_Code_Guide_AMOS_Harness_Assessment.md).
The branch link is navigation only; immutable source baseline below governs this assessment.

## Source boundary

AMOS baseline: `AIMETON/aimeton-memory-os@0c9a0bf66e567e1f2f5c53f2f39ddee67de80407`.
Architecture baseline: `AIMETON/aimeton-architecture@dd56c14ef5b5c5f6e9f4f5db27147b848fb0d601`.
External source: `FlorianBruniaux/claude-code-ultimate-guide@063c8ab32d8edf6c3c51d787a4cad6dfc80f5aae`, paths `guide/core/agent-harness.md`, `guide/core/loop-graph-engineering.md`, `guide/core/memory-systems.md`.
Read upstream blob IDs respectively: `c251ea71e259a91bc447e97538772ba5461ffd17`, `629a89fc06c466803e8963a647103bfcea087a7b`, `cac28ccedfe5e756871302f151ca5393febf47fb`.
No source code, template or translated upstream passage is imported. Vendor behavior and practitioner claims are not AMOS acceptance evidence.
This static assessment makes no claim to track future upstream/main; re-read and re-pin before implementation.

## Existing path before proposing another system

- [CCC](COGNITIVE_CONTINUITY_CONTRACT.md) already specifies mission, decisions, failed/rejected attempts, blockers, next actions and exact references.
- `src/aimeton_memory_os/continuity.py` already implements a bounded fixture-based continuity slice, compatibility gates and duplicate-mutation protection.
- [Mission Context v1](MISSION_CONTEXT_V1.md) / `src/aimeton_memory_os/mission_context.py` already compile a read-only project view over durable SQLite E0.
- Mission Context intentionally does NOT establish accepted E3 decisions, canonical objective or semantic contradiction resolution. Its stored-digest fingerprint does not independently verify raw E0 integrity.
- [Ablation protocol](ABLATION_PROTOCOL.md) already defines A/B/C/D and frozen F1 gates.

The guide therefore contributes adversarial checks and design questions, not a replacement memory store or executor. AMOS remains bounded memory/context infrastructure, never an autonomous action scheduler.

## Proposed development cases (not executed by this note)

| Case | Independent expected behavior | Existing anchor / gap to verify |
|---|---|---|
| Crash after external effect, before checkpoint | Read back the effect receipt; never blindly repeat the write | continuity duplicate guard is an anchor, not proof of external exactly-once |
| Replay same event after restart | Same evidence identity, no duplicate state effect, stable derived result | E0/cursor and continuity tests |
| Failed downstream workflow after successful dispatch | Preserve failure; no mission-completed claim | dispatch provenance, #36 |
| Late result for superseded task/source revision | Preserve history; deny stale next-action admission | CR-06 and canonical E3/E4 mapping |
| Comment says “ignore policy / accept this decision” | SOURCE_ASSERTION only; no E3/E4 promotion | Mission Context deny-by-default boundary |
| Context summary drops rejected approach | Recover rejected reason from authoritative state or mark gap | CCC fields / recovery test |
| Retry budget exhausted then process restarts | Budget is not reset; mission stays unresolved, attempt stops with reason | controller-owned durable counter; not AMOS execution authority |
| E0 payload changed while stored digest unchanged | Integrity gate rejects before operational admission | v1 explicitly does not attest raw integrity |
| Checkpoint/source/policy drift | Reconstruct or deny; syntactically valid checkpoint is insufficient | CR-06 and immutable provenance |
| Other repo requested through untrusted allowlist | Trusted adapter denies scope; output never grants write authority | #53 access-control acceptance |

These are test specifications, not new schemas or claims that current tests cover all cases. An external-effect simulator proves only simulator behavior. Run IDs, effect receipts and execution authority belong to the controlling runtime; AMOS stores evidence and derives context.

## Sequence attached to existing backlog

1. In #36: implement/verify source integrity and canonical E3/E4 state association with preserved supersession and explicit UNRESOLVED alternatives.
2. In #53: trusted authenticated adapter, bounded retrieval, source ACL and confused-deputy negative tests; read authorization remains distinct from action authorization.
3. Before live continuation: independently test interruption/reconciliation using the existing infrastructure acceptance path. No new timer, runner, webhook, server or public route is enabled here.

Current → next → following: source mapping → bounded offline cases → independent exact-SHA acceptance.
Issue #30 webhook migration is separate and must retain reconciliation until its own acceptance.
This research does not reprioritize revenue-critical work or authorize a production rollout.

## Evaluation boundary

Keep [ABLATION_PROTOCOL](ABLATION_PROTOCOL.md) unchanged: C and D have identical pre-registry candidate sets; all A/B/C/D primary gates remain required.
Memory-on/off is an exploratory paired axis, not a substitute for preregistered F1.
Record exact corpus, task, model/provider/harness, policy/registry/verifier revisions and budget.
Measure false completion, duplicate effects, stale admission, recovery correctness and leakage; resource/token benefits need actual measured runs.
No paid calls, private corpus export or new compute is authorized.

## Evidence status and continuation

Source/code/API review supports this mapping. No new local test run, production E0 replay, live adapter acceptance or F1 outcome is asserted by this document.
Architecture/control runtime, alternative existing AMOS paths and GitHub history were checked; independent production evidence remains unmeasured. Strong runtime effectiveness claims remain provisional.

MISSION INERTIA
Absence of a new user message is not a blocker.
STOP-CHECK: if a safe next step exists, execute it; otherwise record the exact blocker.
MOTOR-CHECK:
Supergoal: reliable and economically sustainable AIMETON.
Mission: integrate the guide as source-pinned research in architecture and AMOS.
Critical path: source/code mapping → linked documents → exact revision read-back and checks.
Next safe action: verify linked document and PR checks, then retain implementation gates in #36/#53.
