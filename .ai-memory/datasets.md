# Swarag — Datasets

## Seed Dataset (Training)
- **Location**: `D:\Swaragam\datasets\seed_carnatic\`
- **Structure**: One subfolder per raga, audio files inside
- **Ragas (10)**: Bhairavi, Kalyani, Shankarabharanam, Mohanam, Thodi, Kamboji, Abhogi, Saveri, Madhyamavati, Hamsadhvani
- **Format**: .wav, .mp3, .flac
- **Purpose**: Training data for aggregation pipeline
- **Current clip counts** (as of 2026-03-10, post Phase 2):
  | Raga | Total | Sources |
  |---|---|---|
  | Bhairavi | 11 | 6 clean wav + 1 stem + 4 demucs |
  | Kalyani | 14 | 6 clean wav + 4 varnam + 2 stems + 2 demucs |
  | Shankarabharanam | 9 | 6 clean wav + 1 stem + 2 demucs |
  | Thodi | 10 | 3 stems + 2 demucs (old) + 5 demucs (new external) |
  | Mohanam | 6 | 4 varnam + 2 demucs |
  | Kamboji | 3 | 3 real Kamboji (3 Harikambhoji removed to excluded/, BUG-013) |
  | Abhogi | 7 | 2 demucs + 5 varnams (Zenodo, extracted 2026-03-21) |
  | Saveri | 8 | 3 demucs/stems + 5 varnams (Zenodo, extraction pending BUG-014) |
  | Madhyamavati | 2-3 | demucs |
  | Hamsadhvani | 1 | demucs |
  **Total: 55 clips modeled (5 ragas), ~65+ features total, 5 ragas staged**
  Target: 15 clips per raga. Kamboji (3) and Mohanam (6) still below target.
  **Excluded clips** (moved to excluded/ folders, not deleted):
  - Munnu Ravana (Thodi): entropy 2.4, too concentrated, skewed model
  - Koluvamaregatha (Thodi): low consistency (sim_to_mean=0.050)
- **All audio is now vocal-only** (no instrument contamination)
- **MAX_DURATION_SEC = 360** added to extraction and recognition scripts
- **Saraga extraction script**: scripts/extract_saraga_audio.py
- **Saraga zip location**: H:/Swaragam/Datasets/Audio/saraga1.5_carnatic.zip (13.4 GB)
- **New Thodi external sources** (2026-03-10):
  - `H:\Swaragam\Datasets\Audio\Thodi\` — 5 mp3 files (Malladi Bros, MS Subbulakshmi, etc.)
  - `H:\Swaragam\Datasets\Audio\archive.zip` (3.9 GB) — CompMusic/Dunya dataset
    (7 Todi recordings — same as Saraga, no new audio; has pre-computed pitch tracks)

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
- **36-bin models**: `D:\Swaragam\pcd_results\aggregation\v1.2\run_20260310_085601\`
- **72-bin models (v1.2.4)**: `D:\Swaragam\pcd_results\aggregation\v1.2\run_20260312_205842_72bins\`
- **72-bin models (v1.3 current)**: `D:\Swaragam\pcd_results\aggregation\v1.2\run_20260321_135629\` (5 ragas, 55 clips, PCD=0.7/Dyad=0.3)
- **ALPHA**: 0.01 (Phase 2 fix, was 0.5)
- **Contents**:
  - `pcd_stats/{raga}_pcd_stats.npz` — mean_pcd, std_pcd
  - `dyad_stats/{raga}_dyad_stats.npz` — mean_up, mean_down, std_up, std_down
  - `aggregation_metadata.json`
- **Previous runs** (kept for comparison):
  - `run_20260309_082638` — 50 clips, ALPHA=0.5 (original 6-raga model)
  - `run_20260310_004343` — 48 clips, ALPHA=0.5 (after removing 2 Thodi outliers)
  - `run_20260310_063600` — 53 clips, ALPHA=0.5 (after adding 5 new Thodi)

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
  - Local zip: `D:\Swaragam\datasets\carnatic_varnam_1.0.zip` (28 recordings, 7 ragas)
  - 7 ragas: Abhogi(5), Begada(3), Kalyani(4), Mohanam(4), Sahana(4), Saveri(5), Sri(3)
  - Used: Kalyani(4), Mohanam(4), Abhogi(5 new), Saveri(5 new, pending BUG-014)
  - Available for future: Begada(3), Sahana(4), Sri(3)
- **Dunya Carnatic** — https://dunya.compmusic.upf.edu/carnatic/ (needs API key)
- **MusicBrainz Carnatic** — https://musicbrainz.org/collection/f96e7215-b2bd-4962-b8c9-2b40c17a1ec6
- **Saraga GitHub** — https://github.com/MTG/saraga
  - Organization: https://mtg.github.io/saraga/organization.html
- **Essentia algorithms** — https://essentia.upf.edu/algorithms_overview.html

## Test Results Log

### Run: 2026-03-21 -- v1.3 LOO (5 ragas, 55 clips, Harikambhoji cleaned)
**Models**: run_20260321_135629 (5 ragas, 55 clips)
**Weights**: PCD=0.7, Dyad=0.3
**Scoring**: IDF x Variance, 72 bins, ALPHA=0.01

**LOO Cross-Validation**:
| Raga | Clips | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Thodi | 11 | 5 | 1 | 5 | 83% |
| Kalyani | 14 | 8 | 2 | 4 | 80% |
| Bhairavi | 11 | 2 | 2 | 7 | 50% |
| Shankarabharanam | 9 | 4 | 4 | 1 | 50% |
| Mohanam | 10 | 1 | 5 | 4 | 17% |
| **TOTAL** | **55** | **20** | **14** | **21** | **58.8%** |

Sink analysis: Thodi=5, Kalyani=6, Bhairavi=2, Shankarabharanam=1

**Per-raga dyad weight sandbox** (same session):
| Config | Bhairavi | Kalyani | Thodi | Overall |
|---|---|---|---|---|
| Baseline 0.7/0.3 | 50% | 80% | 83% | 58.8% |
| Bhairavi=0.5/0.5 | 90% | 89% | 43% | 61.5% |
| Global 0.8/0.2 | 67% | 89% | 100% | 65.5% |

**Key findings:**
1. Harikambhoji removal dropped accuracy from 72% to 58.8% (honest)
2. Thodi sink returns at 5 ragas (5/14 wrongs) vs 1/7 at 6 ragas
3. Mohanam worst at 17% -- 5/10 clips go wrong
4. Per-raga weight override is a trade not a fix (Bhairavi up = Thodi down)
5. Carnatic Varnam zip had 5 Abhogi + 5 Saveri varnams ready to extract
6. extract_new_clips.py bug skips Saveri varnams (BUG-014)


**Models**: run_20260320_222322 (6 ragas, 61 clips, MIN_CLIPS_PER_RAGA=5)
**Eval output**: run_20260321_004951
**Scoring**: IDF x Variance, 72 bins, ALPHA=0.01, PER_FILE_TIMEOUT=360s

**Seed Dataset (81 audio files, all ragas including non-modeled)**:
| Raga | Has Model | Total | Correct | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Kalyani | Y | 14 | 10 | 4 | 100% |
| Thodi | Y | 10 | 10 | 0 | 100% |
| Shankarabharanam | Y | 9 | 7 | 1 | 87.5% |
| Kamboji | Y | 8 | 2 | 5 | 66.7% |
| Mohanam | Y | 13 | 2 | 9 | 50% |
| Bhairavi | Y | 11 | 1 | 8 | 33.3% |
| Abhogi | N | 4 | 0 | 3 | 0% (no model) |
| Madhyamavati | N | 4 | 0 | 4 | 0% (all UNKNOWN, correct) |
| Saveri | N | 7 | 0 | 3 | 0% (4 -> Thodi) |
| Hamsadhvani | N | 1 | 0 | 0 | 0% (-> Kalyani) |
| **TOTAL** | | **81** | **32** | **37** | **72.7%** |

**LOO Cross-Validation (6 ragas, 61 clips)**:
| Raga | Clips | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Bhairavi | 11 | 2 | 1 | 8 | 67% |
| Kalyani | 14 | 7 | 1 | 6 | 88% |
| Kamboji | 5 | 0 | 1 | 4 | 0% |
| Mohanam | 11 | 1 | 3 | 7 | 25% |
| Shankarabharanam | 9 | 3 | 1 | 5 | 75% |
| Thodi | 11 | 5 | 0 | 6 | 100% |
| **TOTAL** | **61** | **18** | **7** | **36** | **72.0%** |

**Key findings:**
1. Thodi: PERFECT (10/10 batch, 100% LOO) -- sink completely fixed
2. Kalyani: PERFECT decided (10/10 batch, 88% LOO)
3. Bhairavi: WEAK (33% batch, 67% LOO) -- most clips go UNKNOWN, model issue
4. Mohanam: WEAK (50% batch, 25% LOO) -- most clips go UNKNOWN
5. Non-modeled ragas: Madhyamavati correctly all UNKNOWN; Saveri leaks to Thodi
6. Hamsadhvani -> Kalyani false positive (subset raga, expected)

### Run: 2026-03-10 -- Phase 2 ALPHA fix (sandbox_phase2_alpha.py)
**Models**: ALPHA=0.01 in-memory aggregation (53 clips, 6 ragas)
**Change**: ALPHA 0.5 -> 0.01, tested weight combos: 1.0/0.0, 0.8/0.2, 0.7/0.3, 0.6/0.4

**Dyad Discrimination Improvement**:
| ALPHA | Mean Ratio | Status |
|---|---|---|
| 0.5 (old) | 1.24x | Noise |
| 0.01 (new) | 1.73x | Real signal |

**Random Test Files (ALPHA=0.01, 0.6/0.4)**:
| Audio | Expected | Top 1 | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.000672 | UNKNOWN | CORRECT |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.000254 | UNKNOWN | CORRECT |
| Balap_Test.wav | Bhairavi | Thodi | 0.004447 | HIGH | WRONG (Thodi sink) |
| Kalap_Test.wav | Kalyani | Kalyani | 0.006558 | HIGH | CORRECT |

**Seed Dataset Accuracy (0.6/0.4, ALPHA=0.01)**: 64% (best ever)

**Result: 0.6/0.4 with ALPHA=0.01 applied to production.**


### Run: 2026-03-12 -- Hubness correction sandbox (LOO, 72 bins)
**Script**: sandbox_hubness.py
**Method**: Centered hubness correction (score = raw - avg_sim + global_mean)
**Validation**: Leave-one-out cross-validation (true held-out)

| Method | Correct | Wrong | Unknown | Acc (decided) | Thodi Sink |
|---|---|---|---|---|---|
| 72-bin IDF x Var (no hubness) | 22 | 6 | 25 (47%) | 78.6% | 1/6 |
| 72-bin IDF x Var + hubness | 23 | 8 | 22 (42%) | 74.2% | 0/8 |

Per-raga (with hubness): Bhairavi 75%, Kalyani 88%, Kamboji 50%,
Mohanam 25%, Shankarabharanam 86%, Thodi 100%.
**Verdict: PARKED** -- accuracy drops 4.4%. Revisit at 15+ ragas (BUG-010).

### Run: 2026-03-12 -- LOO cross-validation (36 vs 72 bins)
**Script**: sandbox_loo_validation.py
**Method**: Leave-one-out with IDF x Variance scoring
**Purpose**: True held-out accuracy (no self-evaluation bias)

| Bins | Correct | Wrong | Unknown | Acc (decided) | Thodi Sink |
|---|---|---|---|---|---|
| 36 | 28 | 14 | 11 (21%) | 66.7% | 5/14 |
| 72 | 22 | 6 | 25 (47%) | 78.6% | 1/6 |

Per-raga (72-bin LOO): Thodi 100%, Kalyani 90%, Shankarabharanam 80%,
Bhairavi 67%, Kamboji 0% (all UNKNOWN, only 3 clips), Mohanam 25%.
72 bins: +11.9% accuracy, wrongs halved, Thodi sink nearly eliminated.
UNKNOWN rate higher (47%) due to tighter margins at finer resolution.

### Run: 2026-03-12 -- Phase 4 production test (72 bins, cached features)
**Script**: sandbox_phase4_production.py
**Models**: run_20260312_205842_72bins (72-bin aggregation)
**Scoring**: IDF x Variance weighted PCD (72 bins)

| Raga | Total | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Thodi | 10 | 8 | 0 | 2 | 100% |
| Kamboji | 3 | 3 | 0 | 0 | 100% |
| Kalyani | 14 | 12 | 0 | 2 | 100% |
| Shankarabharanam | 9 | 7 | 1 | 1 | 88% |
| Bhairavi | 11 | 5 | 1 | 5 | 83% |
| Mohanam | 6 | 2 | 2 | 2 | 50% |
| **TOTAL** | **53** | **37** | **4** | **12** | **90%** |

Note: 90% is self-eval (same clips for model and test). True LOO accuracy is 78.6%.

### Run: 2026-03-12 -- Phase 4 bin resolution sandbox
**Script**: sandbox_phase4_bins.py
**Method**: IDF x Variance scoring at 36/48/60/72/96/120 bins

| Bins | Correct | Wrong | Unknown | Acc | Thodi Sink |
|---|---|---|---|---|---|
| 36 | 35 | 7 | 11 | 83% | 1/7 |
| 48 | 35 | 4 | 14 | 90% | 0/4 |
| 72 | 37 | 4 | 12 | 90% | 0/4 |
| 96 | 26 | 1 | 26 | 96%* | 0/1 |
| 120 | 17 | 1 | 35 | 94%* | 0/1 |

*96/120: inflated accuracy due to 49-66% UNKNOWN rate. Too fine.
Winner: 72 bins (most correct, lowest wrongs, reasonable UNKNOWN).

### Run: 2026-03-12 -- Method E production batch (IDF x Variance, v1.2.3)
**Models**: run_20260310_085601 (53 clips, 6 ragas, ALPHA=0.01)
**Scoring**: IDF x Variance weighted PCD (Phase 3 BUG-008 fix)
**Eval output**: run_20260311_235231

**Seed Dataset (53 clips, vocal-only)**:
| Raga | Total | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Thodi | 10 | 10 | 0 | 0 | 100% |
| Kamboji | 3 | 3 | 0 | 0 | 100% |
| Kalyani | 14 | 9 | 3 | 2 | 75% |
| Shankarabharanam | 9 | 4 | 3 | 2 | 57% |
| Bhairavi | 11 | 3 | 4 | 4 | 43% |
| Mohanam | 6 | 2 | 3 | 1 | 40% |
| **TOTAL** | **53** | **31** | **13** | **9** | **70%** |

Overall: Acc(all)=58%, Acc(decided)=70%, Unknown=17%

**Comparison with baseline (v1.2.2)**:
| Metric | Baseline | Method E | Change |
|---|---|---|---|
| Accuracy (decided) | 64% | 70% | +6% |
| Correct | 28 | 31 | +3 |
| Wrong | 15 | 13 | -2 |
| Thodi sink | 14/15 (93%) | ~5/13 (38%) | halved |
| Kamboji | 50% | 100% | +50% |
| Kalyani | 62% | 75% | +13% |

Sandbox predicted 83% (self-eval). Production got 70% (real).
ChatGPT predicted ~75% for held-out -- very close to actual 70%.
### Run: 2026-03-11 -- Production batch evaluation (v1.2.2, ALPHA=0.01)
**Models**: run_20260310_085601 (53 clips, 6 ragas, ALPHA=0.01)
**Eval output**: run_20260311_000811

**Seed Dataset (53 clips, vocal-only)**:
| Raga | Total | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Thodi | 10 | 10 | 0 | 0 | 100% |
| Kalyani | 14 | 8 | 5 | 1 | 62% |
| Shankarabharanam | 9 | 5 | 3 | 1 | 63% |
| Mohanam | 6 | 2 | 1 | 3 | 67% |
| Kamboji | 3 | 1 | 1 | 1 | 50% |
| Bhairavi | 11 | 2 | 5 | 4 | 29% |
| **TOTAL** | **53** | **28** | **15** | **10** | **64%** |

Overall: Acc(all)=53%, Acc(decided)=64%, Unknown=17%
Thodi: 10/10 perfect. Thodi sink: 14/15 wrongs go to Thodi.

**Blind Test (16 files, mix audio from archive.zip + original 4)**:
Known ragas: 3/8 correct (38%). OOD: 2/8 rejected (25%).
Mix audio (with instruments) dramatically reduces accuracy vs vocal-only.
6/8 OOD false positives -- mostly to Thodi (4/6).

**Key findings:**
1. Thodi: PERFECT self-recognition (10/10) but absorbs 14/15 wrongs
2. Vocal-isolated -> 64% acc. Mix audio -> 38%. Vocal isolation critical.
3. OOD rejection works on vocal-only, fails on mix audio
4. Bhairavi worst affected (5/11 seed wrongs -> Thodi, shared komal swaras)
5. Production matches sandbox prediction exactly (64%)

### Run: 2026-03-09 -- 6 ragas, clean vocals, MAX_DURATION=360s
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

### Run: 2026-02-16 — test_bug004_genericness.py (genericness from model PCD)
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

### Run: 2026-03-09 -- 6 ragas, clean vocals, MAX_DURATION=360s
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

### Run: 2026-02-16 — test_dyad_weights.py (weight tuning, no genericness)
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

### Run: 2026-03-09 -- 6 ragas, clean vocals, MAX_DURATION=360s
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

### Run: 2026-02-16 — test_bug004_no_genericness.py (genericness REMOVED)
| Audio | Expected | Predicted | Margin | Tier | Status |
|---|---|---|---|---|---|
| Alapana_HAM_Test.wav | UNKNOWN | Shankarabharanam | 0.00431 | HIGH | FALSE POSITIVE |
| Alapana_Moha_Test.wav | UNKNOWN | Shankarabharanam | 0.003845 | HIGH | FALSE POSITIVE |
| Balap_Test.wav | Bhairavi | Bhairavi | 0.005664 | HIGH | CORRECT |
| Kalap_Test.wav | Kalyani | UNKNOWN | 0.000227 | UNKNOWN | FALSE NEGATIVE |

**Result: 1/4 correct (25%) — SAME as baseline**

**Verdict: HELD. Rankings/margins identical to baseline. Scores shift to positive.**
Ready to apply as clean-up when accuracy improves elsewhere.

### Run: 2026-02-15 — test_recognize_fix.py (dyad fix validation / BASELINE)
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
