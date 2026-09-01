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

## Phase 1-C — Dyad-channel diagnostic

**Date.** 2026-08-25. Script `scripts/sandbox_q003_phase1c_dyad_channel.py`
(committed `9b1dd6d`, sha256
`4d4b0c9d58090744b5e3dee37f42cc63a881357474c2caf5783c933ff7710ada`).
Artifacts: `Q003 Bhairavi Diagnosis results/run_20260825_202704_phase1c/`
(gitignored). Run recorded `git_commit 18b1eaf`. Independently verified
2026-08-25 in a separate read-only gate.

**Objective.** With overlap eliminated (1-A) and the failure localised to the
dyad channel (1-B), determine *why* the dyad channel fails weak ragas.

**Starting evidence.** Phase 1-B: dyad ranks Bhairavi #1 in 0 of 11 of its own
clips; Abhogi 0 of 7; weighted PCD ranks Bhairavi #1. Phase 1-A: mean-PCD
overlap eliminated as the mechanism.

**Research questions.** Five hypotheses, kept strictly separate and none
selected by the run: `H_DATA`, `H_REP`, `H_SHARED-measured`,
`H_SHARED-intrinsic`, `H_SCORE`.

**Methods.** LOO over the canonical 70 clips, models built in memory from
`pcd_results/features_v12/`. Scoring arithmetic imported from
`recognize_raga_v12.py` or mirrored from `confusion_matrix_audit.py:129-148`.
Raw pre-smoothing dyad counts recovered by replicating
`aggregate_all_v12.py:53-105` and reading the matrices before `+= ALPHA`.
Executed in the authorised order **M1 -> M3 -> M2 -> M5 -> M4**. No production
code, dataset or feature cache touched; no subset search; no threshold, weight
or methodology change. The three stale 2026-01-05 `*_dyad_stats.npz` artifacts
were ignored.

**Verification.** Canonical baseline **REPRODUCED**, 10/10 checks, before any
interpretation: 70 clips, 25c/14w/31u; Bhairavi 11 clips 1c/6w/4u; Bhairavi to
Saveri 4, Bhairavi to Thodi 2. Raw-count replication **PASS on all 70 clips**
(every reconstructed matrix reproduces the production vector after smoothing
and normalisation).

### Results

**M1 — per-channel dyad rank and margin.** Bhairavi dyad #1 = **0 of 11**
(median rank 3.0, median gap 0.001168, gap/top 0.2014). Abhogi 0 of 7 (median
rank 4.0). Thodi 7 of 11 (median rank 1.0).

**M3 — ascending vs descending.** Bhairavi up #1 = **0/11**, down #1 =
**0/11**. Thodi up 8, down 7. Model directional asymmetry is near-uniform
across all seven ragas (0.9707–0.9933; Bhairavi 0.9819, Thodi 0.9886).
**No direction rescues Bhairavi**; the failure is not directional, and the
N3-in-avarohana conjecture is NOT supported.

**M2 — Thodi matched control (n = 11 each).**

| Metric | Bhairavi | Thodi |
|---|---|---|
| correct / wrong / unknown | 1 / 6 / 4 | 5 / 2 / 4 |
| PCD #1 | 4 | 7 |
| dyad #1 | **0** | **7** |
| up #1 / down #1 | 0 / 0 | 8 / 7 |
| cosine-dyad #1 | **8** | **5** |
| median transitions | **253** | 233 |
| median stable notes | **335** | 290 |
| median distinct dyads up / down | **66 / 82** | 60 / 59 |
| model L2 up / down | 0.0792 / 0.0728 | 0.0989 / 0.0978 |

Metadata coverage is also matched: both 5 of 11 clips Saraga-verified, both
4 distinct verified works.

**M5 — raw vs L2-normalised dyad sharing.** Cosine on identical models moves
channel leadership: Bhairavi **0 to 8** (+8), Abhogi 0 to 1, Mohanam 2 to 3,
Shankarabharanam 4 to 4, Kalyani 10 to 9, Saveri 6 to 5, Thodi 7 to 5.
Across Bhairavi's clips the dyad leader shifts from `Saveri 8, Thodi 2,
Kalyani 1` to `Bhairavi 8, Saveri 2, Kalyani 1`. Dyad model concentration
(L2 of the L1-normalised model, ascending): **Saveri 0.1377** highest of seven,
**Bhairavi 0.0792** — a **1.74x** ratio. Bhairavi's largest dyad overlap is
with **Thodi** (up 0.6695 / down 0.6393), not Saveri (0.5470 / 0.5171).

**M4 — stability curve, DESCRIPTIVE EVIDENCE ONLY.** Mean cosine distance of a
k-clip model to the k-clip centroid, 100 draws, seed 0. Bhairavi vs Thodi:
k=2 0.2312/0.1679, k=4 0.1058/0.0757, k=6 0.0517/0.0395, k=8 0.0255/0.0183,
k=10 0.0069/0.0052. Bhairavi is less stable than Thodi at every matched k but
mid-pack overall and **more stable than Kalyani**, which achieves 10/14.
**No plateau criterion was invented or applied. M4 did not determine any
diagnosis and is not used to establish `H_DATA`.**

### The wrong / UNKNOWN split — the phase's central result

Bhairavi's 11 clips resolve as **1 correct, 6 wrong, 4 UNKNOWN**. These were
analysed separately and must never be pooled.

**FACT — the dyad channel explains 0 of the 6 wrong classifications.** In
**all 6 of 6** wrong clips `pcd_top` equals the raga that actually won
(Saveri 4, Thodi 2). The error decomposition gives drivers `pcd (both +)` 7,
`dyad` 3 — no wrong clip is dyad-driven. **The PCD channel independently
selects every wrong winner.**

**FACT — the dyad channel explains 3 of the 4 UNKNOWNs.** In
`Bhairavi_clean_2`, `_4` and `_6` the PCD channel ranks Bhairavi first and the
dyad channel pulls the combined margin below `MIN_MARGIN_FINAL` (margins
0.000813, 0.000107, 0.000003). The fourth UNKNOWN (Kamakshi, Sanjay
Subrahmanyan) differs in kind: PCD rank 4, dyad rank 6, `pcd_top` Abhogi —
both channels fail.

**FACT.** Splitting cosine rank by outcome: correct 1/1, **wrong 6/6**,
**unknown 1/4**. Normalisation's channel-level benefit falls predominantly on
the wrong clips. This does **not** establish that any classification would
change — only channel ranks were measured.

### What was established

1. **FACT.** The dyad failure is **not** a transition-data shortage: against an
   exactly matched control Bhairavi has more transitions, more stable notes and
   more distinct dyads in both directions, and still ranks first zero times.
2. **FACT.** The dyad failure is **not** directional (0/11 both ways).
3. **FACT.** The dyad **representation carries** discriminating information —
   8 of 11 under cosine on identical models.
4. **FACT.** Saveri's dyad-channel dominance over Bhairavi is largely a
   **model-concentration artifact** (1.74x), removed by L2 normalisation.
5. **FACT.** Production dyad similarity is an unnormalised dot product
   (`recognize_raga_v12.py:211-214`) and receives **no IDF x Variance
   weighting**, unlike PCD. It rewards concentration.
6. **FACT.** The dyad channel drives 3 of 11 Bhairavi outcomes, all UNKNOWN.

### What remains unestablished

- **NOT ESTABLISHED.** That normalisation would change any classification.
  Only channel ranks were measured; no end-to-end accuracy was computed.
- **UNKNOWN.** Margins under cosine — per-clip cosine values were not written
  to any artifact and are unrecoverable without a rerun.
- **NOT ESTABLISHED — the largest open gap.** Any mechanism for Bhairavi's
  **6 wrong answers**. Phase 1-A eliminated PCD *overlap*; Phase 1-C shows PCD
  nonetheless selects all six winners. Nothing explains them.
- **NOT ESTABLISHED.** Whether Bhairavi's clips are compositionally redundant.
- **NOT ESTABLISHED.** `H_SHARED-intrinsic` — untestable with existing features.
- **NOT ESTABLISHED.** Generalisation to Abhogi: Abhogi gains only +1 under
  cosine versus Bhairavi's +8, so its 0/7 has a different character.

### Hypothesis status

| Hypothesis | Status |
|---|---|
| `H_SCORE` | **SUPPORTED — for UNKNOWNs only.** Not supported for wrong answers |
| `H_SHARED-measured` | **SUPPORTED** — measured sharing tracks concentration, not shape |
| `H_REP` | **WEAKENED** — the information is present in the models |
| `H_DATA` | **WEAKENED at the transition level; NOT ESTABLISHED at the diversity level** |
| `H_SHARED-intrinsic` | **NOT ESTABLISHED** |

### Limitations

1. **6 of 11 Bhairavi clips (`Bhairavi_clean_1..6`) have no recoverable
   composition, performer or source identity.** Composition and performer
   diversity are NOT controlled; every statement about redundancy is limited.
2. n = 11. Differences of 1–3 clips are not statistically meaningful. No
   significance test was performed or is claimed. All comparisons descriptive.
3. The swara table underpinning the Bhairavi/Thodi pairing lives in a rejected
   experiment's sandbox (`sandbox_absent_swara_v2.py:70-78`) and is a
   repository working definition, not an established musicological fact.
4. Tonic quality was not independently validated.
5. `sandbox_q003_phase1c_dyad_channel.py:69` redeclares `MIN_STABLE_FRAMES = 5`
   instead of importing it — an ADR-015 violation. The value is correct and no
   result is affected. Preserved deliberately so executed experiment code is
   not altered retroactively; recorded as follow-up technical debt.

### Decision

**Phase 1-C COMPLETE and independently verified. No intervention authorised.**
No production code, scoring weight, dataset or threshold changed. BUG-010 was
not reopened.

**Phase 1-C does NOT establish the root cause of Bhairavi's failure.** It
resolves the mechanism behind 3 of 10 failures and leaves the mechanism behind
the 6 wrong answers entirely unexplained.

**`Q-003` remains INCONCLUSIVE.** `H_DATA`, `H_REP`, `H_SHARED-measured`,
`H_SHARED-intrinsic` and `H_SCORE` remain distinct; no diagnosis is selected.

### Next permitted step

**Phase 1-D requires a redesigned, scale-controlled test and separate
authorisation.** A naive substitution of cosine for the dot product is
**invalid**: raw dyad similarities span 0.0014–0.0094 while weighted PCD
similarities are ~0.016–0.020, so the dyad channel currently contributes
roughly 2–12% of score magnitude. Cosine is order 0.1–1.0 — roughly 100x
larger. Substituting it at `DYAD_WEIGHT = 0.2` would test **re-weighting
confounded with normalisation**, not normalisation.

A corrected design has been drafted and approved in principle: **C1** current
production baseline (must reproduce 25/14/31), **C2** cosine at matched
cross-raga spread, **C3** naive cosine as a diagnostic control that is
**never a promotion candidate**; outcomes stratified correct / wrong / UNKNOWN.

**Phase 1-D is diagnostic only. ADR-005 blocks production promotion at the
current dataset size** — its revisit gate requires 15-20+ clips per raga and
Bhairavi has 11 — so even a positive result becomes research evidence, not an
engine change.

**Phase 1-D has NOT been executed.**

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

### Correction C-7 — Phase 1-B script provenance status (2026-08-26)

**Identified.** 2026-08-26. **Corrected.** 2026-08-26, by appending this note.

Phase 1-B above records at line 156:

> *"(gitignored). **Uncommitted at time of writing.**"*

**That statement was historically accurate.** When Phase 1-B was written on
2026-08-24, `scripts/sandbox_q003_phase1b_weighted_channels.py` was genuinely
untracked, and the entry correctly disclosed it rather than implying the run
was pinned.

**It is no longer current.** On 2026-08-26 the script was committed in
**`9b1dd6d`** ("Q-003: commit Phase 1-B and Phase 1-C sandbox scripts
(provenance pinning)"), together with the Phase 1-C script. Both were committed
**as-is**, byte-identical to the versions that produced their artifacts:

| Script | sha256 |
|---|---|
| `sandbox_q003_phase1b_weighted_channels.py` | `dafe718e6739e416ddee0cc38f8eef199392f6299dd69fdf4c483e10c2488e40` |
| `sandbox_q003_phase1c_dyad_channel.py` | `4d4b0c9d58090744b5e3dee37f42cc63a881357474c2caf5783c933ff7710ada` |

Provenance was verified before committing: both scripts' modification times
precede their own artifacts (Phase 1-B by 10 s, Phase 1-C by 3 s), so neither
was altered after its run.

**The later commit does not alter Phase 1-B's results.** Committing an existing
file changes only its tracking status. Every measurement, table and count in
the Phase 1-B entry above stands unchanged, and the artifacts in
`Q003 Bhairavi Diagnosis results/run_20260824_214001_phase1b/` are untouched.

**No methodology and no interpretation changed.** Nothing in Phase 1-B was
re-run, re-derived, or re-read. The original text is left exactly as written,
per the append-only rule.

**Bearing on the gate.** None. This is a provenance-tracking correction only.
Its sole effect is that Phase 1-B's analysis code is now reconstructible from
the repository, closing the reproducibility gap that the original note
honestly disclosed.

### Correction C-8 — Phase 1-D design superseded by design audit (2026-09-01)

**Identified.** 2026-09-01, during a read-only Phase 1-D design audit.
**Corrected.** 2026-09-01, by appending this note.

Phase 1-C's "Next permitted step" above records:

> *"A corrected design has been drafted and approved in principle: **C1**
> current production baseline (must reproduce 25/14/31), **C2** cosine at
> matched cross-raga spread, **C3** naive cosine as a diagnostic control..."*

**That was accurate when written.** A subsequent design audit found **C2 as
described is defective**, and the design has been revised.

**Why.** Cosine divides by *two* norms, not one:

| Factor | Effect on dyad rank | Effect on the combined score |
|---|---|---|
| model norm `‖m_r‖` — varies per raga | **rank-changing** — this is the mechanism | yes |
| clip norm `‖x‖` — constant across ragas within a fold | **rank-neutral** | **yes — rescales the channel per clip** |

Phase 1-C's 8/11 result is attributable **entirely** to the model-norm term; the
clip-norm term contributed nothing to it. But Phase 1-D measures *decisions*,
and `MARGIN_STRICT` (0.003) and `MIN_MARGIN_FINAL` (0.001) are **absolute**
thresholds. The clip-norm term would rescale each clip's dyad contribution
against those fixed cutoffs — a per-clip effect that played no part in the
finding being tested. Full cosine therefore conflates the mechanism with an
irrelevant rescaling, which is the exact class of confound the redesign was
commissioned to remove.

**Required corrections, both folded into the plan:**

- **F1** — C2 must be **model-norm-only**:
  `γ · 0.5·(dot(x_up, m_up/‖m_up‖) + dot(x_dn, m_dn/‖m_dn‖))`.
- **F2** — Phase 1-D must **import** `MIN_STABLE_FRAMES` from
  `recognize_raga_v12.py:27` rather than redeclare it (ADR-015, ACTIVE/locked).

**Two further audit findings, recorded because they change how the design is
read rather than what it does:**

- **C2 and C3 produce identical dyad-channel rankings** (γ is a positive global
  scalar and ranks are scale-invariant). C3 is therefore not an independent
  normalisation result. The real factorisation is **C1→C2 = normalisation at
  matched influence** and **C2→C3 = pure effective weight at fixed
  normalisation** — an orthogonal decomposition, and the design's main strength.
- **C0 = PCD-only** was added as an effect ceiling. `L-045` swept 0.6/0.4,
  0.7/0.3 and 0.8/0.2 but never tested PCD-only, so it is new information: if
  C0 ≈ C1, the dyad channel is nearly inert at weight 0.2 and no dyad-side
  change can exceed that difference.

**Bearing on the gate.** None on any Phase 0/1-A/1-B/1-C result. This is a
correction to a **forward-looking design**, not to evidence. No measurement,
table or count above is affected, and the Phase 1-C text is left exactly as
written per the append-only rule.

**Where the current design lives.** `docs/research/Q-003/RESEARCH_PLAN.md`.
That file supersedes the C1/C2/C3 sketch quoted above. **Phase 1-D remains
NOT AUTHORISED and NOT EXECUTED.**
