# AMOS Semantic Relation Layer — Sepia research baseline

Status: **research baseline / Shadow-track candidate**  
Date: 2026-09-06  
Parent issue: #11  
Current AMOS critical path remains: #6 (persistent mission recovery through ContextBundle).

## Source provenance

This baseline distills an owner-supplied external research report:

- artifact name: `AMOS_Semantic_Relation_Layer_Sepia_Research_ru.md`
- artifact SHA-256: `3a28872ff07be9e581089f43adb68ef261d431e33f26c2b7719ba045a555fe0b`
- Sepia upstream: https://github.com/Nanako0129/sepia
- Sepia intake revision: `d8a0f948cc46a0ba0d610df7458c4e8943bfe51a` (v0.8.0)
- architecture intake: AIMETON/aimeton-architecture#161

The external report is research input, not an AMOS normative contract. Claims remain subject to AMOS 3×3, source verification, benchmark evidence and versioned architecture review.

## Decision

### Adopt now as research constraints

AMOS accepts the following as **design constraints for a future semantic extraction layer**, because they strengthen existing evidence/projection boundaries without changing the four-axis model or Compatibility Registry:

1. **Candidate-first semantic storage.**
   Extractors produce candidates. An LLM or parser does not directly create authoritative `O`, `R`, `V` or E3 state.

2. **Exact provenance before semantic promotion.**
   Every candidate intended for later operational use must retain immutable source reference, exact source span or equivalent locator, extraction run/version and derivation status.

3. **Explicit != inferred != derived != verified != authoritative.**
   These are separate dimensions. A single confidence score must not collapse extraction confidence, evidence strength, temporal certainty and authority.

4. **Adjacency is not causality.**
   `before(A,B)`, text order, paragraph adjacency, correlation or shared actors must never silently promote to `causes(A,B)`.

5. **Citation is not support.**
   A link/PR/commit/paper reference may establish `cites`; it does not automatically establish `supports`, `verifies` or `refutes`.

6. **Mention/co-occurrence is not operational relation.**
   Co-mention may create an associative candidate, but cannot by itself establish `interacts_with`, `owns`, `controls`, `approves` or responsibility.

7. **Unknown / unresolved / competing interpretation is valid state.**
   Extraction must be allowed to abstain. Ambiguity must not be forced into the nearest category merely to complete a graph.

8. **Recontextualization is additive.**
   Later evidence may weaken, strengthen, supersede or change interpretation of earlier records, but must not rewrite immutable E0 evidence or silently erase earlier derived state.

9. **Language calibration is first-class.**
   English or Chinese stylistic/extraction observations do not establish Russian extraction quality. Russian must be measured directly.

10. **Schema before downstream consumption.**
    Closed/versioned relation vocabularies and graph validators are required before semantic records can be consumed operationally.

These constraints are consistent with the current AMOS invariant:

`Write_K(input)` preserves evidence, creates projections and leaves ambiguity unresolved; `Read_K` admits only policy/evidence-compatible context.

## What Sepia contributes

Sepia is **not** a semantic parser and is not adopted as an AMOS runtime dependency.

Useful grains are high-level decomposition lenses:

- theme explicitness vs inferred interpretation;
- causal-chain continuity as a diagnostic question;
- event order vs disclosure/revelation order;
- recontextualization after later evidence/reveal;
- actor/network structure as candidate-generation surface;
- paragraph/section QUD (Question Under Discussion);
- discourse moves such as comparison, verification, consequence, contradiction and digression;
- quote-per-finding discipline;
- domain-specific expectations for PR/Issue replies, postmortems, tickets, release notes and technical prose.

Sepia's AI-authorship/humanizer goals, style fingerprints, prose heuristics and model-specific writing signatures are explicitly **out of scope** for AMOS semantics.

## Primary architectural placement

The research report proposed a large semantic stack. AMOS narrows this to preserve the bounded MVP:

```text
E0 Raw Evidence
  -> E1 source-grounded observation/segmentation
  -> SemanticRelationCandidate (Shadow research)
  -> provenance/type/time/evidence checks
  -> candidate O/A projection
  -> existing CR-01..CR-06 compatibility
  -> ContextBundle
```

The semantic layer does **not** replace:

- V/R/O/A;
- CR-01..CR-06;
- immutable evidence;
- authority policy;
- current ContextBundle critical path;
- deterministic verification.

It is a possible future producer of better candidates for O/A and, only with stronger gates, R/V.

## Minimal semantic families to evaluate first

Do not freeze the external report's full predicate list as a canonical ontology yet.

The first Shadow experiment should use only the minimum families needed to test value and safety:

### Reference / provenance
- `mentions`
- `refers_to`
- `cites`
- `derived_from`

### Temporal
- `before`
- `overlaps`
- `during`
- `valid_during`
- `observed_at`
- `asserted_at`

### Evidential
- `asserts`
- `supports`
- `contradicts`
- `verifies`
- `qualifies`

### Causal
- `causes`
- `enables`
- `contributes_to`

### Discourse / QUD
- `raises`
- `answers`
- `explains`
- `compares`
- `corrects`

### Evolution
- `supersedes`
- `recontextualizes`
- `changes_interpretation_of`

Any additional relation remains an experimental/namespaced candidate until benchmark evidence justifies admission.

## Time model: accepted research hypothesis, not yet contract

The external report correctly exposes a likely source of AMOS errors: several clocks may coexist.

Research should distinguish at least:

1. **event / valid time** — when event/state happened or was valid;
2. **observation time** — when an actor/system observed it;
3. **assertion time** — when a source stated it;
4. **recorded time** — when AMOS ingested/recorded it.

A fifth notion, **revelation/discourse position**, is valuable for conversations, investigations and recontextualization, but remains an A-layer research feature until its operational benefit is demonstrated.

This does not modify CR-05/CR-06 yet. Any registry change requires separate versioned architecture work, adversarial fixtures and golden replay.

## Causal safety rule

A causal candidate must not be promoted merely because:

- event A precedes B;
- A and B occur in adjacent sentences/paragraphs;
- the same actor participates in both;
- embeddings are similar;
- a narrative/RCA is written as a clean chain.

For a future accepted causal edge, at least one strong support class should be present:

- explicit causal construction with correct scope;
- authoritative root/contributing-factor claim;
- mechanism/intermediate state;
- counterfactual statement;
- independent verification/experiment.

Until such gates are benchmarked, implicit LLM-generated causality remains A-layer candidate only.

## QUD and discourse

QUD is accepted as a promising **A-layer retrieval/context-selection hypothesis**, not an O fact.

Do not freeze the Sepia simplification "one paragraph = one QUD". The research representation must permit:

- zero, one or several QUD candidates per block;
- partial answers;
- nested/subquestions;
- anchor block/span;
- unanswered/reopened questions.

The value criterion is downstream ContextBundle quality, not similarity to Sepia's prose recommendations.

## Russian language

Russian is a first-class benchmark language. The research baseline identifies NEREL, FrameBank and Russian discourse resources as likely inputs, but none is accepted as sufficient for AMOS.

No RU semantic success claim may be inferred from EN or ZH results.

## External foundations to study before implementation expansion

Priority sources from the research report:

P0:
- MAVEN-ERE — event coreference / temporal / causal / subevent relations;
- TimeML + Allen interval algebra + OWL-Time;
- MATRES / TB-Dense;
- CaTeRS / Causal-TimeBank / CATENA;
- FactBank;
- W3C PROV;
- PDTB / RST;
- QUD dependency parsing / QUDSELECT;
- FEVER / SciFact;
- NEREL / Russian FrameBank.

P1:
- AMR / UDS / PropBank / FrameNet;
- OpenIE;
- Russian discourse resources;
- SHACL;
- GraphRAG only after evidence-aware graph admission exists.

StoryScope/Sepia remain P2-style high-level feature/disclosure research, not core extraction machinery.

## Relationship to current MVP

The semantic research track **must not block** the current bounded MVP acceptance.

Current critical path remains:

```text
raw evidence
-> V/R/O/A projections
-> CR-01..CR-06
-> ContextBundle
-> permitted action
-> deterministic verification
-> replay/recovery
```

Issue #6 remains the operational P0 proof.

Issue #11 is a parallel Shadow research track. Semantic extraction becomes critical-path work only if a small controlled experiment demonstrates a measurable ContextBundle or recovery benefit without increasing policy/evidence leakage.

## First safe experiment

Before designing the full 84-document benchmark proposed by the external report, run a smaller pre-benchmark pilot.

Suggested frozen pilot set:

- 1 RU + 1 EN GitHub Issue/PR discussion;
- 1 RU + 1 EN ADR/engineering note;
- 1 RU + 1 EN incident/postmortem.

Annotate only:

- source spans;
- entity/event mentions;
- explicit claims;
- temporal relations;
- explicit causal relations;
- evidence/support/contradiction;
- QUD/discourse candidates;
- supersession/recontextualization where present.

Measure:

- relation precision/recall;
- provenance completeness;
- temporal relation correctness;
- causal hallucination rate;
- false O/A promotion rate;
- RU/EN gap;
- downstream ContextBundle usefulness.

Only after label definitions and disagreement patterns stabilize should the corpus expand.

## Fork / dependency decision

**NO FORK. NO DIRECT SEPia runtime integration into AMOS.**

Harvest:

- decomposition patterns;
- relation hypotheses;
- evidence-boundary lessons;
- benchmark ideas;
- source papers/datasets.

AMOS owns:

- schemas;
- provenance;
- extraction contracts;
- relation registry;
- compatibility gates;
- validation;
- benchmark;
- runtime.

## Non-goals

This research baseline does not authorize:

- changing CR-01..CR-06;
- changing OCC-49 or other sovereign architecture;
- automatic ontology induction;
- automatic R/V authority extraction;
- automatic causal promotion;
- rewriting existing AMOS MVP around a knowledge graph;
- adding GraphRAG as source of truth;
- introducing paid model calls or new infrastructure;
- treating the external report's proposed thresholds as validated AMOS thresholds.

## Promotion condition

Semantic Relation Layer may move from Shadow research toward AMOS MVP/next-stage architecture only after evidence shows:

1. exact provenance is preserved;
2. relation extraction adds measurable utility over the current projection path;
3. causal and ontology false promotions stay within explicitly accepted bounds;
4. RU and EN behavior is separately measured;
5. compatibility/evidence leakage does not increase;
6. current mission-recovery / ContextBundle acceptance is not regressed.

Until then the correct status is:

`RESEARCH CANDIDATE / SHADOW / NO FORK / NO AUTHORITY`.
