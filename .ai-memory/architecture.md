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
  |-- Weighted fusion (PCD_WEIGHT=0.7, DYAD_WEIGHT=0.3)
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

## Trained Ragas (v1.3: 5 ragas, 55 clips)

| Raga | Clips | LOO Acc (decided) |
|---|---|---|
| Thodi | 11 | 83% |
| Kalyani | 14 | 80% |
| Bhairavi | 11 | 50% |
| Shankarabharanam | 9 | 50% |
| Mohanam | 10 | 17% |

### Staged Ragas (excluded by MIN_CLIPS_PER_RAGA=5 guardrail)
- Kamboji: 3 clips (needs 2 more; 3 Harikambhoji removed, BUG-013)
- Madhyamavati: 2-3 clips (needs 2-3 more)
- Hamsadhvani: 1 clip (needs 4 more)

### Ragas Pending Activation (varnam extraction in progress 2026-03-21)
- Abhogi: 2 existing + 5 new varnams (Zenodo) = 7 clips -> WILL PASS guardrail
- Saveri: 3 existing + 5 new varnams (Zenodo) = 8 clips -> WILL PASS guardrail
- NOTE: extract_new_clips.py skipped Saveri varnams due to BUG-014, needs re-run

## Aggregation Data Location
```
D:\Swaragam\pcd_results\aggregation\v1.2\run_20260321_135629\
  pcd_stats\    -> {raga}_pcd_stats.npz (5 ragas)
  dyad_stats\   -> {raga}_dyad_stats.npz (5 ragas)
  aggregation_metadata.json  (alpha=0.01, bins=72, 55 clips, min_clips=5)
```

## Feature Storage
```
D:\Swaragam\pcd_results\features_v12\           ~65+ .npz files (55 modeled + Abhogi varnams extracted, Saveri pending)
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

## Current Accuracy (v1.3, LOO, 5 ragas, 55 clips)

| Metric | Value |
|---|---|
| Accuracy (decided) | 58.8% |
| Correct | 20 |
| Wrong | 14 |
| Unknown | 21 (38%) |
| Thodi sink | 5/14 wrongs |

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

## Remaining Issues
1. Mohanam: 17% LOO -- worst raga, needs diverse clips
2. Bhairavi: 50% LOO -- PCD overlaps 78% with Thodi, identity is in gamakas
3. Kamboji: excluded (only 3 real clips after Harikambhoji cleanup)
4. BUG-014: extract_new_clips.py skips Saveri varnams (substring matching bug)
5. Abhogi + Saveri varnams ready to activate after BUG-014 fix
6. Per-raga dyad weight tested: Bhairavi=0.5/0.5 -> 90% but tanks Thodi
7. No OOD score floor (margin-only detection)
8. BUG-009: Mix audio causes OOD false positives

## Per-Raga Dyad Weight Sandbox Results (2026-03-21)
| Config | Bhairavi | Kalyani | Thodi | Overall |
|---|---|---|---|---|
| Baseline 0.7/0.3 | 50% | 80% | 83% | 58.8% |
| Bhairavi=0.5/0.5 | 90% | 89% | 43% | 61.5% |
| Bhairavi=0.4/0.6 | 90% | 73% | 0% | 53.8% |
| Global 0.8/0.2 | 67% | 89% | 100% | 65.5% |

## Parked Features
| Feature | Trigger | Sandbox Script |
|---|---|---|
| Hubness correction | Ragas >= 15 | sandbox_hubness.py |
