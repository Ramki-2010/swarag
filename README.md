# Swarag

Swarag is a deterministic Carnatic raga recognition engine built using signal processing and interpretable statistical modeling.

This project avoids deep learning black boxes and instead focuses on structured musical logic using:

- Pitch Class Distributions (PCD)
- Directional dyads (ascent vs descent transitions)
- Pitch stability gating
- Genericness bias correction
- Deterministic scoring

---

## Current Version: v1.2

v1.2 introduces:

- Oscillation-aware pitch stability gate
- Directional dyad modeling (M_up, M_down)
- Genericness Index penalty to reduce major-scale bias
- Versioned aggregation runs
- Fully reproducible evaluation framework

---

## Architecture Overview

Extraction:
- `librosa.pyin` pitch tracking
- Tonic estimation
- Stability gating
- Gated pitch features

Aggregation:
- Mean gated PCD per raga
- Directional dyad matrices
- Laplace smoothing
- Metadata logging

Recognition:
- Gated inference features
- Cosine similarity scoring
- Genericness correction
- Transition guardrails

Evaluation:
- Per-file diagnostics
- Top-2 margin logging
- Per-raga accuracy reporting
- Versioned result folders

---

## Repository Structure

- `scripts/` — Core engine  
- `pcd_results/` — Ignored (local artifacts)  
- `datasets/` — Ignored (local only)


---

## Design Philosophy

Swarag is built on:

- Explainability over opacity
- Musical grammar over pattern memorization
- Bias correction over naive similarity
- Deterministic reproducibility

---

## Status

Active research project.
Currently evaluating bias reduction in v1.2 against sink-raga dominance.
