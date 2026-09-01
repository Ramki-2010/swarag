# Swarag -- Project Status

## Current Version
Swarag v1.3.2 (7 Ragas -- Bhairavi 0.5/0.5 override retired, uniform 0.8/0.2 for all ragas)

> **This document is the source of truth for current project state.**
> For where everything else lives and the recommended reading order, see
> [`docs/START_HERE.md`](docs/START_HERE.md). Detailed research reasoning
> belongs in `docs/research/<GATE>/PHASE_LOG.md`, not here.

---

## Mission

Swarag's primary goal is a usable, explainable Carnatic raga recognizer.

Research into representation, temporal reasoning, phrase modelling, gamakas,
and computational music exists to improve that recognizer and deepen
understanding of Carnatic music -- research is a means, not an end. When
priorities compete, recognition takes precedence, unless a research experiment
is the shortest path to removing a recognition bottleneck (e.g. Q-001 gates
every phrase-based accuracy fix).

---

## What Is Stable

- 72-bin PCD + IDF x Variance weighted dot-product scoring
- Directional dyads with ALPHA=0.01 Laplace smoothing
- PCD_WEIGHT=0.8, DYAD_WEIGHT=0.2, applied uniformly to all ragas
  (Bhairavi 0.5/0.5 override tested and retired in v1.3.2 -- see ADR-006/ADR-013)
- MIN_CLIPS_PER_RAGA=5 guardrail
- Vocal isolation mandatory (Saraga stems + Demucs)
- Per-file timeout in batch evaluation (360s)

### Key Constants
| Constant | Value |
|---|---|
| N_BINS | 72 |
| ALPHA | 0.01 |
| PCD_WEIGHT | 0.8 (global) |
| DYAD_WEIGHT | 0.2 (global) |
| PER_RAGA_WEIGHTS | none (retired) |
| MIN_CLIPS_PER_RAGA | 5 |
| MARGIN_STRICT | 0.003 |
| MIN_MARGIN_FINAL | 0.001 |

### Current Accuracy (LOO, 7 ragas, 70 clips, sandbox_loo_v131_canonical.py)

> **This table is the canonical source for every accuracy figure in the
> repository.** Other documents may summarise it but must point here.
> Regenerate it with the named script -- never edit these numbers by hand.
> Known mirrors: `README.md`, `.ai-memory/architecture.md`.

| Raga | Clips | LOO Acc |
|---|---|---|
| Mohanam | 10 | 100% (1c/0w/9u -- decides rarely) |
| Saveri | 8 | 88% |
| Shankarabharanam | 9 | 80% |
| Kalyani | 14 | 75% |
| Thodi | 11 | 71% |
| Abhogi | 7 | 33% |
| Bhairavi | 11 | 14% (override retired -- cause unproven: representation vs data) |
| **Overall** | **70** | **64.1% decided** |

### What Changed from v1.3.1
- Bhairavi 0.5/0.5 per-raga override retired: canonical rerun confirmed
  it was counter-productive (0% decided for Bhairavi, 9 wrongs)
- All ragas now use uniform 0.8/0.2 global weight
- Prior "67.4%" figure retired: found fabricated on audit -- its per-raga
  rows never summed to its own total. Real config it claimed to describe
  (Bhairavi override) actually scores 60.5% overall.
- New canonical: 64.1% decided (25c/14w/31u)

---

## Known Limitations

- Abhogi: 33% LOO -- STRUCTURAL problem (janya of Kalyani, PCD is strict subset)
  Weight overrides (L-044) and energy-ratio scoring (L-050) both tested,
  both rejected -- confirmed no signal, not just weak. Next: phrase n-grams.
- Bhairavi: 14% LOO -- override retired. Cause UNPROVEN: whether the limit is
  representation (feature) or data (clip diversity) is untested. "More clips"
  is a hypothesis, not a confirmed diagnosis.
  Q-003 Phase 1-A eliminated mean-PCD overlap as the mechanism; Phase 1-B
  localised the failure to the **dyad channel** (ranks Bhairavi #1 in 0 of
  its 11 clips). Localisation is NOT a diagnosis -- the gate is still open.
  Detail: docs/research/Q-003/PHASE_LOG.md
- Mohanam: 100% decided but 9/10 UNKNOWN -- model barely commits. Likely a
  data-diversity limit, but unproven.
- Kamboji: excluded (3 real clips, Saraga exhausted -- 0 new sources)
- Saveri is the new sink (8/14 wrongs) -- was Kalyani pre-retirement
  (corrected 2026-08-24, Q-003 C-6: previously read "6/14"; the documented
  split 6+3+2 summed to 11, not 14. Recomputed from the canonical confusion
  matrix: Saveri 8, Thodi 4, Kalyani 2. Totals unaffected. See
  docs/research/Q-003/PHASE_LOG.md -> Correction C-6.)
- No OOD score floor

---

## Priority Plan

1. **Diagnose Bhairavi -- Q-003** (weakest raga at 14%). The weight hack is
   disproven (override retired), and data-vs-representation as the root cause
   remains UNPROVEN. Phase 0 (documentation provenance), Phase 1-A (PCD
   overlap eliminated) and Phase 1-B (failure localised to the dyad channel)
   are complete. **Superseded 2026-08-24:** this item previously read
   "adding diverse clips is the first test" -- Phases 1-A/1-B ran instead, and
   the indicated next test is now a dyad-channel diagnostic (does Bhairavi's
   dyad matrix lack information, or does the representation fail to express
   it?). That distinguishes H_DATA from H_REP directly. **Requires explicit
   approval before it begins.** Detail: docs/research/Q-003/PHASE_LOG.md
2. **Abhogi -- Q-001B phrase-discrimination experiment** (ARCHITECTURAL):
   every scoring-time approach is rejected (overrides L-044, absent-swara L-046,
   energy-ratio L-050). Q-001A answered: the representation is adequate (no
   evidence of degradation), so phrase-level features are the live candidate.
   Q-001B (pre-registered) tests whether data-discovered n-grams add
   discriminatory power beyond PCD+dyads. Discover candidates from data -- the
   docs' M2-D2-M2 example is musicologically suspect and must not be assumed.
   **Status 2026-08-17:** Q-001B-A completed **INCONCLUSIVE** -- some individual
   Abhogi sequences show evidence of higher-order structure (Holm-significant
   1/7, raw 2/7), but Q-001B-A does not establish Abhogi-level generality or
   discrimination. Q-001B-B **remains blocked** pending additional independent
   Abhogi compositions: the current 7 clips span only 2 compositional units
   (Evvari Bodhana 6, Nannu Brova Neeku 1). Q-001B itself stays ACTIVE.
3. Add 4-6 diverse Mohanam clips -- 100% decided but 9/10 UNKNOWN
4. Add 5-7 real Kamboji clips (YouTube/Rasikas -- Saraga has 0 new sources)
5. Do NOT add more new ragas until weak ones > 60%
6. Re-baseline the accuracy target against 64.1% (the 72-78% target was
   calibrated against the fabricated 67.4% figure)

### Proven Dead Ends (do not re-attempt)
- Abhogi per-raga weight overrides (0% at all weights -- L-044)
- Abhogi absent-swara penalty -- BOTH variants failed (L-046, 2026-04-01):
  * Data-driven: self-harm on 5/7 Abhogi clips
  * Musicological: gamakas leak 6-19% Pa energy, binary detection fails
- Abhogi energy-ratio scoring -- REJECTED 2026-07-11 (L-050, BUG-015):
  Pa/N3 separation ratio 1.01x (none). Abhogi result identical at every
  tested ratio_weight 0.05-0.40. Do not re-attempt without a fundamentally
  different feature (phrase-level, not swara-energy-level).
- Mohanam dyad overrides (no improvement -- data problem)
- Genericness penalty from model PCD (L-016)
- Escalation / dyad-heavy re-scoring (L-017)

---

## Research Gates (Knowledge State)

Work is tracked by what is *known*, not by feature lists. Settled questions
live in ADRs; only open unknowns are gated here. A gate is a diagnostic, not
a promise -- see the Promotion Rule in workflow.md.

**Settled:** 72-bin PCD (ADR-002), IDF x Variance (ADR-003), ALPHA=0.01
(ADR-004) -- proven. Per-raga overrides (ADR-013), absent-swara penalty
(ADR-008), energy-ratio scoring (ADR-014) -- rejected.

### Active Gates

| Gate  | Question | Status | Next action |
|-------|----------|--------|-------------|
| Q-001A | Does production extraction yield stable, meaningful swaras for Abhogi (representation sufficiency)? | ANSWERED 2026-07 -- no evidence of degradation vs easy ragas (n=7, permutation p=0.39, d=0.38; Abhogi median +0.35 vs refs +0.39). Representation adequate; NOT the bottleneck. | done |
| Q-001B | Can data-discovered swara phrase (n-gram) features add discriminatory power beyond the current PCD+dyad representation? | ACTIVE -- unblocked by Q-001A; not answered by Q-001B-A | Q-001B-B needed; blocked on data (see below) |
| Q-001B-A | Do Abhogi stable-note sequences contain trigram structure beyond their own bigram statistics? | COMPLETED 2026-08-17 -- **INCONCLUSIVE**. 7 clips, 50,000 doublet-preserving surrogates, seed 0, alpha 0.05. Raw significant 2/7, Holm-significant 1/7 (223579). Both synthetic controls PASS (positive p=1.99996e-05, negative p=0.328273); sanity A-D PASS on all 7 clips. Measured **sequence-level** higher-order structure only; did **not** establish Abhogi discrimination. | done -- see datasets.md run log and L-054 |
| Q-001B-B | Does composition-held-out discrimination separate Abhogi from its top confuser? | BLOCKED -- only **2 independent compositional units** across 7 clips (Evvari Bodhana 6 clips, Nannu Brova Neeku 1 clip). Composition-held-out folds are not constructible at this diversity (protocol section 4). | Acquire additional independent Abhogi compositions |
| Q-002 | If Q-001B shows phrase power, does a phrase model improve recognition? | Blocked by Q-001B | Phrase-model experiment |
| Q-003 | Is Bhairavi (14%, worst raga) limited by representation or by dataset diversity? | **ACTIVE -- UNANSWERED.** Phase 0 CLOSED 2026-08-21 (`908dbaa`): H_DATA was asserted in 4 places, including locked ADR-013, with no experiment behind it; corrected. Phase 1-A CLOSED 2026-08-21 (`1ef479f`): mean-PCD overlap **eliminated** as the mechanism -- Saveri has the *lowest* overlap (0.6782) yet absorbs 4 of 6 Bhairavi errors. Phase 1-B COMPLETE 2026-08-24 (`9b1dd6d`): failure localised to the dyad channel -- it ranks Bhairavi #1 in **0 of 11** of its own clips (Abhogi: 0 of 7). **Phase 1-C COMPLETE and independently verified 2026-08-25** (`9b1dd6d`): the localisation splits. The dyad channel explains **3 of Bhairavi's 4 UNKNOWNs** (PCD ranked Bhairavi #1; dyad pulled the margin below MIN_MARGIN_FINAL) and **0 of its 6 wrong answers** -- in all 6, `pcd_top` is the raga that won, so **the six wrong classifications remain unexplained**. Also measured: L2-normalised (cosine) dyad similarity ranks Bhairavi #1 in 8 of 11 clips on identical models, and Saveri's dyad dominance tracks model concentration (1.74x). **Channel ranks only -- no accuracy change was measured and normalization is NOT established as a solution.** H_REP and H_DATA are WEAKENED, not resolved; H_SCORE supported for UNKNOWNs only. **Localisation is not a diagnosis; the root cause is not established.** | Phase 1-D (scale-controlled normalisation test) **requires design approval** -- naive cosine substitution is invalid (scale confound), and ADR-005 blocks production promotion at 11 clips. Separately open: the 6 unexplained PCD-driven wrongs. See docs/research/Q-003/PHASE_LOG.md |
| Q-004 | What is the legally permissible reproducibility artifact for Saraga-derived data -- audio, or derived features only? | Pending | Review Saraga license, then record ADR (gates ADR-016's form) |

Rule: do not promote an UNKNOWN to a cause ("data problem", "solved") without
an experiment that isolates it. Rejecting scoring-time features proves only
that scoring-time is exhausted -- nothing about what the real fix is.

**Open note (Q-001A):** the reference band contained 3 sub-chance clips
(Vara Leela Gana Lola, Undan Paada Pankayam, Sundari Nee Divya). Well-
represented ragas should not score below chance -- likely tonic mis-estimation
or heavy-gamaka passages. Diagnose before relying on this band again.

---

## Philosophy

Honest baselines over inflated numbers. Clean data over more data.
Do not state as proven what has only been assumed.