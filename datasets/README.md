# Swarag — Datasets

> **Note**: Audio files are not stored in this repository (gitignored).
> This document describes the dataset structure, sources, and current state.

---

## Dataset Location

All audio lives locally at `D:\Swaragam\datasets\seed_carnatic\` on the development machine.
Each raga has its own subfolder containing vocal-only audio files.

```
datasets/
  seed_carnatic/
    Bhairavi/           11 clips (6 clean wav + 5 Saraga vocal)
    Kalyani/            14 clips (6 clean wav + 4 varnam + 4 Saraga vocal)
    Shankarabharanam/    9 clips (6 clean wav + 3 Saraga vocal)
    Mohanam/            10 clips (4 varnam + 6 Saraga/Demucs vocal)
    Thodi/              11 clips (3 stems + 8 Demucs vocal)
    Kamboji/             3 clips (3 Saraga vocal — Harikambhoji removed)
    Abhogi/              7 clips (2 Demucs + 5 varnam)
    Saveri/              8 clips (3 Demucs/stems + 5 varnam)
    Madhyamavati/        2-3 clips
    Hamsadhvani/         1 clip
  audio test/           4 test files (Hamsadwani, Mohanam, Bhairavi, Kalyani)
```

---

## Current State (v1.3)

### Modeled Ragas (5 — pass MIN_CLIPS_PER_RAGA=5 guardrail)

| Raga | Clips | LOO Accuracy | Notes |
|---|---|---|---|
| Thodi | 11 | 83% | Strongest raga. 2 outliers excluded. |
| Kalyani | 14 | 80% | Most clips. Includes 4 Zenodo varnams. |
| Shankarabharanam | 9 | 50% | 6 clean wav + 3 Saraga. |
| Bhairavi | 11 | 50% | PCD overlaps 78% with Thodi. Identity is in gamakas. |
| Mohanam | 10 | 17% | Weakest raga. Needs diverse clips (different songs). |

### Pending Activation (have enough clips, need feature extraction)

| Raga | Clips | Status |
|---|---|---|
| Abhogi | 7 | 5 new varnams extracted ✅. Ready to aggregate. |
| Saveri | 8 | 5 new varnams skipped by BUG-014. Need re-extraction. |

### Below Guardrail (need more audio)

| Raga | Clips | Needed | Notes |
|---|---|---|---|
| Kamboji | 3 | 2+ more | 3 Harikambhoji clips removed (BUG-013). Need real Kamboji from non-Saraga sources. |
| Madhyamavati | 2-3 | 2-3 more | |
| Hamsadhvani | 1 | 4 more | Subset of Kalyani — may cause false positives. |

---

## Audio Sources

### 1. Original Clean Recordings
- **Files**: `*_clean_*.wav` (Bhairavi, Kalyani, Shankarabharanam)
- **Quality**: Studio-quality solo vocal
- **Status**: Fully used

### 2. Carnatic Varnam Dataset (Zenodo)
- **URL**: https://zenodo.org/records/1257118
- **Local zip**: `D:\Swaragam\datasets\carnatic_varnam_1.0.zip`
- **Content**: 28 solo vocal recordings (7 ragas × 4 singers), with drone only
- **Quality**: Clean, research-grade, no instruments
- **7 Ragas available**:

| Raga | Varnams | Used? |
|---|---|---|
| Kalyani | 4 | ✅ All used |
| Mohanam | 4 | ✅ All used |
| Abhogi | 5 | ✅ All extracted (2026-03-21) |
| Saveri | 5 | ⏳ Pending (BUG-014) |
| Begada | 3 | Available for future |
| Sahana | 4 | Available for future |
| Sri | 3 | Available for future |

### 3. Saraga Carnatic Dataset
- **URL**: https://zenodo.org/records/4301737
- **GitHub**: https://github.com/MTG/saraga
- **Local metadata**: `D:\Swaragam\datasets\saraga-master\` (JSON + md5, NO audio files)
- **Audio**: Not bulk-downloaded. Individual tracks obtained via YouTube/other sources.
- **Content**: 249 recordings, 96 ragas, 52.7 hours
- **Quality**: Concert recordings — require vocal isolation (stems or Demucs)
- **Used for**: Bhairavi (5), Kalyani (4), Shankarabharanam (3), Mohanam (4), Kamboji (3), metadata cross-referencing
- **Key lesson**: Always verify raga labels against Saraga metadata. Harikambhoji ≠ Kamboji (L-040).

### 4. External Thodi Sources
- **Location**: `H:\Swaragam\Datasets\Audio\Thodi\` (5 mp3 files)
- **Artists**: Malladi Bros, MS Subbulakshmi, Hyderabad Bros, etc.
- **Quality**: Concert recordings, Demucs-separated
- **Status**: All used, vocal-isolated

### 5. CompMusic/Dunya Archive
- **Location**: `H:\Swaragam\Datasets\Audio\archive.zip` (3.9 GB)
- **Content**: 7 Todi recordings — same as Saraga, no new audio
- **Status**: Checked, no unique content

---

## Audio Preparation Requirements

All training audio **must be vocal-only**. Instrument contamination (violin, mridangam, tambura) degrades pitch extraction and inflates false positives (BUG-009, L-028).

### Preparation Methods (in preference order)

1. **Saraga multitrack stems** — lossless vocal track (`*.vocal.mp3`)
2. **Demucs htdemucs** — AI source separation (`demucs --two-stems vocals`)
3. **Clean solo recordings** — solo vocal with drone only (e.g., Carnatic Varnam)

### Naming Convention

| Suffix | Meaning |
|---|---|
| `*.vocal.mp3` | Saraga multitrack vocal stem |
| `*.vocal-s.mp3` | Short/alternate vocal stem |
| `*.demucs-vocal.wav` | Demucs-separated vocal |
| `*_clean_*.wav` | Original clean recording |
| `223*gopalkoduri*` | Carnatic Varnam dataset |

### Duration Cap

Processing is capped at **6 minutes** (`MAX_DURATION_SEC=360`). A raga establishes identity in 3-5 minutes. Beyond that is diminishing returns with 10x compute cost.

---

## Excluded Audio (in `excluded/` subfolders)

Audio files moved to `excluded/` subfolders are **not deleted** — they are kept for reference but excluded from training.

| Raga | Excluded Files | Reason |
|---|---|---|
| Mohanam | `Brochevarevarura.demucs-vocal.wav` | Same-song duplicate |
| Mohanam | `Shloka Namaste Sarvalokaanam.demucs-vocal.wav` | Same-song duplicate |
| Mohanam | `Shloka Namaste Sarvalokaanam.vocal.mp3` | Same-song duplicate |
| Mohanam | `Shloka Sri Ramachandra.vocal.mp3` | Too short (936 frames) |
| Kamboji | `Dinamani Vamsa.demucs-vocal.wav` | Same-song duplicate |
| Kamboji | `Dinamani Vamsa.vocal.mp3` | Harikambhoji, not Kamboji |
| Kamboji | `Enadhu Manam Kavalai.vocal.mp3` | Harikambhoji, not Kamboji |
| Kamboji | `Enadhu Manam Kavalai.vocal-s.mp3` | Harikambhoji, not Kamboji |
| Kamboji | `Sanjay Subrahmanyan - Entara Nitana.demucs-vocal.wav` | Harikambhoji, not Kamboji |

---

## Extracted Features

Features are stored as `.npz` files at `D:\Swaragam\pcd_results\features_v12\`.

Each `.npz` contains:
- `feature_version` — "v1.2"
- `raga` — raga label (from folder name)
- `sa_hz` — estimated tonic frequency
- `f0` — raw pitch contour (pYIN)
- `voiced_flag` — voiced/unvoiced per frame
- `cents_gated` — stability-gated pitch in cents (relative to Sa)
- `gating_ratio` — fraction of voiced frames that pass stability gate

---

## Aggregated Models

Models are stored at `D:\Swaragam\pcd_results\aggregation\v1.2\run_YYYYMMDD_HHMMSS\`.

Current: `run_20260321_135629` (v1.3: 5 ragas, 55 clips)

Each model run contains:
- `pcd_stats/{raga}_pcd_stats.npz` — mean PCD, std PCD
- `dyad_stats/{raga}_dyad_stats.npz` — mean_up, mean_down, std_up, std_down
- `aggregation_metadata.json` — run parameters

---

## Future Data Needs (Priority Order)

1. **Mohanam**: 4-6 diverse clips from different songs/artists (not more varnams of the same piece)
2. **Kamboji**: 5-7 real Kamboji clips from YouTube, Rasikas.org, or Carnatic2000
3. **Saveri**: Fix BUG-014, then already have enough (8 clips)
4. **Madhyamavati**: 2-3 more clips to hit guardrail
5. **Hamsadhvani**: 4+ clips (but beware — it's a subset of Kalyani)
6. **New ragas**: Begada (3 varnams available), Sahana (4 varnams available)

---

## Data Integrity Rules

1. **Always cross-reference raga labels** against Saraga/Dunya metadata before adding (L-040)
2. **One version per song** — keep the best vocal isolation, exclude duplicates (L-037)
3. **Minimum 5 clips per raga** to include in model (MIN_CLIPS guardrail, BUG-011)
4. **Vocal-only** — never train on mix audio (L-028, BUG-009)
5. **Verify tonic consistency** — Sa should be in 80-400 Hz range
6. **Never delete** excluded files — move to `excluded/` subfolder
