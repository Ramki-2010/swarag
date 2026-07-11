# Swarag -- Architecture (Current State)

## Version
Swarag v1.3.2 -- Bhairavi override retired, global 0.8/0.2 for all ragas

## Pipeline

```
Audio (.wav / .mp3 / .flac)
  |
  v
Vocal Isolation (Saraga multitrack stems or Demucs htdemucs)
  |
  v
Pitch Extraction (pYIN via librosa, SR=22050, MAX_DURATION_SEC=360)
  |
  v
Tonic (Sa) Estimation (utils.py -> estimate_tonic)
  |  histogram-based + octave-aware candidate scoring
  v
Pitch Normalization (cents relative to Sa, folded to 0-1200)
  |
  v
Feature Computation
  |-- PCD: 72-bin pitch class distribution (17 cents per bin)
  +-- Directional Dyads: stable-region detection + Laplace smoothing
      |-- mean_up   (ascending transitions, 72x72 matrix)
      +-- mean_down (descending transitions, 72x72 matrix)
      |-- ALPHA=0.01 (Phase 2 fix: was 0.5)
  |
  v
Aggregation (aggregate_all_v12.py)
  |-- MIN_CLIPS_PER_RAGA=5 guardrail (excludes thin-data ragas)
  |-- Mean PCD + mean dyads per raga
  v
Raga Scoring (recognize_raga_v12.py)
  |-- IDF x Variance weighted dot-product (PCD + Dyads)
  |-- Weighted fusion (PCD_WEIGHT=0.8, DYAD_WEIGHT=0.2)
  |-- Genericness penalty REMOVED (GENERICNESS_WEIGHT=0.0)
  |-- Escalation DISABLED
  +-- Tiered confidence:
      |-- HIGH:     margin >= 0.003 (MARGIN_STRICT)
      |-- MODERATE: margin >= 0.001 (MIN_MARGIN_FINAL)
      +-- UNKNOWN:  margin < 0.001
  |
  v
Output: { "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Core Scripts

| Script | Responsibility |
|---|---|
| `recognize_raga_v12.py` | Inference engine (72-bin, IDF x Variance) |
| `aggregate_all_v12.py` | Build raga models (with MIN_CLIPS guardrail) |
| `extract_pitch_batch_v12.py` | Pitch extraction + feature creation |
| `batch_evaluate.py` | Evaluation on seed dataset (with per-file timeout) |
| `batch_evaluate_random.py` | Evaluation on unknown clips |
| `utils.py` | Shared utilities (tonic estimation) |

## Support Scripts

| Script | Purpose |
|---|---|
| `extract_new_clips.py` | Feature extraction for new clips |
| `extract_saraga_vocals.py` | Saraga vocal stem extraction |
| `run_demucs_batch.py` | Demucs batch vocal isolation |
| `sandbox_loo_9ragas.py` | LOO validation for 9 ragas |
| `sandbox_loo_validation.py` | LOO cross-validation (36 vs 72 bins) |
| `sandbox_phase2_alpha.py` | Phase 2 ALPHA tuning |
| `sandbox_phase3_thodi_sink.py` | Phase 3 IDF scoring |
| `sandbox_phase3b_variance.py` | Phase 3b variance weighting |
| `sandbox_phase4_bins.py` | Phase 4 bin resolution |
| `sandbox_phase4_production.py` | Phase 4 production test |
| `sandbox_loo_v131_canonical.py` | Canonical v1.3.1 LOO rerun (ground-truth numbers, 2026-06-24) |

## Trained Ragas (v1.3.2: 7 ragas, 70 clips)

| Raga | Clips | LOO Acc (decided) |
|---|---|---|
| Mohanam | 10 | 100% (1c/0w/9u -- decides rarely) |
| Saveri | 8 | 88% |
| Shankarabharanam | 9 | 80% |
| Kalyani | 14 | 75% |
| Thodi | 11 | 71% |
| Bhairavi | 11 | 14% (needs more diverse clips) |
| Abhogi | 7 | 33% |

### Staged Ragas (excluded by MIN_CLIPS_PER_RAGA=5 guardrail)
- Kamboji: 3 clips (needs 2 more; 3 Harikambhoji removed, BUG-013)
- Madhyamavati: 2 clips (needs 3 more)
- Hamsadhvani: 1 clip (needs 4 more)

## Aggregation Data Location
```
D:\Swaragam\pcd_results\aggregation\v1.2\run_20260331_232228\
  pcd_stats\    -> {raga}_pcd_stats.npz (7 ragas)
  dyad_stats\   -> {raga}_dyad_stats.npz (7 ragas)
  aggregation_metadata.json  (alpha=0.01, bins=72, 70 clips, min_clips=5)
```

## Feature Storage
```
D:\Swaragam\pcd_results\features_v12\           75 .npz files (70 modeled + 5 below guardrail)
D:\Swaragam\pcd_results\features_v12\excluded\  duplicates + Thodi outliers + Harikambhoji clips
```

## Shared Constants (must be identical in aggregate + recognize)

| Constant | Value | Notes |
|---|---|---|
| SR | 22050 | Sample rate |
| MAX_DURATION_SEC | 360 | 6-minute cap per file |
| N_BINS | 72 | PCD and dyad bins |
| MIN_STABLE_FRAMES | 5 | Stable region threshold |
| ALPHA | 0.01 | Laplace smoothing (Phase 2 fix) |
| EPS | 1e-8 | Division safety |
| PCD_WEIGHT | 0.8 | Global default (v1.3.1: was 0.7) |
| DYAD_WEIGHT | 0.2 | Global default (v1.3.1: was 0.3) |
| PER_RAGA_WEIGHTS | Bhairavi=(0.5,0.5) | Per-raga override for transition-heavy ragas |
| GENERICNESS_WEIGHT | 0.0 | Disabled |
| MARGIN_STRICT | 0.003 | HIGH confidence threshold |
| MIN_MARGIN_FINAL | 0.001 | MODERATE confidence threshold |
| MIN_CLIPS_PER_RAGA | 5 | Aggregation guardrail (BUG-011) |
| PER_FILE_TIMEOUT | 360 | Batch eval per-file timeout |

## Frozen Output Schema
```python
{ "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Current Accuracy (v1.3.2, LOO, 7 ragas, 70 clips -- rerun 2026-06-24)

| Metric | Value |
|---|---|
| Accuracy (decided) | 64.1% |
| Correct | 25 |
| Wrong | 14 |
| Unknown | 31 (44%) |
| Saveri sink | 6/14 wrongs |
| Thodi sink | 3/14 wrongs |
| Kalyani sink | 2/14 wrongs |

## Accuracy Evolution

| Version | LOO Acc | Key Change |
|---|---|---|
| v1.2 | 25% | Baseline (3 ragas) |
| v1.2.1 | -- | 6 ragas, vocal isolation |
| v1.2.2 | 64% | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | IDF x Variance scoring |
| v1.2.4 | 78.6% | 72-bin PCD (53 clips) |
| v1.2.5 | 72.0% | Expanded to 61 clips, dedup, MIN_CLIPS guardrail |
| v1.3 | 58.8% | Harikambhoji removed, weights 0.7/0.3, honest 5-raga baseline |
| v1.3.1 | 60.5% | Abhogi+Saveri activated, 0.8/0.2, Bhairavi 0.5/0.5 override (counter-productive) |
| v1.3.2 | 64.1% | Bhairavi override retired, global 0.8/0.2 for all ragas |

## Remaining Issues
1. Bhairavi: 14% LOO -- weak but no longer poisoning other ragas (override retired).
   Komal swaras overlap heavily with Saveri and Thodi. Needs more diverse clips.
2. Abhogi: 33% LOO -- STRUCTURAL: janya of Kalyani, PCD is strict subset (L-044)
   Weight overrides tested at 0.6/0.4, 0.5/0.5, 0.4/0.6 -- all 0% for Abhogi.
   Needs QUANTITATIVE features (energy ratios or phrase n-grams) -- see Next Architectural Steps.
3. Mohanam: 100% decided but only 1/10 clips decides (9 UNKNOWN) -- margin too low.
   Needs diverse clips to build a stronger model signature.
4. Kamboji: excluded (3 real clips, Saraga exhausted -- 0 new sources)
5. No OOD score floor (margin-only detection)
6. BUG-009: Mix audio causes OOD false positives

## Proven Dead Ends (do not re-attempt)
- Abhogi per-raga weight overrides: 0% at all tested weights (L-044)
- Abhogi absent-swara penalty: gamakas leak Pa/Ni energy into Abhogi clips (L-046)
  Both data-driven (median threshold) and musicological (known bin ranges) approaches
  failed. Self-harm on 5/7 Abhogi clips. Best result +1 Kalyani, 0 Abhogi improvement.
- Mohanam per-raga weight overrides: no improvement at 0.6/0.4, 0.5/0.5
- Genericness penalty from model PCD: made things worse (L-016)
- Escalation / dyad-heavy re-scoring: crushes margins 5x (L-017)

## Next Architectural Steps
1. Bhairavi: add more diverse clips (currently 6 clean wav + Saraga stems).
   Clips are acoustically similar -- model has low variance, poor discrimination.
2. Abhogi: needs QUANTITATIVE features (energy ratio comparison or phrase-level
   transition patterns), NOT binary absent/present detection. Candidate approaches:
   - Swara energy ratio: compare Pa-energy/Sa-energy between test clip and model
   - Phrase n-grams: detect M2-D2-M2 (Abhogi) vs Pa-D2-N3 (Kalyani) patterns
   - Contour templates: characteristic melodic shapes
3. Mohanam: needs diverse clips (different songs/artists), not code changes
4. Add Kamboji clips (YouTube/Rasikas)

## Parked Features
| Feature | Trigger | Sandbox Script |
|---|---|---|
| Hubness correction | Ragas >= 15 | sandbox_hubness.py |
