# Swarag — Architecture Overview

This document explains the internal architecture and design rationale of Swarag.
It is intended for developers, researchers, and technical collaborators who want
to understand *how* the system works and *why* specific decisions were made.

Swarag is designed as a **music-first MIR system**, where musical validity
precedes machine learning or optimization concerns.

---

## High-Level Pipeline
Audio<br>
↓<br>
Pitch Extraction (pYIN)<br>
↓<br>
Tonic (Sa) Estimation & Normalization<br>
↓<br>
Feature Modeling<br>
├─ Pitch Class Distribution (PCD)<br>
└─ Stable Dyad Transitions<br>
↓<br>
Raga Scoring & Ranking<br>
↓<br>
Confidence-Aware Output


Each stage is intentionally isolated and testable.

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
- 36-bin folded octave (0–1200 cents)
- Tonic-normalized
- Length-independent probability distribution

**What it captures**
- Relative pitch usage
- Presence and absence of swaras
- Broad gamaka influence without destroying detail

PCD serves as the **baseline feature** for raga identity.

---

### 3.2 Stable Dyad Transitions

PCD alone cannot distinguish sibling ragas reliably.
Dyads capture *how pitches move*, not just where they occur.

**Definition**
- Dyads represent transitions between stable pitch regions
- Computed only across frames that exceed a minimum stability duration
- Represented as a 36 × 36 transition matrix

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
  - PCD
  - Dyad matrices
- Outputs are saved with timestamps
- No aggregation run overwrites another

This produces a **raga signature**, not a single exemplar.

---

## Stage 5: Recognition & Scoring

**Input**
- Unseen audio sample

**Process**
- Extract pitch and tonic
- Generate PCD and dyads
- Compare against aggregated raga signatures

**Distance Metrics**
- Jensen–Shannon divergence for PCD
- Jensen–Shannon divergence for dyads
- Weighted combination for final score

**Output**
- Ranked list of ragas
- Top-1 prediction
- Top-3 candidates
- Explicit UNKNOWN / LOW CONFIDENCE state

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

## Current Scope

- Monophonic vocal audio
- Clean or vocal-isolated recordings
- Medium-length excerpts (minutes, not seconds)

---

## Planned Extensions

- Sliding-window inference
- Lightweight classifiers on validated features
- Support for more ragas
- Educational explanations layered on top of results

---

## Summary

Swarag is not a shortcut-based recognizer.
It is a **progressive raga modeling engine** that treats Carnatic music as a
living, expressive system rather than a fixed symbolic grammar.


