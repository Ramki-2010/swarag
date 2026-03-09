# Swarag -- Development Workflow & Process Rules

This document defines HOW work gets done on Swarag.
Every AI agent and every human contributor must follow these rules.

---

## 1. The Development Loop

Every change follows 4 mandatory steps. No exceptions.

```
STEP 1: PLAN
  |  What are we changing? Why? What could break?
  |  Read: bugs.md, architecture.md
  v
STEP 2: IMPLEMENT (sandbox-first)
  |  Apply fix in a test_*.py sandbox script first (Rule 6)
  |  Run sandbox, capture output, compare before/after
  |  Only apply to production if results are BETTER
  v
STEP 3: VERIFY
  |  Run the script. Capture output. Compare to expectations.
  |  Log results in: datasets.md (Test Results Log)
  v
STEP 4: LEARN & DOCUMENT
     Update: bugs.md, lessons.md, architecture.md, datasets.md
     Extract at least one lesson per session.
```

If you skip Step 4, the next session starts blind.
If you skip Step 1, you risk breaking something.

NOTE: For complex or stuck problems, the multi-agent analysis
team is available ON DEMAND via /analyze-swarag.
See Section 12 below. Do NOT run it on every change.

---

## 2. Session Protocol

### Starting a Session

```
1. Read .ai-memory/bugs.md       -- What's broken?
2. Read .ai-memory/lessons.md    -- What do we know?
3. Read .ai-memory/architecture.md -- What's the current state?
4. Read .ai-memory/datasets.md   -- What were the last test results?
5. Read .ai-memory/debug-playbook.md -- How do we debug?
6. Read .ai-memory/workflow.md   -- How do we work? (this file)
7. Ask the user what they want to work on today.
```

### Ending a Session

```
1. Summarize what was done.
2. Update bugs.md:
   - New bugs found?         -> Add with BUG-NNN format
   - Existing bugs fixed?    -> Move to Resolved section with date
   - Bug status changed?     -> Update status
3. Update lessons.md:
   - What did we learn?      -> Add with L-NNN format
   - At least ONE lesson per session
4. Update datasets.md:
   - Any tests run?          -> Log in Test Results section
   - New audio added?        -> Document location
5. Update architecture.md:
   - Any scripts changed?    -> Update script table
   - Any constants changed?  -> Update constants table
   - Any new features added? -> Update pipeline diagram
6. List what should be done next.
```

---

## 3. Fix Priority Rules

When multiple problems exist, always fix in this order:

```
PRIORITY 1: BLOCKING
  Code crashes. Silent failures. Missing constants.
  Nothing else matters until these are fixed.
  Example: BUG-001 (missing MIN_STABLE_FRAMES)

PRIORITY 2: DATA INTEGRITY
  Wrong features. Mismatched constants between scripts.
  Train/inference mismatch.
  Example: Constants not synced between aggregate and recognize

PRIORITY 3: SCORING & THRESHOLDS
  Weight tuning. Margin calibration. Genericness penalty.
  Only tune when the pipeline runs correctly.
  Example: BUG-003 (score compression)

PRIORITY 4: ARCHITECTURAL
  OOD detection. New feature types. Pipeline additions.
  Design first, implement second.
  Example: BUG-002 (Shankarabharanam sink)

PRIORITY 5: DATASET
  Adding ragas. More training clips. External data integration.
  Important but slow. Do after code is stable.
```

---

## 4. Decision Tree: "Will Adding More Data Fix This?"

Before adding data, ask these questions:

```
Is the code crashing?
  YES -> Fix the code first (Priority 1-2)
  NO  -> Continue

Is the pipeline producing correct features?
  NO  -> Fix feature computation (Priority 2)
  YES -> Continue

Are trained ragas being correctly identified?
  NO  -> Fix scoring/thresholds (Priority 3)
  YES -> Continue

Are untrained ragas being falsely classified?
  YES -> Is there an OOD mechanism?
         NO  -> Add score floor / OOD detector (Priority 4)
         YES -> Adding more ragas WILL help (Priority 5)
  NO  -> System is working. Add ragas for coverage (Priority 5)
```

KEY INSIGHT: Adding more ragas REDUCES the OOD problem but
does NOT ELIMINATE it. You always need an absolute score floor.

---

## 5. Sandbox-First Rule (TEST BEFORE PRODUCTION)

Never apply a fix directly to production scripts.
Always validate in a local test script first.

```
PRODUCTION SCRIPTS (do NOT edit until fix is validated):
  - recognize_raga_v12.py
  - aggregate_all_v12.py
  - extract_pitch_batch_v12.py
  - batch_evaluate.py
  - batch_evaluate_random.py
  - utils.py

SANDBOX SCRIPTS (safe to experiment in):
  - test_recognize_fix.py        (current sandbox)
  - Any new test_*.py script
```

### The Sandbox Workflow

```
STEP A: CREATE OR UPDATE a test script
  |  Copy the relevant function/logic from production
  |  Apply the proposed fix in the test script only
  v
STEP B: RUN the test script
  |  Capture full console output
  |  Check: did the fix improve results?
  v
STEP C: COMPARE results
  |  Before-fix vs after-fix — side by side
  |  Check all 4 outcomes:
  |    - Trained ragas still correct?     (no regressions)
  |    - Untrained ragas still rejected?  (no false positives)
  |    - Margins improved?                (score separation)
  |    - Any new failures?                (side effects)
  v
STEP D: DECIDE
  |  Results BETTER  → Apply fix to production script
  |  Results SAME    → Fix is unnecessary, do not apply
  |  Results WORSE   → Reject fix, document why in lessons.md
  |  Results MIXED   → Analyze trade-offs, document in bugs.md
  v
STEP E: APPLY to production (only if Step D = BETTER)
  |  Edit the production script
  |  Run batch_evaluate.py for full validation
  |  Log results in datasets.md
  v
STEP F: DOCUMENT
     Update bugs.md (resolved), lessons.md (what we learned)
```

### Why This Matters

- Production scripts are the STABLE FOUNDATION
- One bad edit can silently break everything (see L-001)
- Test scripts are disposable — production scripts are not
- Comparing before/after in a sandbox catches regressions
- This is how we caught BUG-001: test_recognize_fix.py worked
  but recognize_raga_v12.py was silently crashing

### Current Sandbox Files

| Sandbox Script | Tests What |
|---|---|
| `test_recognize_fix.py` | Dyad fix (stable regions + Laplace + missing constants) |
| (create as needed) | New fixes get their own test script |

---

## 6. Evaluation Protocol

### Before Evaluation
1. Confirm BUG-001 is fixed (missing constants)
2. Confirm virtual environment works
3. Note the AGG_FOLDER path being used

### Running Evaluation
```powershell
Set-Location D:\Swaragam\scripts
.\my_virtual_env_swarag\Scripts\Activate.ps1

# Seed dataset (known ragas):
python batch_evaluate.py

# Unknown audio:
python batch_evaluate_random.py

# Quick validation (4 test files):
python test_recognize_fix.py
```

### After Evaluation
1. Copy the full console output
2. Log results in .ai-memory/datasets.md under Test Results Log
3. Compare against previous runs
4. Identify: improvements, regressions, new bugs

---

## 7. Bug Lifecycle

```
DISCOVERED -> OPEN -> IN PROGRESS -> FIXED -> VERIFIED -> RESOLVED
                |                              |
                +-- WONT FIX (with reason) ----+
```

Each bug entry must have:
- BUG-NNN identifier (never reuse numbers)
- Status
- Found date
- File affected
- Description (what happens)
- Impact (what breaks)
- Root cause (why it happens)
- Evidence (test output, scores, margins)
- Fix (what to change)
- Validated by (how to verify the fix)

When resolved, add:
- Resolution date
- Verification method
- Which test confirmed it

---

## 8. Lesson Lifecycle

Each lesson must have:
- L-NNN identifier (never reuse numbers)
- Date
- Context (what were we doing when we learned this?)
- Rule (the reusable principle)
- Impact (what would go wrong if we forget this?)

Good lessons are ACTIONABLE:
  BAD:  "Shankarabharanam is a problem"
  GOOD: "With only 3 trained ragas, untrained audio gets absorbed
         by the most generic PCD. Need OOD score floor."

---

## 9. Documentation Checklist

Use this checklist at the end of every session:

```
[ ] bugs.md      -- Any new bugs? Any bugs resolved?
[ ] lessons.md   -- At least one new lesson captured?
[ ] datasets.md  -- Any test results to log?
[ ] architecture.md -- Any scripts or constants changed?
[ ] workflow.md  -- Any process improvements?
[ ] agent_spec.md -- Any new rules needed?
[ ] Dossier      -- Update current state / next steps if milestone reached
```

---

## 10. File Naming & Versioning

- Core scripts use `_v12` suffix for current version
- Deprecated scripts go to `scripts/archive/`
- Aggregation runs are timestamped: `run_YYYYMMDD_HHMMSS`
- Evaluation runs are timestamped: `run_YYYYMMDD_HHMMSS`
- Never overwrite previous runs (non-destructive)
- Memory files are living documents (always update, never recreate)

---

## 11. The One Rule Above All

> If something seems wrong, it probably is.
> If a fix feels hacky, there's a better solution.
> If all results say UNKNOWN, the bug is in the code, not the audio.
> If you're not sure, check the memory files first.

---

## 12. Multi-Agent Analysis (ON DEMAND ONLY)

The 5-agent engineering team is a SPECIALIST TOOL, not a routine step.
It exists to crack hard problems. Do NOT activate it for simple tasks.

### When the AI Should SUGGEST It

The AI should say "this might be a good time for /analyze-swarag" when:

  - A bug has persisted across 2+ sessions without resolution
  - A fix made one thing better but broke something else
  - The root cause is unclear after normal debugging
  - A scoring or architectural change has non-obvious trade-offs
  - The user asks "why is X happening?" and the answer isn't simple

### When the User Should Call It

  - Type /analyze-swarag in Continue for full 5-expert analysis
  - Type /debug-swarag for structured 8-step debugging
  - Type /capture-lesson to extract and save a lesson

### When NOT to Use It

  - Adding a missing constant (just do it)
  - Fixing a typo or path (just do it)
  - Updating documentation (just do it)
  - Any task where the fix is already clear

### The 5 Experts

  1. Audio DSP Engineer   -- signal processing, pitch, tonic
  2. MIR Researcher       -- music theory, raga grammar, features
  3. ML Engineer           -- scoring, metrics, calibration, margins
  4. Software Architect   -- contracts, dependencies, drift
  5. Debug Investigator   -- paths, loading, shapes, silent errors

Full expert definitions are in agent_spec.md Rule 13.
