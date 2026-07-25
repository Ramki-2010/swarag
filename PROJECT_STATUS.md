# Swarag -- Project Status

## Current Version
Swarag v1.3.2 (7 Ragas -- Bhairavi 0.5/0.5 override retired, uniform 0.8/0.2 for all ragas)

---

## Mission

Swarag's primary goal is a usable, explainable Carnatic raga recognizer.

Research into representation, temporal reasoning, phrase modelling, gamakas,
and computational music exists to improve that recognizer and deepen
understanding of Carnatic music -- research is a means, not an end. When
priorities compete, recognition takes precedence, unless a research experiment
is the shortest path to removing a recognition bottleneck (e.g. Q-001 gates
every phrase-based accuracy fix).

---

## What Is Stable

- 72-bin PCD + IDF x Variance weighted dot-product scoring
- Directional dyads with ALPHA=0.01 Laplace smoothing
- PCD_WEIGHT=0.8, DYAD_WEIGHT=0.2, applied uniformly to all ragas
  (Bhairavi 0.5/0.5 override tested and retired in v1.3.2 -- see ADR-006/ADR-013)
- MIN_CLIPS_PER_RAGA=5 guardrail
- Vocal isolation mandatory (Saraga stems + Demucs)
- Per-file timeout in batch evaluation (360s)

### Key Constants
| Constant | Value |
|---|---|
| N_BINS | 72 |
| ALPHA | 0.01 |
| PCD_WEIGHT | 0.8 (global) |
| DYAD_WEIGHT | 0.2 (global) |
| PER_RAGA_WEIGHTS | none (retired) |
| MIN_CLIPS_PER_RAGA | 5 |
| MARGIN_STRICT | 0.003 |
| MIN_MARGIN_FINAL | 0.001 |

### Current Accuracy (LOO, 7 ragas, 70 clips, sandbox_loo_v131_canonical.py)
| Raga | Clips | LOO Acc |
|---|---|---|
| Mohanam | 10 | 100% (1c/0w/9u -- decides rarely) |
| Saveri | 8 | 88% |
| Shankarabharanam | 9 | 80% |
| Kalyani | 14 | 75% |
| Thodi | 11 | 71% |
| Abhogi | 7 | 33% |
| Bhairavi | 11 | 14% (override retired -- cause unproven: representation vs data) |
| **Overall** | **70** | **64.1% decided** |

### What Changed from v1.3.1
- Bhairavi 0.5/0.5 per-raga override retired: canonical rerun confirmed
  it was counter-productive (0% decided for Bhairavi, 9 wrongs)
- All ragas now use uniform 0.8/0.2 global weight
- Prior "67.4%" figure retired: found fabricated on audit -- its per-raga
  rows never summed to its own total. Real config it claimed to describe
  (Bhairavi override) actually scores 60.5% overall.
- New canonical: 64.1% decided (25c/14w/31u)

---

## Known Limitations

- Abhogi: 33% LOO -- STRUCTURAL problem (janya of Kalyani, PCD is strict subset)
  Weight overrides (L-044) and energy-ratio scoring (L-050) both tested,
  both rejected -- confirmed no signal, not just weak. Next: phrase n-grams.
- Bhairavi: 14% LOO -- override retired. Cause UNPROVEN: whether the limit is
  representation (feature) or data (clip diversity) is untested. "More clips"
  is a hypothesis, not a confirmed diagnosis.
- Mohanam: 100% decided but 9/10 UNKNOWN -- model barely commits. Likely a
  data-diversity limit, but unproven.
- Kamboji: excluded (3 real clips, Saraga exhausted -- 0 new sources)
- Saveri is the new sink (6/14 wrongs) -- was Kalyani pre-retirement
- No OOD score floor

---

## Priority Plan

1. Diagnose Bhairavi (weakest raga at 14%). The weight hack is disproven
   (override retired), but data-vs-representation as the root cause is still
   UNPROVEN. Adding diverse clips is the first test, not a confirmed fix.
2. **Abhogi -- Q-001 feasibility spike FIRST** (ARCHITECTURAL): every
   scoring-time approach is rejected (overrides L-044, absent-swara L-046,
   energy-ratio L-050). Phrase-level sequence detection (M2-D2-M2 vs Pa-D2-N3)
   is the only untried category -- but it is BLOCKED by Q-001: prove the
   representation can be quantized into swara sequences despite gamaka smearing
   before building any phrase model (Q-002). Do not skip the gate.
3. Add 4-6 diverse Mohanam clips -- 100% decided but 9/10 UNKNOWN
4. Add 5-7 real Kamboji clips (YouTube/Rasikas -- Saraga has 0 new sources)
5. Do NOT add more new ragas until weak ones > 60%
6. Re-baseline the accuracy target against 64.1% (the 72-78% target was
   calibrated against the fabricated 67.4% figure)

### Proven Dead Ends (do not re-attempt)
- Abhogi per-raga weight overrides (0% at all weights -- L-044)
- Abhogi absent-swara penalty -- BOTH variants failed (L-046, 2026-04-01):
  * Data-driven: self-harm on 5/7 Abhogi clips
  * Musicological: gamakas leak 6-19% Pa energy, binary detection fails
- Abhogi energy-ratio scoring -- REJECTED 2026-07-11 (L-050, BUG-015):
  Pa/N3 separation ratio 1.01x (none). Abhogi result identical at every
  tested ratio_weight 0.05-0.40. Do not re-attempt without a fundamentally
  different feature (phrase-level, not swara-energy-level).
- Mohanam dyad overrides (no improvement -- data problem)
- Genericness penalty from model PCD (L-016)
- Escalation / dyad-heavy re-scoring (L-017)

---

## Research Gates (Knowledge State)

Work is tracked by what is *known*, not by feature lists. Settled questions
live in ADRs; only open unknowns are gated here. A gate is a diagnostic, not
a promise -- see the Promotion Rule in workflow.md.

**Settled:** 72-bin PCD (ADR-002), IDF x Variance (ADR-003), ALPHA=0.01
(ADR-004) -- proven. Per-raga overrides (ADR-013), absent-swara penalty
(ADR-008), energy-ratio scoring (ADR-014) -- rejected.

### Active Gates

| Gate  | Question | Status | Next action |
|-------|----------|--------|-------------|
| Q-001 | Can the current pitch representation be reliably quantized into swara sequences despite gamaka smearing? | Active | Feasibility spike (cheap, decisive) |
| Q-002 | If Q-001 passes, do phrase n-grams improve Abhogi / sibling-raga discrimination? | Blocked by Q-001 | Phrase-model experiment |
| Q-003 | Is Bhairavi (14%, worst raga) limited by representation or by dataset diversity? | Unknown, independent of Q-001 | Isolate: add diverse clips vs feature analysis |
| Q-004 | What is the legally permissible reproducibility artifact for Saraga-derived data -- audio, or derived features only? | Pending | Review Saraga license, then record ADR (gates ADR-016's form) |

Rule: do not promote an UNKNOWN to a cause ("data problem", "solved") without
an experiment that isolates it. Rejecting scoring-time features proves only
that scoring-time is exhausted -- nothing about what the real fix is.

---

## Philosophy

Honest baselines over inflated numbers. Clean data over more data.
Do not state as proven what has only been assumed.
