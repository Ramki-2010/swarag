"""
v1.3 lockdown:
1. Move short Mohanam clip (Shloka Sri Ramachandra) to excluded
2. Update recognize_raga_v12.py weights to 0.7/0.3
3. Re-aggregate (5 ragas, 55 clips)
4. Update AGG paths
5. Update all docs (README, PROJECT_STATUS, .ai-memory)
6. Verify, commit, push
"""
import os, subprocess, shutil, json

os.chdir(r"D:\Swaragam")

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r"D:\Swaragam")
    if r.stdout.strip():
        print(r.stdout.strip()[:200])
    if r.returncode != 0 and r.stderr.strip():
        print("ERR:", r.stderr.strip()[:200])
    return r.returncode

# ============================================================
# 1. Move short Mohanam clip feature to excluded
# ============================================================
feat_dir = r"D:\Swaragam\pcd_results\features_v12"
excl_dir = os.path.join(feat_dir, "excluded")
for f in os.listdir(feat_dir):
    if f.startswith("Shloka Sri Ramachandra") and f.endswith(".npz"):
        src = os.path.join(feat_dir, f)
        dst = os.path.join(excl_dir, f)
        shutil.move(src, dst)
        print("[1] Moved feature: {} to excluded/".format(f))

# Move audio too
audio_src = r"D:\Swaragam\datasets\seed_carnatic\Mohanam\Shloka Sri Ramachandra.vocal.mp3"
audio_dst = r"D:\Swaragam\datasets\seed_carnatic\Mohanam\excluded\Shloka Sri Ramachandra.vocal.mp3"
if os.path.exists(audio_src):
    shutil.move(audio_src, audio_dst)
    print("[1] Moved audio: Shloka Sri Ramachandra to excluded/")

# ============================================================
# 2. Update recognize_raga_v12.py weights to 0.7/0.3
# ============================================================
rec_file = r"D:\Swaragam\scripts\recognize_raga_v12.py"
with open(rec_file, "r", encoding="utf-8") as f:
    rec = f.read()

rec = rec.replace("PCD_WEIGHT        = 0.6", "PCD_WEIGHT        = 0.7")
rec = rec.replace("DYAD_WEIGHT       = 0.4", "DYAD_WEIGHT       = 0.3")

with open(rec_file, "w", encoding="utf-8") as f:
    f.write(rec)

# Verify
with open(rec_file, "r", encoding="utf-8") as f:
    v = f.read()
assert "PCD_WEIGHT        = 0.7" in v, "PCD weight not updated!"
assert "DYAD_WEIGHT       = 0.3" in v, "DYAD weight not updated!"
print("[2] recognize_raga_v12.py weights updated to 0.7/0.3")

# ============================================================
# 3. Re-aggregate
# ============================================================
print("[3] Re-aggregating...")
run(r"scripts\my_virtual_env_swarag\Scripts\python.exe scripts\aggregate_all_v12.py")

# Find latest aggregation run
agg_base = r"D:\Swaragam\pcd_results\aggregation\v1.2"
runs = sorted([d for d in os.listdir(agg_base) if d.startswith("run_")])
latest_run = os.path.join(agg_base, runs[-1])
print("[3] Latest aggregation: {}".format(latest_run))

# Read metadata
meta_file = os.path.join(latest_run, "aggregation_metadata.json")
if os.path.exists(meta_file):
    with open(meta_file, "r") as f:
        meta = json.load(f)
    print("[3] Ragas: {}  Clips: {}".format(meta.get("ragas_included", "?"), meta.get("total_clips", "?")))

# ============================================================
# 4. Update AGG paths in batch scripts
# ============================================================
for fname in ["scripts/batch_evaluate.py", "scripts/batch_evaluate_random.py"]:
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "AGG_FOLDER" in line and "=" in line and 'r"' in line:
            lines[i] = 'AGG_FOLDER   = r"{}"\n'.format(latest_run)
            break
    with open(fname, "w", encoding="utf-8") as f:
        f.writelines(lines)
print("[4] AGG paths updated in batch scripts")

# ============================================================
# 5. Update README.md
# ============================================================
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

See [DEVELOPMENT.md](DEVELOPMENT.md) for the mandatory development loop.

## License

MIT License -- see [LICENSE](LICENSE).
'''

with open("README.md", "w", encoding="utf-8") as f:
    f.write(README.strip() + "\n")
print("[5] README.md updated")

# ============================================================
# 6. Update PROJECT_STATUS.md
# ============================================================
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
| Constant | Value | Notes |
|---|---|---|
| N_BINS | 72 | 17 cents per bin |
| ALPHA | 0.01 | Laplace smoothing |
| PCD_WEIGHT | 0.7 | Was 0.6 in v1.2.5 |
| DYAD_WEIGHT | 0.3 | Was 0.4 in v1.2.5 |
| MIN_CLIPS_PER_RAGA | 5 | Guardrail |
| MARGIN_STRICT | 0.003 | HIGH confidence |
| MIN_MARGIN_FINAL | 0.001 | MODERATE confidence |

### Current Accuracy
- LOO (decided): ~58.8% (5 ragas, 55 clips)
- Wrongs: 14 (down from 19 at 0.6/0.4)
- Thodi sink: 5/14 wrongs (down from 10/19)

### Ragas Modeled (v1.3)
| Raga | Clips | LOO Acc |
|---|---|---|
| Thodi | 11 | 83% |
| Kalyani | 14 | 80% |
| Shankarabharanam | 9 | 50% |
| Bhairavi | 11 | 50% |
| Mohanam | 10 | 17% |

### What Changed from v1.2.5
- Removed 3 Harikambhoji clips from Kamboji (wrong raga label)
- Kamboji dropped below guardrail (3 clips < 5 minimum)
- Removed Shloka Sri Ramachandra from Mohanam (936 frames, too short)
- Weights changed from 0.6/0.4 to 0.7/0.3 (fewer wrongs)
- Audio duplicates cleaned (Mohanam: 3 removed, Kamboji: 2 removed)
- Accuracy dropped from 72% to 58.8% (honest -- bad data was inflating it)

---

## Known Limitations

- Mohanam: 17% LOO -- needs diverse clips (current data is too similar)
- Bhairavi: 50% -- PCD overlaps 78% with Thodi, identity is in gamakas
- Kamboji: excluded (only 3 real clips)
- No OOD score floor
- Not robust to polyphonic audio

---

## Priority Plan

1. Fix Mohanam: add 4-6 diverse clips, verify tonic consistency
2. Fix Kamboji: add 5-7 real Kamboji clips (non-Saraga)
3. Per-raga dyad weight for Bhairavi
4. Re-activate Kamboji, target >70% overall
5. Then expand to Saveri, Hamsadhvani

---

## Philosophy

Swarag prioritizes musical validity and interpretability over premature accuracy.
Honest baselines over inflated numbers. Clean data over more data.
'''

with open("PROJECT_STATUS.md", "w", encoding="utf-8") as f:
    f.write(STATUS.strip() + "\n")
print("[6] PROJECT_STATUS.md updated")

# ============================================================
# 7. Update .ai-memory/architecture.md
# ============================================================
ARCH = open(".ai-memory/architecture.md", "r", encoding="utf-8").read()
ARCH = ARCH.replace("v1.2.5", "v1.3")
ARCH = ARCH.replace("PCD_WEIGHT | 0.6", "PCD_WEIGHT | 0.7")
ARCH = ARCH.replace("DYAD_WEIGHT | 0.4", "DYAD_WEIGHT | 0.3")
ARCH = ARCH.replace("6 ragas, 61 clips", "5 ragas, 55 clips")
ARCH = ARCH.replace("run_20260320_222322", latest_run.split("\\")[-1])

with open(".ai-memory/architecture.md", "w", encoding="utf-8") as f:
    f.write(ARCH)
print("[7] architecture.md updated")

# ============================================================
# 8. Update bugs.md -- add BUG-013
# ============================================================
bugs = open(".ai-memory/bugs.md", "r", encoding="utf-8").read()
if "BUG-013" not in bugs:
    bug013 = '''
### BUG-013: Harikambhoji Contamination in Kamboji Training Data
- **Status**: RESOLVED (2026-03-21)
- **Found**: 2026-03-21 (Saraga metadata cross-reference)
- **Description**:
  3 of 6 Kamboji training clips were actually Harikambhoji (parent melakarta,
  different raga). Saraga metadata confirmed: Dinamani Vamsa, Enadhu Manam Kavalai,
  Entara Nitana are all Harikambhoji, not Kamboji.
- **Impact**: Kamboji model was contaminated with wrong-raga data. After removal,
  Kamboji drops below MIN_CLIPS=5 guardrail (3 true clips remain).
  Overall LOO dropped from 72% (6 ragas) to 55.8% (5 ragas) because the
  contaminated model was ironically absorbing some clips into UNKNOWN.
- **Fix**: Moved 3 Harikambhoji audio + features to excluded/.
  Need 2+ more real Kamboji clips to reactivate.
- **Lesson**: Always cross-reference raga labels against Saraga metadata.
  Harikambhoji vs Kamboji is a common confusion (parent vs janya).

'''
    bugs = bugs.replace("## Resolved Bugs", bug013 + "## Resolved Bugs")
    with open(".ai-memory/bugs.md", "w", encoding="utf-8") as f:
        f.write(bugs)
print("[8] bugs.md updated")

# ============================================================
# 9. Add lesson
# ============================================================
lessons = open(".ai-memory/lessons.md", "r", encoding="utf-8").read()
if "L-040" not in lessons:
    new_lesson = '''

### L-040: Cross-Reference Raga Labels Against Authoritative Sources
- **Date**: 2026-03-21
- **Context**: 3/6 Kamboji clips were actually Harikambhoji. Discovered only by
  cross-referencing against Saraga metadata (which uses musicological raga names).
  Harikambhoji is the 28th melakarta (parent); Kamboji is its janya (child).
  They share most swaras but have different characteristic phrases.
- **Rule**: Before adding clips to a raga folder, verify the raga label against
  at least one authoritative source (Saraga, Dunya, or a musicologist). Parent
  vs janya raga confusion (Harikambhoji/Kamboji, Shankarabharanam/Kalyani) is
  a common trap. The audio may sound similar but the model will be contaminated.
- **Impact**: 3 wrong-raga clips dropped Kamboji below guardrail and overall
  accuracy from 72% to 55.8% when cleaned. The contamination was hidden because
  the model appeared to work (66.7% on batch eval).

### L-041: Honest Baselines Are More Valuable Than Inflated Numbers
- **Date**: 2026-03-21
- **Context**: v1.2.5 showed 72% LOO with 6 ragas. After cleaning Harikambhoji
  contamination, accuracy dropped to 55.8% with 5 ragas. The 72% was built on
  dirty data. The 55.8% is honest. Better to know the true baseline and improve
  from there than to build on a false foundation.
- **Rule**: When cleaning data causes accuracy to drop, that's a GOOD sign --
  it means you found and removed a source of error. The new lower number is
  the real starting point. Never keep bad data just because it gives better numbers.
'''
    lessons += new_lesson
    with open(".ai-memory/lessons.md", "w", encoding="utf-8") as f:
        f.write(lessons)
print("[9] lessons.md updated")

# ============================================================
# 10. Verify
# ============================================================
print()
print("=" * 60)
print("VERIFICATION")
print("=" * 60)

checks = []
with open("scripts/recognize_raga_v12.py", "r", encoding="utf-8") as f:
    rc = f.read()
checks.append(("recognize: PCD=0.7", "PCD_WEIGHT        = 0.7" in rc))
checks.append(("recognize: DYAD=0.3", "DYAD_WEIGHT       = 0.3" in rc))

with open("README.md", "r", encoding="utf-8") as f:
    rm = f.read()
checks.append(("README: v1.3", "v1.3" in rm))
checks.append(("README: 0.7/0.3", "PCD=0.7" in rm))
checks.append(("README: 55 clips", "55" in rm))

with open("PROJECT_STATUS.md", "r", encoding="utf-8") as f:
    ps = f.read()
checks.append(("STATUS: v1.3", "v1.3" in ps))
checks.append(("STATUS: 0.7", "0.7" in ps))

with open(".ai-memory/bugs.md", "r", encoding="utf-8") as f:
    b = f.read()
checks.append(("bugs: BUG-013", "BUG-013" in b))

with open(".ai-memory/lessons.md", "r", encoding="utf-8") as f:
    l = f.read()
checks.append(("lessons: L-040", "L-040" in l))
checks.append(("lessons: L-041", "L-041" in l))

all_pass = True
for label, ok in checks:
    print("  [{}] {}".format("OK" if ok else "FAIL", label))
    if not ok:
        all_pass = False

print()
if all_pass:
    print("ALL {} CHECKS PASSED".format(len(checks)))
else:
    print("SOME CHECKS FAILED")
