# Swarag -- Architecture (Current State)

## Version
Swarag v1.3 -- Deterministic DSP Pipeline (72-bin PCD + IDF x Variance + MIN_CLIPS guardrail)

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
  |-- Weighted fusion (PCD_WEIGHT=0.6, DYAD_WEIGHT=0.4)
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
| `sandbox_hubness.py` | Hubness correction (PARKED for 15+ ragas) |

## Trained Ragas (5 ragas, 55 clips)

| Raga | Clips | Batch Eval Acc (decided) |
|---|---|---|
| Bhairavi | 11 | 33% |
| Kalyani | 14 | 100% |
| Shankarabharanam | 9 | 87.5% |
| Mohanam | 11 | 50% |
| Thodi | 11 | 100% |
| Kamboji | 5 | 66.7% |

### Staged Ragas (excluded by MIN_CLIPS_PER_RAGA=5 guardrail)
- Abhogi: 2 clips (needs 3 more)
- Madhyamavati: 2 clips (needs 3 more)
- Saveri: 3 clips (needs 2 more)
- Hamsadhvani: 1 clip (needs 4 more)

## Aggregation Data Location
```
D:\Swaragam\pcd_results\aggregation\v1.2\run_20260321_135629\
  pcd_stats\    -> {raga}_pcd_stats.npz (6 ragas)
  dyad_stats\   -> {raga}_dyad_stats.npz (6 ragas)
  aggregation_metadata.json  (alpha=0.01, bins=72, 61 clips, min_clips=5)
```

## Feature Storage
```
D:\Swaragam\pcd_results\features_v12\           68 unique .npz files
D:\Swaragam\pcd_results\features_v12\excluded\  13 duplicates + 2 Thodi outliers
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
| PCD_WEIGHT | 0.7 | Scoring weight |
| DYAD_WEIGHT | 0.3 | Scoring weight |
| GENERICNESS_WEIGHT | 0.0 | Disabled |
| MARGIN_STRICT | 0.003 | HIGH confidence threshold |
| MIN_MARGIN_FINAL | 0.001 | MODERATE confidence threshold |
| MIN_CLIPS_PER_RAGA | 5 | Aggregation guardrail (BUG-011) |
| PER_FILE_TIMEOUT | 360 | Batch eval per-file timeout |

## Frozen Output Schema
```python
{ "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Current Accuracy (v1.3)

| Metric | LOO | Batch Eval |
|---|---|---|
| Accuracy (decided) | 72.0% | 72.7% |
| Correct | 18/61 | 32/81 |
| Unknown | 36 (59%) | 37 (45.7%) |
| Wrongs | 7 | 12 |

## Accuracy Evolution

| Version | LOO Acc | Key Change |
|---|---|---|
| v1.2 | 25% | Baseline (3 ragas) |
| v1.2.1 | -- | 6 ragas, vocal isolation |
| v1.2.2 | 64% | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | IDF x Variance scoring |
| v1.2.4 | 78.6% | 72-bin PCD (53 clips) |
| v1.3 | 72.0% | Expanded to 61 clips, dedup, MIN_CLIPS guardrail |

## Remaining Issues
1. Bhairavi: 33% batch eval accuracy (8/11 go UNKNOWN) -- model issue
2. Mohanam: 50% accuracy (9/13 go UNKNOWN) -- model issue
3. Kamboji: 66.7% (5/8 go UNKNOWN) -- needs more clips
4. Score compression for sibling ragas
5. No OOD score floor (margin-only detection)
6. BUG-009: Mix audio causes OOD false positives

## Parked Features
| Feature | Trigger | Sandbox Script |
|---|---|---|
| Hubness correction | Ragas >= 15 | sandbox_hubness.py |
