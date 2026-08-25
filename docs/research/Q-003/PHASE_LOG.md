# Q-003 — Phase Log

**Gate question.** Is Bhairavi (14% LOO, the weakest raga) limited by
**representation** or by **dataset diversity**?

Candidate answers: `H_DATA` (dataset diversity), `H_REP` (representation),
`H_BOTH`, `H_UNRESOLVED`.

**Purpose of the gate.** Q-003 is a **diagnostic gate placed before any ML or
feature investment.** The goal is not higher accuracy. The goal is identifying
the bottleneck correctly. A phase that raises accuracy without identifying the
bottleneck has not satisfied this gate.

**Planned progression.**

```
Phase 0 → Phase 1-A → Phase 1-B → diagnosis → intervention
```

Phases are not renamed and not skipped. A phase does not advance without
explicit approval (`docs/START_HERE.md` → Phase transitions).

**This log is append-oriented.** Earlier phases are not rewritten. A later
correction is appended, with the original reasoning preserved.

Current state of the gate: see `PROJECT_STATUS.md` → Research Gates. That is the
authority; this log is the detailed record behind it.

---

## Phase 0 — Documentation provenance audit

**Date.** 2026-08-21. Committed `908dbaa` ("Q-003 Phase 0 closure: correct
unsupported causal and provenance claims").

**Objective.** Before measuring anything, establish what the repository already
claimed about Bhairavi's cause, and whether any of it was evidenced.

**Starting evidence.** `PROJECT_STATUS.md` recorded Bhairavi's cause as
UNPROVEN. Several other documents did not.

**Research questions.**
1. Does the repository already assert an answer to Q-003?
2. If so, is that assertion backed by an experiment?

**Methods.** Repository-wide documentation audit; provenance tracing of each
causal claim to an experiment, artifact or commit.

**Data examined.** Tracked documentation across `README.md`, `adr.md`,
`.ai-memory/`, `docs/`, `datasets/`, and `scripts/` headers.

**Results.**

- **FACT.** The repository asserted `H_DATA` ("needs more diverse clips") in
  **four** places **without an experiment behind it** — including `adr.md`
  ADR-013, which is a *locked* ADR.
- **FACT.** ADR-013's cited evidence was a LOO rerun. That rerun measured
  **accuracy**, not **cause**. The causal sentence did not follow from it.
- **FACT.** The historical Bhairavi–Thodi "78% overlap" figure was **not
  independently verifiable**: its original clip population and outputs were not
  preserved.
- **FACT (C-6, identified in this phase, corrected later — see Correction C-6
  below).** The documented canonical sink attribution "Saveri 6/14, Thodi 3/14,
  Kalyani 2/14" **sums to 11, not 14.**

**Verification.** Each corrected claim was re-traced to its cited artifact or
commit. Claims that could not be traced were marked unestablished rather than
deleted.

**Interpretation.** The repository had **quietly resolved Q-003's open question
toward `H_DATA`** through documentation drift rather than measurement. This is
the failure mode the gate exists to prevent, and it had already occurred inside
the gate's own subject matter.

**What was established.** That `H_DATA` was **asserted but never tested**.

**What remains unestablished.** Everything the gate asks. Phase 0 corrected the
record; it produced **no** evidence about Bhairavi's actual cause.

**Decision.** Phase 0 CLOSED. Four corrections committed (`908dbaa`). The
`H_DATA` assertions were downgraded to hypotheses with their history preserved —
ADR-013's text was annotated, not rewritten.

**Next permitted step.** Phase 1-A, on approval.

---

## Phase 1-A — PCD overlap diagnostic

**Date.** 2026-08-21. Committed `1ef479f`
(`scripts/sandbox_q003_bhairavi_pcd_diagnostic.py`).

**Objective.** Test the repository's standing assumption that Bhairavi fails
because its pitch-class distribution overlaps its confusers'.

**Starting evidence.** Documentation attributed Bhairavi's errors to PCD
similarity with Thodi (the unverifiable "78%" figure). The canonical confusion
matrix shows Bhairavi's 6 wrongs going to **Saveri 4, Thodi 2**.

**Research question.** Does mean-PCD overlap with a confuser predict which raga
absorbs Bhairavi's errors?

**Methods.** Leave-one-out per-clip evaluation reusing canonical functions
imported from `recognize_raga_v12.py` and `confusion_matrix_audit.py` — not
reimplemented. Overlap measured as histogram intersection over 72 normalised
bins, `Σ min(mean_PCD_a, mean_PCD_b)`, the same definition used by
`scripts/_diag_weak_ragas.py`. Intra-cluster dispersion measured as mean
distance to raga centroid.

**Verification.** The script self-validates against the canonical baseline
(10/10 checks) **before** emitting any diagnostic. Baseline reproduced:
**25C / 14W / 31U**, Bhairavi **1c / 6w / 4u**, confusers Saveri 4 / Thodi 2.

**Results.**

| Raga | mean-PCD overlap with Bhairavi | Bhairavi errors absorbed |
|---|---|---|
| Thodi | 0.7840 | 2 |
| Kalyani | 0.7487 | 0 |
| **Saveri** | **0.6782** | **4** |
| Shankarabharanam | 0.6752 | 0 |
| Abhogi | 0.6737 | 0 |
| Mohanam | 0.6593 | 0 |

Intra-cluster dispersion: **Bhairavi 0.0907 — the lowest (tightest) of all seven
ragas.** Saveri 0.2293 — the loosest.

**Interpretation.** The ordering is **inverted** with respect to the hypothesis.
Saveri has the *lowest* overlap of the six comparators and absorbs *two-thirds*
of Bhairavi's errors; Kalyani has higher overlap and absorbs none.

**What was established.**

- **FACT.** Mean-PCD overlap does **not** explain which raga absorbs Bhairavi's
  errors. The overlap hypothesis is **eliminated as the mechanism**.
- **FACT.** Bhairavi's clips form the **tightest cluster in the dataset.**

**What remains unestablished.** The actual mechanism. Eliminating overlap does
not identify what replaced it, and says nothing about `H_DATA` vs `H_REP`.

**Note on interpretation of dispersion.** Low dispersion is **consistent** with
the long-standing observation that Bhairavi's clips are acoustically similar. It
does **not** establish that adding diverse clips would fix the errors — that
inference requires knowing the mechanism, which this phase did not supply.

**Decision.** Phase 1-A CLOSED. Overlap eliminated.

**Next permitted step.** Phase 1-B, on approval.

---

## Phase 1-B — Weighted-channel diagnostic

**Date.** 2026-08-24. Script `scripts/sandbox_q003_phase1b_weighted_channels.py`.
Artifacts: `Q003 Bhairavi Diagnosis results/run_20260824_214001_phase1b/`
(gitignored). **Uncommitted at time of writing.**

**Objective.** With overlap eliminated, measure the two scoring channels
separately and determine which one fails Bhairavi.

**Starting evidence.** Phase 1-A's inverted ordering. Scoring combines a PCD
channel (weight 0.8) and a directional-dyad channel (weight 0.2), and Phase 1-A
measured only *unweighted* PCD overlap — not what the scorer actually uses.

**Research questions.** The five candidate mechanisms specified for this phase:

- **A.** weighted PCD magnitude
- **B.** weighted PCD similarity
- **C.** dyad structure
- **D.** structural subset absorption (Saveri's swara set ⊂ Bhairavi's)
- **E.** no clear mechanism

**Methods.** Per-clip LOO using existing captured features. Measured, per
channel: IDF×Variance-weighted PCD similarity; weighted PCD L2 norms; dyad
similarity; dyad model L2 norms; per-clip **channel ranks** (which raga each
channel ranks first, independently of the other); relationship to incoming error
counts. **No production code or dataset was modified. No threshold was
introduced. No fix was implemented.**

**Verification.** Canonical baseline reproduced before interpretation:
**25C / 14W / 31U**, Bhairavi **1c / 6w / 4u**, confusers Saveri 4 / Thodi 2.

**Results.**

Channel measurements against Bhairavi's clips:

| Raga | wPCD sim | dyad sim | wPCD L2 | dyad L2 | unw. overlap | incoming errors |
|---|---|---|---|---|---|---|
| **Bhairavi** | **0.020005** | 0.004944 | 0.14294 | 0.10767 | — | 0 |
| Saveri | 0.019748 | **0.006243** | **0.15986** | **0.18977** | 0.6782 | 8 |
| Thodi | 0.019513 | 0.005528 | 0.14453 | 0.13919 | 0.7840 | 4 |
| Kalyani | 0.017924 | 0.003109 | 0.14994 | 0.12126 | 0.7487 | 2 |
| Abhogi | 0.017372 | 0.002347 | 0.14593 | 0.10115 | 0.6737 | 0 |
| Mohanam | 0.016587 | 0.002024 | 0.14237 | 0.08674 | 0.6593 | 0 |
| Shankarabharanam | 0.016151 | 0.002793 | 0.14309 | 0.13006 | 0.6752 | 0 |

Per-clip channel ranks — how often each channel ranks the **true** raga first:

| Raga | clips | PCD ranks true #1 | dyad ranks true #1 |
|---|---|---|---|
| **Bhairavi** | 11 | 4 | **0** |
| **Abhogi** | 7 | 3 | **0** |
| Kalyani | 14 | 9 | 10 |
| Thodi | 11 | 7 | 7 |
| Saveri | 8 | 7 | 6 |
| Shankarabharanam | 9 | 5 | 4 |
| Mohanam | 10 | 1 | 2 |

Established facts from these measurements:

- **FACT.** The dyad channel ranks Bhairavi first in **0 of its own 11 clips.**
  Its top pick across those clips is **Saveri 8, Thodi 2, Kalyani 1.**
- **FACT.** Abhogi — the second-weakest raga — shows the **identical 0/7
  signature.** These are the only two ragas with zero dyad-first clips.
- **FACT.** On weighted PCD similarity Bhairavi ranks **1st** (0.020005 vs
  Saveri 0.019748). On dyad similarity it ranks **3rd**, behind Saveri and Thodi.
- **FACT.** In 4 of 11 clips the PCD channel ranks Bhairavi first while the dyad
  channel ranks it 2nd–3rd. **Three of those four end UNKNOWN** — the dyad
  channel pulls otherwise-correct clips below the decision margin.
- **FACT.** IDF×Variance weighting substantially flattens the PCD magnitude
  disparity: raw mean-PCD L2 Saveri/Bhairavi **2.2×** → weighted **1.12×**. The
  dyad channel receives no comparable correction and remains at **1.76×**.

Rank correlations against incoming error counts (n = 6; Bhairavi excluded
because self-overlap is undefined):

| Measure | ρ |
|---|---|
| weighted PCD similarity | +0.941 |
| dyad similarity | +0.941 |
| dyad model L2 | +0.820 |
| unweighted overlap | +0.759 |
| weighted PCD L2 | +0.698 |

**These are directional descriptions only. They are NOT significance tests.** At
n = 6 they do not discriminate between measures, and no discriminating claim is
made from them. The discriminating evidence in this phase is the channel-rank
table, not these coefficients.

**Interpretation.**

| | Mechanism | Verdict |
|---|---|---|
| A | weighted PCD magnitude | **NOT SUPPORTED as framed.** Weighting removes most of the PCD magnitude gap. A magnitude effect survives only on the **dyad** side (1.76×) — a different claim from the one originally proposed. |
| B | weighted PCD similarity | **NOT SUPPORTED.** Bhairavi ranks 1st on its own clips. PCD similarity is not what breaks Bhairavi. |
| C | dyad structure | **SUPPORTED — strongest of the five.** |
| D | structural subset absorption | **NOT ESTABLISHED.** Saveri ⊂ Bhairavi is real per the repository's own swara definitions and is consistent with C, but nothing here separates subset structure from dyad magnitude. Untested. |
| E | no clear mechanism | **Rejected** — a mechanism was localised. |

**What was established.**

- **FACT.** The failure **localises to the dyad channel.**
- **FACT.** PCD similarity is **not** the mechanism. This closes an assumption
  the repository had carried for a long time.

**What remains unestablished — and this is the important part.**

**Phase 1-B is NOT a diagnosis.** It established *where* in the representation
the failure appears. It did **not** establish *why*, and it did **not** answer
the gate.

`H_DATA`, `H_REP` and `H_BOTH` all remain live. Localising to the dyad channel
is compatible with every one of them. At least four explanations remain
**distinguishable open questions**, none of them tested:

1. **Insufficient dyad information in the data** — Bhairavi's clips may not
   exercise enough distinct transitions (would favour `H_DATA`).
2. **Dyad representation limitations** — the directional-dyad feature may be
   unable to express what distinguishes Bhairavi (would favour `H_REP`).
3. **Transition distribution differences** — Bhairavi's transitions may be
   genuinely shared with Saveri and Thodi rather than missing.
4. **Scoring interactions** — the 0.8/0.2 combination, normalisation, or margin
   rules may convert a small dyad deficit into a decision failure.

**These are hypotheses. None is a diagnosis. None may be documented as a cause.**

One inference worth recording, explicitly labelled: Bhairavi's clips form the
tightest cluster in the dataset (Phase 1-A), which weighs **mildly** against a
pure data-incoherence account. **INFERENCE, not fact**, and not sufficient to
discriminate 1 from 2.

**Decision.** Phase 1-B analysis COMPLETE. **No intervention authorised.** No
production code, scoring weight, dataset or threshold changed.

**On BUG-010 (hubness).** Deliberately **not reopened** in this phase.
Rationale: BUG-010 proposes a general correction at the **score** level, while
Phase 1-B localises the problem to the **dyad channel** specifically. Applying a
general correction to a specific, unconfirmed finding would obscure the
mechanism rather than identify it. Recorded for context: BUG-010 was parked
2026-03-12, **before Saveri was activated on 2026-03-31** — it has never been
evaluated against the current confuser set. Reopening remains a decision for
after the mechanism is confirmed.

**Next permitted step.** None taken automatically. The natural candidate is a
**dyad-channel diagnostic** — characterising whether Bhairavi's dyad matrix is
sparse, diffuse, or dominated by transitions shared with Saveri and Thodi, which
would separate explanation 1 from explanation 2 and therefore `H_DATA` from
`H_REP`. **This requires explicit approval before it begins.**

---

## Corrections

Corrections are appended here. Earlier phase text above is left intact.

### Correction C-6 — canonical sink attribution (2026-08-24)

**Identified.** Phase 0. **Corrected.** 2026-08-24.

The documented canonical sink attribution read *"Saveri = 6/14 wrongs,
Thodi = 3/14, Kalyani = 2/14"* — which sums to **11, not 14**.

Recomputed by independent parse of the canonical confusion matrix
(`confusion_matrix_audit.py`, Scenario 1):

| | Documented | Actual |
|---|---|---|
| Saveri | 6/14 | **8/14** |
| Thodi | 3/14 | **4/14** |
| Kalyani | 2/14 | 2/14 |
| **Sum** | **11 ✗** | **14 ✓** |

Only the **sink attribution** was wrong; it **understated Saveri's dominance**.
The C/W/U totals (25/14/31, 64.1%) were unaffected and were independently
reproduced.

The error had propagated to three locations: `.ai-memory/datasets.md:305`,
`.ai-memory/architecture.md:140`, and `PROJECT_STATUS.md:77`. All three
corrected; the original wording is preserved in the correction note at
`.ai-memory/datasets.md:307`.

**Bearing on the gate.** The correction **strengthens** Phase 1-A's finding
rather than altering it: Saveri absorbs a larger share of all errors than
documented, while having the *lowest* mean-PCD overlap with Bhairavi.
