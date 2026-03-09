# Swarag — Carnatic Raga Identification Engine

Swarag is a deterministic Carnatic raga recognition engine built using interpretable signal processing and structured statistical modeling. It emphasizes explainability, musical grammar, and bias correction over black-box learning.

## Version: v1.2.1

v1.2.1 introduces:
- Expanded from 3 to **6 ragas** (Bhairavi, Kalyani, Shankarabharanam, Mohanam, Thodi, Kamboji)
- **Vocal isolation** requirement — all training audio is vocal-only
- **Duration cap** (6 minutes) — 10x faster, no accuracy loss
- **Recalibrated thresholds** — margins tuned to actual score distributions
- Escalation path disabled (was crushing margins)
- Genericness penalty removed (confirmed inert)
- 50 vocal-isolated training clips across 6 ragas

## Core Philosophy

- Relative pitch, not absolute frequency
- Behavioral transitions over scale checklists
- Preserve musical micro-structure
- Vocal-only audio for clean pitch extraction

All modeling is tonic-normalized (Sa).

## Pipeline

```
Audio (.wav / .mp3 / .flac)
  |
  v
Vocal Isolation (if needed: Saraga multitrack stems or Demucs)
  |
  v
Pitch Extraction (pYIN via librosa, 6-min cap)
  |
  v
Tonic (Sa) Estimation (histogram-based, octave-aware)
  |
  v
Pitch Normalization (cents relative to Sa, folded to 0-1200)
  |
  v
Feature Computation
  |-- PCD: 36-bin pitch class distribution
  +-- Directional Dyads: ascending (mean_up) + descending (mean_down)
  |
  v
Raga Scoring
  |-- Dot-product similarity (PCD + Dyads)
  |-- Weighted fusion (PCD=0.6, Dyad=0.4)
  +-- Tiered confidence: HIGH / MODERATE / UNKNOWN
  |
  v
Output: { "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Ragas Currently Modeled

| Raga | Training Clips | Audio Sources |
|---|---|---|
| Bhairavi | 11 | Original seed + Saraga vocal stems + Demucs |
| Kalyani | 14 | Original seed + Carnatic Varnam + Saraga + Demucs |
| Shankarabharanam | 9 | Original seed + Saraga vocal stems + Demucs |
| Mohanam | 6 | Carnatic Varnam + Saraga + Demucs |
| Thodi | 7 | Saraga vocal stems + Demucs |
| Kamboji | 3 | Demucs separated |

## Example Outputs

### Pitch Contour

<p align="center">
  <img src="docs/assets/Shankarabharanam_1_contour_20251228_195000.png" width="700">
</p>

### Pitch Class Distribution (PCD)

<p align="center">
  <img src="docs/assets/Shankarabharanam_pcd.png" width="550">
</p>

### Intra-Raga Statistical Profile

<p align="center">
  <img src="docs/assets/sample_output.png" width="750">
</p>

## Repository Structure

```
scripts/                        Active v1.2 pipeline
  extract_pitch_batch_v12.py        Feature extraction (with 6-min cap)
  aggregate_all_v12.py              Build raga statistical models
  recognize_raga_v12.py             Inference engine
  batch_evaluate.py                 Evaluation on seed dataset
  batch_evaluate_random.py          Evaluation on unknown clips
  utils.py                          Shared utilities (tonic estimation)
  extract_saraga_audio.py           Saraga dataset audio extractor
  test_*.py                         Sandbox test scripts
  archive/                          Deprecated pre-v1.2 scripts

.ai/                            AI agent specification
.ai-memory/                     Project memory (bugs, lessons, architecture)
docs/                           Documentation and visual assets
```

Gitignored locally (not in repo):
- `datasets/` — audio files
- `pcd_results/` — features, models, evaluations
- `demucs_outputs/` — vocal separation outputs
- Virtual environments

## Installation

```bash
pip install -r requirements.txt
```

For vocal separation (optional):
```bash
python -m venv demucs_env
demucs_env/Scripts/activate
pip install demucs
```

## Run Pipeline

All scripts are in `scripts/`. Run in this order:

**Step 1 — Extract pitch features from dataset:**
```bash
python extract_pitch_batch_v12.py
```

**Step 2 — Aggregate raga signatures:**
```bash
python aggregate_all_v12.py
```

**Step 3 — Evaluate:**
```bash
python batch_evaluate.py           # on seed dataset
python batch_evaluate_random.py    # on unknown audio
```

> Note: Update `AGG_FOLDER` in batch scripts to point to the latest run folder from Step 2.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the mandatory development loop, sandbox-first rule, and contribution workflow.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT License — see [LICENSE](LICENSE).
