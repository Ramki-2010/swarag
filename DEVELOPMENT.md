# Swarag — Development Workflow

This document defines how development works on Swarag. Every contributor — human or AI — must follow these rules.

---

## 1. The Development Loop

Every change follows 4 mandatory steps. No exceptions.

```
STEP 1: PLAN
  |  What are we changing? Why? What could break?
  |  Read: .ai-memory/bugs.md, .ai-memory/architecture.md
  v
STEP 2: IMPLEMENT (sandbox-first)
  |  Apply fix in a test_*.py sandbox script first
  |  Run sandbox, capture output, compare before/after
  |  Only apply to production if results are BETTER
  v
STEP 3: VERIFY
  |  Run the script. Capture output. Compare to expectations.
  |  Log results in: .ai-memory/datasets.md (Test Results Log)
  v
STEP 4: LEARN & DOCUMENT
     Update: bugs.md, lessons.md, architecture.md, datasets.md
     Extract at least one lesson per session.
```

If you skip Step 4, the next session starts blind.
If you skip Step 1, you risk breaking something.

---

## 2. Sandbox-First Rule

**Never apply a fix directly to production scripts. Always validate in a sandbox first.**

### Production Scripts (do NOT edit until fix is validated)

| Script | Purpose |
|---|---|
| `recognize_raga_v12.py` | Inference engine |
| `aggregate_all_v12.py` | Build raga models |
| `extract_pitch_batch_v12.py` | Feature extraction |
| `batch_evaluate.py` | Evaluate on seed dataset |
| `batch_evaluate_random.py` | Evaluate on unknown audio |
| `utils.py` | Shared utilities |

### Sandbox Scripts (safe to experiment in)

| Script | Tests What |
|---|---|
| `test_recognize_fix.py` | Dyad fix validation |
| `test_bug004_genericness.py` | Genericness penalty experiments |
| `test_bug004_no_genericness.py` | Genericness removal test |
| `test_dyad_weights.py` | Weight tuning experiments |
| Any new `test_*.py` file | New fix experiments |

### The Sandbox Workflow

```
A. CREATE or UPDATE a test script with the proposed fix
B. RUN the test script, capture output
C. COMPARE results: before-fix vs after-fix
   - Trained ragas still correct?     (no regressions)
   - Untrained ragas still rejected?  (no false positives)
   - Margins improved?                (score separation)
   - Any new failures?                (side effects)
D. DECIDE:
   BETTER  → Apply to production
   SAME    → Do not apply (unnecessary)
   WORSE   → Reject, document why in lessons.md
   MIXED   → Analyze trade-offs, document in bugs.md
E. APPLY to production (only if BETTER)
F. Run batch_evaluate.py for full validation
G. DOCUMENT in bugs.md + lessons.md + datasets.md
```

---

## 3. Audio Requirements

All training audio must be **vocal-only**. Instrument contamination (violin, mridangam) degrades pitch extraction.

### How to Prepare Audio

1. **Check for multitrack stems first** — Saraga dataset includes vocal-only stems for ~168 recordings (free, lossless separation)
2. **Use Demucs for mix recordings** — `demucs --two-stems vocals` separates vocals from instruments
3. **Carnatic Varnam recordings** are already clean (solo vocal + drone)
4. **Duration cap**: Processing is capped at 6 minutes. A raga establishes identity in 3-5 minutes.

### Audio Source Quality

| Source | Quality | Action |
|---|---|---|
| `*_clean_*.wav` (original seed) | Clean vocal | Ready to use |
| `223*gopalkoduri*` (Carnatic Varnam) | Solo vocal + drone | Ready to use |
| `*.vocal.mp3` (Saraga stem) | Multitrack vocal | Ready to use |
| `*.vocal.mp3` (Demucs output) | AI-separated vocal | Check for artifacts |
| Concert recording (mix) | Vocal + instruments | Must isolate first |

---

## 4. Pipeline Execution Order

```bash
# Step 1: Extract features from audio
python extract_pitch_batch_v12.py

# Step 2: Aggregate raga models
python aggregate_all_v12.py

# Step 3a: Evaluate on training data
python batch_evaluate.py

# Step 3b: Evaluate on unknown audio
python batch_evaluate_random.py
```

> Update `AGG_FOLDER` in batch scripts to point to the latest aggregation run folder.

---

## 5. Project Memory System

All project state lives in `.ai-memory/`. These files are the project's living documentation.

| File | Purpose | When to Update |
|---|---|---|
| `bugs.md` | Track every bug — active and resolved | New bug found or bug fixed |
| `lessons.md` | Reusable rules from debugging | Every session (at least one) |
| `architecture.md` | Current system state | Scripts or constants changed |
| `datasets.md` | Dataset info + test results log | Tests run or audio added |
| `debug-playbook.md` | Debugging priority order | New failure pattern found |
| `workflow.md` | Development process rules | Process itself changes |
| `Swarag_Project_Dossier_v1_2.txt` | High-level project summary | Major milestones |

### Bug Format
```
### BUG-NNN: Title
- **Status**: OPEN / FIXED / RESOLVED / PARTIALLY FIXED
- **Found**: date
- **File**: affected script
- **Description**: what happens
- **Impact**: what breaks
- **Root Cause**: why it happens
- **Fix**: what to change
```

### Lesson Format
```
### L-NNN: Title
- **Date**: date
- **Context**: what we were doing
- **Rule**: the reusable principle
- **Impact**: what goes wrong if forgotten
```

---

## 6. Fix Priority Order

When multiple bugs exist, fix in this order:

| Priority | Category | Example |
|---|---|---|
| 1 | BLOCKING | Code crashes, missing constants |
| 2 | DATA INTEGRITY | Mismatched constants, wrong features |
| 3 | SCORING & THRESHOLDS | Weight tuning, margin calibration |
| 4 | ARCHITECTURAL | OOD detection, new feature types |
| 5 | DATASET | Adding ragas, more training clips |

Never skip a higher priority to work on a lower one.

---

## 7. Adding a New Raga

1. **Collect audio** — minimum 15 vocal-only clips recommended
   - Check Saraga dataset first (multitrack vocal stems)
   - Use Demucs for mix-only recordings
   - Carnatic Varnam dataset has clean solo vocals
2. **Create folder** — `datasets/seed_carnatic/{RagaName}/`
3. **Run extraction** — `python extract_pitch_batch_v12.py`
4. **Re-aggregate** — `python aggregate_all_v12.py`
5. **Evaluate** — `python batch_evaluate.py` + `python batch_evaluate_random.py`
6. **Document** — Update `datasets.md` and `architecture.md`

---

## 8. Shared Constants

These must be identical across `aggregate_all_v12.py`, `recognize_raga_v12.py`, and all test scripts:

| Constant | Value | Purpose |
|---|---|---|
| `N_BINS` | 36 | PCD histogram bins |
| `MIN_STABLE_FRAMES` | 5 | Stable region detection |
| `ALPHA` | 0.5 | Laplace smoothing |
| `EPS` | 1e-8 | Numerical stability |
| `MAX_DURATION_SEC` | 360 | Audio duration cap (6 min) |

Changing any of these requires re-extraction and re-aggregation of all features.

---

## 9. AI Agent Development

This project uses AI-assisted development. The AI agent specification is in `.ai/agent_spec.md`.

Key rules for AI agents:
- **Read all `.ai-memory/` files** at the start of every session
- **Update all `.ai-memory/` files** at the end of every session
- **Follow the sandbox-first rule** — never edit production scripts directly
- **Follow the development loop** — Plan → Implement → Verify → Document

---

## 10. The One Rule Above All

> If something seems wrong, it probably is.
> If a fix feels hacky, there's a better solution.
> If all results say UNKNOWN, the bug is in the code, not the audio.
> If you're not sure, check the memory files first.
