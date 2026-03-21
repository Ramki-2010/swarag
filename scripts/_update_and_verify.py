"""
Update all repo files to v1.2.5, then verify before commit.
"""
import os
os.chdir(r"D:\Swaragam")

# ============================================================
# 1. README.md
# ============================================================
README = '''# Swarag -- Carnatic Raga Identification Engine

Swarag is a deterministic Carnatic raga recognition engine built using interpretable signal processing and structured statistical modeling. It emphasizes explainability, musical grammar, and bias correction over black-box learning.

## Version: v1.2.5

v1.2.5 introduces:
- **6 active ragas** with **61 deduplicated clips** (Bhairavi, Kalyani, Shankarabharanam, Mohanam, Thodi, Kamboji)
- **72-bin PCD** -- finer microtonal resolution (was 36-bin), +11.9% accuracy
- **IDF x Variance weighted scoring** -- downweights common bins, upweights distinctive bins
- **ALPHA=0.01** Laplace smoothing fix -- dyad discrimination 1.24x to 1.73x
- **MIN_CLIPS_PER_RAGA=5 guardrail** -- prevents thin-data ragas from poisoning the model
- **Duplicate feature detection and cleanup** -- deduped 81 inflated features down to 68
- **Vocal isolation** requirement -- all training audio is vocal-only
- **LOO cross-validation accuracy: 72.0%** (decided-only, 6 ragas, 61 clips)
- 3 new ragas staged (Abhogi, Madhyamavati, Saveri) -- awaiting more data (need 5+ clips each)

### Version History

| Version | Accuracy | Key Change |
|---|---|---|
| v1.2 | 25% | Baseline (3 ragas) |
| v1.2.1 | -- | 6 ragas, vocal isolation, OOD fixed |
| v1.2.2 | 64% | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | IDF x Variance PCD weighting |
| v1.2.4 | 78.6% | 72-bin PCD (6 ragas, 53 clips) |
| v1.2.5 | 72.0% | Expanded data (61 clips), dedup, MIN_CLIPS guardrail |

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
Vocal Isolation (Saraga multitrack stems or Demucs htdemucs)
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
  |-- PCD: 72-bin pitch class distribution (17 cents per bin)
  +-- Directional Dyads: ascending (mean_up) + descending (mean_down)
  |
  v
Raga Scoring
  |-- IDF x Variance weighted dot-product (PCD + Dyads)
  |-- Weighted fusion (PCD=0.6, Dyad=0.4)
  |-- MIN_CLIPS_PER_RAGA guardrail (excludes thin-data ragas)
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
| Mohanam | 11 | Carnatic Varnam + Saraga stems + Demucs |
| Thodi | 11 | Saraga vocal stems + Demucs |
| Kamboji | 5 | Saraga vocal stems + Demucs |

### Staged (awaiting more data, need 5+ clips each)

| Raga | Current Clips | Status |
|---|---|---|
| Abhogi | 2 | Needs 3 more |
| Madhyamavati | 2 | Needs 3 more |
| Saveri | 3 | Needs 2 more |
| Hamsadhvani | 1 | Needs 4 more |

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
  recognize_raga_v12.py             Inference engine (72-bin, IDF x Variance)
  aggregate_all_v12.py              Build raga models (with MIN_CLIPS guardrail)
  extract_pitch_batch_v12.py        Feature extraction (with 6-min cap)
  batch_evaluate.py                 Evaluation on seed dataset
  batch_evaluate_random.py          Evaluation on unknown clips
  utils.py                          Shared utilities (tonic estimation)
  extract_saraga_vocals.py          Saraga vocal stem extraction
  extract_new_clips.py              Feature extraction for new clips
  run_demucs_batch.py               Demucs batch vocal isolation
  sandbox_*.py                      Phase 2-4 sandbox test scripts
  archive/                          Deprecated pre-v1.2 scripts

.ai/                            AI agent specification
.ai-memory/                     Project memory (bugs, lessons, architecture)
docs/                           Documentation and visual assets
```

Gitignored locally (not in repo):
- `datasets/` -- audio files
- `pcd_results/` -- features, models, evaluations
- `demucs_outputs/` -- vocal separation outputs
- `demucs_staging/` -- files queued for Demucs
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

**Step 1 -- Extract pitch features from dataset:**
```bash
python extract_pitch_batch_v12.py
```

**Step 2 -- Aggregate raga signatures:**
```bash
python aggregate_all_v12.py
```

**Step 3 -- Evaluate:**
```bash
python batch_evaluate.py           # on seed dataset
python batch_evaluate_random.py    # on unknown audio
```

> Note: Update `AGG_FOLDER` in batch scripts to point to the latest run folder from Step 2.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the mandatory development loop, sandbox-first rule, and contribution workflow.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT License -- see [LICENSE](LICENSE).
'''

with open("README.md", "w", encoding="utf-8") as f:
    f.write(README.strip() + "\n")
print("[1/4] README.md updated")

# ============================================================
# 2. PROJECT_STATUS.md
# ============================================================
STATUS = '''# Swarag -- Project Status

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
'''

with open("PROJECT_STATUS.md", "w", encoding="utf-8") as f:
    f.write(STATUS.strip() + "\n")
print("[2/4] PROJECT_STATUS.md updated")

# ============================================================
# 3. .gitignore -- add demucs_staging/
# ============================================================
with open(".gitignore", "r", encoding="utf-8") as f:
    gi = f.read()

if "demucs_staging" not in gi:
    gi = gi.replace("demucs_outputs/", "demucs_outputs/\ndemucs_staging/")
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gi)
    print("[3/4] .gitignore updated (added demucs_staging/)")
else:
    print("[3/4] .gitignore already up to date")

# ============================================================
# 4. Stage everything
# ============================================================
import subprocess

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r"D:\Swaragam")
    out = (r.stdout.strip() + "\n" + r.stderr.strip()).strip()
    return r.returncode, out

# Core files
for f in [
    "README.md", "PROJECT_STATUS.md", ".gitignore",
    ".ai-memory/",
    "scripts/aggregate_all_v12.py",
    "scripts/recognize_raga_v12.py",
    "scripts/batch_evaluate.py",
    "scripts/batch_evaluate_random.py",
    "scripts/extract_new_clips.py",
    "scripts/extract_saraga_vocals.py",
    "scripts/run_demucs_batch.py",
    "scripts/sandbox_loo_9ragas.py",
    "scripts/sandbox_loo_validation.py",
    "scripts/sandbox_phase1_fast.py",
    "scripts/sandbox_phase1_pcd_only.py",
    "scripts/sandbox_phase2_alpha.py",
    "scripts/sandbox_phase3_thodi_sink.py",
    "scripts/sandbox_phase3b_variance.py",
    "scripts/sandbox_phase4_bins.py",
    "scripts/sandbox_phase4_production.py",
    "scripts/sandbox_hubness.py",
    "scripts/diag_alpha.py",
    "scripts/diag_scores.py",
    "scripts/extract_new_thodi.py",
    "scripts/plan_a_full_scan.py",
    "scripts/plan_a_saraga_audit.py",
    "scripts/_apply_phase3_edit.py",
    "scripts/_apply_phase3_v2.py",
    "scripts/_fix_agg_paths.py",
    "scripts/_push_72bins.py",
    "scripts/_update_all_docs.py",
]:
    run("git add " + f)

print("[4/4] All files staged")

# ============================================================
# 5. VERIFY -- show what will be committed
# ============================================================
print()
print("=" * 70)
print("VERIFICATION -- Files staged for commit:")
print("=" * 70)
_, out = run("git diff --cached --stat")
print(out)

print()
print("=" * 70)
print("VERIFICATION -- Key content checks:")
print("=" * 70)

# Check README
with open("README.md") as f:
    rm = f.read()
checks = [
    ("README: v1.2.5", "v1.2.5" in rm),
    ("README: 72-bin", "72-bin" in rm),
    ("README: IDF x Variance", "IDF x Variance" in rm),
    ("README: MIN_CLIPS", "MIN_CLIPS_PER_RAGA" in rm),
    ("README: 61 clips", "61" in rm),
    ("README: LOO 72.0%", "72.0%" in rm),
    ("README: Mohanam 11", "Mohanam | 11" in rm),
    ("README: Kamboji 5", "Kamboji | 5" in rm),
    ("README: staged ragas table", "Abhogi" in rm and "Saveri" in rm),
]

with open("PROJECT_STATUS.md") as f:
    ps = f.read()
checks += [
    ("STATUS: v1.2.5", "v1.2.5" in ps),
    ("STATUS: 72-bin", "72-bin" in ps),
    ("STATUS: ALPHA 0.01", "0.01" in ps),
    ("STATUS: MIN_CLIPS", "MIN_CLIPS_PER_RAGA" in ps),
    ("STATUS: evolution table", "v1.2.2" in ps and "v1.2.5" in ps),
]

with open(".gitignore") as f:
    gic = f.read()
checks += [
    ("GITIGNORE: demucs_staging", "demucs_staging" in gic),
]

with open("scripts/recognize_raga_v12.py") as f:
    rc = f.read()
checks += [
    ("recognize: N_BINS=72", "N_BINS           = 72" in rc),
    ("recognize: ALPHA=0.01", "ALPHA             = 0.01" in rc),
    ("recognize: IDF weights", "compute_pcd_weights" in rc),
]

with open("scripts/aggregate_all_v12.py") as f:
    ag = f.read()
checks += [
    ("aggregate: N_BINS=72", "N_BINS = 72" in ag),
    ("aggregate: ALPHA=0.01", "ALPHA = 0.01" in ag),
    ("aggregate: MIN_CLIPS", "MIN_CLIPS_PER_RAGA" in ag),
    ("aggregate: exclusion logic", "FILTER: exclude ragas" in ag),
]

all_pass = True
for label, result in checks:
    sym = "PASS" if result else "FAIL"
    if not result:
        all_pass = False
    print("  [{}] {}".format(sym, label))

print()
if all_pass:
    print("ALL CHECKS PASSED -- ready to commit.")
else:
    print("SOME CHECKS FAILED -- review before committing!")
