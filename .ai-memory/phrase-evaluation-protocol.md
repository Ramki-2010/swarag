# Swarag — Phrase Evaluation Protocol v1.0

Canonical, long-lived methodology for evaluating phrase-level (order-dependent,
sequence, n-gram, motif) hypotheses in Swarag. Consolidates methodology that
emerged across Q-001A, Q-001B planning, and the Q-001B Feasibility Review —
not a new research philosophy, a formalization of one already in use.

Companion documents, not duplicated here:
- `.ai-memory/evaluation-protocol.md` — general LOO/accuracy methodology
  (applies to every gate below; this document adds the phrase-specific layer
  on top of it, it does not replace it).
- `.ai-memory/workflow.md` — the Promotion Rule and Fix Priority framework
  (Section 3b, "Research vs Recognition") that phrase gates operate inside.
- `PROJECT_STATUS.md` — the live Research Gates table (which gates exist,
  their status). This document defines *how* a gate is run; that table
  defines *which* gates exist.

Source tags used throughout: **[Repo]** = derived from logged repository
evidence · **[Lit]** = MIR/statistics literature · **[Protocol]** = new
formalization, justified below · **[Judgment]** = expert judgment, flagged
as such.

---

## 1. Purpose

Defines the mandatory methodology for designing, running, validating, and
promoting or rejecting any phrase-level hypothesis, for any raga, present or
future. Governs the discovery-to-promotion pipeline for order-dependent
features specifically — scoring-time swara-energy features (weight overrides,
absent-swara penalties, energy ratios) remain governed by the Fix Priority
framework in `workflow.md`, not this document.

**[Protocol]** This document exists because the same three corrections —
mean-vs-threshold verdict errors, LOO leakage through aggregate model
components, and composition/performer confounds — each had to be discovered
once, ad hoc, during Q-001A/Q-001B planning. The purpose is to make each of
them a standing requirement instead of a lesson that has to be relearned per
raga.

Q-001B is the first *instance* this protocol governs, not its subject. This
document does not redesign Q-001B, does not resolve the current dataset's
limitations, and does not propose new experiments — see Section 10.

---

## 2. Guiding Philosophy

Each principle below is a restatement of an existing Swarag rule, not a new
one — source given inline.

- **Smallest falsifiable experiment first.** **[Repo]** `workflow.md` §3b;
  Bible §7's Hypothesis → Sandbox → LOO → Error analysis → Documentation →
  Production lifecycle.
- **Evidence before architecture.** **[Repo]** The Promotion Rule
  (`workflow.md`): *Observation → Hypothesis → Experiment → Evidence →
  ADR/Lesson → Production.* Discussion is not evidence; agreement is not
  evidence.
- **Sandbox before production.** **[Repo]** `workflow.md` §5; no phrase
  feature touches a production script before a PASS verdict (Section 8).
- **Deterministic DSP first, ML only over validated features.** **[Repo]**
  Vision Bible §10; Architectural Vision, "Machine Learning" section.
- **Reproducibility.** **[Repo]** A canonical number must trace to a
  checked-in script, never a hand-typed table — the specific, costly lesson
  of the fabricated 67.4% baseline (Dossier §11).
- **Explainability is a design requirement, not optional.** **[Repo]** Bible
  §3.
- **Statistical promotion only.** **[Repo]** No hypothesis is promoted on a
  topline number or discussion alone (Promotion Rule; L-050's topline-hides-
  target-miss finding).
- **Research serves the recognizer.** **[Repo]** `workflow.md` §3b: research
  is prioritized only when it is the shortest path to removing a recognition
  bottleneck.
- **UNKNOWN over wrong certainty.** **[Repo]** Dossier §7, key decisions.
- **Failed experiments are permanent knowledge.** **[Repo]** Bible §3;
  Architectural Vision, "Core Philosophy."

---

## 3. Research Gates

**[Repo, generalized]** A gate is a single, pre-registered scientific
question, tracked by knowledge state (per `PROJECT_STATUS.md`'s existing
convention: ANSWERED / ACTIVE / BLOCKED / PENDING), not by feature or
deliverable. Q-001A and Q-001B are the working template; this section
generalizes their shape.

**One gate, one question.** A gate that would answer two questions at once
must be split before pre-registration. (Q-001A → representation sufficiency;
Q-001B → phrase discriminatory power — kept separate rather than merged
precisely because they can fail independently and a bundled verdict would
not say which part failed.)

Every gate's pre-registration document must specify, before implementation
begins:

| Field | Requirement |
|---|---|
| **Objective** | One sentence, one question, falsifiable. |
| **Required evidence** | What data/experiment resolves it — named, not vague. |
| **Acceptable outcomes** | PASS / FAIL / INCONCLUSIVE, each with a stated meaning for *this* gate (Section 8 gives the generic definitions; a gate may narrow them, never widen them). |
| **Promotion criteria** | Pre-registered, quantitative, met in full or not at all (Section 7). |
| **Failure criteria** | Pre-registered, symmetric to promotion criteria — not merely "promotion criteria not met." |
| **Inconclusive criteria** | Stated *up front* as a legitimate, anticipated outcome, not discovered after the fact when results are ambiguous. |

**[Repo]** Rule, verbatim in spirit from `PROJECT_STATUS.md`: *do not promote
an UNKNOWN to a cause without an experiment that isolates it.* Rejecting one
candidate mechanism proves that mechanism is exhausted — it proves nothing
about what the true cause is. (The Abhogi swara-energy-level category's
closure, after three independent rejected mechanisms — L-044, L-046, L-050 —
is the template for when a *category*, not just one method, may be
considered closed.)

A gate's dependency chain (e.g., Q-001A unblocking Q-001B) must be stated
explicitly in the gate's pre-registration and reflected in
`PROJECT_STATUS.md`'s status column — a gate is BLOCKED until its dependency
is ANSWERED, never run speculatively ahead of it.

---

## 4. Dataset Requirements

**[Protocol, literature- and repo-backed]** This section is the direct
formalization of the composition confound surfaced during Q-001B planning.

- **Composition independence.** Every clip used in a phrase gate must carry
  a composition/piece identifier. No fold may hold out a clip while a clip
  of the *same composition* remains in that fold's training set. This is
  Swarag's version of the MIR **artist/album filter** — the established
  practice of preventing same-artist or same-recording material from
  appearing on both sides of a train/test split, because its absence is
  documented to inflate performance estimates independent of the underlying
  musical signal. **[Lit]** *(Pampalk et al. 2005; Flexer & Schnitzer 2010,
  "artist"/"album" effects.)*
- **Performer independence.** A milder version of the same problem: the same
  composition sung by different performers still shares its melodic
  backbone. Performer diversity alone does not satisfy composition
  independence — it reduces, but does not remove, the confound.
- **Metadata requirements.** Every clip's provenance record must include:
  composition ID, performer ID, source dataset, and isolation method
  (Demucs / stem / clean). **[Repo, gap identified]** `datasets.md`'s current
  per-clip source table has no composition-ID field — this is a real,
  standing gap this protocol requires closed incrementally, starting with
  any clip entering a phrase gate.
- **Effective sample size.** Every gate reports both the raw clip count *and*
  the count of independent compositional units per class. A gate's
  statistical "n," for power purposes, is the compositional-unit count, not
  the clip count. **[Repo]** These numbers can diverge sharply — a
  7-clip class can collapse to as few as 3 independent units once grouped by
  composition.
- **Confuser identification.** Before any discrimination gate is
  pre-registered, its confuser class must be read empirically from current
  confusion-matrix evidence, not assumed or designed in. **[Repo]** This
  generalizes Q-001B_Research_Plan.md's own rule verbatim: *"read from
  confusion_matrix_audit.py before running (do not assume — pull it)."*
- **Dataset quality is not certified by the clip-count guardrail alone.**
  `MIN_CLIPS_PER_RAGA` (architecture.md) governs whether a raga is modeled at
  all. It does not certify adequacy for a *phrase* gate specifically — a
  raga can clear the clip-count guardrail while containing only one or two
  independent compositions, which this protocol treats as insufficient
  regardless of clip count.

---

## 5. Experimental Requirements

- **Pre-registration is mandatory**, not optional or occasional: hypothesis,
  null hypothesis, dataset, metric, and all three outcome criteria (Section
  3) written before implementation begins. **[Repo]** Matches
  `Q-001B_Research_Plan.md`'s structure; this protocol makes that structure
  mandatory for every future gate, not a one-off best practice.
- **Train-only feature discovery.** Any data-discovered feature (n-grams,
  motifs, thresholds) must be discovered inside each training fold only,
  never on the full dataset and then evaluated on it. **[Repo]** This is the
  L-049 leak (BUG-018) — a fold-exclusion bug that inflated one sandbox's
  baseline by 4.2 points before being caught by cross-checking against the
  canonical script. Explicitly forbidden for any future phrase feature.
- **Leakage validation.** Before any custom evaluation script's output is
  trusted, its baseline must be run against the canonical LOO script on
  identical config. A mismatch blocks interpretation of the rest of that
  script's output until resolved. **[Repo]** `evaluation-protocol.md` §7b,
  generalized from a one-off check to a standing requirement for phrase
  scripts specifically.
- **Grouped validation where appropriate.** Composition-grouped (or
  performer-grouped, if composition identity is unavailable) fold
  construction is mandatory whenever Section 4 identifies shared-composition
  clips in either the target or the confuser class. Leave-one-*clip*-out is
  not an acceptable substitute for leave-one-*composition*-out once sharing
  is known to exist.
- **Statistical reporting.** Every gate reports paired per-fold deltas, not
  only a topline mean. **[Repo]** Generalizes L-050 (a positive topline
  delta can hide that the target metric itself never moved) and
  `evaluation-protocol.md` §7a (always check the specific target row, every
  time, not only the aggregate).
- **Reproducibility.** Every gate's implementation is a checked-in
  `sandbox_*.py` script, never a manual calculation or unsaved notebook run.
  Results are logged in the mandatory format from `evaluation-protocol.md`
  §4, including the row-sum-against-TOTAL check *before* committing — the
  specific check that would have caught the 67.4% fabrication had it existed
  at the time.

---

## 6. Null Model Policy

**[Protocol, literature-informed]** New formalization — built from
Q-001B_Research_Plan.md's own nearest-centroid/permutation design, standard
sequence-significance practice, and the composition-confound finding.

- **Acceptable surrogate method.** Order-scrambled swara sequences —
  shuffled within a clip while preserving that clip's own unigram and bigram
  statistics — as the null model for "does higher-order structure carry
  information at all." This test requires no cross-clip independence, so it
  is usable even at very low compositional-unit counts, making it the
  cheapest first gate before committing to a full discrimination experiment.
- **Validation requirement.** A surrogate generator must preserve exactly the
  lower-order statistics it claims to control for. A surrogate that also
  disturbs unigram or bigram frequencies conflates "any structure differs"
  with "the specific higher-order structure under test differs" — an
  invalid test.
- **Positive control.** Run the existing PCD+dyad baseline itself through
  the same evaluation pipeline as a known-real effect. If the pipeline
  cannot detect a signal already known to exist, its output on an unknown
  hypothesis cannot be trusted either.
- **Negative control.** Compare composition-matched clips from the *same*
  class against each other. This should show near-zero apparent
  discrimination; a positive result here is direct, operational evidence
  that a gate's apparent signal is composition-specific rather than
  raga-general — the concrete test for the confound described in Section 4.
- **Identity control.** A clip (or a composition-mate) should score at or
  near ceiling against itself. A sanity check that the pipeline is not
  systematically too noisy to detect a real effect.
- **Reporting requirement.** Any gate using n-gram or motif discovery
  reports the real-vs-surrogate result *and* the negative-control result
  together, before any promotion claim is made. Neither alone is sufficient.

---

## 7. Statistical Standards

- **Effect sizes are reported alongside significance, always.** **[Repo]**
  Matches Q-001A's own reporting practice (n=7, permutation p=0.39, d=0.38).
- **Paired permutation or sign testing on per-fold deltas is the default
  significance test**, not a mean-vs-threshold binary. **[Repo]**
  `Q-001B_Research_Plan.md`, citing L-052.
- **Confidence is tagged per claim** — verified / inferred / uncertain —
  consistent with the project's existing proven/rejected/unknown
  knowledge-state taxonomy.
- **Promotion bars are three-part, minimum:** magnitude (a pre-registered
  effect-size floor), significance (a pre-registered p-value bar), and
  consistency (the effect replicates across a majority of folds, not one
  fold's noise). **[Repo]** The specific thresholds are gate-specific;
  Q-001B's own bar — Δ ≥ +0.10, p < 0.05, cross-fold trigram consistency —
  is the template for the *shape* a bar must take. A significance test
  alone, without an effect-size floor and a consistency check, does not
  satisfy this protocol.
- **A null result under a design with a known inflationary bias is treated
  as a *stronger* null, not a weaker one.** **[Protocol]** If a design biased
  toward finding a false positive (e.g., uncontrolled composition sharing)
  still fails to reach significance, that failure is more, not less,
  informative than a null under a clean design. This asymmetry does not run
  the other direction: a *positive* result under an uncontrolled design is
  not trustworthy regardless of magnitude.
- **INCONCLUSIVE is not a failure.** **[Repo]** Pre-registered as a common,
  acceptable outcome at low compositional-unit counts (`Q-001B_Research_Plan.md`'s
  own "Known Risk — Power" section). It routes to a specific, named data or
  design gap — never to lowering the promotion bar to force a verdict.

---

## 8. Promotion Policy

- **PASS** — every pre-registered promotion criterion met, on a
  leakage-controlled and (where Section 4 requires it) composition-grouped
  design. The gate is marked ANSWERED in `PROJECT_STATUS.md`; an ADR is
  written; the finding may unblock a dependent gate or feed a scoring-time
  change proposal — which still passes through the Fix Priority framework
  (`workflow.md`) before touching production. A PASS on an uncontrolled
  design is not a PASS; it is INCONCLUSIVE pending a controlled rerun.
- **FAIL** — every pre-registered failure criterion met. Marked ANSWERED (a
  negative answer is still an answer) and added to the Proven Dead Ends
  list. **[Repo]** Per `workflow.md` §3b, a FAIL closes the specific
  mechanism tested, not the entire research direction — unless every
  mechanism in that category has now failed independently (the Abhogi
  swara-energy-level category's closure after L-044/L-046/L-050 is the
  precedent for when a category, not just a method, is closed).
- **INCONCLUSIVE** — neither bar met, most commonly a pre-anticipated power
  shortfall. The gate stays ACTIVE with a specific, named gap stated (e.g.,
  "needs N additional independent compositions for raga X"), never a vague
  "needs more data."
- No hypothesis reaches production without a PASS on a leakage-controlled
  design. This restates and locks the existing Promotion Rule specifically
  for phrase-level features.

---

## 9. Documentation Policy

After every completed phrase gate, update, in the same session (per
`workflow.md` §9's checklist, phrase-specific additions marked **[new]**):

- `PROJECT_STATUS.md` — gate status and next action.
- `lessons.md` — at least one L-NNN, in the actionable form
  `workflow.md` §8 already requires (context, rule, impact — not a
  restated observation).
- `bugs.md` — if the gate surfaced a leakage or tooling defect, as Q-001B
  planning did with BUG-018.
- `datasets.md` — the run logged in the mandatory format, TOTAL row checked
  against its own per-class sum before committing.
- **[new]** `datasets.md`'s composition-ID field — updated for any clip
  newly classified as part of this gate's dataset audit.
- `adr.md` — for any PASS or FAIL, the decision and its evidence trail.
- This document — only when the *methodology itself* changes (Section 10),
  never for an individual gate's outcome.

---

## 10. Scope and Limitations

**Designed to answer:** how any phrase/sequence-order hypothesis, for any
raga, is designed, validated, and promoted or rejected.

**Not designed to answer:** whether a specific hypothesis is true (that is
what an individual gate, such as Q-001B, determines); whether phrase
features are worth pursuing ahead of other feature categories (that is Fix
Priority territory in `workflow.md`); dataset collection logistics (that is
Dataset Chronicle territory). This document does not resolve Q-001B's
current dataset limitations and does not propose new experiments.

**Assumptions:** relies on `datasets.md` provenance being accurate and
complete enough to establish composition-sharing; relies on the confusion
matrix being run fresh before each gate, not assumed from memory.

**Known limitation:** composition metadata does not yet exist for every
historical clip — only externally-sourced clips (e.g., Zenodo collections)
currently carry documented composition identity. Until that gap is closed
project-wide, Section 4's composition-independence requirement applies only
where composition identity is actually known; a gate must state this
explicitly as a limitation rather than silently assuming independence for
undocumented clips.

**Conditions for revising this protocol:** a new confound class is
discovered that Sections 4–7 don't address (the way the composition
confound extended, without replacing, the leakage discipline already
encoded here); a gate run under this protocol produces a promotion decision
later found wrong (triggers a protocol post-mortem, not only a lesson
entry); established MIR or statistical practice materially changes.

---

## 11. Future Compatibility

Sections 2–9 reference no raga as a precondition; Abhogi appears only as an
illustrative example in Sections 4 and 6.

Any raga pair sharing a parent/janya or scale-overlap relationship — of
which Abhogi/Kalyani is one instance of a general class, not a special case
— is a candidate for this protocol's confuser-identification and
composition-independence requirements. Ragas not yet past the modeling
guardrail (Kamboji, Madhyamavati, Hamsadhvani) are subject to Section 4's
dataset requirements the same way Abhogi and Kalyani were, before any
future phrase gate involving them is pre-registered.
