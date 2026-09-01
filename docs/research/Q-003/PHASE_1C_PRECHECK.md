# Q-003 Phase 1-C — Pre-Execution Verification

## Objective

Verify whether the redesigned Phase 1-C is executable.

Do not run Phase 1-C yet.

Do not modify production code.

Do not modify methodology.

Do not modify datasets.

Do not modify documentation.

Do not stage, commit, or push.

This is a read-only verification gate.

## Context

Q-003 remains UNANSWERED and INCONCLUSIVE.

Phase 1-A eliminated raw mean-PCD overlap
as the explanation for Bhairavi confusion.

Phase 1-B localized the remaining issue
toward the dyad channel.

It did not establish the cause.

Phase 1-C therefore investigates the dyad channel.

The methodology audit rejected the original Phase 1-C design.

Three measurements were confounded or invalid.

The redesigned phase must avoid those problems.

## Research hypotheses

Keep these hypotheses distinct.

- H_DATA — insufficient or redundant data.
- H_REP — representation cannot express discrimination.
- H_SHARED-measured — observed dyads overlap due extraction.
- H_SHARED-intrinsic — true musical dyads genuinely overlap.
- H_SCORE — scoring interaction degrades useful dyad signal.

Do not collapse these hypotheses.

Do not select a diagnosis during pre-check.

## Required verification

### 1. Raw dyad counts

Determine whether raw pre-smoothing dyad counts exist.

Check `features_v12` and relevant aggregation outputs.

Determine whether counts survive before Laplace smoothing.

Report:

- exact source file;
- available fields;
- whether raw counts are recoverable;
- whether M1 remains executable;
- any limitations.

Do not create substitute metrics.

### 2. Directional dyads

Determine whether ascending and descending dyads remain separately stored.

Inspect:

- feature artifacts;
- aggregation artifacts;
- relevant production scripts;
- metadata schemas.

Report:

- exact storage location;
- field names;
- whether both directions are recoverable;
- whether direction-split analysis is executable.

Do not modify artifacts.

### 3. Bhairavi provenance

Audit all 11 Bhairavi clips.

Determine available:

- composition identity;
- performer identity;
- source identity;
- provenance evidence;
- missing metadata.

Do not infer composition identity.

Do not invent metadata.

Clearly distinguish FACT from UNKNOWN.

Report coverage numerically.

### 4. Thodi matched control

Verify that Bhairavi and Thodi both have 11 clips.

Verify the repository's swara definitions.

Verify whether their modeled swara sets are identical.

Confirm the exact source files.

Do not assume the prior analysis is correct.

### 5. Existing dyad scoring

Inspect `recognize_raga_v12`.

Verify:

- dyad similarity calculation;
- directional handling;
- normalization;
- weighting;
- final score combination;
- rank calculation;
- margin calculation.

Do not modify scoring code.

### 6. Existing captured results

Verify that Phase 1-B already contains:

- per-clip dyad scores;
- dyad ranks;
- PCD ranks;
- sufficient information for margin analysis.

Identify anything missing.

Do not rerun experiments.

## Proposed Phase 1-C

Do not execute this phase yet.

Assess whether these measurements are technically executable:

### M1 — Rank and margin control

Measure dyad rank and margin per clip.

Purpose:

Determine whether useful dyad signal exists
before final-score combination.

### M2 — Thodi matched comparison

Compare Bhairavi and Thodi directly.

Use identical clip counts.

Use the repository's swara definitions.

Treat Thodi as the primary matched control.

### M3 — Direction-split dyads

Analyze ascending and descending transitions separately.

Do not average them before analysis.

Determine whether direction contains discriminatory information.

### M4 — Stability curve

Measure dyad-model stability across matched clip counts.

Use k = 2 through n where feasible.

Compare Bhairavi and strong ragas at matched k.

Do not invent a plateau threshold.

Do not claim H_DATA is proven.

### M5 — Normalized sharing

Compare raw and L2-normalized dyad models.

Separate magnitude effects from distributional overlap.

Do not treat either result as causal proof.

## Dropped measurement

Do not implement unrestricted subset search.

The previous formulation was invalid.

A high-dimensional subset search can produce
separation through chance at small sample sizes.

Do not reintroduce it without a new
held-out or permutation-controlled design.

## Required confounders

Explicitly check whether analysis can account for:

- clip count;
- token count;
- composition diversity;
- performer diversity;
- tonic quality;
- stable-note yield;
- direction;
- model magnitude;
- smoothing.

If a confounder cannot be controlled,
label the corresponding conclusion limited.

## Pre-registered interpretation limits

Phase 1-C may establish localisation.

It may show consistency with H_DATA.

It may show consistency with H_REP.

It may identify scoring interaction.

It may identify directional information.

It must not claim causal diagnosis without evidence.

It must not claim that adding data will fix recognition.

It must not claim that changing representation will fix recognition.

It must not modify production scoring based on results.

## Required output

Produce a concise audit report.

Use these headings exactly:

1. Verification Summary
2. Raw Dyad Count Availability
3. Directional Dyad Availability
4. Bhairavi Provenance Audit
5. Thodi Matched-Control Verification
6. Existing Scoring Verification
7. Phase 1-B Artifact Availability
8. Phase 1-C Executability
9. Blocking Issues
10. Recommended Execution Order
11. Interpretation Boundaries
12. Approval Required

For each finding classify it:

- VERIFIED FACT
- NOT ESTABLISHED
- UNKNOWN
- BLOCKED
- INFERENCE

Cite exact files and relevant lines.

## Stop condition

STOP after producing the audit.

Do not execute Phase 1-C.

Do not create Phase 1-C scripts.

Do not alter documentation.

Do not alter hypotheses.

Do not stage anything.

Do not commit anything.

Do not push anything.

If any prerequisite fails, explain precisely why.

If all prerequisites pass, report:

`PHASE 1-C READY FOR SEPARATE AUTHORIZATION`

Do not treat that statement as authorization.

## Governance

Follow the repository's CLAUDE.md.

Follow `.ai/agent_spec.md`.

Follow the existing Q-003 phase trail.

Do not bypass frozen methodology.

Do not resolve contradictions by guessing.

Do not convert inference into fact.

Do not silently repair documentation.

If evidence contradicts the proposed design,
stop and report the contradiction.

The purpose of this step is verification.

It is not experimentation.