# Swarag — Lessons Learned

## Lesson Log

### L-001: Silent Exception Swallowing Hides Critical Bugs
- **Date**: 2026-02-15
- **Context**: `recognize_raga_v12.py` wraps the entire recognition in
  `except Exception` and returns UNKNOWN. When `MIN_STABLE_FRAMES` was
  missing, every call crashed with `NameError` — but the error was never
  visible. Every file silently returned UNKNOWN.
- **Rule**: Never use bare `except Exception` without at minimum logging
  the traceback. If a function silently degrades, add at least
  `print(f"ERROR: {e}")` or `traceback.print_exc()` so failures are visible.
- **Impact**: This bug could have gone undetected for weeks.

### L-002: Constants Must Be Synchronized Across Pipeline Scripts
- **Date**: 2026-02-15
- **Context**: `aggregate_all_v12.py` defines `MIN_STABLE_FRAMES=5`,
  `ALPHA=0.5`, `EPS=1e-8`. These same constants must appear in
  `recognize_raga_v12.py` because inference must match training exactly.
- **Rule**: Any constant used in both aggregation and recognition must
  be defined in both scripts with identical values. Consider extracting
  shared constants into a `config.py` module in the future.
- **Impact**: Mismatch between training and inference features produces
  garbage similarity scores.

### L-003: Test Scripts Should Use Production Thresholds
- **Date**: 2026-02-15
- **Context**: `test_recognize_fix.py` uses relaxed thresholds
  (MARGIN_STRICT=0.003, MIN_MARGIN_FINAL=0.0005) while production uses
  (MARGIN_STRICT=0.05, MIN_MARGIN_FINAL=0.01). This makes test results
  misleading — files that pass the test would fail in production.
- **Rule**: Test scripts should either (a) use production thresholds, or
  (b) clearly report raw margins and let the human judge. Avoid different
  thresholds that give false confidence.

### L-004: Shankarabharanam Is the Default Attractor
- **Date**: 2026-02-15
- **Context**: Any raga not in the training set gets classified as
  Shankarabharanam because its PCD is the most "generic" (major-scale-like).
  This is the "Shankarabharanam sink" problem.
- **Rule**: With only 3 trained ragas, the system cannot reject unknown
  ragas reliably. Margin thresholds alone are insufficient — an absolute
  score floor or OOD detection mechanism is needed.
- **Impact**: High false positive rate on out-of-distribution audio.

### L-005: Score Compression Makes Margins Unreliable
- **Date**: 2026-02-15
- **Context**: All scores from `test_recognize_fix.py` are negative
  (range -0.114 to -0.143). The genericness penalty dominates, pushing
  all scores below zero and compressing the effective margin range.
  A margin of 0.005 looks "large" in percentage terms but is actually
  tiny in absolute score space.
- **Rule**: When tuning margin thresholds, always inspect the actual
  score range first. If scores span only 0.03 total, a margin threshold
  of 0.05 will reject everything.

### L-006: Dyad Fix Is Necessary But Not Sufficient
- **Date**: 2026-02-15
- **Context**: Adding stable-region detection + Laplace smoothing to
  inference dyads (matching aggregation) correctly identifies Bhairavi.
  But it does not solve Shankarabharanam sink or Kalyani compression.
- **Rule**: The dyad fix is a prerequisite for correct operation but
  additional work is needed: OOD detection, genericness tuning, and
  potentially phrase-level features for sibling raga separation.

### L-007: Always Activate Virtual Environment Before Running Scripts
- **Date**: 2026-02-15
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
- **Date**: 2026-02-15
- **Context**: `cd scripts && python test.py` fails in PowerShell.
- **Rule**: Use semicolon (`;`) as statement separator in PowerShell,
  or use `Set-Location` instead of `cd`.

### L-009: Adding More Ragas Reduces OOD Problem But Does Not Eliminate It
- **Date**: 2026-02-15
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
- **Date**: 2026-02-15
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
- **Date**: 2026-02-16
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
- **Date**: 2026-02-16
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
- **Date**: 2026-02-16
- **Context**: `docs/ARCHITECTURE.md` says scoring uses Jensen-Shannon
  divergence. `recognize_raga_v12.py` actually uses `np.dot()` (dot-product
  similarity). These are fundamentally different metrics.
- **Rule**: When refactoring scoring, always check what the documentation
  says and update EITHER the docs or the code to match. Never let them
  drift apart.
- **Impact**: A new contributor reading the docs would expect JSD-based
  scoring and be confused by the actual implementation.

### L-014: Multi-Agent Is an On-Demand Expert, Not a Routine Step
- **Date**: 2026-02-16
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
- **Date**: 2026-02-16
- **Context**: BUG-001 (missing constants) was applied directly to
  production because the sandbox had validated it in a prior session.
  But the proper flow is: local sandbox fix -> run -> compare -> THEN
  push to production. Skipping steps erodes discipline.
- **Rule**: Always follow the full sandbox flow. Even if the fix is
  "just 3 constants," run the sandbox, capture output, confirm results
  match expectations, THEN apply to production. No shortcuts.
- **Impact**: The one time you skip, that's the time it breaks.

### L-016: Genericness From Model PCD Makes Things Worse
- **Date**: 2026-02-16
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
- **Date**: 2026-02-16
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
- **Date**: 2026-02-16
- **Context**: test_dyad_weights.py tested 3 weight configs:
  Baseline (0.6/0.4), Dyad-heavy (0.3/0.7), Dyad-only (0.0/1.0).
  Baseline gave the best margins for BOTH trained ragas simultaneously.
  Bhairavi: 0.005664 (baseline) vs 0.002954 (dyad-heavy) vs 0.000245 (dyad-only).
  Kalyani: 0.001131 (baseline) vs 0.000227 (dyad-heavy) vs WRONG (dyad-only).
- **Rule**: Don't tune weights until the underlying models are solid.
  Weight tuning on noisy models produces unreliable conclusions.
  Get data right first, then re-evaluate weights.

### L-019: Get Data Before Tuning Code
- **Date**: 2026-02-16
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
- **Date**: 2026-03-09
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
- **Date**: 2026-03-09
- **Context**: Old recognize_raga.py had MAX_DURATION_SEC=360 (6 min cap).
  v1.2 dropped it. Some Saraga recordings are 40-65 minutes long.
  Processing 13.2 hours of audio took hours. With the 6-min cap restored,
  extraction ran in minutes. A raga establishes identity in 3-5 minutes.
- **Rule**: Always cap audio duration at 6 minutes for both feature
  extraction and recognition. The PCD stabilizes within minutes.
  Beyond that is diminishing returns.
- **Impact**: 10x speedup with no accuracy loss.

### L-022: Adding Ragas Fixes OOD Better Than Code Changes
- **Date**: 2026-03-09
- **Context**: Expanding from 3 to 6 ragas eliminated the Shankarabharanam
  sink for OOD test files. Hamsadwani and Mohanam now return UNKNOWN
  instead of being misclassified. Multiple code fixes (genericness tuning,
  weight changes) failed to fix this. Adding ragas succeeded.
- **Rule**: When the model has too few ragas, OOD rejection is impossible
  because there are not enough candidates to create meaningful margins.
  Adding ragas crowds out the generic attractor. Data beats code.

### L-023: Laplace Smoothing ALPHA Must Scale With Matrix Size
- **Date**: 2026-03-10
- **Context**: Dyad matrices (36x36 = 1296 cells) had ALPHA=0.5.
  Total Laplace mass = 1296 * 0.5 = 648. Typical file has ~370 transitions.
  Signal ratio: 370/1018 = 36%. Noise dominated 64% of the matrix.
  Dyad similarities were ~0.001 for ALL ragas — essentially random.
  Chordia & Rae (2007) used 12x12 matrices (144 cells). With 144 cells,
  ALPHA=0.5 would add only 72 total — much more reasonable.
- **Rule**: ALPHA must be proportional to 1/(matrix_size). For 1296 cells,
  ALPHA=0.01 gives signal ratio 97% and discrimination ratio 5.88x.
  General formula: ALPHA < (mean_transitions / matrix_cells) * 0.1.
- **Impact**: ALPHA=0.01 improved dyad discrimination from 1.24x to 1.73x,
  and overall accuracy from 61% to 64%.

### L-024: Outlier Clips Can Skew Entire Raga Models
- **Date**: 2026-03-10
- **Context**: Munnu Ravana (Thodi) had entropy 2.4 (vs 2.9-3.2 for others)
  and self-similarity 0.2022 (2x higher than any other clip). It was pulling
  the Thodi mean model toward its Sa-heavy profile. Koluvamaregatha had
  sim_to_mean=0.050 (lowest of all Thodi clips, vs 0.060-0.105 for others).
- **Rule**: Before aggregation, check intra-raga consistency:
  1. Pairwise dot-product between clips (should be >0.04)
  2. Similarity to mean (should be >0.06)
  3. Entropy should be within 0.5 of the raga median
  Outliers should be excluded (moved to excluded/ folder, not deleted).
- **Impact**: Removing 2 outliers from 7 Thodi clips improved Thodi
  self-recognition from HIGH=6 to HIGH=5 (with 0 wrong), and reduced
  overall wrongs from 20 to 18.

### L-025: PCD-Only Scoring Is a Valid Stabilization Step
- **Date**: 2026-03-10
- **Context**: When dyads were broken (ALPHA=0.5, all similarities ~0.001),
  temporarily setting DYAD_WEIGHT=0.0 doubled margins and stabilized
  classification. This exposed the real problem (Thodi sink) that was
  previously masked by dyad noise.
- **Rule**: When a feature channel is suspected broken, disable it
  temporarily and test PCD-only. If margins improve, the feature was
  actively hurting. Fix the feature before re-enabling.
  This is diagnostic, not permanent.
- **Impact**: PCD-only immediately revealed that dyads were compressing
  margins by ~40%, leading to the ALPHA fix.

### L-026: Dyad Discrimination Ratio Is the Key Metric for ALPHA Tuning
- **Date**: 2026-03-10
- **Context**: The discrimination ratio (self-similarity / mean-other-similarity)
  directly measures whether dyads can tell ragas apart.
  ALPHA=0.5: ratio 1.24x (useless). ALPHA=0.01: ratio 1.73x (useful).
  Diminishing returns below 0.01 (0.001 gives 1.75x, 0.0001 gives 1.75x).
- **Rule**: When tuning ALPHA, measure discrimination ratio, not raw
  similarity values. Target: >1.5x for useful dyads. >2x for strong dyads.
  Sweep: [0.5, 0.1, 0.01, 0.001] and pick the knee point.
- **Impact**: This metric gave clear evidence that ALPHA=0.01 was the
  right value, avoiding guesswork.

### L-027: Consensus Across Independent Analyses Validates the Plan
- **Date**: 2026-03-10
- **Context**: Three independent analyses (our multi-agent team, the user's
  own analysis, and Grok's analysis) all converged on the same 3-phase plan:
  Phase 1 (PCD-only), Phase 2 (ALPHA fix), Phase 3 (OOD hybrid).
  The user correctly noted this convergence IS the validation.
- **Rule**: When multiple independent analyses agree, the confidence in
  the plan is high. Don't keep searching for alternatives — execute.
  Convergence from different perspectives is stronger evidence than
  any single deep analysis.
- **Impact**: Avoided analysis paralysis. Moved to execution immediately.
### L-028: Vocal Isolation Is Not Optional for Recognition
- **Date**: 2026-03-11
- **Context**: Blind test on 16 files: vocal-isolated clips scored 64% accuracy
  and 100% OOD rejection (2/2). Mix audio (full concert with instruments) scored
  38% accuracy and only 25% OOD rejection (2/8). The same system, same models,
  same thresholds -- the only difference was vocal isolation.
- **Rule**: Vocal isolation (Demucs or multitrack stems) must be a mandatory
  preprocessing step, not optional. Without it, pYIN picks up violin, tambura,
  and mridangam pitches that inflate scores and destroy margin-based rejection.
  Never evaluate or deploy without vocal isolation in the pipeline.
- **Impact**: Without this rule, the system appears to work in testing (vocal-only)
  but fails catastrophically on real-world concert recordings.

### L-029: Blind Testing Reveals What Self-Testing Hides
- **Date**: 2026-03-11
- **Context**: Sandbox testing (on seed features) showed 64% accuracy. The blind
  test on unseen mix audio from archive.zip showed 38%. The sandbox was right
  about vocal-isolated performance but couldn't predict mix-audio degradation.
  Additionally, the sandbox only tested 4 random files -- expanding to 16
  revealed the Thodi sink is far worse on OOD audio than expected (6/8 false pos).
- **Rule**: Always run a blind test with anonymized files BEFORE declaring a
  milestone. Include both known-raga and OOD-raga files. Include mix audio
  (not just vocal-isolated) to test real-world conditions. Sandbox results on
  training data are necessary but not sufficient.
- **Impact**: Prevents overconfidence. The 64% number is real for vocal-only,
  but the system is not ready for general audio without vocal isolation.

### L-030: IDF x Variance Is the Right PCD Weighting for Raga Discrimination
- **Date**: 2026-03-12
- **Context**: Tested 5 PCD scoring methods: baseline dot-product, mean-subtracted,
  cosine, IDF-only, variance-only, and IDF x variance combined.
  IDF x variance won decisively: 83% sandbox (vs 64% baseline), 70% production.
  It downweights common swaras (Sa, Pa) and upweights distinctive ones.
  This is the MIR equivalent of TF-IDF: common features are noise, rare features are signal.
- **Rule**: When a feature dimension is shared by all classes, it adds noise to
  similarity scoring. Weight each dimension inversely by its commonality (IDF)
  and variability (1/std). The combined weight focuses the dot-product on what
  actually distinguishes the classes.
- **Impact**: +6% production accuracy, Thodi sink halved, Kamboji and Kalyani
  dramatically improved. Single biggest architectural improvement after ALPHA fix.

### L-031: Sandbox Self-Evaluation Overestimates by 10-15%
- **Date**: 2026-03-12
- **Context**: Method E sandbox showed 83% accuracy on 53 clips. Production batch
  on the same 53 clips showed 70%. The 13% gap is because sandbox builds models
  and evaluates on the same clips (self-recognition bias). ChatGPT predicted
  ~75% for held-out data -- very close to actual 70%.
- **Rule**: Always expect 10-15% accuracy drop from sandbox to production when
  training and test sets overlap. Sandbox results are useful for comparing methods
  (relative ranking is preserved) but absolute numbers are optimistic.
  True accuracy requires held-out validation or cross-validation.
- **Impact**: Prevents overconfidence in sandbox results. The relative ordering
  of methods (E > D2 > C > A > baseline > B > D) is reliable even if absolute
  numbers are inflated.


### L-032: Hubness Correction Needs Scale to Work
- **Date**: 2026-03-12
- **Context**: Tested centered hubness correction (score = raw - avg_sim + global_mean)
  on 6 ragas / 53 clips with LOO validation. Thodi sink eliminated (0/8) but overall
  accuracy dropped 78.6% -> 74.2%. Multi-agent analysis found bias values (+-0.0003
  to +-0.0008) are below the noise floor of pYIN pitch extraction at 72 bins.
  With only 6 ragas (15 unique model pairs), avg_sim values are statistically fragile.
- **Rule**: Hubness correction requires sufficient model diversity to produce stable
  avg_sim values. At 6 ragas, the correction is too weak to help but strong enough
  to hurt. Wait for 15+ ragas (105+ unique pairs) before re-testing.
  Keep the sandbox script ready (sandbox_hubness.py).
- **Trigger**: Re-run sandbox_hubness.py when raga count >= 15.
- **Impact**: Prevents premature adoption of a correction that would reduce accuracy.
  The idea is correct; the timing is wrong.

### L-033: Leave-One-Out Is the Gold Standard for Small Datasets
- **Date**: 2026-03-12
- **Context**: Sandbox self-eval showed 83% (36-bin) and 90% (72-bin). Production
  batch showed 70%. LOO showed 66.7% (36-bin) and 78.6% (72-bin). The LOO numbers
  are the most trustworthy because they eliminate self-evaluation bias entirely.
  Each clip is scored against a model built WITHOUT that clip.
- **Rule**: For datasets under 100 clips, always use LOO cross-validation to get
  true accuracy. Self-eval overestimates by 10-15%. Production batch results fall
  between self-eval and LOO. LOO is pessimistic but honest.
- **Impact**: Prevents overconfidence. LOO confirmed that 72 bins genuinely improve
  accuracy (66.7% -> 78.6%), not just an artifact of self-evaluation.

### L-034: 72 Bins Resolve Microtonal Distinctions That 36 Bins Cannot
- **Date**: 2026-03-12
- **Context**: Shuddha Ma (~498 cents) and prati Ma (~590 cents) are 92 cents apart.
  At 36 bins (33 cents/bin), they land 2-3 bins apart. At 72 bins (17 cents/bin),
  they land 6 bins apart. This directly separates Kalyani (prati Ma) from
  Shankarabharanam (shuddha Ma). Same applies to komal vs shuddha Ri/Ga/Da.
  LOO results: Kalyani 58% -> 90%, wrongs halved from 14 to 6.
- **Rule**: PCD bin resolution must be fine enough to separate swaras that
  distinguish sibling ragas. For Carnatic music with 16 swarasthanas,
  72 bins (17 cents each) is the minimum for reliable microtonal separation.
  36 bins (33 cents) is too coarse. 96+ bins causes margin collapse (too sparse).
- **Impact**: Single largest accuracy gain in the project: +11.9% LOO accuracy
  from a pure code change with zero new data.

### L-035: Multi-Agent Analysis Is Decisive for Mixed-Result Decisions
- **Date**: 2026-03-12
- **Context**: Hubness correction showed mixed results (Thodi sink eliminated but
  accuracy dropped). The 5-expert multi-agent analysis provided unanimous clarity:
  park it, don't discard it. Each expert identified the same root cause from their
  domain (noise floor, statistical fragility, small-sample artifacts, maintenance
  burden). No single perspective would have been as convincing.
- **Rule**: When a fix shows mixed results (improves some metrics, hurts others),
  invoke the multi-agent analysis. The cross-domain perspectives cut through
  ambiguity. Reserve it for genuinely hard decisions (not routine fixes).
- **Impact**: Prevented both premature adoption (would have hurt accuracy) and
  premature rejection (would have lost a valuable future feature).
