# Swarag -- Carnatic Raga Identification Engine

Swarag is a deterministic Carnatic raga recognition engine built using interpretable signal processing and structured statistical modeling. It emphasizes explainability, musical grammar, and bias correction over black-box learning.

## Version: v1.3.2

v1.3.2 retires the Bhairavi per-raga weight override:
- Canonical LOO audit found the override scored 0% decided for Bhairavi
  (9 wrongs) -- confirmed counter-productive, not just unproven
- All 7 ragas now use uniform PCD=0.8/Dyad=0.2 weighting
- LOO accuracy: 64.1% decided (25c/14w/31u), sandbox_loo_v131_canonical.py
- Weakest raga is now Bhairavi (14%, needs diverse clips) rather than
  Abhogi (33%, structural janya problem -- see L-044, BUG-015)
- A prior 67.4% figure was found fabricated (per-raga rows never summed
  to their stated total) and has been retired from all documentation

### Version History

| Version | Accuracy | Ragas | Key Change |
|---|---|---|---|
| v1.2 | 25% | 3 | Baseline |
| v1.2.1 | -- | 6 | Vocal isolation, OOD fixed |
| v1.2.2 | 64% | 6 | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | 6 | IDF x Variance scoring |
| v1.2.4 | 78.6% | 6 | 72-bin PCD |
| v1.2.5 | 72.0% | 6 | Expanded data, dedup, MIN_CLIPS guardrail |
| v1.3 | 58.8% | 5 | Harikambhoji removed, weights 0.7/0.3, honest baseline |
| v1.3.1 | 60.5% | 7 | Abhogi+Saveri activated, 0.8/0.2, Bhairavi override (later confirmed counter-productive) |
| v1.3.2 | 64.1% | 7 | Bhairavi override retired, uniform 0.8/0.2 for all ragas |

## Core Philosophy

- Relative pitch, not absolute frequency
- Behavioral transitions over scale checklists
- Preserve musical micro-structure
- Vocal-only audio for clean pitch extraction

All modeling is tonic-normalized (Sa).

## Pipeline

```
Audio (.wav / .mp3 / .flac)
  |
  v
Vocal Isolation (Saraga multitrack stems or Demucs htdemucs)
  |
  v
Pitch Extraction (pYIN via librosa, 6-min cap)
  |
  v
Tonic (Sa) Estimation (histogram-based, octave-aware)
  |
  v
Pitch Normalization (cents relative to Sa, folded to 0-1200)
  |
  v
Feature Computation
  |-- PCD: 72-bin pitch class distribution (17 cents per bin)
  +-- Directional Dyads: ascending (mean_up) + descending (mean_down)
  |
  v
Raga Scoring
  |-- IDF x Variance weighted dot-product (PCD + Dyads)
  |-- Weighted fusion (PCD=0.8, Dyad=0.2; Bhairavi override: 0.5/0.5)
  |-- Per-raga weight overrides for transition-heavy ragas
  |-- MIN_CLIPS_PER_RAGA guardrail (excludes thin-data ragas)
  +-- Tiered confidence: HIGH / MODERATE / UNKNOWN
  |
  v
Output: { "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Ragas Currently Modeled

| Raga | Training Clips | LOO Accuracy |
|---|---|---|
| Thodi | 11 | 100% |
| Saveri | 8 | 88% |
| Shankarabharanam | 9 | 86% |
| Kalyani | 14 | 67% |
| Bhairavi | 11 | 40% (0.5/0.5 override) |
| Mohanam | 10 | 33% |
| Abhogi | 7 | 25% |

### Staged / Excluded (need more data)

| Raga | Current Clips | Status |
|---|---|---|
| Kamboji | 3 | Needs 2+ real clips (Harikambhoji removed) |
| Madhyamavati | 2 | Needs 3 more |
| Hamsadhvani | 1 | Needs 4 more |

## Repository Structure

```
scripts/                        Active v1.3.1 pipeline
  recognize_raga_v12.py             Inference engine (72-bin, IDF x Variance, 0.8/0.2 + Bhairavi 0.5/0.5)
  aggregate_all_v12.py              Build raga models (with MIN_CLIPS guardrail)
  extract_pitch_batch_v12.py        Feature extraction (with 6-min cap)
  batch_evaluate.py                 Evaluation on seed dataset (per-file timeout)
  batch_evaluate_random.py          Evaluation on unknown clips
  utils.py                          Shared utilities (tonic estimation)
  sandbox_*.py                      Phase 2-4 sandbox test scripts
  archive/                          Deprecated pre-v1.2 scripts

.ai/                            AI agent specification
.ai-memory/                     Project memory (bugs, lessons, architecture)
docs/                           Documentation and visual assets
```

## Installation

```bash
pip install -r requirements.txt
```

## Run Pipeline

```bash
python extract_pitch_batch_v12.py    # Step 1: Extract features
python aggregate_all_v12.py          # Step 2: Build models
python batch_evaluate.py             # Step 3: Evaluate
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the development loop and sandbox-first rule.
See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT License -- see [LICENSE](LICENSE).
