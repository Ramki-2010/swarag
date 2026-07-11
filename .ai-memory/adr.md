# Swarag — Architecture Decision Records

Mandated by the Vision Bible (Section 12). Each ADR documents a decision
already made and evidenced elsewhere in the memory files. Generated
2026-07-11 against v1.3.2. Format: Context -> Decision -> Consequence -> Status.

---

### ADR-001: Deterministic DSP over Machine Learning
- **Context**: Small dataset (<100 clips), need for interpretable errors.
- **Decision**: Use hand-designed DSP features (PCD, dyads) with deterministic
  scoring rather than a trained classifier.
- **Consequence**: No black-box failures; every error is traceable to a
  specific feature or weight. Slower to add new discriminative power than ML.
- **Status**: ACTIVE. Revisit per ML Roadmap (Bible Section 10) once
  deterministic features mature and diverse data exists.
- **Source**: ARCHITECTURE.md Design Constraints; Bible Section 10.

### ADR-002: 72-bin Pitch Class Distribution
- **Context**: 36-bin PCD could not separate shuddha Ma from prati Ma
  (92 cents apart, only 2-3 bins at 36-bin resolution).
- **Decision**: Use 72 bins (17 cents/bin) as the PCD resolution.
- **Consequence**: +11.9% LOO accuracy (66.7% -> 78.6% in the 6-raga
  sandbox). 96+ bins tested and rejected — too sparse, inflated UNKNOWN rate.
- **Status**: ACTIVE, locked.
- **Source**: L-034, Run 2026-03-12 (LOO 36 vs 72 bins).

### ADR-003: IDF x Variance PCD Weighting
- **Context**: Common swaras (Sa, Pa) shared across all ragas were diluting
  dot-product similarity.
- **Decision**: Weight each PCD bin by inverse document frequency times
  1/std, downweighting common swaras and upweighting distinctive ones.
- **Consequence**: +6% production accuracy over baseline dot-product;
  single biggest improvement after the ALPHA fix.
- **Status**: ACTIVE, locked.
- **Source**: L-030.

### ADR-004: Laplace Smoothing ALPHA = 0.01
- **Context**: ALPHA=0.5 on 1296-cell dyad matrices added more smoothing
  mass (648) than signal (~370 transitions/file); dyad similarities were
  ~0.001 for all ragas (noise).
- **Decision**: Set ALPHA=0.01, scaled to matrix size.
- **Consequence**: Discrimination ratio improved 1.24x -> 1.73x.
- **Status**: ACTIVE, locked.
- **Source**: L-023, L-026.

### ADR-005: Global Fusion Weight PCD=0.8 / Dyad=0.2
- **Context**: At 7 ragas / 70 clips, 72x72 dyad matrices are still sparse.
  Weight sweep tested 0.6/0.4, 0.7/0.3, 0.8/0.2.
- **Decision**: 0.8/0.2 as the global default, applied uniformly to all
  ragas as of v1.3.2 (see ADR-013 — no per-raga exceptions remain).
- **Consequence**: Fewest wrongs of the configs tested at fixed margin
  threshold.
- **Status**: ACTIVE. Revisit when per-raga clip counts reach 15-20+ and
  dyad discrimination ratio exceeds 2.0x.
- **Source**: L-045.

### ADR-006: Per-Raga Override — Bhairavi = 0.5/0.5 [SUPERSEDED]
- **Context**: Bhairavi's dyads were believed genuinely distinctive
  (unlike most ragas, where per-raga overrides just trade accuracy
  between ragas).
- **Decision**: Override fusion weight to 0.5/0.5 for Bhairavi only.
- **Consequence**: Appeared net-positive against a 67.4% LOO table logged
  at the time. That table was later found fabricated — its per-raga rows
  never summed to its own TOTAL row. On the canonical rerun
  (`sandbox_loo_v131_canonical.py`), the override produced 0% decided for
  Bhairavi (9 wrongs).
- **Status**: **SUPERSEDED by ADR-013.** Kept as a record that a decision
  was made on unverified evidence — this is the concrete case for ADR-011
  (LOO is the only tier trusted for accuracy claims).
- **Source**: L-042, datasets.md baseline reconciliation, commit b1a1ac9.

### ADR-007: MIN_CLIPS_PER_RAGA = 5 Guardrail
- **Context**: Adding ragas with 1-3 clips (Abhogi, Saveri, Madhyamavati at
  the time) dropped LOO accuracy from 72.0% to 41.7% — thin models became
  false attractors.
- **Decision**: Exclude any raga with fewer than 5 clips from aggregation.
  Keep features on disk (not deleted) so they activate automatically once
  the threshold is met.
- **Consequence**: Prevents thin-data sink behavior. Currently excludes
  Kamboji (3), Madhyamavati (2), Hamsadhvani (1).
- **Status**: ACTIVE, locked.
- **Source**: L-036, BUG-011.

### ADR-008: Absent-Swara Penalty — Rejected
- **Context**: Abhogi (janya, subset of Kalyani's swaras) needed a way to
  score "expected but absent" swaras. Two approaches tried: data-driven
  (median threshold on model PCD) and musicological (known swara bin ranges).
- **Decision**: Reject both. Gamaka ornamentation spreads energy into
  neighboring swara bins, so a "missing" swara still shows 6-19% energy —
  binary absent/present detection cannot separate signal from gamaka leakage.
- **Consequence**: Do not re-attempt binary absent-swara detection. Active
  replacement direction: quantitative energy-ratio comparison
  (`sandbox_abhogi_ratio.py`, BUG-015).
- **Status**: REJECTED, added to proven-dead-ends list.
- **Source**: L-046, BUG-015.

### ADR-009: Mandatory Vocal Isolation
- **Context**: Blind test showed 64% accuracy / 100% OOD rejection on
  vocal-isolated audio vs 38% accuracy / 25% OOD rejection on mix audio,
  same models and thresholds.
- **Decision**: Vocal isolation (Saraga stems or Demucs) is a mandatory
  pipeline step, not optional preprocessing.
- **Consequence**: BUG-009 (mix audio OOD false positives) remains open
  specifically because this mandate is not yet enforced in code — confirmed
  2026-07-10: `scripts/recognize_raga_v12.py` contains no vocal/Demucs/
  isolation check. Policy exists, enforcement does not.
- **Status**: ACTIVE as policy; enforcement OPEN (tracked under BUG-009).
- **Source**: L-028, L-029, BUG-009.

### ADR-010: Sandbox-First Development
- **Context**: A silent production breakage (BUG-001) demonstrated that
  direct edits to production scripts are unsafe without a comparison step.
- **Decision**: Every fix is implemented in a `test_*.py` / `sandbox_*.py`
  script, compared before/after, and only promoted to production if results
  are strictly better.
- **Consequence**: Near-zero code regressions since adoption. Notably did
  NOT prevent the Bhairavi override (ADR-006) from shipping on fabricated
  documentation — sandbox-first protects code paths, not the accuracy
  numbers logged about them. See ADR-011.
- **Status**: ACTIVE, mandatory. See workflow.md Section 5.
- **Source**: L-011, L-015, workflow.md.

### ADR-011: LOO Cross-Validation as the Trust Standard
- **Context**: Self-evaluation (model built and tested on the same clips)
  overestimated accuracy by 10-15% versus true held-out performance. Later,
  a hand-typed LOO table (67.4%) was found fabricated — internally
  inconsistent row sums — despite looking like a real run.
- **Decision**: Leave-one-out cross-validation, run via a checked-in script
  (not hand-typed), is the only accuracy number treated as canonical.
- **Consequence**: Canonical baseline is pessimistic but honest. Directly
  caused the Bhairavi override retirement (ADR-013) once the real rerun
  contradicted the fabricated one.
- **Status**: ACTIVE, locked.
- **Source**: L-031, L-033, ADR-013.

### ADR-012: Multi-Agent Analysis Is On-Demand, Not Routine
- **Context**: Running the 5-expert analysis on every change wastes tokens
  on decisions that don't need it.
- **Decision**: Reserve `/analyze-swarag` for genuinely hard, cross-domain,
  or mixed-result decisions.
- **Consequence**: Faster iteration on routine work.
- **Status**: ACTIVE, locked.
- **Source**: L-014, workflow.md Section 12.

### ADR-013: Retire Bhairavi Per-Raga Override
- **Context**: Canonical LOO rerun (`sandbox_loo_v131_canonical.py`)
  showed the Bhairavi 0.5/0.5 override at 0% decided (9 wrongs), directly
  contradicting the 40% figure ADR-006 was built on.
- **Decision**: Retire the override. Bhairavi uses the uniform 0.8/0.2
  global weight like every other raga (ADR-005).
- **Consequence**: Overall canonical LOO moved 60.5% (with override,
  confirmed bad) -> 64.1% (without it), +3.6pp. Bhairavi itself sits at
  14% decided standalone — weak, but no longer masked by an unsupported
  weight hack. Its real fix is more diverse training clips.
  Follow-up (2026-07-11): `scripts/confusion_matrix_audit.py` — the very
  script whose Scenario 1/2 comparison motivated this retirement — was
  found still hardcoding the override as its own "canonical" default one
  commit later. Fixed same day. See Section 11 of the Dossier.
- **Status**: ACTIVE, locked. Commit `21da815`.
- **Source**: datasets.md CANONICAL v1.3.2 table, commit `21da815`.

### ADR-014: Energy-Ratio Scoring — Rejected for Abhogi/Kalyani Separation
- **Context**: BUG-015 (Abhogi janya absorption) needed a successor to the
  rejected absent-swara penalty (ADR-008). Quantitative Pa/N3 energy-ratio
  comparison (`sandbox_abhogi_ratio.py`) was proposed as a more precise,
  non-binary alternative.
- **Decision**: Reject. Phase 1 diagnostic showed Abhogi and Kalyani's Pa
  energy distributions have essentially no separation (ratio=1.01x, 4/7
  Abhogi clips overlap Kalyani's Pa range). Phase 2 LOO sweep confirmed
  this at the outcome level: Abhogi's per-raga result was byte-identical
  (C=1/W=2/U=4, 33%) at every tested ratio_weight from 0.05 to 0.40. The
  approach's own topline "+1.0% improvement" was unrelated collateral
  (Bhairavi/Thodi gains, a Mohanam regression) and did not reflect any
  actual signal for the target raga.
- **Consequence**: Confirms the Abhogi problem is not solvable by any
  scoring-time adjustment to PCD-derived features (weight overrides,
  absent-swara penalty, and now energy ratios have all failed for the
  same underlying reason: gamaka spillover makes Abhogi and Kalyani's
  swara-energy profiles genuinely overlap, not just hard to threshold).
  Points decisively toward phrase-level or sequence-level features
  (n-grams, contour templates) as the only untried category.
- **Status**: REJECTED, added to proven-dead-ends list.
- **Source**: BUG-015, L-050, datasets.md Run 2026-07-11.

### ADR-015: Audit Scripts Import Shared Constants Instead of Duplicating
- **Context**: Both `confusion_matrix_audit.py` and `sandbox_abhogi_ratio.py`
  hardcoded their own copies of scoring constants (N_BINS, ALPHA, weights,
  PER_RAGA_WEIGHTS). One of those copies drifted stale for a single commit
  (2026-07-11) and silently mislabeled a retired config as canonical
  (BUG-017).
- **Decision**: Both scripts now `from recognize_raga_v12 import (...)`
  the shared scoring constants instead of redefining them. Already
  established as safe by `batch_evaluate.py`'s existing import of
  `recognize_raga_v12.recognize_raga`.
- **Consequence**: The specific "duplicate constant drifts stale" failure
  mode is now structurally impossible for these two files — if production
  constants change, both scripts pick up the change automatically with no
  manual sync step to forget. Does not prevent other corruption patterns
  (e.g. the docs/ARCHITECTURE.md editor-placeholder corruption, BUG-017) —
  those need a different mitigation (see BUG-017's recommended pre-commit
  check, not yet implemented).
- **Status**: ACTIVE, locked.
- **Source**: BUG-017, L-002, this session.

---

## Maintenance Rule

New ADRs are added, never edited after Status is set to ACTIVE/REJECTED —
if a decision is reversed, write a new ADR that supersedes the old one and
mark the old one's Status as SUPERSEDED with a pointer forward. ADR-006 /
ADR-013 is the reference example for how to do this.
