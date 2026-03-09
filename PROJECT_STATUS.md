# Swarag — Project Status

## Current Version
Swarag v1.2.1 (Deterministic DSP Architecture — 6-Raga Expansion)

---

## What Is Stable

- Pitch extraction using pYIN (with 6-minute duration cap)
- Tonic-relative normalization
- Pitch Class Distribution (PCD) features (36-bin)
- Directional dyad transitions (ascending `mean_up` / descending `mean_down`)
- Vocal isolation pipeline (Saraga multitrack stems + Demucs htdemucs)
- Non-destructive, versioned aggregation pipeline (`pcd_stats/`, `dyad_stats/`)
- Schema-aligned loading with frozen output contract
- Tiered confidence system (HIGH / MODERATE / UNKNOWN)
- OOD rejection for untrained ragas

### Frozen Output Schema
All recognition calls return a fixed dict format:
```python
{ "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

### Ragas Currently Modeled (v1.2.1)
- Bhairavi (11 clips)
- Kalyani (14 clips)
- Shankarabharanam (9 clips)
- Mohanam (6 clips)
- Thodi (7 clips)
- Kamboji (3 clips)

### Changes from v1.2
- Genericness penalty removed (confirmed inert — did not affect ranking)
- Escalation path disabled (was crushing Kalyani margins 5x)
- Margin thresholds recalibrated (MARGIN_STRICT: 0.05 -> 0.003)
- Duration cap restored (MAX_DURATION_SEC = 360)
- All audio vocal-isolated (no instrument contamination)
- Expanded from 3 to 6 ragas (OOD false positives eliminated)

### Observed Performance
- Trained ragas correctly ranked as #1
- OOD ragas (Hamsadwani, Mohanam test) correctly return UNKNOWN
- Threshold recalibration in progress
- Score compression still present for sibling ragas

---

## Known Limitations

- Kamboji has only 3 training clips (below 15-clip target)
- Mohanam has only 6 training clips (below 15-clip target)
- Top-1 accuracy can be unstable for sibling ragas (Kalyani/Shankarabharanam)
- Sensitive to tonic alignment across pipelines
- No absolute score floor for OOD rejection (relies on margin only)
- Not robust to polyphonic or percussion-heavy recordings
- No motif or gamaka contour modeling

---

## Actively Improving

- Threshold calibration for 6-raga model
- Expanding training data for Kamboji and Mohanam
- Adding test audio for new ragas (Thodi, Kamboji, Mohanam)

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
