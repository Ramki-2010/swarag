"""
Update all .ai-memory files to v1.2.5 state.
Then verify all updates are consistent.
"""
import os
os.chdir(r"D:\Swaragam")

# ============================================================
# 1. architecture.md
# ============================================================
ARCH = r'''# Swarag -- Architecture (Current State)

## Version
Swarag v1.2.5 -- Deterministic DSP Pipeline (72-bin PCD + IDF x Variance + MIN_CLIPS guardrail)

## Pipeline

```
Audio (.wav / .mp3 / .flac)
  |
  v
Vocal Isolation (Saraga multitrack stems or Demucs htdemucs)
  |
  v
Pitch Extraction (pYIN via librosa, SR=22050, MAX_DURATION_SEC=360)
  |
  v
Tonic (Sa) Estimation (utils.py -> estimate_tonic)
  |  histogram-based + octave-aware candidate scoring
  v
Pitch Normalization (cents relative to Sa, folded to 0-1200)
  |
  v
Feature Computation
  |-- PCD: 72-bin pitch class distribution (17 cents per bin)
  +-- Directional Dyads: stable-region detection + Laplace smoothing
      |-- mean_up   (ascending transitions, 72x72 matrix)
      +-- mean_down (descending transitions, 72x72 matrix)
      |-- ALPHA=0.01 (Phase 2 fix: was 0.5)
  |
  v
Aggregation (aggregate_all_v12.py)
  |-- MIN_CLIPS_PER_RAGA=5 guardrail (excludes thin-data ragas)
  |-- Mean PCD + mean dyads per raga
  v
Raga Scoring (recognize_raga_v12.py)
  |-- IDF x Variance weighted dot-product (PCD + Dyads)
  |-- Weighted fusion (PCD_WEIGHT=0.6, DYAD_WEIGHT=0.4)
  |-- Genericness penalty REMOVED (GENERICNESS_WEIGHT=0.0)
  |-- Escalation DISABLED
  +-- Tiered confidence:
      |-- HIGH:     margin >= 0.003 (MARGIN_STRICT)
      |-- MODERATE: margin >= 0.001 (MIN_MARGIN_FINAL)
      +-- UNKNOWN:  margin < 0.001
  |
  v
Output: { "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Core Scripts

| Script | Responsibility |
|---|---|
| `recognize_raga_v12.py` | Inference engine (72-bin, IDF x Variance) |
| `aggregate_all_v12.py` | Build raga models (with MIN_CLIPS guardrail) |
| `extract_pitch_batch_v12.py` | Pitch extraction + feature creation |
| `batch_evaluate.py` | Evaluation on seed dataset (with per-file timeout) |
| `batch_evaluate_random.py` | Evaluation on unknown clips |
| `utils.py` | Shared utilities (tonic estimation) |

## Support Scripts

| Script | Purpose |
|---|---|
| `extract_new_clips.py` | Feature extraction for new clips |
| `extract_saraga_vocals.py` | Saraga vocal stem extraction |
| `run_demucs_batch.py` | Demucs batch vocal isolation |
| `sandbox_loo_9ragas.py` | LOO validation for 9 ragas |
| `sandbox_loo_validation.py` | LOO cross-validation (36 vs 72 bins) |
| `sandbox_phase2_alpha.py` | Phase 2 ALPHA tuning |
| `sandbox_phase3_thodi_sink.py` | Phase 3 IDF scoring |
| `sandbox_phase3b_variance.py` | Phase 3b variance weighting |
| `sandbox_phase4_bins.py` | Phase 4 bin resolution |
| `sandbox_phase4_production.py` | Phase 4 production test |
| `sandbox_hubness.py` | Hubness correction (PARKED for 15+ ragas) |

## Trained Ragas (6 ragas, 61 clips)

| Raga | Clips | Batch Eval Acc (decided) |
|---|---|---|
| Bhairavi | 11 | 33% |
| Kalyani | 14 | 100% |
| Shankarabharanam | 9 | 87.5% |
| Mohanam | 11 | 50% |
| Thodi | 11 | 100% |
| Kamboji | 5 | 66.7% |

### Staged Ragas (excluded by MIN_CLIPS_PER_RAGA=5 guardrail)
- Abhogi: 2 clips (needs 3 more)
- Madhyamavati: 2 clips (needs 3 more)
- Saveri: 3 clips (needs 2 more)
- Hamsadhvani: 1 clip (needs 4 more)

## Aggregation Data Location
```
D:\Swaragam\pcd_results\aggregation\v1.2\run_20260320_222322\
  pcd_stats\    -> {raga}_pcd_stats.npz (6 ragas)
  dyad_stats\   -> {raga}_dyad_stats.npz (6 ragas)
  aggregation_metadata.json  (alpha=0.01, bins=72, 61 clips, min_clips=5)
```

## Feature Storage
```
D:\Swaragam\pcd_results\features_v12\           68 unique .npz files
D:\Swaragam\pcd_results\features_v12\excluded\  13 duplicates + 2 Thodi outliers
```

## Shared Constants (must be identical in aggregate + recognize)

| Constant | Value | Notes |
|---|---|---|
| SR | 22050 | Sample rate |
| MAX_DURATION_SEC | 360 | 6-minute cap per file |
| N_BINS | 72 | PCD and dyad bins |
| MIN_STABLE_FRAMES | 5 | Stable region threshold |
| ALPHA | 0.01 | Laplace smoothing (Phase 2 fix) |
| EPS | 1e-8 | Division safety |
| PCD_WEIGHT | 0.6 | Scoring weight |
| DYAD_WEIGHT | 0.4 | Scoring weight |
| GENERICNESS_WEIGHT | 0.0 | Disabled |
| MARGIN_STRICT | 0.003 | HIGH confidence threshold |
| MIN_MARGIN_FINAL | 0.001 | MODERATE confidence threshold |
| MIN_CLIPS_PER_RAGA | 5 | Aggregation guardrail (BUG-011) |
| PER_FILE_TIMEOUT | 360 | Batch eval per-file timeout |

## Frozen Output Schema
```python
{ "final": str, "ranking": list, "margin": float, "confidence_tier": str }
```

## Current Accuracy (v1.2.5)

| Metric | LOO | Batch Eval |
|---|---|---|
| Accuracy (decided) | 72.0% | 72.7% |
| Correct | 18/61 | 32/81 |
| Unknown | 36 (59%) | 37 (45.7%) |
| Wrongs | 7 | 12 |

## Accuracy Evolution

| Version | LOO Acc | Key Change |
|---|---|---|
| v1.2 | 25% | Baseline (3 ragas) |
| v1.2.1 | -- | 6 ragas, vocal isolation |
| v1.2.2 | 64% | ALPHA fix (0.5 to 0.01) |
| v1.2.3 | 70% | IDF x Variance scoring |
| v1.2.4 | 78.6% | 72-bin PCD (53 clips) |
| v1.2.5 | 72.0% | Expanded to 61 clips, dedup, MIN_CLIPS guardrail |

## Remaining Issues
1. Bhairavi: 33% batch eval accuracy (8/11 go UNKNOWN) -- model issue
2. Mohanam: 50% accuracy (9/13 go UNKNOWN) -- model issue
3. Kamboji: 66.7% (5/8 go UNKNOWN) -- needs more clips
4. Score compression for sibling ragas
5. No OOD score floor (margin-only detection)
6. BUG-009: Mix audio causes OOD false positives

## Parked Features
| Feature | Trigger | Sandbox Script |
|---|---|---|
| Hubness correction | Ragas >= 15 | sandbox_hubness.py |
'''

with open(".ai-memory/architecture.md", "w", encoding="utf-8") as f:
    f.write(ARCH.strip() + "\n")
print("[1/5] architecture.md updated")

# ============================================================
# 2. bugs.md -- add BUG-011, update existing bugs
# ============================================================
with open(".ai-memory/bugs.md", "r", encoding="utf-8") as f:
    bugs = f.read()

# Add BUG-011 if not present
if "BUG-011" not in bugs:
    bug011 = '''
### BUG-011: Thin-Data Ragas Poison Model (Saveri/Abhogi Sink)
- **Status**: RESOLVED (2026-03-20)
- **Found**: 2026-03-20 (sandbox_loo_9ragas.py)
- **Description**:
  When ragas with <5 training clips (Abhogi=2, Madhyamavati=2, Saveri=3)
  are included in aggregation, they become attractors (sinks) that absorb
  wrongs from other ragas. Saveri absorbed 12/21 wrongs, Abhogi absorbed 5/21.
  LOO accuracy dropped from 72.0% (6 ragas) to 41.7% (9 ragas).
- **Root Cause**: Thin-data raga models are unstable -- their mean PCD/dyads
  are dominated by 1-2 clips and do not represent the raga reliably.
  IDF weighting amplifies their distinctive bins, making them "attractive"
  to other ragas' clips.
- **Fix**: Added MIN_CLIPS_PER_RAGA=5 guardrail to aggregate_all_v12.py.
  Ragas below threshold are excluded from aggregation with a warning.
  Features are kept (not deleted) so they can be activated when more data arrives.
- **Evidence**:
  - 9-raga LOO: 41.7% (15c/21w/32u). Saveri=12 wrongs, Abhogi=5 wrongs.
  - 6-raga LOO: 72.0% (18c/7w/36u). No sink ragas.
- **Verified**: Re-aggregation with guardrail excludes 3 ragas, accuracy restored.

### BUG-012: Duplicate Features Inflate Clip Counts
- **Status**: RESOLVED (2026-03-20)
- **Found**: 2026-03-20 (feature audit)
- **Description**:
  13 feature files had duplicates (same audio processed twice with different
  timestamps). Inflated total from 68 unique to 81. Some ragas appeared to
  have more data than they actually did.
- **Fix**: Identified duplicates by matching raga + source filename prefix.
  Moved 13 duplicates to features_v12/excluded/. Also removed 25 .dup files
  left by previous cleanup attempts.
- **Evidence**: 81 features -> 68 unique after dedup.

'''
    # Insert before "## Resolved Bugs"
    bugs = bugs.replace("## Resolved Bugs", bug011 + "## Resolved Bugs")

# Update BUG-008 status
bugs = bugs.replace(
    "### BUG-008: Thodi Sink (Cross-Raga Leakage)\n- **Status**: MOSTLY RESOLVED",
    "### BUG-008: Thodi Sink (Cross-Raga Leakage)\n- **Status**: RESOLVED (Phase 3+4+5: IDF x Variance + 72 bins + MIN_CLIPS guardrail)"
)

with open(".ai-memory/bugs.md", "w", encoding="utf-8") as f:
    f.write(bugs)
print("[2/5] bugs.md updated")

# ============================================================
# 3. lessons.md -- add new lessons
# ============================================================
with open(".ai-memory/lessons.md", "r", encoding="utf-8") as f:
    lessons = f.read()

new_lessons = '''

### L-036: Thin-Data Ragas Are Poison, Not Just Weak
- **Date**: 2026-03-20
- **Context**: Adding 3 new ragas (Abhogi=2, Saveri=3, Madhyamavati=2 clips)
  dropped LOO accuracy from 72.0% to 41.7%. They didn't just fail to recognize
  themselves -- they actively absorbed wrongs from established ragas.
  Saveri became a mega-sink (12/21 wrongs).
- **Rule**: Never include a raga in aggregation with fewer than 5 clips.
  Thin-data models are unstable and their IDF-amplified distinctive bins
  become false attractors. Use MIN_CLIPS_PER_RAGA guardrail.
  Keep the features staged; activate when data threshold is met.
- **Impact**: Without the guardrail, every new raga added with 1-3 clips
  would degrade the entire system.

### L-037: Duplicate Features Silently Inflate Accuracy
- **Date**: 2026-03-20
- **Context**: Feature extraction ran twice on some audio files, producing
  duplicate .npz files with different timestamps. This inflated clip counts
  (81 vs 68 actual) and biased mean models toward duplicated clips.
- **Rule**: Before aggregation, always audit for duplicates by matching
  raga + source filename prefix. The timestamp portion of .npz filenames
  varies between runs, so match on the content identifier only.
- **Impact**: Inflated confidence in model stability. Some ragas appeared
  to have more diverse training data than they actually did.

### L-038: Don't Kill Long-Running Processes at 80%
- **Date**: 2026-03-20
- **Context**: Killed a batch_evaluate.py run after 2 hours (80% complete)
  because it was using the wrong model. Should have let it finish since it
  only had ~20 min remaining, then discarded the results.
- **Rule**: If a long process is >50% complete, let it finish unless it's
  actively harmful (not just using wrong params). The cost of restarting
  from zero always exceeds the cost of waiting for completion.
- **Impact**: Wasted 2 hours of compute. Had to restart from scratch.

### L-039: Add Per-File Timeouts to Batch Processing
- **Date**: 2026-03-20
- **Context**: batch_evaluate.py had no per-file timeout. If pYIN hangs on
  a corrupted or very long audio file, the entire batch blocks indefinitely.
  Added ThreadPoolExecutor with PER_FILE_TIMEOUT=360s per file.
- **Rule**: Any batch processing script that runs external algorithms (pYIN,
  Demucs, etc.) on user-provided audio must have a per-file timeout.
  Use concurrent.futures.ThreadPoolExecutor with timeout, not signal-based
  approaches (which don't work on Windows threads).
- **Impact**: Prevents infinite hangs on bad files.
'''

if "L-036" not in lessons:
    lessons += new_lessons

with open(".ai-memory/lessons.md", "w", encoding="utf-8") as f:
    f.write(lessons)
print("[3/5] lessons.md updated")

# ============================================================
# 4. datasets.md -- add v1.2.5 results
# ============================================================
with open(".ai-memory/datasets.md", "r", encoding="utf-8") as f:
    ds = f.read()

# Update clip counts table
ds = ds.replace(
    "**Total: 53 clips across 6 ragas**",
    "**Total: 61 clips across 6 modeled ragas (68 features total, 3 ragas staged)**"
)

# Update aggregation model location
ds = ds.replace(
    '- **72-bin models (current)**: `D:\\Swaragam\\pcd_results\\aggregation\\v1.2\\run_20260312_205842_72bins\\`',
    '- **72-bin models (v1.2.4)**: `D:\\Swaragam\\pcd_results\\aggregation\\v1.2\\run_20260312_205842_72bins\\`\n- **72-bin models (v1.2.5 current)**: `D:\\Swaragam\\pcd_results\\aggregation\\v1.2\\run_20260320_222322\\` (6 ragas, 61 clips, MIN_CLIPS=5)'
)

# Add v1.2.5 test results
new_results = '''
### Run: 2026-03-21 -- v1.2.5 Batch Evaluation (6 ragas, 61 clips, 72 bins)
**Models**: run_20260320_222322 (6 ragas, 61 clips, MIN_CLIPS_PER_RAGA=5)
**Eval output**: run_20260321_004951
**Scoring**: IDF x Variance, 72 bins, ALPHA=0.01, PER_FILE_TIMEOUT=360s

**Seed Dataset (81 audio files, all ragas including non-modeled)**:
| Raga | Has Model | Total | Correct | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Kalyani | Y | 14 | 10 | 4 | 100% |
| Thodi | Y | 10 | 10 | 0 | 100% |
| Shankarabharanam | Y | 9 | 7 | 1 | 87.5% |
| Kamboji | Y | 8 | 2 | 5 | 66.7% |
| Mohanam | Y | 13 | 2 | 9 | 50% |
| Bhairavi | Y | 11 | 1 | 8 | 33.3% |
| Abhogi | N | 4 | 0 | 3 | 0% (no model) |
| Madhyamavati | N | 4 | 0 | 4 | 0% (all UNKNOWN, correct) |
| Saveri | N | 7 | 0 | 3 | 0% (4 -> Thodi) |
| Hamsadhvani | N | 1 | 0 | 0 | 0% (-> Kalyani) |
| **TOTAL** | | **81** | **32** | **37** | **72.7%** |

**LOO Cross-Validation (6 ragas, 61 clips)**:
| Raga | Clips | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Bhairavi | 11 | 2 | 1 | 8 | 67% |
| Kalyani | 14 | 7 | 1 | 6 | 88% |
| Kamboji | 5 | 0 | 1 | 4 | 0% |
| Mohanam | 11 | 1 | 3 | 7 | 25% |
| Shankarabharanam | 9 | 3 | 1 | 5 | 75% |
| Thodi | 11 | 5 | 0 | 6 | 100% |
| **TOTAL** | **61** | **18** | **7** | **36** | **72.0%** |

**Key findings:**
1. Thodi: PERFECT (10/10 batch, 100% LOO) -- sink completely fixed
2. Kalyani: PERFECT decided (10/10 batch, 88% LOO)
3. Bhairavi: WEAK (33% batch, 67% LOO) -- most clips go UNKNOWN, model issue
4. Mohanam: WEAK (50% batch, 25% LOO) -- most clips go UNKNOWN
5. Non-modeled ragas: Madhyamavati correctly all UNKNOWN; Saveri leaks to Thodi
6. Hamsadhvani -> Kalyani false positive (subset raga, expected)

'''

if "run_20260321_004951" not in ds:
    # Add before the first old test result
    ds = ds.replace("### Run: 2026-03-10", new_results + "### Run: 2026-03-10")

with open(".ai-memory/datasets.md", "w", encoding="utf-8") as f:
    f.write(ds)
print("[4/5] datasets.md updated")

# ============================================================
# 5. debug-playbook.md -- update aggregation path
# ============================================================
with open(".ai-memory/debug-playbook.md", "r", encoding="utf-8") as f:
    dbg = f.read()

dbg = dbg.replace(
    "Current: pcd_results/aggregation/v1.2/run_20260312_205842_72bins/",
    "Current: pcd_results/aggregation/v1.2/run_20260320_222322/"
)
dbg = dbg.replace(
    "Scoring: IDF x Variance weighted, 72 bins (Phase 4, v1.2.4)",
    "Scoring: IDF x Variance weighted, 72 bins, MIN_CLIPS=5 (v1.2.5)"
)

# Add new failure pattern
if "Thin-data raga" not in dbg:
    dbg = dbg.replace(
        "| UnicodeEncodeError",
        "| New raga tanks accuracy | Thin-data raga sink (need 5+ clips) -- BUG-011 |\n| UnicodeEncodeError"
    )

with open(".ai-memory/debug-playbook.md", "w", encoding="utf-8") as f:
    f.write(dbg)
print("[5/5] debug-playbook.md updated")

# ============================================================
# VERIFY
# ============================================================
print()
print("=" * 60)
print("VERIFICATION")
print("=" * 60)

checks = []
for fname, terms in [
    (".ai-memory/architecture.md", ["v1.2.5", "72-bin", "MIN_CLIPS_PER_RAGA", "61 clips", "run_20260320_222322", "72.0%", "72.7%"]),
    (".ai-memory/bugs.md", ["BUG-011", "BUG-012", "MIN_CLIPS_PER_RAGA"]),
    (".ai-memory/lessons.md", ["L-036", "L-037", "L-038", "L-039"]),
    (".ai-memory/datasets.md", ["run_20260321_004951", "run_20260320_222322", "72.7%"]),
    (".ai-memory/debug-playbook.md", ["run_20260320_222322", "Thin-data raga"]),
]:
    with open(fname, "r", encoding="utf-8") as f:
        content = f.read()
    for term in terms:
        ok = term in content
        checks.append((fname.split("/")[-1] + ": " + term, ok))
        if not ok:
            print("  [FAIL] {} missing '{}'".format(fname, term))

passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print("  {}/{} checks passed".format(passed, total))
if passed == total:
    print("  ALL CHECKS PASSED")
else:
    print("  SOME CHECKS FAILED")
