# Swarag — Known Bugs & Issues

## Active Bugs

### BUG-002: Shankarabharanam Sink (OOD Absorption)
- **Status**: OPEN — architectural issue
- **Found**: 2025-02-15 (test_recognize_fix.py run)
- **Description**:
  Untrained ragas (Hamsadwani, Mohanam) are confidently misclassified as
  Shankarabharanam. The major-scale-like PCD of Shankarabharanam attracts
  any raga with a broadly distributed pitch histogram.
- **Impact**: False positives on out-of-distribution audio.
- **Evidence**:
  - Hamsadwani -> Shankarabharanam (margin 0.00431)
  - Mohanam -> Shankarabharanam (margin 0.003845)
- **Root Cause**: No out-of-distribution (OOD) detection mechanism.
  The system picks the "least bad" match from its trained set.
  Shankarabharanam has the most generic/uniform PCD, so it wins by default.
- **Potential Fixes**:
  1. Increase genericness penalty weight
  2. Add minimum absolute score threshold (not just margin)
  3. Add OOD detector (e.g., max score below threshold -> UNKNOWN)
  4. Train more ragas to crowd out false matches

### BUG-003: Kalyani / Shankarabharanam Score Compression
- **Status**: OPEN — scoring issue
- **Found**: 2025-02-15 (test_recognize_fix.py run)
- **Description**:
  Kalyani is ranked #1 for Kalyani test audio, but the margin between
  Kalyani and Shankarabharanam is only 0.000227 — far too small for any
  reasonable confidence threshold.
- **Impact**: Kalyani audio returns UNKNOWN even though it IS the correct
  top-1 prediction.
- **Evidence**:
  - Kalyani:          -0.142419
  - Shankarabharanam: -0.142646
  - Margin:            0.000227
- **Root Cause**: These are sibling ragas sharing most swaras. The current
  PCD + directional dyad features may not have enough discriminative power
  to separate them cleanly. All scores are also negative (genericness
  penalty outweighs similarities), compressing the effective range.
- **Updated Evidence (2025-02-16, test_dyad_weights.py)**:
  Without genericness, first-pass (0.6/0.4) Kalyani margin is actually
  0.001131 — but escalation (0.3/0.7) crushes it to 0.000227 (see BUG-007).
- **Potential Fixes**:
  1. Remove genericness penalty (confirmed inert, ready to apply)
  2. Fix escalation (BUG-007) so first-pass margin is preserved
  3. Add more training clips for both ragas (priority — only 6-10 clips)
  4. Add phrase-level features specific to Kalyani vs Shankarabharanam

### BUG-004: Genericness Penalty Does Not Affect Ranking
- **Status**: OPEN — first fix attempt REJECTED
- **Found**: 2025-02-16 (architectural audit)
- **File**: `scripts/recognize_raga_v12.py`, function `_score_models()`
- **Description**:
  `compute_genericness(pcd)` is computed from the TEST audio's PCD only.
  It does not reference any raga model. Since the same PCD is used for
  every raga in the loop, the same genericness value is subtracted from
  ALL scores equally. This means the penalty does not change ranking.
- **Fix Attempt 1 (REJECTED 2025-02-16)**:
  Compute genericness from MODEL PCD instead of test PCD.
  Result: Made things WORSE. Shankarabharanam had lowest model entropy
  (3.248) so it got the smallest penalty. Kalyani flipped from #1 to #2.
  All model entropies too close (3.25-3.29) to differentiate.
  Sandbox: test_bug004_genericness.py
- **Fix Attempt 2 (HELD 2025-02-16)**:
  Remove genericness entirely. Rankings and margins identical to baseline
  (confirms penalty was inert). Scores shift negative to positive.
  Clean-up only, no accuracy gain. Held until accuracy improves.
  Sandbox: test_bug004_no_genericness.py
- **Remaining options**:
  1. Remove genericness (ready to apply, no accuracy change)
  2. Try different penalty: KL divergence from uniform
  3. Move to post-scoring filter
  4. Skip BUG-004 entirely and focus on what actually moves accuracy

### BUG-005: ESCALATION_MARGIN Defined But Never Used
- **Status**: OPEN — dead code
- **Found**: 2025-02-16 (architectural audit)
- **File**: `scripts/recognize_raga_v12.py`
- **Description**:
  `ESCALATION_MARGIN = 0.02` is declared in CONFIG but never referenced
  in the code. The escalation path triggers whenever `margin < MARGIN_STRICT`,
  regardless of how small the margin is.
- **Impact**: Dead code. Suggests the tiered confidence was incompletely
  implemented. The original intent may have been:
  - `margin >= MARGIN_STRICT (0.05)` -> HIGH
  - `margin >= ESCALATION_MARGIN (0.02)` -> try escalation
  - `margin < ESCALATION_MARGIN` -> skip straight to UNKNOWN
- **Root Cause**: Incomplete implementation during v1.2 rewrite.
- **Fix**: Either use it or remove it. If used, add a check before
  escalation: `if margin < ESCALATION_MARGIN: return UNKNOWN`

### BUG-006: Margin Thresholds Miscalibrated for Actual Score Range
- **Status**: OPEN — threshold issue
- **Found**: 2025-02-16 (architectural audit)
- **File**: `scripts/recognize_raga_v12.py`
- **Description**:
  Production thresholds `MARGIN_STRICT=0.05` and `MIN_MARGIN_FINAL=0.01`
  are larger than the actual score spread observed in test runs (~0.03 total).
  This means nothing can ever reach HIGH confidence, and most results
  will be UNKNOWN even when the ranking is correct.
- **Impact**: System is overly conservative — rejects correct predictions.
- **Evidence**:
  - Best Bhairavi margin: 0.005664 (below MARGIN_STRICT=0.05)
  - Total score spread: ~0.03 (MARGIN_STRICT=0.05 exceeds this)
- **Root Cause**: Thresholds were likely set before genericness penalty
  was added, when scores were positive and had wider spread.
- **Fix**: Recalibrate after removing genericness (scores become positive)
  and after adding more training data. Set thresholds based on actual
  score distributions from a full evaluation run.

### BUG-007: Escalation Path Crushes Kalyani Margin
- **Status**: OPEN — confirmed harmful
- **Found**: 2025-02-16 (test_dyad_weights.py)
- **File**: `scripts/recognize_raga_v12.py`, escalation logic
- **Description**:
  When the first-pass margin (0.6 PCD / 0.4 Dyad) is below MARGIN_STRICT,
  the code re-scores with escalation weights (0.3 PCD / 0.7 Dyad).
  For Kalyani, this REDUCES the margin from 0.001131 to 0.000227 — a 5x
  degradation. The PCD is what provides the Kalyani signal (Ma1 vs Ma2),
  and shifting weight away from PCD destroys it.
- **Impact**: Kalyani goes from correct-but-tight (#1 with 0.001131)
  to UNKNOWN (margin 0.000227 below MIN_MARGIN_FINAL).
- **Evidence (test_dyad_weights.py, no genericness)**:
  - First pass (0.6/0.4): Kalyani #1, margin 0.001131
  - Escalation (0.3/0.7): Kalyani #1, margin 0.000227
  - Dyad-only (0.0/1.0): Shankarabharanam #1 (ranking flipped)
- **Root Cause**: Escalation assumes dyads are more discriminative than
  PCD. With only 6 training clips, dyad matrices are too noisy to lead.
  The PCD difference (Ma1 vs Ma2 bin) is small but real; shifting weight
  away from PCD dilutes the only signal that works.
- **Fix**: Hold until more training data is added. With 15-20 clips,
  dyad matrices may become strong enough for escalation to help.
  Alternative: remove escalation entirely and rely on first-pass only.

---

## Resolved Bugs

### BUG-001: Missing Constants in recognize_raga_v12.py
- **Resolved**: 2025-02-16
- **Fix**: Added MIN_STABLE_FRAMES=5, ALPHA=0.5, EPS=1e-8 to CONFIG.
  Also added error logging to except block (traceback.print_exc).
- **Verified**: Production import test + sandbox test pass.
