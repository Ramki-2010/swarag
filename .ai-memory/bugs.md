# Swarag — Known Bugs & Issues

## Active Bugs

### BUG-002: OOD Sink (was Shankarabharanam, now Thodi)
- **Status**: PARTIALLY RESOLVED — shifted from Shankarabharanam to Thodi
- **Found**: 2026-02-15 (test_recognize_fix.py run)
- **Updated**: 2026-03-10 (Phase 2 analysis)
- **Description**:
  Originally: untrained ragas misclassified as Shankarabharanam.
  After expanding to 6 ragas: OOD test files (Hamsadwani, Mohanam) now
  correctly return UNKNOWN. The OOD false positive issue is FIXED.
  However, cross-raga leakage now goes to Thodi (10/18 seed wrongs).
- **Impact**: OOD false positives fixed. Intra-trained leakage remains.
- **Evidence (Phase 2)**:
  - Hamsadwani -> UNKNOWN (margin 0.000672) CORRECT
  - Mohanam -> UNKNOWN (margin 0.000254) CORRECT
  - But 10/18 seed misclassifications go to Thodi
- **Root Cause**: Thodi has concentrated PCD on Sa/Ni/Ma (universal swaras),
  giving it high dot-product with many other ragas' audio.
- **Fix Applied**: Expanded to 6 ragas (eliminated Shankarabharanam sink),
  boosted Thodi to 10 clips, excluded 2 outlier clips.
- **Remaining**: See BUG-008 for Thodi sink details.

### BUG-003: Score Compression Between Sibling Ragas
- **Status**: IMPROVED — margins 1.6-5x better after Phase 1-2 fixes
- **Found**: 2026-02-15 (test_recognize_fix.py run)
- **Updated**: 2026-03-10 (Phase 2 ALPHA fix)
- **Description**:
  Sibling ragas (sharing most swaras) have very small margins.
  Originally Kalyani margin was 0.000227. After Phase 2 fixes:
  Kalyani margin is now 0.006558-0.008833 (HIGH confidence).
- **Impact**: Largely resolved for Kalyani. Bhairavi still shows
  compression vs Thodi (margin 0.002-0.004).
- **Fixes Applied**:
  1. Genericness removed (scores shifted positive) — BUG-004
  2. Escalation disabled (preserved first-pass margin) — BUG-007
  3. Thresholds recalibrated (0.003/0.001) — BUG-006
  4. ALPHA fixed (0.5→0.01, dyads now contribute) — Phase 2
  5. Training data expanded (6→53 clips, 6 ragas)
- **Remaining**: Bhairavi/Thodi separation needs improvement.

### BUG-004: Genericness Penalty Does Not Affect Ranking
- **Status**: RESOLVED (2026-03-09)
- **Found**: 2026-02-16 (architectural audit)
- **Fix**: Set GENERICNESS_WEIGHT = 0.0 in recognize_raga_v12.py.
  Penalty was mathematically inert (same value subtracted from all scores).
  Removal shifts scores from negative to positive, no ranking change.
- **Verified**: sandbox_phase1_fast.py confirms margins unchanged.

### BUG-005: ESCALATION_MARGIN Defined But Never Used
- **Status**: RESOLVED (2026-03-09)
- **Found**: 2026-02-16 (architectural audit)
- **Fix**: Escalation path disabled entirely. Replaced with simple
  two-tier confidence: HIGH (margin >= 0.003), MODERATE (>= 0.001).
  ESCALATION_MARGIN constant removed along with escalation logic.

### BUG-006: Margin Thresholds Miscalibrated for Actual Score Range
- **Status**: RESOLVED (2026-03-09)
- **Found**: 2026-02-16 (architectural audit)
- **Fix**: Recalibrated thresholds based on empirical score distributions:
  - MARGIN_STRICT: 0.05 -> 0.003 (HIGH confidence)
  - MIN_MARGIN_FINAL: 0.01 -> 0.001 (MODERATE confidence)
  Now 27/53 clips reach HIGH, 2 reach MODERATE (was 0 before).

### BUG-007: Escalation Path Crushes Kalyani Margin
- **Status**: RESOLVED (2026-03-09)
- **Found**: 2026-02-16 (test_dyad_weights.py)
- **Fix**: Escalation path disabled entirely. Confidence tier changed
  from ESCALATED to MODERATE. First-pass margin (0.6/0.4) is now final.
  Kalyani margin improved from 0.000227 (escalated) to 0.008833 (HIGH).

### BUG-008: Thodi Sink (Cross-Raga Leakage)
- **Status**: RESOLVED (Phase 3+4+5: IDF x Variance + 72 bins + MIN_CLIPS guardrail) (Phase 3+4: IDF x Variance + 72 bins)
- **Found**: 2026-03-10 (sandbox_phase1_fast.py / sandbox_phase2_alpha.py)
- **Description**:
  Thodi model attracts many non-Thodi clips. 10/18 seed misclassifications
  go to Thodi. Thodi has concentrated PCD on bins 0, 35, 14, 21, 20
  (Sa, Ni, Ma, Da, Pa) — universal strong swaras that appear in most ragas.
- **Impact**: 34% of seed clips are WRONG, most leaking to Thodi.
- **Evidence**:
  - Thodi self: 10/10 correct (9 HIGH, 1 UNKNOWN) — excellent
  - But Kalyani->Thodi (5 clips), Shankarabharanam->Thodi (3),
    Bhairavi->Thodi (3), Kamboji->Thodi (1) leaking
- **Root Cause**: PCD overlap on universal swaras (Sa, Pa, Ma).
  Thodi's distinctive features (Ri1, Ga2, Da1 gamakas) are better
  captured by dyads than PCD.
- **Mitigation Applied**:
  1. Excluded 2 outlier clips (Munnu Ravana, Koluvamaregatha)
  2. Added 5 new Thodi clips from external sources
  3. Fixed ALPHA (0.5->0.01) to make dyads discriminative
- **Production Evidence (2026-03-11)**:
  Seed: 14/15 total wrongs go to Thodi. Blind test: 4/6 OOD false positives -> Thodi.
  Mix audio (with instruments) makes it worse -- instrument noise boosts Thodi PCD match.
- **Remaining**: Dyads improved discrimination ratio to 2.03x for Thodi
  but leakage persists. Needs: more Kamboji/Bhairavi data,
  Phase 3 OOD hybrid detection (top_score - mean_score metric),
  and mandatory vocal isolation for inference.

### BUG-009: Mix Audio Causes OOD False Positives
- **Status**: OPEN -- design limitation
- **Found**: 2026-03-11 (blind test with archive.zip mix audio)
- **Description**:
  OOD rejection works correctly on vocal-isolated audio (2/2 original tests -> UNKNOWN)
  but fails on full mix recordings with instruments (6/6 new OOD tests -> FALSE POSITIVE).
  Violin, mridangam, and tambura add pitch content that inflates dot-product scores,
  pushing margins above the UNKNOWN threshold.
- **Impact**: System is unreliable on non-vocal-isolated audio.
- **Evidence**:
  - Vocal-only OOD: 2/2 correctly rejected (Hamsadwani, Mohanam alapana)
  - Mix OOD: 0/6 rejected (Behag, Kamas, Saveri, Sahana, Hindolam, Hamsadhvani)
  - Mix OOD margins: 0.0016-0.0140 (all above 0.001 MODERATE threshold)
- **Root Cause**: pYIN extracts pitches from ALL sources (vocal + violin + mridangam).
  Instrument pitches inflate the PCD, making scores artificially high and margins wide.
- **Potential Fixes**:
  1. Mandatory Demucs vocal isolation before recognition (recommended)
  2. Add instrument-contamination detection (energy in non-vocal bands)
  3. Raise margin thresholds for mix audio (separate threshold set)
  4. Train on mix audio too (but degrades model quality)

---


### BUG-011: Thin-Data Ragas Poison Model (Saveri/Abhogi Sink)
- **Status**: RESOLVED (2026-03-20)
- **Found**: 2026-03-20 (sandbox_loo_9ragas.py)
- **Description**:
  When ragas with <5 training clips (Abhogi=2, Madhyamavati=2, Saveri=3)
  are included in aggregation, they become attractors (sinks) that absorb
  wrongs from other ragas. Saveri absorbed 12/21 wrongs, Abhogi absorbed 5/21.
  LOO accuracy dropped from 72.0% (6 ragas) to 41.7% (9 ragas).
- **Root Cause**: Thin-data raga models are unstable -- their mean PCD/dyads
  are dominated by 1-2 clips and do not represent the raga reliably.
  IDF weighting amplifies their distinctive bins, making them "attractive"
  to other ragas' clips.
- **Fix**: Added MIN_CLIPS_PER_RAGA=5 guardrail to aggregate_all_v12.py.
  Ragas below threshold are excluded from aggregation with a warning.
  Features are kept (not deleted) so they can be activated when more data arrives.
- **Evidence**:
  - 9-raga LOO: 41.7% (15c/21w/32u). Saveri=12 wrongs, Abhogi=5 wrongs.
  - 6-raga LOO: 72.0% (18c/7w/36u). No sink ragas.
- **Verified**: Re-aggregation with guardrail excludes 3 ragas, accuracy restored.

### BUG-012: Duplicate Features Inflate Clip Counts
- **Status**: RESOLVED (2026-03-20)
- **Found**: 2026-03-20 (feature audit)
- **Description**:
  13 feature files had duplicates (same audio processed twice with different
  timestamps). Inflated total from 68 unique to 81. Some ragas appeared to
  have more data than they actually did.
- **Fix**: Identified duplicates by matching raga + source filename prefix.
  Moved 13 duplicates to features_v12/excluded/. Also removed 25 .dup files
  left by previous cleanup attempts.
- **Evidence**: 81 features -> 68 unique after dedup.


### BUG-013: Harikambhoji Contamination in Kamboji Training Data
- **Status**: RESOLVED (2026-03-21)
- **Found**: 2026-03-21 (Saraga metadata cross-reference)
- **Description**: 3/6 Kamboji clips were actually Harikambhoji (parent melakarta).
- **Fix**: Moved to excluded/. Kamboji dropped below guardrail (3 clips remain).
- **Impact**: Overall LOO dropped 72% to 58.8% (honest baseline).

## Resolved Bugs

### BUG-001: Missing Constants in recognize_raga_v12.py
- **Resolved**: 2026-02-16
- **Fix**: Added MIN_STABLE_FRAMES=5, ALPHA=0.5, EPS=1e-8 to CONFIG.
  Also added error logging to except block (traceback.print_exc).
- **Verified**: Production import test + sandbox test pass.


### BUG-010: Hubness Correction Parked (Premature at 6 Ragas)
- **Status**: PARKED -- revisit when raga count >= 15
- **Found**: 2026-03-12 (sandbox_hubness.py, multi-agent analysis)
- **Trigger**: When raga count reaches 15+, re-run sandbox_hubness.py LOO test
- **Description**:
  Centered hubness correction (score = raw - avg_sim + global_mean)
  eliminates Thodi sink entirely (0/8 wrongs to Thodi) and improves weak
  ragas (Bhairavi +8%, Shankarabharanam +6%, Kamboji +50%), but drops
  overall LOO accuracy from 78.6% to 74.2% due to 2 new wrongs from
  small-sample instability.
- **Why parked (not rejected)**:
  Multi-agent analysis (5 experts unanimous):
  - Architecturally correct -- penalizes hub ragas (Thodi bias +0.000783)
  - Bias values too small at 6 ragas (+-0.0003-0.0008 vs noise floor)
  - New wrongs are small-sample artifacts (Kamboji has only 3 clips)
  - At 15+ ragas, bias spread will be >= 0.002 -> correction becomes reliable
  - Correction is below pYIN pitch extraction noise floor at 72 bins
- **Sandbox reference**: scripts/sandbox_hubness.py (full LOO test)
- **Evidence**:
  Hubness diagnostic: Thodi=HUB (+0.000783), Kalyani=HUB (+0.000359),
  Shankarabharanam=ok, Bhairavi=ok, Kamboji=low, Mohanam=low.
  LOO 72-bin: No hubness=78.6% (22c/6w/25u), +Hubness=74.2% (23c/8w/22u).
  Thodi sink: 1/6 -> 0/8. But +2 new wrongs (Bhairavi->Kamboji, Kamboji->Mohanam).
