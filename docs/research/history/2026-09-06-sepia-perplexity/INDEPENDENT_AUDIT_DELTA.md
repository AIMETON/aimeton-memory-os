# Independent audit cross-review delta

Status: **AMOS research interpretation / non-normative / Shadow-track**  
Date: 2026-09-06  
Primary research artifact: `AMOS_Semantic_Relation_Layer_Sepia_Research_ru.md`  
Independent audit artifact: `Аудит AMOS Semantic Layer.md`  
Parent research: #11  
Shadow pilot: #13

## Purpose

Preserve the independent audit as external research evidence while separating:

`auditor claim -> AIMETON cross-check -> accepted research delta -> future verification`.

This note does not change V/R/O/A, CR-01..CR-06, OCC-49, runtime schemas or the current AMOS MVP critical path.

## Audit contributions accepted into the research track

### A1. Recontextualization needs an independent formal foundation

Accepted.

Sepia/StoryScope is useful evidence that later disclosure can change interpretation of earlier material, but its `recontextualization depth` metric is not a formal memory-update semantics.

AMOS should therefore research recontextualization against:
- belief revision;
- defeasible / non-monotonic reasoning;
- truth-maintenance / dependency tracking;
- temporal epistemic state;
- provenance-preserving interpretation revision.

The existing AMOS rule remains stronger than a narrative metric:

`later evidence may change interpretation without rewriting E0`.

No AGM operator or belief-revision formalism is adopted yet. This is a literature/research lead, not a schema decision.

### A2. Mature NLP formalisms should constrain, not be reinvented

Accepted with qualification.

The audit correctly reinforces the requirement to compare AMOS candidates against mature resources such as:
- PropBank / FrameNet / FrameBank;
- AMR / UDS;
- OpenIE;
- event extraction / MAVEN-ERE / ACE-style resources;
- TimeML / interval algebra;
- PDTB / RST;
- QUD parsing;
- argument mining / FEVER / SciFact;
- provenance standards.

However, AMOS must not blindly inherit any one external representation.

External formalisms are:
- candidate semantic substrates;
- label sources;
- benchmark baselines;
- adapter inputs.

AMOS keeps an owned minimal contract because authority, evidence provenance, temporal validity, compatibility and ContextBundle projection are not supplied by AMR, PropBank, OpenIE, PDTB or GraphRAG.

### A3. QUD/discourse vocabulary should be grounded upstream

Accepted.

Sepia is not the canonical QUD or discourse ontology.

For Shadow research:
- Sepia move vocabulary may seed candidate labels;
- QUD parsing and PDTB/RST-like relations should be evaluated directly;
- paragraph boundaries must not be treated as a guaranteed one-QUD unit;
- QUD/theme/discourse remain A-layer candidates until downstream utility is demonstrated.

### A4. Russian calibration needs native evidence

Accepted.

Russian semantic/discourse behavior cannot be inferred from Sepia's English/Chinese style calibration.

Native-RU evaluation must cover:
- entity/coreference;
- semantic roles;
- temporal anchoring;
- causal connectives and scope;
- source/claim attribution;
- QUD/discourse segmentation;
- recontextualization/correction.

### A5. Actor/social-network measurements are candidate-generation signals only

Accepted.

Co-occurrence, affect sign, density and clustering may be useful diagnostics or priors for candidate generation, but they cannot directly establish:
`interacts_with`, `owns`, `controls`, `supports`, `opposes` or responsibility.

This is consistent with the existing AMOS research baseline.

## Audit claims corrected or not adopted

### C1. "The primary report did not provide a full classical-NLP comparison"

**Not accepted.**

The archived primary report already contains a substantial comparison section:
`# J. External technologies to study` and `## J1. Sepia against mature approaches`, covering SRL, OpenIE, AMR, UDS, event extraction, temporal extraction, causal extraction, discourse parsing, QUD parsing, claim/evidence extraction, GraphRAG and ontology induction.

The audit usefully reiterates this comparison but does not fill a missing section.

### C2. "The primary report lacked a full JSON Schema draft"

**Not accepted.**

The archived primary report already contains:
`# G. AMOS schema draft` and `## G2. Core JSON Schema proposal v0.1`.

The schema remains a research proposal rather than an adopted AMOS contract, but it was present in the primary report.

### C3. "QUDsim move-sequence corpus = 61,608 stories"

**Conflict detected; do not use.**

The archived primary research matrix distinguishes:
- **StoryScope**: 61,608 stories;
- **QUDsim**: 100 documents, 180 QUD-document pairs, 3,584 segment pairs and 601 QUD types.

Therefore the audit's `61,608 stories` attribution to QUDsim is inconsistent with the primary research record. No benchmark sizing, prior or threshold may use that audit number unless independently re-verified from the QUDsim primary paper.

### C4. "AMOS Event-node should use PropBank roles"

**Too prescriptive; not adopted.**

PropBank/FrameNet/FrameBank are valuable baselines and source vocabularies. AMOS should preserve mappings to their original labels, but the AMOS core role contract must be selected by benchmark utility and projection requirements.

No external role inventory becomes sovereign AMOS semantics merely because it is mature.

### C5. "AMOS SemanticNode can directly inherit AMR node/edge typing"

**Not adopted.**

AMR is a possible extraction substrate, not the AMOS evidence/authority model.

Any AMR-derived node/edge remains a candidate with:
- source span/provenance;
- extractor/version;
- explicit/inferred status;
- time;
- evidence status;
- compatibility gate;
- projection status.

### C6. "ContextBundle compilation directly corresponds to GraphRAG community summarization"

**Not adopted as architecture equivalence.**

GraphRAG may be a useful retrieval experiment later. ContextBundle has additional AIMETON requirements: bounded mission/scope, role/authority, evidence admission, temporal validity, compatibility and explicit exclusions.

GraphRAG cannot become the source of truth or a substitute for V/R/O/A coordination.

### C7. AI-vs-human move-frequency distributions as semantic priors

**Restricted.**

These distributions may be retained as research diagnostics or benchmark stratification signals.

They must not:
- affect truth or authority;
- determine ontology admission;
- become production extraction thresholds;
- bias AMOS toward "human-like" semantic structures.

AMOS optimizes semantic fidelity and mission recovery, not human-authorship appearance.

## New research lead created by the audit

The most valuable net-new direction is:

**recontextualization / interpretation revision as an AMOS-native evidence-governed update mechanism.**

Research question:

> Given immutable earlier evidence E0/E1 and later evidence E7, how should AMOS represent the transition from interpretation I1 to I2 without rewriting source history, while preserving scope, time, competing hypotheses, decision lineage and projection admissibility?

Candidate families to compare before any schema adoption:
- AGM-style belief revision;
- belief update vs belief revision;
- defeasible/non-monotonic reasoning;
- truth maintenance systems;
- assumption-based truth maintenance;
- provenance semirings/dependency lineage;
- temporal/bitemporal knowledge revision;
- argumentation frameworks for conflicting claims.

Sepia's `recontextualization depth` is only the discovery signal that motivated this research lane.

## Effect on #13 Shadow pilot

The six-document pre-benchmark remains the correct next gate.

Add two explicit evaluation questions:

1. Can later evidence produce a reversible `InterpretationRevision` / recontextualization record without mutating earlier evidence or collapsing competing claims?
2. Does QUD/discourse enrichment improve ContextBundle selection independently of any AI-vs-human style-frequency prior?

No larger ontology freeze or GraphRAG/AMR runtime integration is authorized by this audit.

## Current decision

`AUDIT ACCEPTED AS RESEARCH EVIDENCE WITH CORRECTIONS`

Net effect:
- strengthens no-fork / no-direct-Sepia decision;
- strengthens grounding in mature NLP formalisms;
- creates a focused recontextualization/belief-revision research lane;
- does **not** change the current AMOS P0 mission-recovery critical path;
- does **not** promote the audit's external-stack recommendations into architecture invariants.
