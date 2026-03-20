"""
Session documentation update: Phase 3 + Phase 4 + Hubness + LOO validation.
Updates all 7 memory files comprehensively.
"""
import os

os.chdir(r"D:\Swaragam\.ai-memory")


# ============================================================
# 1. BUGS.MD
# ============================================================
with open("bugs.md", "r", encoding="utf-8") as f:
    content = f.read()

# Update BUG-008 status to reflect Phase 3+4 improvements
old_bug8 = "- **Status**: PARTIALLY RESOLVED (Phase 3: IDF x Variance weighting) \u2014 reduced but present"
new_bug8 = "- **Status**: MOSTLY RESOLVED (Phase 3+4: IDF x Variance + 72 bins)"
if old_bug8 in content:
    content = content.replace(old_bug8, new_bug8)
else:
    # Try without em dash
    old_bug8b = "- **Status**: PARTIALLY RESOLVED (Phase 3: IDF x Variance weighting) -- reduced but present"
    content = content.replace(old_bug8b, new_bug8)

# Add Phase 4 evidence to BUG-008
old_phase3_fix = "- **Phase 3 Fix Applied (2026-03-12)**:"
new_phase3_fix = """- **Phase 4 Fix Applied (2026-03-12)**: 72-bin PCD resolution.
  72 bins separate shuddha Ma / prati Ma (6 bins apart vs 2-3 at 36 bins).
  LOO accuracy: 66.7% (36-bin) -> 78.6% (72-bin). Wrongs: 14 -> 6.
  Thodi sink: 5/14 -> 1/6 (nearly eliminated).
  Kalyani: 58% -> 90%, Shankarabharanam: 75% -> 80%, Bhairavi: 62% -> 67%.
- **Phase 3 Fix Applied (2026-03-12)**:"""
content = content.replace(old_phase3_fix, new_phase3_fix)

# Add BUG-010 (hubness parked)
bug010 = """

### BUG-010: Hubness Correction Parked (Premature at 6 Ragas)
- **Status**: PARKED -- revisit when raga count >= 15
- **Found**: 2026-03-12 (sandbox_hubness.py, multi-agent analysis)
- **Trigger**: When raga count reaches 15+, re-run sandbox_hubness.py LOO test
- **Description**:
  Centered hubness correction (score = raw - avg_sim + global_mean)
  eliminates Thodi sink entirely (0/8 wrongs to Thodi) and improves weak
  ragas (Bhairavi +8%, Shankarabharanam +6%, Kamboji +50%), but drops
  overall LOO accuracy from 78.6% to 74.2% due to 2 new wrongs from
  small-sample instability.
- **Why parked (not rejected)**:
  Multi-agent analysis (5 experts unanimous):
  - Architecturally correct -- penalizes hub ragas (Thodi bias +0.000783)
  - Bias values too small at 6 ragas (+-0.0003-0.0008 vs noise floor)
  - New wrongs are small-sample artifacts (Kamboji has only 3 clips)
  - At 15+ ragas, bias spread will be >= 0.002 -> correction becomes reliable
  - Correction is below pYIN pitch extraction noise floor at 72 bins
- **Sandbox reference**: scripts/sandbox_hubness.py (full LOO test)
- **Evidence**:
  Hubness diagnostic: Thodi=HUB (+0.000783), Kalyani=HUB (+0.000359),
  Shankarabharanam=ok, Bhairavi=ok, Kamboji=low, Mohanam=low.
  LOO 72-bin: No hubness=78.6% (22c/6w/25u), +Hubness=74.2% (23c/8w/22u).
  Thodi sink: 1/6 -> 0/8. But +2 new wrongs (Bhairavi->Kamboji, Kamboji->Mohanam).
"""

content = content.rstrip() + "\n" + bug010

with open("bugs.md", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: bugs.md")


# ============================================================
# 2. LESSONS.MD
# ============================================================
with open("lessons.md", "r", encoding="utf-8") as f:
    content = f.read()

new_lessons = """

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
"""

content = content.rstrip() + "\n" + new_lessons

with open("lessons.md", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: lessons.md")


# ============================================================
# 3. DATASETS.MD -- Add Phase 4 LOO results + hubness results
# ============================================================
with open("datasets.md", "r", encoding="utf-8") as f:
    content = f.read()

# Add new run entries before the Method E entry
marker = "### Run: 2026-03-12 -- Method E production batch"
new_runs = """### Run: 2026-03-12 -- Hubness correction sandbox (LOO, 72 bins)
**Script**: sandbox_hubness.py
**Method**: Centered hubness correction (score = raw - avg_sim + global_mean)
**Validation**: Leave-one-out cross-validation (true held-out)

| Method | Correct | Wrong | Unknown | Acc (decided) | Thodi Sink |
|---|---|---|---|---|---|
| 72-bin IDF x Var (no hubness) | 22 | 6 | 25 (47%) | 78.6% | 1/6 |
| 72-bin IDF x Var + hubness | 23 | 8 | 22 (42%) | 74.2% | 0/8 |

Per-raga (with hubness): Bhairavi 75%, Kalyani 88%, Kamboji 50%,
Mohanam 25%, Shankarabharanam 86%, Thodi 100%.
**Verdict: PARKED** -- accuracy drops 4.4%. Revisit at 15+ ragas (BUG-010).

### Run: 2026-03-12 -- LOO cross-validation (36 vs 72 bins)
**Script**: sandbox_loo_validation.py
**Method**: Leave-one-out with IDF x Variance scoring
**Purpose**: True held-out accuracy (no self-evaluation bias)

| Bins | Correct | Wrong | Unknown | Acc (decided) | Thodi Sink |
|---|---|---|---|---|---|
| 36 | 28 | 14 | 11 (21%) | 66.7% | 5/14 |
| 72 | 22 | 6 | 25 (47%) | 78.6% | 1/6 |

Per-raga (72-bin LOO): Thodi 100%, Kalyani 90%, Shankarabharanam 80%,
Bhairavi 67%, Kamboji 0% (all UNKNOWN, only 3 clips), Mohanam 25%.
72 bins: +11.9% accuracy, wrongs halved, Thodi sink nearly eliminated.
UNKNOWN rate higher (47%) due to tighter margins at finer resolution.

### Run: 2026-03-12 -- Phase 4 production test (72 bins, cached features)
**Script**: sandbox_phase4_production.py
**Models**: run_20260312_205842_72bins (72-bin aggregation)
**Scoring**: IDF x Variance weighted PCD (72 bins)

| Raga | Total | Correct | Wrong | Unknown | Acc (decided) |
|---|---|---|---|---|---|
| Thodi | 10 | 8 | 0 | 2 | 100% |
| Kamboji | 3 | 3 | 0 | 0 | 100% |
| Kalyani | 14 | 12 | 0 | 2 | 100% |
| Shankarabharanam | 9 | 7 | 1 | 1 | 88% |
| Bhairavi | 11 | 5 | 1 | 5 | 83% |
| Mohanam | 6 | 2 | 2 | 2 | 50% |
| **TOTAL** | **53** | **37** | **4** | **12** | **90%** |

Note: 90% is self-eval (same clips for model and test). True LOO accuracy is 78.6%.

### Run: 2026-03-12 -- Phase 4 bin resolution sandbox
**Script**: sandbox_phase4_bins.py
**Method**: IDF x Variance scoring at 36/48/60/72/96/120 bins

| Bins | Correct | Wrong | Unknown | Acc | Thodi Sink |
|---|---|---|---|---|---|
| 36 | 35 | 7 | 11 | 83% | 1/7 |
| 48 | 35 | 4 | 14 | 90% | 0/4 |
| 72 | 37 | 4 | 12 | 90% | 0/4 |
| 96 | 26 | 1 | 26 | 96%* | 0/1 |
| 120 | 17 | 1 | 35 | 94%* | 0/1 |

*96/120: inflated accuracy due to 49-66% UNKNOWN rate. Too fine.
Winner: 72 bins (most correct, lowest wrongs, reasonable UNKNOWN).

"""

content = content.replace(marker, new_runs + marker)

# Update aggregated models section to include 72-bin models
old_agg = '- **Location**: `D:\\Swaragam\\pcd_results\\aggregation\\v1.2\\run_20260310_085601\\`'
new_agg = """- **36-bin models**: `D:\\Swaragam\\pcd_results\\aggregation\\v1.2\\run_20260310_085601\\`
- **72-bin models (current)**: `D:\\Swaragam\\pcd_results\\aggregation\\v1.2\\run_20260312_205842_72bins\\`"""
content = content.replace(old_agg, new_agg)

with open("datasets.md", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: datasets.md")


# ============================================================
# 4. ARCHITECTURE.MD -- Update to v1.2.4, 72 bins, new sandboxes
# ============================================================
with open("architecture.md", "r", encoding="utf-8") as f:
    content = f.read()

# Version bump
content = content.replace("Swarag v1.2.3", "Swarag v1.2.4")
content = content.replace("Phase 3 IDF x Variance scoring applied",
                          "Phase 4: 72-bin PCD + IDF x Variance + hubness parked")

# Update N_BINS in pipeline diagram
content = content.replace(
    "|-- PCD: 36-bin pitch class distribution",
    "|-- PCD: 72-bin pitch class distribution (Phase 4: was 36)")
content = content.replace(
    "|-- mean_up   (ascending transitions, 36x36 matrix)",
    "|-- mean_up   (ascending transitions, 72x72 matrix)")
content = content.replace(
    "|-- mean_down (descending transitions, 36x36 matrix)",
    "|-- mean_down (descending transitions, 72x72 matrix)")

# Update constants table
content = content.replace("| N_BINS | 36 |", "| N_BINS | **72** |")

# Add Phase 4 sandbox scripts
old_sandbox_table = "| `diag_alpha.py` | Laplace ALPHA impact analysis (transition counts) |"
new_sandbox_table = """| `diag_alpha.py` | Laplace ALPHA impact analysis (transition counts) |
| `sandbox_phase3_thodi_sink.py` | Phase 3: IDF vs mean-sub vs cosine scoring |
| `sandbox_phase3b_variance.py` | Phase 3b: IDF vs variance vs combined (Method E) |
| `sandbox_phase4_bins.py` | Phase 4: PCD bin resolution (36/48/60/72/96/120) |
| `sandbox_phase4_production.py` | Phase 4: 72-bin production test (cached features) |
| `sandbox_loo_validation.py` | LOO cross-validation (36 vs 72 bins) |
| `sandbox_hubness.py` | Hubness correction test (LOO, PARKED) |"""
content = content.replace(old_sandbox_table, new_sandbox_table)

# Add Phase 4 key finding
phase4_finding = """
## Phase 4 Key Finding: 72-bin PCD Resolution
- 36 bins (33 cents/bin) too coarse: shuddha Ma and prati Ma only 2-3 bins apart
- 72 bins (17 cents/bin): Ma1 and Ma2 are 6 bins apart -> separates Kalyani/Shankarabharanam
- LOO accuracy: 66.7% (36-bin) -> 78.6% (72-bin) = +11.9%
- Wrongs halved: 14 -> 6. Thodi sink: 5/14 -> 1/6
- 96+ bins causes margin collapse (too sparse for 53 clips)
- Pure code change, no new data needed

## Hubness Correction (PARKED for 15+ ragas)
- Centered correction: score = raw - avg_sim[raga] + global_mean
- Eliminates Thodi sink (0/8) but drops LOO accuracy 78.6% -> 74.2%
- Multi-agent analysis: unanimously park (bias values below noise floor at 6 ragas)
- Trigger: re-test when raga count >= 15 (sandbox_hubness.py ready)

"""
content = content.replace(
    "## Phase 3 Key Finding:",
    phase4_finding + "## Phase 3 Key Finding:")

# Update current accuracy
content = content.replace(
    "Accuracy (excl UNKNOWN): **70%** (Method E: IDF x Variance)",
    "Accuracy (excl UNKNOWN): **78.6% LOO** (72-bin IDF x Variance)")

# Update aggregation location
content = content.replace(
    "run_20260310_085601\\",
    "run_20260312_205842_72bins\\")
content = content.replace(
    "(alpha=0.01, bins=36, 53 files)",
    "(alpha=0.01, bins=72, 53 files)")

with open("architecture.md", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: architecture.md")


# ============================================================
# 5. WORKFLOW.MD -- Add parked features section
# ============================================================
with open("workflow.md", "r", encoding="utf-8") as f:
    content = f.read()

parked_section = """

---

## 13. Parked Features (Activate at Scale)

Some features have been validated in sandbox but are premature for the
current dataset size. Check this table when adding ragas.

| Feature | Parked Since | Trigger | Sandbox Script | Bug Ref |
|---|---|---|---|---|
| Hubness correction (centered) | 2026-03-12 | Ragas >= 15 | sandbox_hubness.py | BUG-010 |

When adding ragas, check this table. If trigger condition is met,
re-run the sandbox script with LOO validation before integrating.
"""

# Add before the last line if not already present
if "Parked Features" not in content:
    content = content.rstrip() + "\n" + parked_section

with open("workflow.md", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: workflow.md")


# ============================================================
# 6. DEBUG-PLAYBOOK.MD -- Update shapes, bin count, add LOO reference
# ============================================================
with open("debug-playbook.md", "r", encoding="utf-8") as f:
    content = f.read()

# Update aggregation path
content = content.replace(
    "Current: pcd_results/aggregation/v1.2/run_20260310_085601/",
    "Current: pcd_results/aggregation/v1.2/run_20260312_205842_72bins/")
content = content.replace(
    "Scoring: IDF x Variance weighted (Phase 3, v1.2.3)",
    "Scoring: IDF x Variance weighted, 72 bins (Phase 4, v1.2.4)")

# Update array shapes
content = content.replace("(PCD: 36, Dyads: 1296)", "(PCD: 72, Dyads: 5184)")

# Add LOO validation to common patterns
old_pattern = "| ModuleNotFoundError | Virtual environment not activated |"
new_pattern = """| ModuleNotFoundError | Virtual environment not activated |
| Sandbox accuracy much higher than LOO | Self-evaluation bias -- use LOO for true accuracy |
| Accuracy drops when adding scoring layer | Feature too weak for current dataset size (see BUG-010) |"""
content = content.replace(old_pattern, new_pattern)

with open("debug-playbook.md", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: debug-playbook.md")


# ============================================================
# 7. DOSSIER -- Full update
# ============================================================
with open("Swarag_Project_Dossier_v1_2.txt", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("Swarag v1.2.3 -- Project Dossier", "Swarag v1.2.4 -- Project Dossier")
content = content.replace("Version:  v1.2.3", "Version:  v1.2.4")
content = content.replace(
    "Updated:  2026-03-12 (Phase 3 IDF x Variance scoring)",
    "Updated:  2026-03-12 (Phase 4: 72-bin PCD + IDF x Variance)")

# Update current state section
content = content.replace(
    "Best accuracy: 70% (excl UNKNOWN), up from 25% baseline",
    "Best accuracy: 78.6% LOO (72-bin IDF x Variance), up from 25% baseline")

# Update evolution table
old_evo_last = "| 2026-03-12 | v1.2.3 | 6 | 53 | 70% | Phase 3: IDF x Variance PCD weighting |"
new_evo = """| 2026-03-12 | v1.2.3 | 6 | 53 | 70% | Phase 3: IDF x Variance PCD weighting |
| 2026-03-12 | v1.2.4 | 6 | 53 | 78.6% LOO | Phase 4: 72-bin PCD + hubness parked |"""
content = content.replace(old_evo_last, new_evo)

# Update lessons/bugs counts
content = content.replace("Lessons learned (31)", "Lessons learned (35)")

# Add Phase 4 to current state
content = content.replace(
    "- IDF x Variance PCD weighting (Thodi sink halved, +6% accuracy)",
    "- IDF x Variance PCD weighting (Thodi sink halved, +6% accuracy)\n  - 72-bin PCD resolution (LOO: 66.7% -> 78.6%, wrongs 14 -> 6)\n  - Hubness correction tested and PARKED for 15+ ragas (BUG-010)")

# Update open issues
content = content.replace(
    "  - BUG-008: Thodi sink (10/18 seed wrongs go to Thodi)",
    "  - BUG-008: Thodi sink (mostly resolved: 1/6 in LOO at 72 bins)")

# Update next steps
old_next = """Immediate:  Run production batch evaluation with ALPHA=0.01 models
Short-term: Phase 3"""
new_next = """Immediate:  Add more data for weak ragas:
            - Kamboji: 3 -> 10+ clips (currently fragile, 0% in LOO)
            - Mohanam: 6 -> 15 clips (25% LOO, needs diversity)
            - Bhairavi: add diverse clips (67% LOO, komal swara confusion)
Short-term: Add new ragas (Hamsadhwani, Abhogi, Madhyamavati, Saveri)
            -> improves IDF weights + OOD rejection
            -> re-test hubness correction at 15+ ragas (BUG-010)
Medium:     OOD hybrid detection (top_score - mean_score)
            Visualize dyad matrices
            Cross-validation with k-fold
Long-term:  72 Melakartas -> janya ragas -> phrase modeling
            -> gamaka analysis -> live inference -> Android

=========================================================
OLD NEXT STEPS (kept for reference, superseded by above)
=========================================================

OLD Immediate:  Run production batch evaluation with ALPHA=0.01 models
OLD Short-term: Phase 3"""
content = content.replace(old_next, new_next)

# Update script counts
content = content.replace(
    "Python code (6 production + 6 sandbox)",
    "Python code (6 production + 13 sandbox)")

with open("Swarag_Project_Dossier_v1_2.txt", "w", encoding="utf-8") as f:
    f.write(content)
print("OK: dossier")


print()
print("=== ALL 7 FILES UPDATED ===")
