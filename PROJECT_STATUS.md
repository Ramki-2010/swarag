# Swarag -- Project Status

## Current Version
Swarag v1.2.5 (Deterministic DSP Architecture -- 6-Raga, 72-bin, IDF x Variance)

---

## What Is Stable

- Pitch extraction using pYIN (with 6-minute duration cap)
- Tonic-relative normalization (histogram-based, octave-aware)
- 72-bin Pitch Class Distribution (PCD) features (17 cents per bin)
- Directional dyad transitions (ascending `mean_up` / descending `mean_down`)
- IDF x Variance weighted dot-product scoring
- Laplace smoothing ALPHA=0.01 (Phase 2 fix)
- MIN_CLIPS_PER_RAGA=5 guardrail (prevents thin-data raga sinks)
- Vocal isolation pipeline (Saraga multitrack stems + Demucs htdemucs)
- Non-destructive, versioned aggregation pipeline (`pcd_stats/`, `dyad_stats/`)
- Schema-aligned loading with frozen output contract
- Tiered confidence system (HIGH / MODERATE / UNKNOWN)
- OOD rejection for untrained ragas
- Duplicate feature detection and cleanup

### Frozen Output Schema
All recognition calls return a fixed dict format:
```python
{ "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

### Key Constants
| Constant | Value | Notes |
|---|---|---|
| N_BINS | 72 | Was 36 (Phase 4) |
| ALPHA | 0.01 | Was 0.5 (Phase 2 fix) |
| MIN_CLIPS_PER_RAGA | 5 | BUG-011 guardrail |
| PCD_WEIGHT | 0.6 | |
| DYAD_WEIGHT | 0.4 | |
| MARGIN_STRICT | 0.003 | HIGH confidence threshold |
| MIN_MARGIN_FINAL | 0.001 | MODERATE threshold |

### Ragas Currently Modeled (v1.2.5)
| Raga | Clips | LOO Accuracy |
|---|---|---|
| Bhairavi | 11 | 67% |
| Kalyani | 14 | 88% |
| Shankarabharanam | 9 | 75% |
| Mohanam | 11 | 25% |
| Thodi | 11 | 100% |
| Kamboji | 5 | 0% |
| **Total** | **61** | **72.0% (decided)** |

### Staged Ragas (need 5+ clips)
- Abhogi (2 clips, needs 3 more)
- Madhyamavati (2 clips, needs 3 more)
- Saveri (3 clips, needs 2 more)
- Hamsadhvani (1 clip, needs 4 more)

### Evolution (v1.2 to v1.2.5)
| Version | Accuracy | Clips | Key Change |
|---|---|---|---|
| v1.2 | 25% | ~20 | Baseline (3 ragas) |
| v1.2.1 | -- | 50 | 6 ragas, vocal isolation |
| v1.2.2 | 64% | 53 | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | 53 | IDF x Variance scoring |
| v1.2.4 | 78.6% | 53 | 72-bin PCD |
| v1.2.5 | 72.0% | 61 | Expanded data, dedup, MIN_CLIPS guardrail |

---

## Known Limitations

- Kamboji has only 5 training clips (0% LOO -- needs more diverse clips)
- Mohanam at 25% LOO -- many clips go UNKNOWN
- Score compression still present for sibling ragas (Bhairavi/Thodi)
- Sensitive to tonic alignment across pipelines
- No absolute score floor for OOD rejection (relies on margin only)
- Not robust to polyphonic or percussion-heavy recordings
- No motif or gamaka contour modeling

---

## Actively Improving

- Expanding training data for staged ragas (Abhogi, Madhyamavati, Saveri, Hamsadhvani)
- Investigating 72% vs 78.6% gap (expanded Mohanam/Kamboji data)
- Hubness correction (parked until 15+ ragas)

---

## Explicitly Out of Scope (For Now)

- Deep learning classifiers (insufficient dataset size; explainability prioritized)
- Hard-coded arohanam / avarohanam rule systems
- Real-time / live inference
- Instrument-only or polyphonic audio

## Future Roadmap

- Expand to full 72 Melakarta raga set
- Add janya ragas
- Phrase motif detection
- Improved Sa drift handling
- Gamaka modeling via micro-contour analysis
- Android deployment prototype
- Live singing inference support

---

## Philosophy

Swarag prioritizes musical validity and interpretability over premature accuracy.
Features are validated musically before any learning or optimization is introduced.
