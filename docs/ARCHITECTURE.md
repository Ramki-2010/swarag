# Swarag — Architecture Overview

This document explains the internal architecture and design rationale of Swarag.
It is intended for developers, researchers, and technical collaborators who want
to understand *how* the system works and *why* specific decisions were made.

Swarag is designed as a **music-first MIR system**, where musical validity
precedes machine learning or optimization concerns.

---

## High-Level Pipeline

`
Audio (.wav / .mp3 / .flac)
  |
  v
Vocal Isolation (Saraga multitrack stems or Demucs htdemucs)
  |
  v
Pitch Extraction (pYIN, 6-minute cap)
  |
  v
Tonic (Sa) Estimation & Normalization
  |
  v
Feature Modeling
  |-- Pitch Class Distribution (PCD, 72-bin)
  +-- Directional Dyad Transitions (mean_up / mean_down)
  |
  v
Aggregation --> Versioned Raga Signatures (pcd_stats/ + dyad_stats/)
  |
  v
Raga Scoring & Ranking
  |-- IDF x Variance weighted dot-product (PCD + Dyads)
  |-- Weighted fusion (PCD=0.7, Dyad=0.3)
  |-- MIN_CLIPS_PER_RAGA=5 guardrail
  +-- Tiered confidence: HIGH / MODERATE / UNKNOWN
  |
  v
Output: { final, ranking, margin, confidence_tier }
`

Each stage is intentionally isolated and testable.

---

## Stage 0: Vocal Isolation

Carnatic concert recordings contain violin, mridangam, and tambura alongside
vocals. These instruments contaminate pitch extraction (especially violin,
which plays the same raga phrases).

**Requirement**: All audio must be vocal-only before entering the pipeline.

**Methods** (in preference order):
1. **Saraga multitrack stems** -- lossless vocal track from the dataset (168 tracks available)
2. **Demucs htdemucs** -- AI-based source separation (`--two-stems vocals`)
3. **Clean recordings** -- solo vocal with drone only (e.g., Carnatic Varnam dataset)

---

## Stage 1: Pitch Extraction

**Algorithm:** pYIN (via librosa)

**Why pYIN**
- Produces continuous pitch contours
- Preserves micro-variations and gamakas
- More stable for non-Western melodic music than frame-wise YIN

**Key Properties**
- No hard smoothing applied
- Voiced/unvoiced frames explicitly tracked
- Pitch range kept wide to avoid cutting valid alapana phrases

- **Duration cap**: Only the first 6 minutes are processed (`MAX_DURATION_SEC=360`).
  A raga establishes its identity within 3-5 minutes. Processing beyond that
  has diminishing returns but 10x the compute cost.

The goal at this stage is **maximum musical fidelity**, not cleanliness.

---

## Stage 2: Tonic (Sa) Estimation

Carnatic music is tonic-relative. Absolute frequency is meaningless without Sa.

**Approach**
- Histogram-based peak detection on pitch values
- Octave-aware tonic candidate selection
- Validation using pitch stability and density near Sa

**Design Decision**
- Never assume median pitch = Sa
- Never fix tonic across singers
- Always normalize pitch to cents relative to estimated Sa

Errors here propagate downstream, so this stage is treated as critical infrastructure.

---

## Stage 3: Feature Modeling

Swarag models ragas as *statistical musical behavior* rather than symbolic rules.

### 3.1 Pitch Class Distribution (PCD)

**Representation**
- 72-bin folded octave (0–1200 cents, 17 cents per bin)
- Tonic-normalized
- Length-independent probability distribution

**What it captures**
- Relative pitch usage
- Presence and absence of swaras
- Broad gamaka influence without destroying detail

PCD serves as the **baseline feature** for raga identity.

**IDF x Variance Weighting** (v1.2.3+)
- Each PCD bin is weighted by IDF (inverse document frequency) times 1/std
- Downweights common swaras (Sa, Pa) shared by all ragas
- Upweights distinctive swaras that differentiate ragas
- This is the MIR equivalent of TF-IDF for pitch distributions

---

### 3.2 Directional Dyad Transitions

PCD alone cannot distinguish sibling ragas reliably.
Dyads capture *how pitches move*, not just where they occur.

In v1.2, dyads are **directional** -- split into ascending and descending
transitions -- because Carnatic ragas are structurally asymmetric:
arohanam is not equal to avarohanam.

**Definition**
- Dyads represent transitions between stable pitch regions
- Computed only across frames that exceed a minimum stability duration
  (`MIN_STABLE_FRAMES=5`)
- Split into two directed matrices:
  - `mean_up` -- ascending transitions (arohanam character)
  - `mean_down` -- descending transitions (avarohanam character)
- Each represented as a 72 x 72 transition matrix
- Laplace smoothing with ALPHA=0.01 (scaled for matrix size)

**Why “Stable” Dyads**
- Avoids noise from rapid pitch jitter
- Preserves musically meaningful transitions
- Reflects raga grammar (e.g., characteristic phrases)

Dyads are additive — they refine decisions without replacing PCD.

---

## Stage 4: Aggregation

For each raga:

- Multiple samples are aggregated
- Mean and variance are computed for:
  - PCD -> saved to `pcd_stats/`
  - Directional dyad matrices -> saved to `dyad_stats/`
- A `metadata.json` is written alongside each aggregation run
- Outputs are saved with version timestamps in named subfolders
- No aggregation run overwrites another (non-destructive by design)

This produces a **raga signature**, not a single exemplar.

---

## Stage 5: Recognition & Scoring

**Input**
- Unseen audio sample

**Process**
- Extract pitch and tonic
- Generate PCD and dyads
- Compare against aggregated raga signatures

**Scoring**
- IDF x Variance weighted dot-product for PCD
- Dot-product similarity for directional dyads (up + down averaged)
- Weighted combination: `score = 0.7 * pcd_sim + 0.3 * dyad_sim`

**Tiered Confidence System**

| Tier | Condition | Meaning |
|---|---|---|
| HIGH | margin >= 0.003 | Strong separation, high confidence |
| MODERATE | 0.001 <= margin < 0.003 | Acceptable separation |
| UNKNOWN | margin < 0.001 | Too close to call -- returns UNKNOWN |

**Output -- Frozen Interface Contract**
```python
{ "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```
- `final` -- top predicted raga name, or "UNKNOWN / LOW CONFIDENCE"
- `ranking` -- ordered list of (raga, score) candidates
- `margin` -- score gap between top-1 and top-2
- `confidence_tier` -- "HIGH", "MODERATE", or "UNKNOWN"


UNKNOWN is a deliberate design choice, not a failure case.

---

## Design Constraints (Intentional)

Swarag explicitly avoids:

- Hard-coded arohanam / avarohanam rules
- Absolute pitch templates
- Premature machine learning classifiers
- Black-box decision making
- Over-smoothing pitch contours

Every feature must first prove **musical validity** before optimization.

---

## Architectural Philosophy

- Music first, models second
- Validate features before learning
- Prefer interpretable errors over silent failures
- UNKNOWN is safer than wrong certainty
- Scale complexity only when data demands it

---

## Current Scope (v1.3)

- 5 ragas modeled: Bhairavi, Kalyani, Shankarabharanam, Mohanam, Thodi
- 55 vocal-isolated training clips
- 72-bin PCD with IDF x Variance weighting
- Directional dyads with ALPHA=0.01 Laplace smoothing
- MIN_CLIPS_PER_RAGA=5 guardrail
- Monophonic vocal audio (vocal-isolated)
- Medium-length excerpts (capped at 6 minutes)
- Staged ragas (below guardrail): Kamboji(3), Abhogi(7*), Saveri(8*), Madhyamavati(2-3), Hamsadhvani(1)
  (*pending feature extraction)
- LOO accuracy: 58.8% decided (honest baseline)

---

## Planned Extensions

- Expand to full 72 Melakarta raga set
- Add janya ragas
- Phrase motif detection
- Improved Sa drift handling
- Gamaka modeling via micro-contour analysis
- Sliding-window inference for longer recordings
- Lightweight classifiers on top of validated features
- Android deployment prototype
- Live singing inference support
- Educational explanations layered on top of results

---

## Summary

Swarag is not a shortcut-based recognizer.
It is a **progressive raga modeling engine** that treats Carnatic music as a
living, expressive system rather than a fixed symbolic grammar.


