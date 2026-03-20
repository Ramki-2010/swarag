# Swarag — Architecture (Current State)

## Version
Swarag v1.2.4 — Deterministic DSP Pipeline (Phase 4: 72-bin PCD + IDF x Variance + hubness parked)

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
  |-- PCD: 72-bin pitch class distribution (Phase 4: was 36)
  +-- Directional Dyads: stable-region detection + Laplace smoothing
      |-- mean_up   (ascending transitions, 72x72 matrix)
      +-- mean_down (descending transitions, 36x36 matrix)
      |-- ALPHA=0.01 (Phase 2 fix: was 0.5, which destroyed dyad signal)
  |
  v
Raga Scoring
  |-- IDF x Variance weighted dot-product (PCD + Dyads)
  |-- Weighted fusion (PCD_WEIGHT=0.6, DYAD_WEIGHT=0.4)
  |-- Genericness penalty REMOVED (GENERICNESS_WEIGHT=0.0, BUG-004)
  |-- Escalation DISABLED (BUG-007: crushed margins 5x)
  +-- Tiered confidence:
      |-- HIGH:     margin >= 0.003 (MARGIN_STRICT)
      |-- MODERATE: margin >= 0.001 (MIN_MARGIN_FINAL)
      +-- UNKNOWN:  margin < 0.001
  |
  v
Output: { "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Core Scripts (6 active files in scripts/)

| Script | Responsibility |
|---|---|
| `extract_pitch_batch_v12.py` | Pitch extraction + feature creation |
| `aggregate_all_v12.py` | Builds raga statistical models |
| `recognize_raga_v12.py` | Inference engine |
| `batch_evaluate.py` | Evaluation on known (seed) dataset |
| `batch_evaluate_random.py` | Evaluation on unknown/random clips |
| `utils.py` | Shared utilities (tonic estimation) |

## Sandbox Scripts (Phase 1-2 investigation)

| Script | Purpose |
|---|---|
| `sandbox_phase1_fast.py` | PCD-only scoring test (cached features) |
| `sandbox_phase2_alpha.py` | ALPHA comparison (0.5 vs 0.01), weight grid |
| `sandbox_phase1_pcd_only.py` | Original PCD-only sandbox (full extraction) |
| `diag_scores.py` | Score breakdown per raga per test file |
| `diag_alpha.py` | Laplace ALPHA impact analysis (transition counts) |
| `sandbox_phase3_thodi_sink.py` | Phase 3: IDF vs mean-sub vs cosine scoring |
| `sandbox_phase3b_variance.py` | Phase 3b: IDF vs variance vs combined (Method E) |
| `sandbox_phase4_bins.py` | Phase 4: PCD bin resolution (36/48/60/72/96/120) |
| `sandbox_phase4_production.py` | Phase 4: 72-bin production test (cached features) |
| `sandbox_loo_validation.py` | LOO cross-validation (36 vs 72 bins) |
| `sandbox_hubness.py` | Hubness correction test (LOO, PARKED) |
| `extract_new_thodi.py` | Feature extraction for 5 new Thodi clips |

## Legacy Support Scripts (in scripts/ or scripts/archive/)

| Script | Purpose |
|---|---|
| `test_recognize_fix.py` | Baseline validation of dyad fix |
| `test_bug004_genericness.py` | BUG-004 fix attempt 1 — REJECTED |
| `test_bug004_no_genericness.py` | BUG-004 fix attempt 2 — APPLIED |
| `test_dyad_weights.py` | Weight tuning test (baseline vs dyad-heavy vs dyad-only) |

## Trained Ragas (6 ragas, 53 clips)

| Raga | Clips | Sources |
|---|---|---|
| Bhairavi | 11 | 6 clean wav + 1 stem + 4 demucs |
| Kalyani | 14 | 6 clean wav + 4 varnam + 2 stems + 2 demucs |
| Shankarabharanam | 9 | 6 clean wav + 1 stem + 2 demucs |
| Thodi | 10 | 3 stems + 2 demucs (old) + 5 demucs (new external) |
| Mohanam | 6 | 4 varnam + 2 demucs |
| Kamboji | 3 | 3 demucs |

Note: 2 Thodi outliers excluded (Munnu Ravana, Koluvamaregatha) —
moved to features_v12/excluded/ and seed_carnatic/Thodi/excluded/.
Munnu Ravana: entropy 2.4 (too concentrated, skewed model).
Koluvamaregatha: low consistency with other Thodi clips (sim_to_mean=0.050).

## Aggregation Data Location
```
D:\Swaragam\pcd_results\aggregation\v1.2\run_20260312_205842_72bins\
  pcd_stats\    -> {raga}_pcd_stats.npz
  dyad_stats\   -> {raga}_dyad_stats.npz
  aggregation_metadata.json  (alpha=0.01, bins=72, 53 files)
```

## Shared Constants (must be identical in aggregate + recognize)

| Constant | Value | Notes |
|---|---|---|
| SR | 22050 | Sample rate |
| MAX_DURATION_SEC | 360 | 6-minute cap per file |
| N_BINS | **72** | PCD and dyad bins |
| MIN_STABLE_FRAMES | 5 | Stable region threshold |
| ALPHA | **0.01** | **Phase 2 fix: was 0.5** |
| EPS | 1e-8 | Division safety |
| PCD_WEIGHT | 0.6 | Scoring weight |
| DYAD_WEIGHT | 0.4 | Scoring weight |
| GENERICNESS_WEIGHT | 0.0 | Disabled (BUG-004 fix) |
| MARGIN_STRICT | 0.003 | HIGH confidence threshold |
| MIN_MARGIN_FINAL | 0.001 | MODERATE confidence threshold |

## Frozen Output Schema
```python
{ "final": str, "ranking": list, "margin": float }
```
Plus optional `"confidence_tier": str` added in v1.2.

## Resolved Architectural Issues
- BUG-004: Genericness penalty removed (GENERICNESS_WEIGHT=0.0)
- BUG-005: Escalation disabled entirely
- BUG-006: Thresholds recalibrated (0.003/0.001)
- BUG-007: Escalation disabled (was crushing margins 5x)

## Remaining Architectural Issues
1. BUG-008: Thodi sink — Thodi model attracts other ragas (10/18 wrongs)
2. BUG-003: Score compression (improved but not eliminated)
3. Bhairavi test file misclassifies as Thodi (shared komal swaras)
4. Kamboji has only 3 clips (below 15-clip target)
5. No OOD score floor (margin-only detection, Phase 3 planned)

## Phase 2 Key Finding: ALPHA Impact on Dyad Discrimination
| ALPHA | Discrimination Ratio | Dyad Sim Range | Status |
|---|---|---|---|
| 0.5 (old) | 1.24x avg | 0.0009 - 0.0016 | Essentially noise |
| **0.01 (new)** | **1.73x avg** | **0.005 - 0.023** | **Real signal** |



## Phase 4 Key Finding: 72-bin PCD Resolution
- 36 bins (33 cents/bin) too coarse: shuddha Ma and prati Ma only 2-3 bins apart
- 72 bins (17 cents/bin): Ma1 and Ma2 are 6 bins apart -> separates Kalyani/Shankarabharanam
- LOO accuracy: 66.7% (36-bin) -> 78.6% (72-bin) = +11.9%
- Wrongs halved: 14 -> 6. Thodi sink: 5/14 -> 1/6
- 96+ bins causes margin collapse (too sparse for 53 clips)
- Pure code change, no new data needed

## Hubness Correction (PARKED for 15+ ragas)
- Centered correction: score = raw - avg_sim[raga] + global_mean
- Eliminates Thodi sink (0/8) but drops LOO accuracy 78.6% -> 74.2%
- Multi-agent analysis: unanimously park (bias values below noise floor at 6 ragas)
- Trigger: re-test when raga count >= 15 (sandbox_hubness.py ready)

## Phase 3 Key Finding: IDF x Variance PCD Weighting
- Common swaras (Sa, Pa, Ni) downweighted by IDF (present in all ragas)
- Low-variance bins downweighted (ragas agree -> not distinctive)
- High-variance bins upweighted (ragas differ -> distinctive swaras)
- Formula: weight = idf / (std + eps), normalized to sum = N_BINS
- Thodi sink: 93% -> 38% of wrongs
- Kamboji: 50% -> 100%, Kalyani: 62% -> 75%
- Sandbox predicted 83% (self-eval), production got 70% (real)
## Current Accuracy (Phase 2 sandbox, ALPHA=0.01, 0.6/0.4)
- 53 seed clips: 27 HIGH + 2 MOD = 29 correct, 16 WRONG, 8 UNKNOWN
- Accuracy (excl UNKNOWN): **78.6% LOO** (72-bin IDF x Variance)
- OOD: Both Hamsadwani and Mohanam correctly return UNKNOWN
- Phase 3 Method E (IDF x Variance) applied: 64% -> 70%
- Blind test (mix audio): 38% known, 25% OOD rejection (BUG-009)
- Vocal isolation is mandatory for reliable results (L-028)
