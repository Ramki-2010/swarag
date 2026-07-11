# Swarag — Feature Registry

Mandated by the Vision Bible (Section 12, Living Knowledge). Every row below
is sourced from an existing lesson, bug, commit, or architecture entry —
nothing here is a new claim. Generated 2026-07-11 against v1.3.2.

Status legend: **ACTIVE** (in production), **PARKED** (validated, waiting on
a trigger condition), **REJECTED** (tested, does not work — kept for record),
**RETIRED** (was active, removed after evidence showed it hurt).

---

## Pitch & Preprocessing

| Feature | Status | Params | Source |
|---|---|---|---|
| Vocal isolation (Saraga stems / Demucs htdemucs) | ACTIVE | Stems preferred over Demucs | L-020, L-028 |
| pYIN pitch extraction | ACTIVE | librosa, SR=22050 | ARCHITECTURE.md Stage 1 |
| Duration cap | ACTIVE | MAX_DURATION_SEC=360 | L-021 |
| Tonic (Sa) estimation | ACTIVE | Histogram + octave-aware peak detection, utils.py | ARCHITECTURE.md Stage 2 |
| Per-file timeout (batch) | ACTIVE | PER_FILE_TIMEOUT=360s, ThreadPoolExecutor | L-039 |

## Core Representation

| Feature | Status | Params | Source |
|---|---|---|---|
| Pitch Class Distribution (PCD) | ACTIVE | 72 bins, 17 cents/bin, tonic-normalized | L-034 |
| IDF x Variance PCD weighting | ACTIVE | Downweights common swaras, upweights distinctive | L-030 |
| Directional dyads (mean_up / mean_down) | ACTIVE | 72x72 matrices, MIN_STABLE_FRAMES=5 | ARCHITECTURE.md Stage 3.2 |
| Laplace smoothing (dyads) | ACTIVE | ALPHA=0.01 (scaled to matrix size) | L-023 |

## Scoring & Fusion

| Feature | Status | Params | Source |
|---|---|---|---|
| Global PCD/Dyad fusion weight | ACTIVE | 0.8 / 0.2, applied uniformly to all ragas | L-045, commit 21da815 |
| Per-raga weight override (Bhairavi 0.5/0.5) | **RETIRED (v1.3.2)** | Confirmed 0% decided for Bhairavi on canonical LOO — was built on a fabricated 67.4% table | ADR-006, ADR-013, commit 21da815 |
| Per-raga weight override (general, Mohanam/Abhogi) | REJECTED | Trades one raga's accuracy for another's | L-042, L-044 |
| Genericness penalty | REJECTED | Mathematically inert on ranking; worse when computed from model PCD | L-012, L-016 |
| Escalation (dyad-heavy re-scoring) | REJECTED | Crushes margins ~5x with thin data | L-017 |
| Confidence tiers | ACTIVE | HIGH >=0.003, MODERATE >=0.001, else UNKNOWN | BUG-006 (resolved) |
| Hubness correction (centered) | PARKED | Trigger: ragas >= 15 | BUG-010, L-032, L-035 |

## Data Guardrails

| Feature | Status | Params | Source |
|---|---|---|---|
| MIN_CLIPS_PER_RAGA guardrail | ACTIVE | 5 clips minimum before aggregation | L-036, BUG-011 |
| Duplicate feature dedup | ACTIVE (process, not code) | Match by raga + filename prefix, not timestamp | L-037, BUG-012 |
| Outlier clip exclusion | ACTIVE (process) | Pairwise sim >0.04, sim-to-mean >0.06, entropy within 0.5 of median | L-024 |
| Raga label cross-reference vs Saraga/Dunya metadata | ACTIVE (process) | Prevents parent/janya mislabeling | L-040, BUG-013 |

## Janya / Parent-Child Separation (Abhogi problem)

| Feature | Status | Params | Source |
|---|---|---|---|
| Absent-swara penalty (data-driven, median threshold) | REJECTED | Self-harm on 5/7 Abhogi clips | L-046 |
| Absent-swara penalty (musicological bin ranges) | REJECTED | Gamaka spillover puts 6-19% energy in "absent" swaras | L-046 |
| Swara energy-ratio comparison (quantitative) | REJECTED (2026-07-11) | `sandbox_abhogi_ratio.py`, BUG-015. Abhogi score identical at every tested weight (0.05-0.40) -- confirmed no signal, not just weak. | BUG-015, L-050 |
| Phrase n-gram detection | PARKED (not yet implemented) | Candidate: M2-D2-M2 vs Pa-D2-N3 | architecture.md Next Steps |

## Evaluation / Governance

| Feature | Status | Params | Source |
|---|---|---|---|
| LOO as sole canonical trust tier | ACTIVE | `sandbox_loo_v131_canonical.py` is the permanent ground-truth rerun script | ADR-011, commit b1a1ac9 |
| Fabricated-table detection (row-sum check) | ACTIVE (process) | Any logged table's per-raga rows must sum to its TOTAL row before being trusted | 2026-07-10/11 audit history (this table caught two separate fabrications) |
| LOO fold completeness check | ACTIVE (process) | Any custom LOO script's baseline must be cross-checked against `sandbox_loo_v131_canonical.py` on identical config before its results are trusted -- a mismatch means a fold-exclusion bug, not a config difference | BUG-018, L-049 |

## OOD / Robustness

| Feature | Status | Params | Source |
|---|---|---|---|
| Margin-only OOD rejection | ACTIVE (partial) | No absolute score floor yet | BUG-009 |
| Mandatory vocal isolation for inference | ACTIVE (policy, NOT enforced in code) | Confirmed 2026-07-10: `recognize_raga_v12.py` has no vocal/Demucs/isolation check | L-028, L-029, BUG-009, ADR-009 |
| Absolute score floor / OOD detector | NOT IMPLEMENTED | Open architectural gap | BUG-009, workflow.md Section 4 |

---

## Maintenance Rule

When a feature changes status, update its row here in the same commit as
the code change. Two features in this table (Bhairavi override, and the
67.4% baseline it was validated against) were retired in the same session
this registry was corrected in — that is not a coincidence: the fabricated
table is what made the override look good in the first place. Any future
"this feature helps X%" claim must cite a canonical LOO run, not a
self-eval or a hand-typed table.
