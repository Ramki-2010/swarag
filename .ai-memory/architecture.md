# Swarag — Architecture (Current State)

## Version
Swarag v1.2 — Deterministic DSP Pipeline

## Pipeline

```
Audio (.wav / .mp3 / .flac)
  |
  v
Pitch Extraction (pYIN via librosa)
  |
  v
Tonic (Sa) Estimation (utils.py -> estimate_tonic)
  |  histogram-based + octave-aware candidate scoring
  v
Pitch Normalization (cents relative to Sa, folded to 0-1200)
  |
  v
Feature Computation
  |-- PCD: 36-bin pitch class distribution
  +-- Directional Dyads: stable-region detection + Laplace smoothing
      |-- mean_up   (ascending transitions, 36x36 matrix)
      +-- mean_down (descending transitions, 36x36 matrix)
  |
  v
Raga Scoring
  |-- Dot-product similarity (PCD + Dyads)
  |-- Weighted fusion (PCD_WEIGHT=0.6, DYAD_WEIGHT=0.4)
  |-- Genericness penalty (Shannon entropy, weight=0.05)
  +-- Tiered confidence:
      |-- HIGH:      margin >= MARGIN_STRICT (0.05 production / 0.003 test)
      |-- ESCALATED: re-score with dyad-heavy weights (0.3/0.7)
      +-- UNKNOWN:   margin < MIN_MARGIN_FINAL
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

## Support Scripts

| Script | Purpose |
|---|---|
| `test_recognize_fix.py` | Baseline validation of dyad fix |
| `test_bug004_genericness.py` | BUG-004 fix attempt 1 — REJECTED |
| `test_bug004_no_genericness.py` | BUG-004 fix attempt 2 — HELD |
| `test_dyad_weights.py` | Weight tuning test (baseline vs dyad-heavy vs dyad-only) |

## Trained Ragas (3 current, 6 planned)
- Bhairavi (6 clips)
- Kalyani (10 clips)
- Shankarabharanam (6 clips)
- Mohanam (4 clips — newly added from Carnatic Varnam, not yet aggregated)
- Thodi (0 clips — awaiting Saraga extraction)
- Kamboji (0 clips — awaiting Saraga extraction)

## Aggregation Data Location
```
D:\Swaragam\pcd_results\aggregation\v1.2\run_20260309_082638\
  pcd_stats\    -> {raga}_pcd_stats.npz
  dyad_stats\   -> {raga}_dyad_stats.npz
  aggregation_metadata.json
```

## Shared Constants (must be identical in aggregate + recognize)

| Constant | Value | Used In |
|---|---|---|
| N_BINS | 36 | aggregate_all_v12.py, recognize_raga_v12.py, test_recognize_fix.py |
| MIN_STABLE_FRAMES | 5 | aggregate_all_v12.py, recognize_raga_v12.py, test_recognize_fix.py |
| ALPHA | 0.5 | aggregate_all_v12.py, recognize_raga_v12.py, test_recognize_fix.py |
| EPS | 1e-8 | aggregate_all_v12.py, recognize_raga_v12.py, test_recognize_fix.py |

## Frozen Output Schema
```python
{ "final": str, "ranking": list, "margin": float }
```
Plus optional `"confidence_tier": str` added in v1.2.

## Known Architectural Issues
1. BUG-002: Shankarabharanam sink — no OOD rejection
2. BUG-003: Score compression between sibling ragas
3. BUG-004: Genericness penalty does not affect ranking (inert)
4. BUG-005: ESCALATION_MARGIN dead code
5. BUG-006: Margin thresholds miscalibrated
6. BUG-007: Escalation path crushes Kalyani margin (0.001131 → 0.000227)

## Current Decision: Data Before Code
All code changes (genericness removal, escalation fix, threshold tuning)
are HELD until training data is expanded from 6 to 15-20 clips per raga.
Models built from 6 clips are too noisy for meaningful code tuning.
