# Swarag — Lessons Learned

## Lesson Log

### L-001: Silent Exception Swallowing Hides Critical Bugs
- **Date**: 2025-02-15
- **Context**: `recognize_raga_v12.py` wraps the entire recognition in
  `except Exception` and returns UNKNOWN. When `MIN_STABLE_FRAMES` was
  missing, every call crashed with `NameError` — but the error was never
  visible. Every file silently returned UNKNOWN.
- **Rule**: Never use bare `except Exception` without at minimum logging
  the traceback. If a function silently degrades, add at least
  `print(f"ERROR: {e}")` or `traceback.print_exc()` so failures are visible.
- **Impact**: This bug could have gone undetected for weeks.

### L-002: Constants Must Be Synchronized Across Pipeline Scripts
- **Date**: 2025-02-15
- **Context**: `aggregate_all_v12.py` defines `MIN_STABLE_FRAMES=5`,
  `ALPHA=0.5`, `EPS=1e-8`. These same constants must appear in
  `recognize_raga_v12.py` because inference must match training exactly.
- **Rule**: Any constant used in both aggregation and recognition must
  be defined in both scripts with identical values. Consider extracting
  shared constants into a `config.py` module in the future.
- **Impact**: Mismatch between training and inference features produces
  garbage similarity scores.

### L-003: Test Scripts Should Use Production Thresholds
- **Date**: 2025-02-15
- **Context**: `test_recognize_fix.py` uses relaxed thresholds
  (MARGIN_STRICT=0.003, MIN_MARGIN_FINAL=0.0005) while production uses
  (MARGIN_STRICT=0.05, MIN_MARGIN_FINAL=0.01). This makes test results
  misleading — files that pass the test would fail in production.
- **Rule**: Test scripts should either (a) use production thresholds, or
  (b) clearly report raw margins and let the human judge. Avoid different
  thresholds that give false confidence.

### L-004: Shankarabharanam Is the Default Attractor
- **Date**: 2025-02-15
- **Context**: Any raga not in the training set gets classified as
  Shankarabharanam because its PCD is the most "generic" (major-scale-like).
  This is the "Shankarabharanam sink" problem.
- **Rule**: With only 3 trained ragas, the system cannot reject unknown
  ragas reliably. Margin thresholds alone are insufficient — an absolute
  score floor or OOD detection mechanism is needed.
- **Impact**: High false positive rate on out-of-distribution audio.

### L-005: Score Compression Makes Margins Unreliable
- **Date**: 2025-02-15
- **Context**: All scores from `test_recognize_fix.py` are negative
  (range -0.114 to -0.143). The genericness penalty dominates, pushing
  all scores below zero and compressing the effective margin range.
  A margin of 0.005 looks "large" in percentage terms but is actually
  tiny in absolute score space.
- **Rule**: When tuning margin thresholds, always inspect the actual
  score range first. If scores span only 0.03 total, a margin threshold
  of 0.05 will reject everything.

### L-006: Dyad Fix Is Necessary But Not Sufficient
- **Date**: 2025-02-15
- **Context**: Adding stable-region detection + Laplace smoothing to
  inference dyads (matching aggregation) correctly identifies Bhairavi.
  But it does not solve Shankarabharanam sink or Kalyani compression.
- **Rule**: The dyad fix is a prerequisite for correct operation but
  additional work is needed: OOD detection, genericness tuning, and
  potentially phrase-level features for sibling raga separation.

### L-007: Always Activate Virtual Environment Before Running Scripts
- **Date**: 2025-02-15
- **Context**: Running `python test_recognize_fix.py` without activating
  `my_virtual_env_swarag` fails with `ModuleNotFoundError: numpy`.
- **Rule**: Always activate the venv first:
  ```powershell
  Set-Location D:\Swaragam\scripts
  .\my_virtual_env_swarag\Scripts\Activate.ps1
  python <script>.py
  ```
  Or use the full path: `.\my_virtual_env_swarag\Scripts\python.exe <script>.py`

### L-008: PowerShell Does Not Support && Operator
- **Date**: 2025-02-15
- **Context**: `cd scripts && python test.py` fails in PowerShell.
- **Rule**: Use semicolon (`;`) as statement separator in PowerShell,
  or use `Set-Location` instead of `cd`.

### L-009: Adding More Ragas Reduces OOD Problem But Does Not Eliminate It
- **Date**: 2025-02-15
- **Context**: Asked whether adding more ragas to training would fix
  BUG-002 (Shankarabharanam sink). Analysis showed that more ragas
  reduce the "unknown space" (fewer inputs are truly OOD), but there
  will ALWAYS be audio that doesn't belong to any trained raga.
- **Rule**: Adding data is a PRIORITY 5 fix. It reduces the problem
  but does not eliminate it. An absolute score floor (OOD detector)
  is needed regardless of how many ragas are trained. Always fix code
  before adding data. See workflow.md Section 4 (Decision Tree).
- **Impact**: Without this understanding, one could spend weeks
  collecting data when a 5-line code fix would solve the root cause.

### L-010: Fix Priority Order Prevents Wasted Effort
- **Date**: 2025-02-15
- **Context**: With 3 active bugs (missing constants, OOD sink, score
  compression), it was tempting to jump to the most interesting problem.
  But fixing BUG-002 or BUG-003 is pointless if BUG-001 (missing
  constants) means the production script silently crashes on every call.
- **Rule**: Always follow the fix priority order:
  1. BLOCKING (crashes, silent failures)
  2. DATA INTEGRITY (feature mismatches)
  3. SCORING (weight tuning)
  4. ARCHITECTURAL (OOD detection)
  5. DATASET (adding ragas)
  Never skip a higher priority to work on a lower one.
- **Impact**: Without this discipline, you fix the roof while the
  foundation is cracked.

### L-011: Sandbox-First Prevents Production Breakage
- **Date**: 2025-02-16
- **Context**: Architectural audit of recognize_raga_v12.py revealed
  7 findings, some requiring significant changes. Applying them directly
  to production could introduce regressions. The existing test_recognize_fix.py
  already proved this pattern: it validated the dyad fix safely before
  production was touched.
- **Rule**: Never edit production scripts directly. Always:
  1. Apply the fix in a test_*.py sandbox script
  2. Run it against test audio
  3. Compare before vs after
  4. Only apply to production if results are BETTER
  See agent_spec.md RULE 6 and workflow.md Section 5.
- **Impact**: One bad edit to recognize_raga_v12.py could silently
  break all recognition (as BUG-001 demonstrated).

### L-012: A Penalty That Doesn't Change Ranking Is Useless
- **Date**: 2025-02-16
- **Context**: Architectural audit found that `compute_genericness(pcd)`
  is computed from the test PCD only, producing the same value for every
  raga. Subtracting the same constant from all scores does not change
  ranking or margin — it only shifts absolute values.
- **Rule**: Any scoring component that does not vary across candidates
  is mathematically inert for ranking. Before adding a penalty or bonus,
  ask: "Does this value differ between raga A and raga B?" If not, it
  cannot help differentiate them.
- **Impact**: The genericness penalty was believed to help suppress
  Shankarabharanam. In reality it compresses all scores equally and
  contributes to BUG-003 and BUG-006.

### L-013: Document Architecture Says JSD, Code Uses Dot-Product
- **Date**: 2025-02-16
- **Context**: `docs/ARCHITECTURE.md` says scoring uses Jensen-Shannon
  divergence. `recognize_raga_v12.py` actually uses `np.dot()` (dot-product
  similarity). These are fundamentally different metrics.
- **Rule**: When refactoring scoring, always check what the documentation
  says and update EITHER the docs or the code to match. Never let them
  drift apart.
- **Impact**: A new contributor reading the docs would expect JSD-based
  scoring and be confused by the actual implementation.

### L-014: Multi-Agent Is an On-Demand Expert, Not a Routine Step
- **Date**: 2025-02-16
- **Context**: Initially integrated the 5-agent analysis as a mandatory
  Step 2 in every development loop. The founder correctly pointed out
  this wastes resources, time and tokens on simple tasks. The multi-agent
  should only be called for genuinely complex cross-domain problems.
- **Rule**: The multi-agent team is a SPECIALIST TOOL. Keep it on-demand.
  The AI should SUGGEST it when stuck ("Want me to run /analyze-swarag?"),
  but never run it automatically. Simple fixes don't need 5 experts.
- **Impact**: Without this restraint, every missing-constant fix would
  burn tokens on 5 expert analyses that add zero value.

### L-015: No Shortcutting Sandbox-First, Even for Obvious Fixes
- **Date**: 2025-02-16
- **Context**: BUG-001 (missing constants) was applied directly to
  production because the sandbox had validated it in a prior session.
  But the proper flow is: local sandbox fix -> run -> compare -> THEN
  push to production. Skipping steps erodes discipline.
- **Rule**: Always follow the full sandbox flow. Even if the fix is
  "just 3 constants," run the sandbox, capture output, confirm results
  match expectations, THEN apply to production. No shortcuts.
- **Impact**: The one time you skip, that's the time it breaks.

### L-016: Genericness From Model PCD Makes Things Worse
- **Date**: 2025-02-16
- **Context**: BUG-004 fix attempt — moved genericness computation from
  test PCD to model PCD. Expected Shankarabharanam to get penalized most.
  Instead, Shankarabharanam had the LOWEST entropy (3.248), meaning it
  got the SMALLEST penalty. Result: Shankarabharanam became even more
  dominant. Kalyani ranking flipped from #1 to #2. Bhairavi margin shrunk.
- **Rule**: Before implementing a penalty fix, inspect the actual data
  first. The assumption "Shankarabharanam has the most generic PCD" was
  wrong — its trained PCD is actually the most concentrated. Model
  entropy values are too close (3.25-3.29) to differentiate meaningfully.
- **Impact**: Without sandbox testing, this fix would have silently
  made production results worse. Sandbox-first workflow saved us.

### L-017: Escalation (Dyad-Heavy) Hurts When Training Data Is Thin
- **Date**: 2025-02-16
- **Context**: test_dyad_weights.py showed that escalation (0.3/0.7)
  crushes Kalyani's margin from 0.001131 to 0.000227 — a 5x degradation.
  Dyad-only (0.0/1.0) flipped the ranking entirely (Shankarabharanam #1).
  With only 6 clips per raga, dyad matrices are too noisy to carry
  more weight than PCD.
- **Rule**: Don't increase dyad weight until training data is sufficient
  (15-20 clips minimum). The dyads need stable averages to be
  discriminative. With thin data, PCD is the more reliable signal.
- **Impact**: The escalation path actively harms Kalyani recognition.
  Logged as BUG-007.

### L-018: Baseline Weights (0.6/0.4) Are Best With Current Data
- **Date**: 2025-02-16
- **Context**: test_dyad_weights.py tested 3 weight configs:
  Baseline (0.6/0.4), Dyad-heavy (0.3/0.7), Dyad-only (0.0/1.0).
  Baseline gave the best margins for BOTH trained ragas simultaneously.
  Bhairavi: 0.005664 (baseline) vs 0.002954 (dyad-heavy) vs 0.000245 (dyad-only).
  Kalyani: 0.001131 (baseline) vs 0.000227 (dyad-heavy) vs WRONG (dyad-only).
- **Rule**: Don't tune weights until the underlying models are solid.
  Weight tuning on noisy models produces unreliable conclusions.
  Get data right first, then re-evaluate weights.

### L-019: Get Data Before Tuning Code
- **Date**: 2025-02-16
- **Context**: Multiple code fixes attempted (genericness from model PCD,
  genericness removal, dyad weight tuning) — none improved accuracy
  beyond the baseline. All 3 ragas have only 6-10 training clips.
  The MIR Researcher pointed out 6 clips is too thin for stable models.
- **Rule**: When accuracy is stuck and training data is thin, adding
  more data is more likely to help than code changes. Code tuning on
  noisy models is like adjusting a camera lens when the film is blurry.
  Priority: data first, code second.
- **Impact**: Prevents wasting cycles on code fixes that can't improve
  results until the foundation (training data) is solid.

### L-020: Instrument Contamination Affects Pitch Extraction
- **Date**: 2025-03-09
- **Context**: Saraga concert recordings contain violin, mridangam, and
  tambura alongside vocals. pYIN picks up violin pitches (same raga but
  different timbre/octave), adding noise to PCD and dyad matrices.
  168 Saraga tracks have multitrack stems; we extracted vocal-only for 8.
  Remaining 16 were processed with Demucs htdemucs for vocal isolation.
- **Rule**: Always use vocal-only audio for pitch-based raga recognition.
  Check for multitrack stems first (free, lossless). Use Demucs for
  mix-only recordings. Never feed full concert audio to pYIN.
- **Impact**: Cleaner features, OOD false positives eliminated.

### L-021: Duration Cap Has No Accuracy Cost But Massive Speed Gain
- **Date**: 2025-03-09
- **Context**: Old recognize_raga.py had MAX_DURATION_SEC=360 (6 min cap).
  v1.2 dropped it. Some Saraga recordings are 40-65 minutes long.
  Processing 13.2 hours of audio took hours. With the 6-min cap restored,
  extraction ran in minutes. A raga establishes identity in 3-5 minutes.
- **Rule**: Always cap audio duration at 6 minutes for both feature
  extraction and recognition. The PCD stabilizes within minutes.
  Beyond that is diminishing returns.
- **Impact**: 10x speedup with no accuracy loss.

### L-022: Adding Ragas Fixes OOD Better Than Code Changes
- **Date**: 2025-03-09
- **Context**: Expanding from 3 to 6 ragas eliminated the Shankarabharanam
  sink for OOD test files. Hamsadwani and Mohanam now return UNKNOWN
  instead of being misclassified. Multiple code fixes (genericness tuning,
  weight changes) failed to fix this. Adding ragas succeeded.
- **Rule**: When the model has too few ragas, OOD rejection is impossible
  because there are not enough candidates to create meaningful margins.
  Adding ragas crowds out the generic attractor. Data beats code.