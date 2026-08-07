# Q-001B Research Plan (Pre-Registration)

**Status:** proposed — pre-registered before implementation, per the Promotion Rule.
**Depends on:** Q-001A (answered: no evidence the representation degrades on Abhogi;
Q-001B unblocked).

---

## Research Question
Does phrase (swara-order) information provide discriminatory power for Abhogi
**beyond** what the current order-limited representation already captures?

The current representation is order-limited: 72-bin PCD (order-free) plus
directional dyads (adjacent pairs ≈ bigrams). "Phrase information" here means
**higher-order swara n-grams (n ≥ 3)** — structure the current features cannot see.

## Hypothesis (single, falsifiable)
Adding **data-discovered swara trigram** features to an order-limited baseline
(unigram + directional bigram) **improves leave-one-out discrimination of Abhogi
from its top confuser** by a pre-registered margin.

## Null Hypothesis
Trigram features add no discrimination beyond the unigram+bigram baseline:
the paired per-fold improvement is ≤ 0 or statistically indistinguishable from 0.

## Dataset
- **Target:** Abhogi clips (deduplicated — one isolation per performance;
  Demucs-vocal is canonical per ADR-009). Current n ≈ 7.
- **Confuser:** Abhogi's empirical **top misclassification target**, read from
  `confusion_matrix_audit.py` before running (do not assume — pull it). Likely
  a scale-overlapping raga; the confuser is fixed once, before implementation.
- Two-class problem (Abhogi vs top confuser). Multi-class generalization is a
  later question, not this one.

## Inputs
- Cached raw `f0` from `features_v12` (validated bit-exact in L-051), fed through
  the **existing** `stable_bins_from_f0()` → swara-index sequence per clip.
- No new extraction. No production changes. Sandbox reads the same cache Q-001A uses.

## Outputs
- Per-fold LOO discrimination for baseline vs baseline+trigram.
- The trigrams discovered per fold, with their per-class occurrence rates.
- A separation verdict (see Metrics) and a per-clip CSV.

## Metrics
- **Discrimination:** leave-one-clip-out balanced accuracy of a minimal,
  leakage-free classifier (nearest-centroid on L1-normalized feature vectors).
- **Primary quantity:** paired Δ(balanced accuracy) = (baseline+trigram) − (baseline),
  computed per fold.
- **Significance:** paired permutation / sign test on the per-fold Δ, plus effect
  size — **not** a mean-vs-threshold binary (L-052).
- **Feature discovery is done INSIDE each training fold** (rank trigrams by
  train-only class-separation, keep top-k=5), then evaluated on the held-out clip.
  Discovering on the full set then testing on it is the L-049 leakage bug and is
  forbidden.

## Promotion Criteria (pre-registered — all three required)
1. Mean paired Δ(balanced accuracy) ≥ **+0.10**.
2. Paired permutation test **p < 0.05**.
3. The top discovered trigrams are **consistent across a majority of folds**
   (not fold-specific noise).
Meeting all three → phrase information carries real discriminatory power →
promote to a fuller Q-002 phrase-recognition experiment.

## Failure Criteria (pre-registered)
- Δ ≤ 0, or not significant → trigrams add nothing beyond the current
  representation for Abhogi → **deprioritize phrase modelling for Abhogi**, and
  redirect to the data/representation questions instead.

## Known Risk — Power (stated up front, per L-052)
n ≈ 7 Abhogi clips makes fold-wise trigram discovery underpowered and
overfit-prone. **INCONCLUSIVE is a likely and acceptable pre-registered outcome**;
it is not a failure of the method. If results are directional but not significant,
the honest next step is more Abhogi/confuser clips before re-deciding — not a
verdict either way. We will not over-read a small effect at this n.

## Estimated Implementation Scope
- One sandbox script (~120–180 lines) reusing `stable_bins_from_f0()` and the
  cached-`f0` loader; numpy only; no scipy, no production edits.
- Runtime: seconds (cache hits).
- Deliverables: the script, a per-clip/per-fold CSV, and a result summary.
- Nothing touches production until promotion criteria are met.

---

## Design Notes (rationale, kept minimal)
- **Baseline = unigram + directional bigram** deliberately mirrors "the current
  representation" so the test isolates the *new* information (n ≥ 3), not order
  in general. A weaker unigram-only baseline would overstate phrase value.
- **Nearest-centroid** chosen over any trained classifier to keep the experiment
  interpretable and leakage-resistant at tiny n; no hyperparameters to tune.
- **Two-class, top-confuser** keeps the question falsifiable and small; it asks
  exactly whether phrases help where the recognizer actually fails.
