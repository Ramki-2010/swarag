# Swarag — Project Status

## Current Version
Swarag 1.0 (Baseline Feature Engine)

---

## What Is Stable

- Pitch extraction using pYIN
- Tonic-relative normalization
- Pitch Class Distribution (PCD) features
- Stable dyad (pitch transition) features
- Non-destructive, timestamped aggregation pipeline
- Consistent Top-3 raga identification

---

## Known Limitations

- Top-1 accuracy unstable for sibling ragas
- Sensitive to tonic alignment across pipelines
- Dyads require longer audio for stability
- Not robust to percussion-heavy or polyphonic recordings

---

## Actively Improving

- Tonic alignment consistency
- Confidence calibration
- Adding structurally distinct ragas
- Diagnostic visualizations for failure cases

---

## Explicitly Out of Scope (For Now)

- Deep learning classifiers
- Rule-based arohanam / avarohanam logic
- Real-time inference
- Instrument-only audio

---

## Philosophy

Swarag prioritizes musical validity and interpretability over premature accuracy.
Features are validated musically before any learning or optimization is introduced.
