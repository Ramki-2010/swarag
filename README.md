# 🎵 Swarag — Carnatic Raga Identification Engine

Swarag is a research-driven Carnatic raga identification engine that analyzes audio directly, modeling ragas as pitch behavior and pitch movement rather than fixed note rules or symbolic representations.

Unlike rule-based systems or black-box classifiers, Swarag treats ragas as musical grammars — defined by how pitches are used and how they move, not just which swaras appear.

---

## Motivation

Most existing raga identification approaches struggle with real Carnatic performances because they rely on:

- static arohanam / avarohanam rules
- absolute pitch templates
- aggressive smoothing that destroys gamakas
- early reliance on opaque ML models

Carnatic music is tonic-relative, ornament-rich, and improvisational.  
Swarag is built to respect those realities.

---

## Core Idea

Swarag is based on three principles:

- Relative pitch, not absolute frequency  
- Behavior over checklists  
- Preserve musical information early  

All analysis is normalized to the singer’s tonic (Sa).  
Gamakas and micro-variations are preserved, not smoothed away prematurely.

---

## What Swarag Does Today

Swarag 1.0 currently supports:

- Vocal pitch extraction using pYIN
- Automatic tonic (Sa) estimation
- Conversion to tonic-relative cents
- Pitch Class Distribution (PCD) modeling (36 bins)
- Stable dyad (pitch transition) modeling
- Aggregation of raga signatures from multiple samples
- Distance-based raga recognition (Jensen–Shannon divergence)
- Confidence-aware output (Top-1 / Top-3 / Unknown)
- Fully versioned, reproducible aggregation runs

---

## What Swarag Is NOT (Yet)

- No deep learning classifiers yet
- No hard-coded arohanam / avarohanam rules
- No absolute pitch assumptions
- No real-time inference
- No percussion-heavy audio handling

These are future extensions, not current guarantees.

---

## Project Status

Swarag has completed its baseline feature extraction and validation phase.

### Achieved
- Stable tonic-relative feature extraction
- Statistical separation between ragas
- Pitch transition grammar captured via dyads
- Consistent Top-3 recognition
- Modular, non-destructive experiment pipeline

### Current Focus
- Adding more structurally distinct ragas
- Fixing tonic alignment consistency
- Improving Top-1 ranking stability
- Calibrating confidence thresholds

## Sample Output

Below is a representative output from **Swarag 1.0**, showing raga-level statistical structure derived from tonic-normalized pitch analysis.

<p align="center">
  <img src="docs/assets/sample_output.png" alt="Swarag sample output" width="800"/>
</p>

**What this shows**
- Tonic-normalized pitch-class statistics
- Singer-agnostic raga structure
- Clear separation between structurally similar ragas

This output is generated entirely from audio input, without hand-coded raga rules.

---

## Project Structure

- swarag/
- ├── scripts/
- │ ├── extract_pitch_batch.py
- │ ├── aggregate_pcds.py
- │ ├── aggregate_dyads.py
- │ ├── recognize_raga.py
- │ └── batch_evaluate.py
- ├── pcd_results/
- └── datasets/


---


---

## Aggregation Policy

- All aggregation outputs are timestamped
- No aggregation run overwrites a previous run
- Every experiment is reproducible

---

## Quick Start (Experimental)

```bash
git clone https://github.com/Ramki-2010/swarag.git
cd swarag

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## Typical workflow:

- python extract_pitch_batch.py
- python aggregate_pcds.py
- python aggregate_dyads.py
- python batch_evaluate.py

```

## Tech Stack:
- Python 3.10+
- Librosa
- NumPy
- SciPy
- Matplotlib

## Data:
- Swarag operates on user-provided or publicly licensed audio.
- No private user data is collected.

## License:
- MIT License.

## Contributions:
Contributions are welcome for:

- Adding new ragas
- Improving tonic estimation
- Performance optimization
- Evaluation and diagnostics
- Documentation

## Please open an issue or discussion before major changes.

## One Line Summary:
- Swarag models Carnatic ragas as pitch behavior and movement, building intelligence only after musical truth is validated.
