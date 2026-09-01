# Q-003 — Research Plan

**Gate question.** Is Bhairavi (14% LOO, the weakest raga) limited by
**representation** or by **dataset diversity**?

**Purpose.** Q-003 is a diagnostic gate placed **before** any ML or feature
investment. The goal is not higher accuracy; it is identifying the bottleneck
correctly.

**Status of the gate: ACTIVE — UNANSWERED.** Current state is owned by
`PROJECT_STATUS.md` → Research Gates. The detailed phase record is
`docs/research/Q-003/PHASE_LOG.md`. This document holds **methodology for the
next phase only**; it does not restate results.

> **Why this file exists.** `CLAUDE.md` §4a places "the active research plan" at
> level 3 of the source-of-truth hierarchy. Q-003 had no such document — its
> plan lived in successive external directives, which meant it did not survive
> between sessions. Recorded as finding **H-2** in
> `docs/repository-consistency-audit.md`. This file closes that gap.

---

## Phase 1-D — pre-registration (DESIGNED, AUDITED, **NOT EXECUTED**)

**Question.** Does normalised dyad similarity materially change **recognition**
— not channel rank — when its influence on the score is held constant?

**Authorisation status: NOT AUTHORISED.** Designed and design-audited. Two
required corrections (F1, F2 below) were identified by the audit and are folded
into the design as written here. Execution needs separate, explicit approval.

### Starting evidence

From verified Phase 1-C (`run_20260825_202704_phase1c/`, commit `18b1eaf`):

- dyads explain **3 of 4** Bhairavi UNKNOWNs and **0 of 6** wrong answers;
- `pcd_top` equals the winner in **6/6** wrong clips;
- cosine moves Bhairavi **0/11 → 8/11** channel leadership, Saveri 8/11 → 2/11;
- **per-clip cosine values and margins were not captured** and are unrecoverable
  without a rerun.

### Hypotheses

Kept strictly separate. None is selected by this phase.

| | Hypothesis |
|---|---|
| `H_SCORE-practical` | The dyad channel's information loss is a scoring artifact that **materially changes classifications** when corrected at matched influence |
| `H_SCORE-cosmetic` | The channel reordering is real but too small at `DYAD_WEIGHT = 0.2` to change decisions |
| `H_TRADE` | Normalisation redistributes error — Bhairavi improves, other ragas degrade |

`H_DATA`, `H_REP`, `H_SHARED-measured` and `H_SHARED-intrinsic` are **not under
test here**; their status carries forward from Phase 1-C unchanged.

### The scale problem this phase exists to avoid

Raw dyad similarities span **0.0014–0.0094**; weighted PCD similarities are
**~0.016–0.020**. At `DYAD_WEIGHT = 0.2` the dyad channel contributes roughly
**2–12%** of score magnitude. Cosine similarities are order **0.1–1.0** —
roughly **100× larger**.

**Substituting cosine at the unchanged weight would test re-weighting
confounded with normalisation, not normalisation.**

### Experimental conditions

| | Condition | Dyad similarity | Weight | Role |
|---|---|---|---|---|
| **C0** | PCD ONLY | — | `DYAD_WEIGHT = 0` | **Effect ceiling.** Bounds the entire phase |
| **C1** | BASELINE | `0.5·(dot(x_up, m_up) + dot(x_dn, m_dn))` | 0.2 | Production. **Must reproduce 25c/14w/31u** |
| **C2** | MODEL-NORM, MATCHED | `γ · 0.5·(dot(x_up, m_up/‖m_up‖) + dot(x_dn, m_dn/‖m_dn‖))` | 0.2 | **Primary test** |
| **C3** | MODEL-NORM, NAIVE | same as C2 with `γ = 1` | 0.2 | **Control only. NEVER a promotion candidate** |

**What C1 → C2 → C3 decomposes into.** Because ranks are invariant under
multiplication by a positive scalar, **C2 and C3 produce identical dyad-channel
rankings**. Therefore:

- **C1 → C2** = the normalisation effect, at matched channel influence
- **C2 → C3** = the pure effective-weight effect, at fixed normalisation

That is an orthogonal factorisation, and it is the design's main strength.

**C3 and L-017.** C3 knowingly reproduces the dyad-heavy configuration L-017
rejected ("Don't increase dyad weight until training data is sufficient —
15-20 clips minimum"). It is a control that quantifies the confound C2 removes.
It must never be read as a tested candidate.

### Scale-control method (pre-registered formula)

What moves rankings is not a channel's magnitude but its **spread across
candidate ragas within a fold**.

```
For LOO fold f over the 7 candidate ragas r:
    S_raw(f) = std_r[ d_raw(f, r) ]
    S_nrm(f) = std_r[ d_nrm(f, r) ]

    γ = mean_f[ S_raw(f) ] / mean_f[ S_nrm(f) ]     ← one global scalar
```

- γ is computed deterministically from all 70 folds **before any accuracy is
  computed**, so it cannot be tuned to an outcome.
- It equalises the dyad channel's mean cross-raga spread between C1 and C2 —
  matched influence on score *differences*.
- **PCD, weights, margins, `ALPHA` and every production parameter are
  untouched.** `DYAD_WEIGHT` stays 0.2.
- γ's value must be reported.

**Pre-registered sensitivity variants** (reported, not separate conditions):
per-fold `γ(f) = S_raw(f)/S_nrm(f)`, and the same matching using `max−min`
instead of `std`. Both named now so neither is a post-hoc choice.

### Required corrections from the design audit

| | Change | Status |
|---|---|---|
| **F1** | **C2 must be model-norm-only, not full cosine.** Full cosine divides by `‖m_r‖` (per-raga, rank-changing — the mechanism) **and** by `‖x‖` (constant across ragas, rank-neutral, but it rescales the channel per clip against the **absolute** thresholds `MARGIN_STRICT`/`MIN_MARGIN_FINAL`). Phase 1-C's 8/11 is attributable **entirely** to the model-norm term; the clip-norm term played no part in it and would contaminate an end-to-end measurement | **REQUIRED — folded in above** |
| **F2** | Import `MIN_STABLE_FRAMES` from `recognize_raga_v12.py:27` rather than redeclaring it. ADR-015 is **ACTIVE, locked**; the Phase 1-C script violated it at line 69 and that violation is preserved for provenance, but Phase 1-D must not repeat it | **REQUIRED** |
| **F3** | Capture per-clip **values**, not only ranks — all conditions, all seven ragas, plus per-clip margins, γ, and per-fold `S_raw`/`S_nrm`. Closes the Phase 1-C gap | **REQUIRED** |
| **F4** | Consider matching on the **decision-relevant** statistic. The decision rule consumes top1−top2 of the combined score and the dyad channel enters additively, so its decision-relevant contribution is its own top1−top2 gap, not its σ across all seven ragas | **RECOMMENDED** |
| **F5** | Add **C0 = PCD only**. `L-045` swept 0.6/0.4, 0.7/0.3 and 0.8/0.2 but **never tested PCD-only**, so this is new information and it bounds the phase: if C0 ≈ C1 the dyad channel is nearly inert at weight 0.2 and no dyad-side change can exceed that difference | **RECOMMENDED — folded in above** |

### Free correctness check the design must exploit

A model-norm-only C2 **must reproduce Phase 1-C's dyad ranks exactly**:

```
Bhairavi 8/11 · Thodi 5/11 · Kalyani 9/14 · Saveri 5/8
Shankarabharanam 4/9 · Mohanam 3/10 · Abhogi 1/7
```

If it does not, the implementation is wrong. See Stop condition 3.

### Metrics

**Per clip, per condition:** dyad similarity for all 7 ragas; dyad rank of the
true raga; dyad leader; final score per raga; final margin; tier; predicted;
outcome.

**Aggregate:** C/W/U per raga and overall, every condition.

**Bhairavi-specific:** C/W/U; dyad rank distribution; dyad leader distribution.

**Saveri attraction, specifically:** Bhairavi clips where Saveri leads the dyad
channel; Bhairavi wrongs predicted Saveri; Saveri's total incoming errors.

**Alternative-explanation test.** Report **delta versus concentration rank**.
Dividing by `‖m_r‖` could simply install a diffuse-favouring prior with Bhairavi
incidentally diffuse. Phase 1-C's own numbers argue against it — concentration
ascending is Mohanam 0.0602 < Abhogi 0.0700 < **Bhairavi 0.0792** < Kalyani
0.0847 < Shankarabharanam 0.0912 < Thodi 0.0989 < Saveri 0.1377, while deltas
are Mohanam +1, Abhogi +1, **Bhairavi +8**, Kalyani −1, Shankarabharanam 0,
Thodi −2, Saveri −1. **Not monotone in diffuseness.** This must be reported
explicitly; it is the strongest available discriminator between "corrects a
distortion" and "changes the prior".

**Optional:** dyad discrimination ratio per raga per condition, using the
repository's own definition (`L-026`: self-similarity ÷ mean-other-similarity;
>1.5× useful, >2× strong). Bears on ADR-005's revisit gate, which is closed
regardless.

**Reported constants:** γ, mean `S_raw`, mean `S_nrm`.

### Outcome stratification

**correct / wrong / unknown reported separately and never pooled** — overall,
per raga, and for Bhairavi. Plus a **condition transition matrix**: every clip
that changes category, with direction.

**Pre-registered primaries:** Bhairavi and the 70-clip overall. Everything else
is context. With 4 conditions × 7 ragas × 3 outcome categories the over-reading
risk is real and no significance test is available to restrain it.

### Controls

1. **C1 must reproduce the canonical baseline exactly** — 25c/14w/31u; Bhairavi
   1/6/4; Saveri 4 / Thodi 2 (`evaluation-protocol.md` §7b).
2. Raw-count replication check, as Phase 1-C (`np.allclose` on all 70 clips).
3. **All seven ragas reported**, not only Bhairavi — Phase 1-C showed
   normalisation *costs* Thodi (−2), Kalyani (−1), Saveri (−1) at channel level.
4. Thodi retained as the n=11 matched control.

### Confounds — stated, not solved

1. **Intrinsic and unavoidable:** normalisation changes the channel's *geometry*,
   not only its scale. Scale can be matched; geometry cannot. This phase isolates
   "normalised vs not, at matched influence" — the closest achievable to the
   question, **not** a clean decomposition.
2. γ is data-derived. The pre-registered formula prevents tuning; it remains
   data-dependent.
3. A global γ over- or under-matches individual folds. The per-fold sensitivity
   check bounds this; it does not remove it.
4. **Bhairavi provenance: 6 of 11 clips (`Bhairavi_clean_1..6`) have no
   recoverable composition, performer or source identity.** Carried forward.
5. **n = 11. A change of 1–3 clips is not statistically meaningful.** No
   significance test is available or claimed. Every comparison is descriptive.
6. LOO's one-fewer-clip disadvantage for the true raga is identical across
   conditions — it cancels in the comparison, not in absolute figures.

### Interpretation matrix — fixed before execution

| Bhairavi C2 vs C1 | Overall (70 clips) C2 vs C1 | Reading |
|---|---|---|
| improves | improves or flat | **`H_SCORE-practical` supported.** A candidate correction — still requires its own ADR and separate authorisation |
| improves | degrades | **`H_TRADE` supported.** Not a fix; error redistribution |
| unchanged | any | **`H_SCORE-cosmetic` supported.** Channel reordering does not survive to decisions |
| degrades | any | **Contradicts the Phase 1-C channel finding. Report the contradiction; do not rationalise it** |

**C3 is read only as** the magnitude of the confound the matching removed. Never
as a result about normalisation.

**Fixed non-inferences:**

- No rank change may be called causal.
- No accuracy claim without the end-to-end numbers.
- **Phase 1-D may observe changes among the six wrong clips but may not diagnose
  why PCD selects Saveri/Thodi.** That is a separate unresolved question. The
  tension is real — cosine ranks Bhairavi #1 in 6/6 wrong clips, so movement
  there is possible; movement is an observation, not an explanation.
- **No production change follows from Phase 1-D alone.** See ADR-005 below.

### Stop conditions

1. C1 fails to reproduce the canonical baseline → **STOP**, emit nothing
   interpretive.
2. Raw-count replication fails on any clip → **STOP**.
3. **C2's dyad ranks do not reproduce Phase 1-C's** (Bhairavi 8/11 etc.) →
   **STOP**; the implementation is wrong.
4. `S_nrm(f) ≈ 0` in any fold, making γ degenerate → **STOP** and report.
5. Any production, dataset, feature-cache or artifact file shows modified →
   **STOP**.
6. Regardless of outcome: **report and stop.** No promotion, no production edit,
   no documentation edit without separate authorisation.

### ADR-005 forecloses promotion regardless of outcome

`adr.md` ADR-005 is **ACTIVE**, and its revisit gate reads:

> *"Revisit when per-raga clip counts reach **15-20+** and dyad discrimination
> ratio exceeds **2.0x**."*

Both conditions must hold. **Bhairavi has 11 clips — the first condition is
unmet.** Therefore **even a strongly positive C2 cannot license a production
change.** Phase 1-D is diagnostic only, and its report must say so. This is
pre-registered, not to be discovered afterwards.

### Required artifacts

`per_clip_by_condition.csv` · `condition_transitions.csv` ·
`phase1d_measurements.json` · `run_metadata.json` — the last recording γ, mean
`S_raw`, mean `S_nrm`, all imported constants, commit, software versions, and
every negative assertion (`modified_production_code: false`, etc.) as Phase 1-C
did.

### Reproducibility requirements

- The sandbox must be **committed with or before execution** — Phase 1-B and 1-C
  were pinned retroactively in `9b1dd6d`; Phase 1-D should not repeat that.
- Constants **imported, never re-declared** — ADR-015 (see F2).
- Fully deterministic: LOO is exhaustive and Phase 1-D introduces **no
  sampling**, so no seed is required. Any future sampling must pre-register one.

### Exact execution command

```
cd D:\Swaragam\scripts
PYTHONIOENCODING=utf-8 ..\my_virtual_env_swarag\Scripts\python.exe sandbox_q003_phase1d_normalized_dyads.py
```

### Design-audit verdict

**Ready to execute after F1 and F2**, which are folded into the design above.

Why the corrected design is valid: the PCD channel is **provably invariant**
across conditions (`idf_var_weights()` at `confusion_matrix_audit.py:96-103`
reads only `m["pcd"]`), so any difference is attributable to the dyad channel
alone; C1→C2 isolates the model-norm correction at matched influence; C2→C3
isolates effective weight at fixed normalisation; C2 carries a free correctness
check against Phase 1-C's published ranks; outcomes are stratified; and every
conclusion is fenced by ADR-005 and by the n=11 descriptive-only constraint.

---

## After Phase 1-D

**The six PCD-driven wrong answers remain unexplained and hold the majority of
Bhairavi's failure mass.** Phase 1-A eliminated PCD *overlap*; Phase 1-C showed
PCD nonetheless selects all six winners. No phase has explained them, and
Phase 1-D is explicitly barred from doing so.

That investigation is the natural successor and has **not** been designed.
Sequencing is a decision for the researcher, not an inference from this plan.
