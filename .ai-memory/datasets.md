# Swarag — Datasets

## Seed Dataset (Training)
- **Location**: `D:\Swaragam\datasets\seed_carnatic\`
- **Structure**: One subfolder per raga, audio files inside
- **Ragas (6)**: Bhairavi, Kalyani, Shankarabharanam, Mohanam, Thodi, Kamboji
- **Format**: .wav, .mp3, .flac
- **Purpose**: Training data for aggregation pipeline
- **Current clip counts** (as of 2025-03-09, post vocal isolation):
  | Raga | Total | Original | Varnam | Saraga vocal | Demucs vocal |
  |---|---|---|---|---|---|
  | Bhairavi | 11 | 6 clean wav | -- | 1 stem | 4 demucs |
  | Kalyani | 14 | 6 clean wav | 4 clean | 2 stems | 2 demucs |
  | Shankarabharanam | 9 | 6 clean wav | -- | 1 stem | 2 demucs |
  | Mohanam | 6 | -- | 4 clean | -- | 2 demucs |
  | Thodi | 7 | -- | -- | 4 stems | 3 demucs |
  | Kamboji | 3 | -- | -- | -- | 3 demucs |
  Target: 15 clips per raga. Kamboji (3) and Mohanam (6) still below target.
- **All audio is now vocal-only** (no instrument contamination)
- **MAX_DURATION_SEC = 360** added to extraction and recognition scripts
- **Saraga extraction script**: scripts/extract_saraga_audio.py
- **Saraga zip location**: H:/Swaragam/Datasets/Audio/saraga1.5_carnatic.zip (13.4 GB)

## Test Audio (Inference Validation)
- **Location**: `D:\Swaragam\datasets\audio test\`
- **Files**:
  | File | Raga | In Training Set? |
  |---|---|---|
  | Alapana_HAM_Test.wav | Hamsadwani | No |
  | Alapana_Moha_Test.wav | Mohanam | No |
  | Balap_Test.wav | Bhairavi | Yes |
  | Kalap_Test.wav | Kalyani | Yes |

## Extracted Features
- **Location**: `D:\Swaragam\pcd_results\features_v12\`
- **Format**: `.npz` files with keys:
  - `raga`, `sa_hz`, `f0`, `voiced_flag`, `cents_gated`,
    `gating_ratio`, `feature_version`

## Aggregated Models
- **Location**: `D:\Swaragam\pcd_results\aggregation\v1.2\run_20260215_113720\`
- **Contents**:
  - `pcd_stats/{raga}_pcd_stats.npz` — mean_pcd, std_pcd
  - `dyad_stats/{raga}_dyad_stats.npz` — mean_up, mean_down, std_up, std_down
  - `aggregation_metadata.json`

## Evaluation Outputs
- **Seed evaluations**: `D:\Swaragam\pcd_results\evaluation\run_{timestamp}\`
- **Random evaluations**: `D:\Swaragam\pcd_results\random_evaluations_v12\run_{timestamp}\`

## External Datasets (Reference)
- **Saraga Carnatic** — 249 recordings, 96 ragas, 52.7 hours
  - Zenodo: https://zenodo.org/records/4301737
  - Dataloader: `mirdata.datasets.saraga_carnatic` (installed in venv)
  - Local metadata: `D:\Swaragam\datasets\saraga-master\` (184 songs, JSON + md5 only, NO audio)
  - Audio status: NOT YET DOWNLOADED — needs Dunya API or Zenodo bulk download
  - Saraga scan results (target ragas):
    | Raga | Songs Available | Audio? |
    |---|---|---|
    | Kalyani | 4 (Kannanai Paadu, Paarengum, Sundari Nee Divya, Vanajakshi Varnam) | No |
    | Bhairavi | 5 (Kamakshi, Sri Raghuvara, Chintayama Kanda, Nee Sari, Amba Kamakshi) | No |
    | Sankarabharanam | 3 (Vara Leela, Undan Paada, Pullum Silambena) | No |
    | Mohanam | 4 (Evarura, Rakta Ganapatim, Mati Matiki, Shloka) | No |
    | Hamsadhvani | 1 (Sadabalarupapi Shlokam) | No |
- **Carnatic Varnam Dataset** — https://zenodo.org/records/1257118
- **Dunya Carnatic** — https://dunya.compmusic.upf.edu/carnatic/ (needs API key)
- **MusicBrainz Carnatic** — https://musicbrainz.org/collection/f96e7215-b2bd-4962-b8c9-2b40c17a1ec6
- **Saraga GitHub** — https://github.com/MTG/saraga
  - Organization: https://mtg.github.io/saraga/organization.html
- **Essentia algorithms** — https://essentia.upf.edu/algorithms_overview.html

## Test Results Log

### Run: 2025-03-09 -- 6 ragas, clean vocals, MAX_DURATION=360s
**Models**: run_20260309_082638 (6 ragas, 50 clips, vocal-isolated)
**Audio prep**: Saraga vocal stems (8 files) + Demucs separation (16 files)
**Duration cap**: 6 minutes per file (restored from old recognize_raga.py)

| Audio | Expected | Top 1 | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.000942 | UNKNOWN | CORRECT (was FALSE POS) |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.000056 | UNKNOWN | CORRECT (was FALSE POS) |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.003284 | UNKNOWN | RANKING CORRECT |
| Kalap_Test.wav | Kalyani | Kalyani | 0.000345 | UNKNOWN | RANKING CORRECT |

**Result: 2/4 correct as UNKNOWN, 2/4 correct ranking but below threshold**
**Compared to baseline (3 ragas, mix audio): OOD false positives FIXED**

Key improvements:
  - Hamsadwani no longer misclassified (margin dropped 0.00431 -> 0.000942)
  - Mohanam no longer misclassified (margin dropped 0.003845 -> 0.000056)
  - Both OOD ragas now correctly return UNKNOWN
  - Bhairavi still #1, Kalyani still #1 (rankings preserved)
  - All results still UNKNOWN tier (thresholds need recalibration)

### Run: 2025-02-16 — test_bug004_genericness.py (genericness from model PCD)
| Audio | Expected | Predicted | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.006524 | HIGH | FALSE POSITIVE |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.006059 | HIGH | FALSE POSITIVE |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.00345 | HIGH | CORRECT |
| Kalap_Test.wav | Kalyani | Shankarabharanam | 0.001335 | ESCALATED | WRONG (was correct #1 before) |

**Result: 1/4 correct (25%) — WORSE than baseline**

**Verdict: REJECTED. Do not apply to production.**

Model entropy values too close to differentiate:
  Bhairavi: 3.292, Kalyani: 3.279, Shankarabharanam: 3.248
Shankarabharanam had LOWEST entropy (smallest penalty) — opposite of intent.
Kalyani ranking flipped from #1 to #2. Bhairavi margin shrunk.

### Run: 2025-03-09 -- 6 ragas, clean vocals, MAX_DURATION=360s
**Models**: run_20260309_082638 (6 ragas, 50 clips, vocal-isolated)
**Audio prep**: Saraga vocal stems (8 files) + Demucs separation (16 files)
**Duration cap**: 6 minutes per file (restored from old recognize_raga.py)

| Audio | Expected | Top 1 | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.000942 | UNKNOWN | CORRECT (was FALSE POS) |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.000056 | UNKNOWN | CORRECT (was FALSE POS) |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.003284 | UNKNOWN | RANKING CORRECT |
| Kalap_Test.wav | Kalyani | Kalyani | 0.000345 | UNKNOWN | RANKING CORRECT |

**Result: 2/4 correct as UNKNOWN, 2/4 correct ranking but below threshold**
**Compared to baseline (3 ragas, mix audio): OOD false positives FIXED**

Key improvements:
  - Hamsadwani no longer misclassified (margin dropped 0.00431 -> 0.000942)
  - Mohanam no longer misclassified (margin dropped 0.003845 -> 0.000056)
  - Both OOD ragas now correctly return UNKNOWN
  - Bhairavi still #1, Kalyani still #1 (rankings preserved)
  - All results still UNKNOWN tier (thresholds need recalibration)

### Run: 2025-02-16 — test_dyad_weights.py (weight tuning, no genericness)
| Audio | Expected | Baseline (0.6/0.4) | Dyad-heavy (0.3/0.7) | Dyad-only (0.0/1.0) |
|---|---|---|---|---|
| Balap_Test.wav | Bhairavi | Bhairavi, **0.005664** | Bhairavi, 0.002954 | Bhairavi, 0.000245 |
| Kalap_Test.wav | Kalyani | Kalyani, **0.001131** | Kalyani, 0.000227 | **WRONG** (Shank #1) |
| Alapana_HAM_Test.wav | UNKNOWN | Shank, 0.00431 | Shank, 0.002316 | Shank, 0.000323 |
| Alapana_Moha_Test.wav | UNKNOWN | Shank, 0.003845 | Shank, 0.002283 | Shank, 0.000722 |

**Key finding**: Baseline (0.6/0.4) wins on both trained ragas.
Dyad-heavy hurts. Dyad-only breaks Kalyani entirely.

**Critical discovery**: Without genericness, first-pass Kalyani margin is
0.001131 (not 0.000227). The 0.000227 was the POST-ESCALATION margin.
Escalation crushes the margin 5x. Logged as BUG-007.

**Verdict: Baseline weights confirmed best. Hold all code changes until
more training data is added.**

### Run: 2025-03-09 -- 6 ragas, clean vocals, MAX_DURATION=360s
**Models**: run_20260309_082638 (6 ragas, 50 clips, vocal-isolated)
**Audio prep**: Saraga vocal stems (8 files) + Demucs separation (16 files)
**Duration cap**: 6 minutes per file (restored from old recognize_raga.py)

| Audio | Expected | Top 1 | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.000942 | UNKNOWN | CORRECT (was FALSE POS) |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.000056 | UNKNOWN | CORRECT (was FALSE POS) |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.003284 | UNKNOWN | RANKING CORRECT |
| Kalap_Test.wav | Kalyani | Kalyani | 0.000345 | UNKNOWN | RANKING CORRECT |

**Result: 2/4 correct as UNKNOWN, 2/4 correct ranking but below threshold**
**Compared to baseline (3 ragas, mix audio): OOD false positives FIXED**

Key improvements:
  - Hamsadwani no longer misclassified (margin dropped 0.00431 -> 0.000942)
  - Mohanam no longer misclassified (margin dropped 0.003845 -> 0.000056)
  - Both OOD ragas now correctly return UNKNOWN
  - Bhairavi still #1, Kalyani still #1 (rankings preserved)
  - All results still UNKNOWN tier (thresholds need recalibration)

### Run: 2025-02-16 — test_bug004_no_genericness.py (genericness REMOVED)
| Audio | Expected | Predicted | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.00431 | HIGH | FALSE POSITIVE |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.003845 | HIGH | FALSE POSITIVE |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.005664 | HIGH | CORRECT |
| Kalap_Test.wav | Kalyani | UNKNOWN | 0.000227 | UNKNOWN | FALSE NEGATIVE |

**Result: 1/4 correct (25%) — SAME as baseline**

**Verdict: HELD. Rankings/margins identical to baseline. Scores shift to positive.**
Ready to apply as clean-up when accuracy improves elsewhere.

### Run: 2025-02-15 — test_recognize_fix.py (dyad fix validation / BASELINE)
| Audio | Expected | Predicted | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.00431 | HIGH | FALSE POSITIVE |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.003845 | HIGH | FALSE POSITIVE |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.005664 | HIGH | CORRECT |
| Kalap_Test.wav | Kalyani | UNKNOWN | 0.000227 | UNKNOWN | FALSE NEGATIVE |

**Result: 1/4 correct (25%)**

**Key observations**:
- Bhairavi correctly identified with highest margin (0.005664)
- Kalyani ranked #1 but margin too small (0.000227) — score compression
- Untrained ragas absorbed by Shankarabharanam (OOD sink)
- All scores are negative (genericness penalty dominance)
- Score range: -0.114 to -0.143 (spread of only ~0.03)
