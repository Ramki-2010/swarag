# Swarag -- Project Status

## Current Version
Swarag v1.3 (5-Raga Honest Baseline -- Harikambhoji cleaned, 72-bin, IDF x Variance)

---

## What Is Stable

- 72-bin PCD + IDF x Variance weighted dot-product scoring
- Directional dyads with ALPHA=0.01 Laplace smoothing
- PCD_WEIGHT=0.7, DYAD_WEIGHT=0.3 (PCD-heavy -- fewer wrongs)
- MIN_CLIPS_PER_RAGA=5 guardrail
- Vocal isolation mandatory (Saraga stems + Demucs)
- Per-file timeout in batch evaluation (360s)

### Key Constants
| Constant | Value |
|---|---|
| N_BINS | 72 |
| ALPHA | 0.01 |
| PCD_WEIGHT | 0.7 |
| DYAD_WEIGHT | 0.3 |
| MIN_CLIPS_PER_RAGA | 5 |
| MARGIN_STRICT | 0.003 |
| MIN_MARGIN_FINAL | 0.001 |

### Current Accuracy (LOO, 5 ragas, 55 clips)
| Raga | Clips | LOO Acc |
|---|---|---|
| Thodi | 11 | 83% |
| Kalyani | 14 | 80% |
| Shankarabharanam | 9 | 50% |
| Bhairavi | 11 | 50% |
| Mohanam | 10 | 17% |
| **Overall** | **55** | **~58.8% decided** |

### What Changed from v1.2.5
- Removed 3 Harikambhoji clips from Kamboji (wrong raga label -- BUG-013)
- Removed short Mohanam clip (936 frames)
- Audio duplicates cleaned (Mohanam: 3 removed, Kamboji: 2 removed)
- Weights: 0.6/0.4 to 0.7/0.3 (fewer wrongs)
- Accuracy: 72% to 58.8% (honest -- bad data was inflating it)

---

## Known Limitations

- Mohanam: 17% LOO -- needs diverse clips
- Bhairavi: 50% -- PCD overlaps 78% with Thodi
- Kamboji: excluded (3 real clips, need 2+ more)
- No OOD score floor

---

## Priority Plan

1. Fix Mohanam: add 4-6 diverse clips
2. Fix Kamboji: add 5-7 real clips (non-Saraga)
3. Per-raga dyad weight for Bhairavi
4. Target: 70-80% overall after fixes
5. Then expand to Saveri, Hamsadhvani

---

## Philosophy

Honest baselines over inflated numbers. Clean data over more data.
