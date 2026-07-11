# Swarag — Dataset Chronicle

Mandated by the Vision Bible (Section 12). datasets.md logs *test results*
chronologically; this document logs *dataset composition and scoring
config changes* chronologically — a distinct axis. Generated 2026-07-11.

---

## 2026-02-15 — Project Start
- 3 ragas, small clip counts (exact count: [TBD]).
- Mix of instrument-contaminated and clean audio.

## 2026-03-09 — Vocal Isolation Pass
- Saraga vocal stems (8 tracks) + Demucs separation (16 tracks).
- Result: 6 ragas, 50 clips, all vocal-isolated. MAX_DURATION_SEC=360 added.
- **Source**: L-020, L-021.

## 2026-03-10 — Thodi Outlier Removal + External Expansion
- 2 outlier Thodi clips excluded; 5 new Thodi clips added externally.
- Result: 53 clips, 6 ragas.
- **Source**: L-024.

## 2026-03-20 — Guardrail Introduction + Dedup
- 9-raga attempt collapsed LOO 72.0% -> 41.7% (thin-data sink, BUG-011).
- MIN_CLIPS_PER_RAGA=5 guardrail introduced. 13 duplicate files removed.
- Result: 6 ragas modeled, 61 clips.
- **Source**: L-036, L-037, BUG-011, BUG-012.

## 2026-03-21 — Harikambhoji Contamination Cleanup
- 3/6 Kamboji clips found mislabeled (actually Harikambhoji). Removed.
- Kamboji dropped to 3 clips, below guardrail.
- LOO dropped 72% -> 58.8% as a direct, honest consequence (L-041).
- Result: 5 ragas modeled, 55 clips.
- **Source**: L-040, L-041, BUG-013.

## 2026-03-31 — Abhogi + Saveri Activation
- 5 Abhogi + 5 Saveri varnams (already-downloaded Zenodo zip) extracted,
  pushing both past the guardrail. Fusion weight changed 0.7/0.3 -> 0.8/0.2.
- Result: 7 ragas modeled, 70 clips — this composition has not changed
  since; every subsequent entry below is a scoring-config or documentation
  change on top of the same 70 clips.
- **Source**: L-045.

## 2026-04-01 — Absent-Swara Sandbox (no composition change)
- Sandbox evaluation only, testing absent-swara penalty. Rejected (L-046).
- **Source**: L-046.

## 2026-06-24 — First Baseline Reconciliation Audit (no composition change)
- Documentation audit resolved three competing LOO numbers (64.9%, 67.4%,
  60.5%) — reconciliation later found to be itself unverified (see below).
- **Source**: datasets.md, session_summary_20260624.md.

## 2026-07-10 — Documentation Consistency Pass #1 (no composition change)
- Fixed stale weight line in docs/ARCHITECTURE.md, a Run A arithmetic
  typo, and two stale cross-references. Flagged (not fixed) an internal
  inconsistency in the "canonical" 67.4% Run B table.
- Created first drafts of this chronicle, feature-registry.md, adr.md,
  evaluation-protocol.md. **These were never merged into the repo** — the
  session ended with a patch file that was not applied.
- **Source**: this project's session history.

## 2026-07-11 — Fabrication Discovered; Bhairavi Override Retired
- `sandbox_loo_v131_canonical.py` added as the first script-verified,
  checked-in LOO runner (previously all "canonical" tables were hand-typed).
- Rerun revealed the 67.4% Run B table was fabricated: its per-raga rows
  summed to 34c/13w/23u, not the stated 29c/14w/27u. The real config it
  claimed to describe (Bhairavi 0.5/0.5 override) actually scores 60.5%
  overall, with Bhairavi itself at 0% decided (9 wrongs).
- Bhairavi override retired (ADR-013). All ragas now use uniform 0.8/0.2.
- New canonical: **64.1% decided (25c/14w/31u)**, no composition change —
  this is a scoring-config change only, same 70 clips as 2026-03-31.
- docs/ARCHITECTURE.md found with a corrupted header (editor placeholder
  text `// ... existing code ...` committed literally, wrapping a third,
  never-referenced 72.3% variant of the same retired table). Fixed.
- PROJECT_STATUS.md found fully un-migrated from v1.3.1 language (5 stale
  Bhairavi-override references). Fixed.
- Vision Bible artifacts (this chronicle + 3 others) actually merged this
  time.
- **Source**: commits b1a1ac9, 87902ca, 21da815; this session.

---

## Current State (as of last entry above)

- 7 ragas modeled: Thodi(11), Bhairavi(11), Kalyani(14), Saveri(8),
  Shankarabharanam(9), Mohanam(10), Abhogi(7) — 70 clips total, unchanged
  since 2026-03-31.
- Scoring config (not composition) changed 2026-07-11: no per-raga
  overrides remain; uniform 0.8/0.2 global weight.
- 3 ragas staged below guardrail: Kamboji(3), Madhyamavati(2), Hamsadhvani(1).

## Known Gaps in This Chronicle

- Exact clip count/composition at 2026-02-15 project start: [TBD].
- Per-clip provenance is in datasets.md's seed table by design, not
  duplicated here — this document tracks *when composition or scoring
  config changed and why*.

## Maintenance Rule

Any change to which clips are in aggregation, OR any change to a scoring
config that a prior canonical accuracy number depended on (weights, ALPHA,
overrides), gets an entry here — even if clip count is unchanged, as the
2026-07-11 entry demonstrates. A scoring-only change can move accuracy by
+3.6pp just as much as a data change can.
