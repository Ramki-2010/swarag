# Swarag -- Project Status

## Current Version
Swarag v1.3.1 (7 Ragas -- Abhogi + Saveri activated, PCD-heavy 0.8/0.2)

---

## What Is Stable

- 72-bin PCD + IDF x Variance weighted dot-product scoring
- Directional dyads with ALPHA=0.01 Laplace smoothing
- PCD_WEIGHT=0.8, DYAD_WEIGHT=0.2 (PCD-heavy -- fewest wrongs)
- PER_RAGA_WEIGHTS: Bhairavi=(0.5, 0.5) -- dyad-heavy override for Bhairavi
- MIN_CLIPS_PER_RAGA=5 guardrail
- Vocal isolation mandatory (Saraga stems + Demucs)
- Per-file timeout in batch evaluation (360s)

### Key Constants
| Constant | Value |
|---|---|
| N_BINS | 72 |
| ALPHA | 0.01 |
| PCD_WEIGHT | 0.8 (global) |
| DYAD_WEIGHT | 0.2 (global) |
| PER_RAGA: Bhairavi | 0.5/0.5 |
| MIN_CLIPS_PER_RAGA | 5 |
| MARGIN_STRICT | 0.003 |
| MIN_MARGIN_FINAL | 0.001 |

### Current Accuracy (LOO, 7 ragas, 70 clips, with Bhairavi override)
| Raga | Clips | LOO Acc |
|---|---|---|
| Thodi | 11 | 100% |
| Saveri | 8 | 88% |
| Shankarabharanam | 9 | 86% |
| Kalyani | 14 | 67% |
| Bhairavi | 11 | 40% (0.5/0.5 override) |
| Mohanam | 10 | 33% |
| Abhogi | 7 | 25% |
| **Overall** | **70** | **67.4% decided** |

### What Changed from v1.3
- Abhogi activated (7 clips: 2 existing + 5 Zenodo varnams)
- Saveri activated (8 clips: 3 existing + 5 Zenodo varnams)
- Weights: 0.7/0.3 to 0.8/0.2 global (PCD-heavy, fewer wrongs)
- Bhairavi per-raga override: 0.5/0.5 (dyad-heavy, validated in sandbox)
- Duplicates cleaned (kamalambike Thodi, Rama Namam Madhyamavati, Nannu Brova Abhogi)
- Accuracy: 58.8% (5 ragas) to 67.4% (7 ragas, with override)

---

## Known Limitations

- Abhogi: 25% LOO -- STRUCTURAL problem (janya of Kalyani, PCD is strict subset)
  Weight overrides tested at 0.6/0.4, 0.5/0.5, 0.4/0.6 -- all 0%. Only fixed by
  Bhairavi override side-effect (25%). Next approach: quantitative swara energy ratio (sandbox_abhogi_ratio.py).
- Mohanam: 33% LOO -- needs diverse clips (different songs/artists)
  Dyad overrides tested, no improvement. This is a data problem.
- Kamboji: excluded (3 real clips, Saraga exhausted -- 0 new sources)
- Kalyani absorbs Abhogi wrongs (structural, not fixable by weights)
- No OOD score floor

---

## Priority Plan

1. **Abhogi energy-ratio sandbox** (ARCHITECTURAL): run sandbox_abhogi_ratio.py.
   Quantitative Pa/N3 ratio comparison vs model expected. Absent-swara penalty is a proven dead end (L-046).
2. Add 5-7 real Kamboji clips (YouTube/Rasikas -- Saraga has 0 new sources)
3. Add 4-6 diverse Mohanam clips (different songs/artists)
4. Do NOT add more new ragas until weak ones > 60%
5. Target: 72-78% decided accuracy with 7-8 ragas

### Proven Dead Ends (do not re-attempt)
- Abhogi per-raga weight overrides (0% at all weights -- L-044)
- Abhogi absent-swara penalty -- BOTH variants failed (L-046, 2026-04-01):
  * Data-driven: self-harm on 5/7 Abhogi clips
  * Musicological: gamakas leak 6-19% Pa energy, binary detection fails
- Mohanam dyad overrides (no improvement -- data problem)
- Genericness penalty from model PCD (L-016)
- Escalation / dyad-heavy re-scoring (L-017)

---

## Philosophy

Honest baselines over inflated numbers. Clean data over more data.
