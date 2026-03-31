# Swarag -- Project Status

## Current Version
Swarag v1.3.1 (7 Ragas -- Abhogi + Saveri activated, PCD-heavy 0.8/0.2)

---

## What Is Stable

- 72-bin PCD + IDF x Variance weighted dot-product scoring
- Directional dyads with ALPHA=0.01 Laplace smoothing
- PCD_WEIGHT=0.8, DYAD_WEIGHT=0.2 (PCD-heavy -- fewest wrongs)
- MIN_CLIPS_PER_RAGA=5 guardrail
- Vocal isolation mandatory (Saraga stems + Demucs)
- Per-file timeout in batch evaluation (360s)

### Key Constants
| Constant | Value |
|---|---|
| N_BINS | 72 |
| ALPHA | 0.01 |
| PCD_WEIGHT | 0.8 |
| DYAD_WEIGHT | 0.2 |
| MIN_CLIPS_PER_RAGA | 5 |
| MARGIN_STRICT | 0.003 |
| MIN_MARGIN_FINAL | 0.001 |

### Current Accuracy (LOO, 7 ragas, 70 clips, 0.8/0.2)
| Raga | Clips | LOO Acc |
|---|---|---|
| Thodi | 11 | 100% |
| Bhairavi | 11 | 100% (1c, 10u) |
| Kalyani | 14 | 88% |
| Saveri | 8 | 75% |
| Shankarabharanam | 9 | 67% |
| Mohanam | 10 | 20% |
| Abhogi | 7 | 0% |
| **Overall** | **70** | **64.9% decided** |

### What Changed from v1.3
- Abhogi activated (7 clips: 2 existing + 5 Zenodo varnams)
- Saveri activated (8 clips: 3 existing + 5 Zenodo varnams)
- Weights: 0.7/0.3 to 0.8/0.2 (PCD-heavy, fewer wrongs: 13 vs 17)
- Duplicates cleaned (kamalambike Thodi, Rama Namam Madhyamavati, Nannu Brova Abhogi)
- Accuracy: 58.8% (5 ragas) to 64.9% (7 ragas)

---

## Known Limitations

- Abhogi: 0% LOO -- janya of Kalyani, all wrongs absorbed by Kalyani
- Mohanam: 20% LOO -- needs diverse clips (different songs/artists)
- Bhairavi: 100% decided but 10/11 UNKNOWN -- needs more decisive features
- Kamboji: excluded (3 real clips, need 2+ more non-Harikambhoji)
- Kalyani is the new sink (absorbs 7/13 wrongs, mostly Abhogi)
- No OOD score floor

---

## Priority Plan

1. Add 5-7 real Kamboji clips (YouTube/Rasikas, non-Saraga)
2. Add 4-6 diverse Mohanam clips (different songs/artists)
3. Test Abhogi/Bhairavi dyad weight override (0.4/0.6)
4. Do NOT add more new ragas until weak ones > 60%
5. Target: 72-78% decided accuracy with 7-8 ragas

---

## Philosophy

Honest baselines over inflated numbers. Clean data over more data.
