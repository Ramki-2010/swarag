"""Steps 5-10: Update docs, verify, commit, push."""
import os
os.chdir(r"D:\Swaragam")

AGG_RUN = "run_20260321_135629"

# 5. README.md
README = '''# Swarag -- Carnatic Raga Identification Engine

Swarag is a deterministic Carnatic raga recognition engine built using interpretable signal processing and structured statistical modeling. It emphasizes explainability, musical grammar, and bias correction over black-box learning.

## Version: v1.3

v1.3 introduces:
- **Harikambhoji contamination removed** from Kamboji (3/6 clips were wrong raga)
- **PCD-heavy weights** (0.7/0.3) -- fewer wrongs, better decided accuracy
- **5 active ragas** with **55 deduplicated clips** (Bhairavi, Kalyani, Shankarabharanam, Mohanam, Thodi)
- Kamboji dropped below MIN_CLIPS=5 guardrail (needs 2+ real clips to reactivate)
- Short/weak clips removed (Shloka Sri Ramachandra, 936 frames)
- LOO accuracy: ~58.8% decided (honest baseline, 5 ragas)

### Version History

| Version | Accuracy | Ragas | Key Change |
|---|---|---|---|
| v1.2 | 25% | 3 | Baseline |
| v1.2.1 | -- | 6 | Vocal isolation, OOD fixed |
| v1.2.2 | 64% | 6 | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | 6 | IDF x Variance scoring |
| v1.2.4 | 78.6% | 6 | 72-bin PCD |
| v1.2.5 | 72.0% | 6 | Expanded data, dedup, MIN_CLIPS guardrail |
| v1.3 | 58.8% | 5 | Harikambhoji removed, weights 0.7/0.3, honest baseline |

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
  |-- Weighted fusion (PCD=0.7, Dyad=0.3)
  |-- MIN_CLIPS_PER_RAGA guardrail (excludes thin-data ragas)
  +-- Tiered confidence: HIGH / MODERATE / UNKNOWN
  |
  v
Output: { "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Ragas Currently Modeled

| Raga | Training Clips | LOO Accuracy |
|---|---|---|
| Thodi | 11 | 83% |
| Kalyani | 14 | 80% |
| Shankarabharanam | 9 | 50% |
| Bhairavi | 11 | 50% |
| Mohanam | 10 | 17% |

### Staged / Excluded (need more data)

| Raga | Current Clips | Status |
|---|---|---|
| Kamboji | 3 | Needs 2+ real clips (Harikambhoji removed) |
| Saveri | 3 | Needs 2 more |
| Abhogi | 2 | Needs 3 more |
| Madhyamavati | 2 | Needs 3 more |
| Hamsadhvani | 1 | Needs 4 more |

## Repository Structure

```
scripts/                        Active v1.3 pipeline
  recognize_raga_v12.py             Inference engine (72-bin, IDF x Variance, 0.7/0.3)
  aggregate_all_v12.py              Build raga models (with MIN_CLIPS guardrail)
  extract_pitch_batch_v12.py        Feature extraction (with 6-min cap)
  batch_evaluate.py                 Evaluation on seed dataset (per-file timeout)
  batch_evaluate_random.py          Evaluation on unknown clips
  utils.py                          Shared utilities (tonic estimation)
  sandbox_*.py                      Phase 2-4 sandbox test scripts
  archive/                          Deprecated pre-v1.2 scripts

.ai/                            AI agent specification
.ai-memory/                     Project memory (bugs, lessons, architecture)
docs/                           Documentation and visual assets
```

## Installation

```bash
pip install -r requirements.txt
```

## Run Pipeline

```bash
python extract_pitch_batch_v12.py    # Step 1: Extract features
python aggregate_all_v12.py          # Step 2: Build models
python batch_evaluate.py             # Step 3: Evaluate
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the development loop and sandbox-first rule.
See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT License -- see [LICENSE](LICENSE).
'''

with open("README.md", "w", encoding="utf-8") as f:
    f.write(README.strip() + "\n")
print("[5] README.md")

# 6. PROJECT_STATUS.md
STATUS = '''# Swarag -- Project Status

## Current Version
Swarag v1.3 (5-Raga Honest Baseline -- Harikambhoji cleaned, 72-bin, IDF x Variance)

---

## What Is Stable

- 72-bin PCD + IDF x Variance weighted dot-product scoring
- Directional dyads with ALPHA=0.01 Laplace smoothing
- PCD_WEIGHT=0.7, DYAD_WEIGHT=0.3 (PCD-heavy -- fewer wrongs)
- MIN_CLIPS_PER_RAGA=5 guardrail
- Vocal isolation mandatory (Saraga stems + Demucs)
- Per-file timeout in batch evaluation (360s)

### Key Constants
| Constant | Value |
|---|---|
| N_BINS | 72 |
| ALPHA | 0.01 |
| PCD_WEIGHT | 0.7 |
| DYAD_WEIGHT | 0.3 |
| MIN_CLIPS_PER_RAGA | 5 |
| MARGIN_STRICT | 0.003 |
| MIN_MARGIN_FINAL | 0.001 |

### Current Accuracy (LOO, 5 ragas, 55 clips)
| Raga | Clips | LOO Acc |
|---|---|---|
| Thodi | 11 | 83% |
| Kalyani | 14 | 80% |
| Shankarabharanam | 9 | 50% |
| Bhairavi | 11 | 50% |
| Mohanam | 10 | 17% |
| **Overall** | **55** | **~58.8% decided** |

### What Changed from v1.2.5
- Removed 3 Harikambhoji clips from Kamboji (wrong raga label -- BUG-013)
- Removed short Mohanam clip (936 frames)
- Audio duplicates cleaned (Mohanam: 3 removed, Kamboji: 2 removed)
- Weights: 0.6/0.4 to 0.7/0.3 (fewer wrongs)
- Accuracy: 72% to 58.8% (honest -- bad data was inflating it)

---

## Known Limitations

- Mohanam: 17% LOO -- needs diverse clips
- Bhairavi: 50% -- PCD overlaps 78% with Thodi
- Kamboji: excluded (3 real clips, need 2+ more)
- No OOD score floor

---

## Priority Plan

1. Fix Mohanam: add 4-6 diverse clips
2. Fix Kamboji: add 5-7 real clips (non-Saraga)
3. Per-raga dyad weight for Bhairavi
4. Target: 70-80% overall after fixes
5. Then expand to Saveri, Hamsadhvani

---

## Philosophy

Honest baselines over inflated numbers. Clean data over more data.
'''

with open("PROJECT_STATUS.md", "w", encoding="utf-8") as f:
    f.write(STATUS.strip() + "\n")
print("[6] PROJECT_STATUS.md")

# 7. architecture.md
arch = open(".ai-memory/architecture.md", "r", encoding="utf-8").read()
arch = arch.replace("v1.2.5", "v1.3").replace("PCD_WEIGHT | 0.6", "PCD_WEIGHT | 0.7").replace("DYAD_WEIGHT | 0.4", "DYAD_WEIGHT | 0.3")
arch = arch.replace("6 ragas, 61 clips", "5 ragas, 55 clips")
# Update agg path
import re
arch = re.sub(r"run_20260320_\d+", AGG_RUN, arch)
with open(".ai-memory/architecture.md", "w", encoding="utf-8") as f:
    f.write(arch)
print("[7] architecture.md")

# 8. bugs.md
bugs = open(".ai-memory/bugs.md", "r", encoding="utf-8").read()
if "BUG-013" not in bugs:
    bug013 = """
### BUG-013: Harikambhoji Contamination in Kamboji Training Data
- **Status**: RESOLVED (2026-03-21)
- **Found**: 2026-03-21 (Saraga metadata cross-reference)
- **Description**: 3/6 Kamboji clips were actually Harikambhoji (parent melakarta).
- **Fix**: Moved to excluded/. Kamboji dropped below guardrail (3 clips remain).
- **Impact**: Overall LOO dropped 72% to 58.8% (honest baseline).

"""
    bugs = bugs.replace("## Resolved Bugs", bug013 + "## Resolved Bugs")
    with open(".ai-memory/bugs.md", "w", encoding="utf-8") as f:
        f.write(bugs)
print("[8] bugs.md")

# 9. lessons.md
lessons = open(".ai-memory/lessons.md", "r", encoding="utf-8").read()
if "L-040" not in lessons:
    lessons += """

### L-040: Cross-Reference Raga Labels Against Authoritative Sources
- **Date**: 2026-03-21
- **Context**: 3/6 Kamboji clips were Harikambhoji. Parent vs janya confusion.
- **Rule**: Always verify raga labels against Saraga/Dunya metadata before training.
- **Impact**: Contamination hidden by apparent 66.7% accuracy.

### L-041: Honest Baselines Beat Inflated Numbers
- **Date**: 2026-03-21
- **Context**: Cleaning bad data dropped accuracy from 72% to 58.8%.
- **Rule**: Never keep bad data for better numbers. The honest number is the foundation.
"""
    with open(".ai-memory/lessons.md", "w", encoding="utf-8") as f:
        f.write(lessons)
print("[9] lessons.md")

# 10. Verify
print()
print("=" * 60)
checks = [
    ("recognize: PCD=0.7", "PCD_WEIGHT       = 0.7" in open("scripts/recognize_raga_v12.py").read()),
    ("recognize: DYAD=0.3", "DYAD_WEIGHT      = 0.3" in open("scripts/recognize_raga_v12.py").read()),
    ("README: v1.3", "v1.3" in open("README.md").read()),
    ("STATUS: v1.3", "v1.3" in open("PROJECT_STATUS.md").read()),
    ("STATUS: 0.7", "0.7" in open("PROJECT_STATUS.md").read()),
    ("bugs: BUG-013", "BUG-013" in open(".ai-memory/bugs.md").read()),
    ("lessons: L-040", "L-040" in open(".ai-memory/lessons.md").read()),
    ("arch: v1.3", "v1.3" in open(".ai-memory/architecture.md").read()),
    ("batch: " + AGG_RUN, AGG_RUN in open("scripts/batch_evaluate.py").read()),
]
passed = 0
for label, ok in checks:
    sym = "OK" if ok else "FAIL"
    print("  [{}] {}".format(sym, label))
    if ok: passed += 1

print()
print("{}/{} checks passed".format(passed, len(checks)))
if passed == len(checks):
    print("ALL PASSED -- ready to commit")
