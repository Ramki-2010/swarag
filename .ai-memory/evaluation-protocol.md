# Swarag — Evaluation Protocol

Mandated by the Vision Bible (Section 12) and Bible Section 3 ("Honest
Leave-One-Out validation before celebrating results"). Generated 2026-07-11
against v1.3.2.

---

## 1. Accuracy Metrics — Definitions

| Term | Definition |
|---|---|
| Correct (C) | Top-1 prediction matches ground truth and confidence tier != UNKNOWN |
| Wrong (W) | Top-1 prediction != ground truth and confidence tier != UNKNOWN |
| Unknown (U) | Confidence tier == UNKNOWN (margin < MIN_MARGIN_FINAL) |
| Acc (decided) | C / (C + W) — accuracy excluding UNKNOWN outputs |
| Acc (all) | C / (C + W + U) — accuracy treating UNKNOWN as a miss |

**Acc (decided) is the headline number used across this project.** Always
report U (count and %) alongside it — a high decided-accuracy with 90%
UNKNOWN (see: Mohanam, v1.3.2, 1c/0w/9u) is not the same claim as one with
10% UNKNOWN, even though both round to "100% decided."

## 2. Evaluation Tiers — Trust Ranking (highest to lowest)

1. **LOO (Leave-One-Out) cross-validation, run via a checked-in script** —
   CANONICAL. Each clip is scored against a model built without that clip.
   This is the only number that may be called "the accuracy" without a
   qualifier — and it must be the output of an actual script run, not a
   hand-typed table. (ADR-011, L-033)
2. **Production batch evaluation** (`batch_evaluate.py`) — informative, not
   canonical.
3. **Sandbox self-evaluation** — diagnostic only. Expect +10-15% inflation
   vs LOO (L-031).
4. **Blind test on unseen/anonymized audio** — required before declaring
   any milestone (L-029).

**Rule**: a milestone or version bump may only cite a Tier 1 (LOO) number,
and that number must trace to a script, not a manually written table.

## 3. Running a Canonical LOO

```powershell
Set-Location D:\Swaragam\scripts
.\my_virtual_env_swarag\Scripts\Activate.ps1
python sandbox_loo_v131_canonical.py
```

`sandbox_loo_v131_canonical.py` is the permanent ground-truth rerun script
(added commit `b1a1ac9`). Use it, not a new ad-hoc script, unless the
production config itself changes in a way it doesn't cover.

Preconditions:
- Confirm AGG_FOLDER matches the latest aggregation run.
- Confirm all constants (ALPHA, N_BINS, MIN_STABLE_FRAMES, fusion weights)
  match production `recognize_raga_v12.py` exactly.

## 4. Logging a Run (mandatory format)

Every LOO run logged in datasets.md Test Results Log must include:
1. Date, script name, model/aggregation run ID.
2. Full per-raga table: Raga | Clips | Correct | Wrong | Unknown | Acc (decided).
3. **A TOTAL row whose C/W/U columns are the sum of the per-raga columns —
   verify this arithmetic before committing, not after.** The 67.4% "Run B"
   table (2026-03-31, believed canonical for over three months) was
   discovered fabricated on 2026-07-10 specifically because its rows summed
   to 34/13/23, not the stated 29/14/27. It had been driving a real
   architectural decision (the Bhairavi override, ADR-006) the entire time.
4. Config used: fusion weights, any per-raga overrides, margin thresholds.
5. Sink analysis: which raga(s) absorbed the wrongs.

## 5. Canonical Baseline Rule

At any point in time there is exactly **one** canonical LOO number.
- Current canonical: **64.1% decided (25c/14w/31u), v1.3.2**, uniform
  0.8/0.2, no per-raga overrides. `sandbox_loo_v131_canonical.py`,
  2026-07-11.
- Prior canonical (retired): 67.4%, fabricated, never a real run — do not
  cite.
- Prior canonical (superseded): 60.5%, v1.3.1 with Bhairavi 0.5/0.5
  override — confirmed real but confirmed worse than uniform weighting.
- When a new canonical run is logged, update architecture.md,
  PROJECT_STATUS.md, and the Dossier in the same session. A canonical
  number correct in one file and stale in another is worse than not having
  one — this exact failure mode recurred twice (2026-06-24 and 2026-07-10
  audits) on the same project.

## 6. When to Re-run vs. When to Reconcile

- **Numbers merely disagree across files, but a script-verified run log
  exists somewhere**: reconcile by pointing every file at that run.
- **No script-verified run log exists, or an existing table fails the
  row-sum check in Section 4**: re-run. Do not hand-edit counts to match a
  percentage — reconstructing "plausible" numbers is how the 67.4% table
  happened in the first place (L-041).

## 7. Diagnostic Sub-Protocols (not full LOO)

- **Ablation**: disable one feature channel and compare margins (L-025).
- **Discrimination ratio**: self-similarity / mean-other-similarity, used
  for dyad ALPHA tuning. Target >1.5x useful, >2x strong (L-026).
- **Weight sweep**: fixed dataset, vary fusion weight, compare C/W/U
  across configs (L-018, L-045).

These are sandbox diagnostics. Their output informs a decision; it is never
itself logged as a canonical accuracy number — a lesson learned twice now.

## 7a. Evaluating a Targeted Fix (fix aimed at one specific raga/failure mode)

When a change is meant to fix a specific raga (e.g. BUG-015's Abhogi
problem), the topline decided-accuracy delta is NOT the metric that
answers "did the fix work." Check the target raga's own per-raga row
first, always:

- Target raga's C/W/U unchanged across the tested range -> the approach
  has no effect on the thing it was built for, regardless of what the
  topline number says (2026-07-11: `sandbox_abhogi_ratio.py` reported
  "+1.0% IMPROVEMENT" while Abhogi itself was byte-identical at every
  tested weight — see L-050, BUG-015).
- Always check EVERY raga's row, not just the target and the topline —
  a positive topline can hide a regression in an unrelated raga (same
  run: Mohanam regressed 100%->50% while contributing to a "positive"
  topline delta).
- Do not trust a script's own auto-generated verdict ("IMPROVEMENT" /
  "REGRESSION") if it only checks the topline number. Read the per-raga
  breakdown yourself before acting on the recommendation.

## 7b. Validating a New or Modified LOO Script

Any custom LOO implementation (not `sandbox_loo_v131_canonical.py` itself)
must be validated before its output is trusted, every time it's written
or changed:

1. Run it with the exact production config (uniform weights, no overrides).
2. Compare its baseline C/W/U against `sandbox_loo_v131_canonical.py`'s
   on the same config.
3. If they don't match exactly, the custom script has a fold-exclusion
   bug — do not proceed to interpret its sweep/comparison results until
   the mismatch is found and fixed.

This is not optional or occasional. 2026-07-11: `sandbox_abhogi_ratio.py`
had a real bug — dyads weren't excluded from the held-out fold, only PCD
was — that inflated its baseline by 4.2pp (68.3% vs the true 64.1%) and
would have gone uncaught if the two scripts' outputs hadn't happened to
be compared. See BUG-018, L-049.

---

## Maintenance Rule

If production scoring code changes in any way that affects margins
(weights, ALPHA, bin count, guardrails, per-raga overrides added or
removed), the existing canonical LOO number is invalidated immediately —
re-run via `sandbox_loo_v131_canonical.py` (or its successor) before making
any accuracy claim anywhere else in the documentation.
