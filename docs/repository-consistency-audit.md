# Repository Consistency Audit

**Date.** 2026-09-01 · **Commit.** `0bf39cb` · **Scope.** Repository-wide, read-only.

**Nothing was modified, renamed, deleted, committed, or pushed.** No unresolved
question was decided — the naming question in particular is presented as
alternatives, not a recommendation acted upon.

Severity scale: `CRITICAL` · `HIGH` · `MEDIUM` · `LOW` · `INFORMATIONAL`

---

## Resolution status

**Added after the audit. The findings below are unaltered.** This audit is a
dated snapshot taken at `0bf39cb`; some findings have since been closed.

| Finding | Status |
|---|---|
| C-1 | **RESOLVED** in `416cc44` -- `README.md:71` corrected |
| C-2 | **RESOLVED** in `416cc44` -- `docs/ARCHITECTURE.md:36` corrected; now agrees with its own `:185-186` |
| D-1 | **RESOLVED** in `416cc44` -- README run commands use the venv interpreter and `scripts/` paths |
| D-2 | **RESOLVED** in `416cc44` -- `DEVELOPMENT.md` commands corrected; `AGG_FOLDER` behaviour documented |
| I-1 | **RESOLVED** in `416cc44` -- `PROJECT_STATUS.md` declared canonical; README and `.ai-memory` point to it |
| B-1 | **PARTIALLY RESOLVED** in `416cc44` -- naming architecture established (`CLAUDE.md` 1a). The prose rename of ~84 occurrences remains deferred |

All other findings were open as of `416cc44`. **This table is not maintained
continuously** -- check `git log` for anything closed since. Section L's
disposition lists reflect the audit as taken, not current state.

---

## A. Executive summary

30 finding entries covering 29 distinct issues (J-1 cross-lists C-3). **No fabricated numbers and no silently-drifted results were
found** — the numerical record is in good order, which is the outcome that
matters most for a research repository.

The problems are of three kinds:

1. **One unresolved decision** — the project is named `Swarag` throughout the
   repository, not `Swaragam`. This blocks the README redesign and is yours to
   settle (§B, §L4).
2. **One technical claim that is wrong in two documents** — the IDF×Variance
   weighting is described as applying to dyads. It does not. `docs/ARCHITECTURE.md`
   contradicts *itself* on this point, and `README.md` inherited the wrong half
   (§C-1, §C-2).
3. **Documented workflows that no longer match the repository** — commands that
   would fail as written, a constants policy superseded by a locked ADR, and a
   README that presents a finished engine rather than a research project with
   four open gates (§D, §E, §J).

**Verified sound:** the canonical accuracy table, all confidence thresholds, the
virtual-environment references, and the Q-003 phase record.

---

## B. Naming inconsistencies

### B-1 · CRITICAL (decision required — not decided here)

| | |
|---|---|
| **Location** | Repository-wide |
| **Observed** | `Swarag` used as the project name in 87 places; `Swaragam` appears 174 times but **exclusively as a filesystem path** (`D:\Swaragam\`, `H:\Swaragam\`) and **never as a project name** |
| **Expected/canonical** | **Undetermined.** No canonical decision exists in the repository |
| **Evidence** | `CLAUDE.md:1` "CLAUDE.md — Swarag Research & Repository Governance" · `CONTRIBUTING.md:1,3,5` · `DEVELOPMENT.md:1,3` · `README.md:1` · git remote `https://github.com/Ramki-2010/swarag.git` · venv `my_virtual_env_swarag` · `requirements.txt:1` |
| **Confidence** | High — exhaustive `git grep` over tracked files |
| **Files affected** | `README.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `adr.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, `requirements.txt`, `.ai/agent_spec.md`, `.ai-memory/*` (8 files), plus — under the fullest option — the GitHub repo slug and the venv directory name |

**Separation by identifier class, as requested:**

| Class | Current value | Changing it costs |
|---|---|---|
| Project / display name | `Swarag` | Documentation edits only |
| GitHub repository slug | `swarag` | Repo rename; old clone URLs redirect but every documented clone command changes |
| Filesystem paths | `D:\Swaragam\`, `H:\Swaragam\` | **Already "Swaragam".** Local only, not portable, appears in ~174 doc references |
| Python package/module identifiers | *none* — flat scripts, no package | Zero cost; nothing to rename |
| Virtual environment | `my_virtual_env_swarag` | Recreating the env; `CLAUDE.md` §9 forbids creating another without authorisation |
| Documentation references | `Swarag` | The 87 occurrences above |

**Naming architectures — alternatives, no recommendation acted on:**

- **Option 1 — Display/slug split.** Display name `Swaragam`; repo slug, venv and
  code identifiers stay `swarag`. Precedent: Kubernetes/`k8s`, PostgreSQL/`psql`.
  *Cost:* documentation only. *Risk:* two names in circulation, which must be
  stated once in the README so it reads as intentional rather than as drift.
- **Option 2 — Full rename to `Swaragam`.** Every document, the repo slug, and
  the venv. *Cost:* highest. *Risk:* touches `CLAUDE.md` §9's venv rule and
  invalidates documented clone commands.
- **Option 3 — Standardise on `Swarag`.** Zero changes; contradicts the stated
  intent to use `Swaragam`.
- **Option 4 — Rename filesystem paths to match the chosen name.** Independent of
  1–3; affects ~174 documentation references and every absolute path in
  `.ai-memory/`. Highest churn, lowest benefit.

### B-2 · INFORMATIONAL

`Swargam` — the spelling explicitly guarded against — occurs **0 times** in
tracked files. The guard is unnecessary but harmless.

---

## C. Technical inconsistencies

### C-1 · HIGH — README misstates where IDF×Variance weighting applies

| | |
|---|---|
| **Location** | `README.md:71` |
| **Observed** | `IDF x Variance weighted dot-product (PCD + Dyads)` |
| **Canonical** | IDF×Variance applies to **PCD only**. The dyad channel uses a raw, unweighted dot product |
| **Evidence** | `recognize_raga_v12.py:210` `pcd_sim = np.dot(pcd_w_arr, model_w)` (weighted) vs `:211-212` `up_sim = np.dot(test_up, model["mean_up"])` (unweighted). `compute_pcd_weights()` at `:159-182` is applied to PCD alone. Independently established by Q-003 Phase 1-C |
| **Confidence** | High — read directly from production source |
| **Resolution** | Correct to `IDF x Variance weighted dot-product (PCD); unweighted dot-product (Dyads)` |
| **Files affected** | `README.md` |

### C-2 · HIGH — `docs/ARCHITECTURE.md` contradicts itself on the same point

| | |
|---|---|
| **Location** | `docs/ARCHITECTURE.md:36` vs `:185-186` |
| **Observed** | `:36` "IDF x Variance weighted dot-product (**PCD + Dyads**)" — wrong. `:185-186` "IDF x Variance weighted dot-product **for PCD**" / "Dot-product similarity for directional dyads" — **correct** |
| **Canonical** | Lines 185-186 |
| **Evidence** | Same source lines as C-1. The two statements sit 149 lines apart in one document |
| **Confidence** | High |
| **Resolution** | Correct `:36` to match `:185-186`. **This is the origin of C-1** — `README.md:71` reproduces `:36` verbatim, so fixing ARCHITECTURE without README leaves the error in circulation |
| **Files affected** | `docs/ARCHITECTURE.md`, `README.md` |

### C-3 · HIGH — `DEVELOPMENT.md` §8 conflicts with ADR-015 (ACTIVE, locked)

| | |
|---|---|
| **Location** | `DEVELOPMENT.md:195` |
| **Observed** | "These must be identical across `aggregate_all_v12.py`, `recognize_raga_v12.py`, and all test scripts" — a duplicate-and-manually-sync policy |
| **Canonical** | ADR-015: scripts **import** shared constants instead of redefining them, making the drift failure mode "structurally impossible" |
| **Evidence** | `adr.md:189-208` (Status: **ACTIVE, locked**); ADR-015 was created precisely because a duplicated constant drifted stale and mislabelled a retired config as canonical (BUG-017) |
| **Confidence** | High |
| **Resolution** | Rewrite §8 to present the constants as a **reference table sourced from `recognize_raga_v12.py`**, with an explicit instruction to import rather than copy |
| **Files affected** | `DEVELOPMENT.md` |

### C-4 · MEDIUM — production declares `MIN_STABLE_FRAMES` twice

| | |
|---|---|
| **Location** | `recognize_raga_v12.py:27` and `aggregate_all_v12.py:16` |
| **Observed** | `MIN_STABLE_FRAMES = 5` in both |
| **Canonical** | Single owner, per ADR-015's principle and the ADR-017 `FEATURE_VERSION` precedent |
| **Evidence** | Both files read directly. Values currently **agree**, so nothing is broken today |
| **Confidence** | High |
| **Resolution** | Have `aggregate_all_v12.py` import from `recognize_raga_v12.py`. **Production change — requires its own authorisation and sandbox validation per ADR-010** |
| **Files affected** | `aggregate_all_v12.py`, `DEVELOPMENT.md` §8 |

### C-5 · MEDIUM — known ADR-015 violation in a committed sandbox

| | |
|---|---|
| **Location** | `scripts/sandbox_q003_phase1c_dyad_channel.py:69` |
| **Observed** | `MIN_STABLE_FRAMES = 5` redeclared although exported by `recognize_raga_v12.py:27` |
| **Canonical** | Import it |
| **Evidence** | Documented in commit `9b1dd6d` and in `PHASE_LOG.md` Phase 1-C limitations |
| **Confidence** | High |
| **Resolution** | **Do not fix.** Preserved deliberately so executed experiment code is not altered retroactively; the value is correct and no Phase 1-C result is affected. Correct sourcing applies to future scripts |
| **Files affected** | none — recorded technical debt |

---

## D. Path inconsistencies

### D-1 · HIGH — README run commands fail as written

| | |
|---|---|
| **Location** | `README.md:131-135` |
| **Observed** | `python extract_pitch_batch_v12.py` (and two more) run from the repository root |
| **Canonical** | Scripts live in `scripts/`; the canonical interpreter is `my_virtual_env_swarag\Scripts\python.exe` |
| **Evidence** | `ls scripts/` confirms location. `CLAUDE.md` §9: "The bare `python` on PATH is a separate install **without numpy** and will fail." `L-070`-class lesson recorded at `.ai-memory/lessons.md:70-77` |
| **Confidence** | High |
| **Resolution** | Show `cd scripts` plus the venv interpreter, or full paths |
| **Files affected** | `README.md` |

### D-2 · HIGH — same defect in `DEVELOPMENT.md`

Locations `DEVELOPMENT.md:109,112,115,118,186,187,188`. Identical observed value,
canonical value, evidence, and resolution as D-1. Confidence High.
**Files affected:** `DEVELOPMENT.md`.

### D-3 · MEDIUM — README repository structure is incomplete

| | |
|---|---|
| **Location** | `README.md:107-121` |
| **Observed** | Lists `scripts/`, `.ai/`, `.ai-memory/`, `docs/` only |
| **Canonical** | Tracked top-level also includes `datasets/`, `notebooks/`, `archive/`, `.githooks/`, and root files `CLAUDE.md`, `PROJECT_STATUS.md`, `adr.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, `LICENSE`, `requirements.txt` |
| **Evidence** | `git ls-files` |
| **Confidence** | High |
| **Resolution** | Complete the listing; update `docs/` description, which now holds `START_HERE.md`, `ARCHITECTURE.md`, `research/Q-003/` |
| **Files affected** | `README.md` |

### D-4 · LOW — two tracked directories are effectively empty

`notebooks/` contains no files; `archive/` contains only `config_backup.yaml`.
Neither is documented. Confidence High. Resolution: document their purpose or
retire them — not urgent.

### D-5 · MEDIUM — documented aggregation layout does not match disk

| | |
|---|---|
| **Location** | `docs/ARCHITECTURE.md:32,165` |
| **Observed** | Signatures written to `pcd_stats/` + `dyad_stats/` |
| **Canonical on disk** | Only `pcd_results/aggregation/stats/` exists, containing **3 of 7** ragas' `*_dyad_stats.npz`, dated **2026-01-05** — a stale layout no longer written by `aggregate_all_v12.py:209` |
| **Evidence** | `find` over the repository; `aggregate_all_v12.py:27` sets `DYAD_DIR = RUN_DIR/dyad_stats` |
| **Confidence** | High |
| **Resolution** | Note that persisted per-raga dyad models are stale and partial, and that current analyses build models in memory |
| **Files affected** | `docs/ARCHITECTURE.md`, possibly `.ai-memory/architecture.md` |

### D-6 · INFORMATIONAL — `benchmark.py` does not exist

ADR-016 requires a one-command reproducible benchmark and **already records its
own enforcement as OPEN**. Self-disclosed, not a new inconsistency.

---

## E. Research-status inconsistencies

### E-1 · HIGH — README does not disclose that the project has open research gates

| | |
|---|---|
| **Location** | `README.md` overall |
| **Observed** | Research status appears only inside a v1.3.2 version bullet (`:12-20`). No gate is named except Q-003, in passing |
| **Canonical** | `PROJECT_STATUS.md` "Research Gates": Q-001A ANSWERED · Q-001B **ACTIVE** · Q-001B-A COMPLETED (INCONCLUSIVE) · Q-001B-B **BLOCKED** · Q-002 blocked · Q-003 **ACTIVE — UNANSWERED** · Q-004 pending |
| **Evidence** | `PROJECT_STATUS.md:130-160` |
| **Confidence** | High |
| **Resolution** | Add a research-status section sourced from `PROJECT_STATUS.md`. **No status may be upgraded or downgraded in the process** |
| **Files affected** | `README.md` |

### E-2 · MEDIUM — README omits the navigation entry point

`README.md` links `PROJECT_STATUS.md` and `docs/research/Q-003/PHASE_LOG.md`
(both at `:20`) but never `docs/START_HERE.md`, which `CLAUDE.md` §4a/§4b
establish as the reading-order entry point. Confidence High.
**Files affected:** `README.md`.

### E-3 · MEDIUM — README carries no limitations section

`PROJECT_STATUS.md` "Known Limitations" records Abhogi 33% structural, Bhairavi
14% cause UNPROVEN, Mohanam 9/10 UNKNOWN, Kamboji excluded, Saveri as sink, no
OOD floor. None appear in the README. Confidence High. Resolution: add,
**verbatim**, without softening. **Files affected:** `README.md`.

---

## F. Numerical inconsistencies

### F-1 · INFORMATIONAL — the canonical accuracy table **PASSES** every check

| | |
|---|---|
| **Location** | `README.md:86-95` |
| **Verification** | Clips 10+8+9+14+11+7+11 = **70** ✓ · Correct = **25** ✓ · Wrong = **14** ✓ · Unknown = **31** ✓ · Per-raga decided accuracy recomputes exactly (Saveri 7/8 = 88%, Kalyani 6/8 = 75%, Thodi 5/7 = 71%, Abhogi 1/3 = 33%, Bhairavi 1/7 = 14%) · Total 25/39 = **64.1%** ✓ |
| **Cross-check** | Bhairavi 1c/6w/4u matches the Phase 1-C artifacts (`run_20260825_202704_phase1c/per_clip.csv`) exactly |
| **Confidence** | High |

**This is the row-sum check that the fabricated 67.4% figure failed.** The table
passes it. Recorded as a positive finding.

### F-2 · LOW — "clips" is undefined for staged ragas

`README.md:99-103` gives Kamboji 3, Madhyamavati 2, Hamsadhvani 1. The feature
cache holds Kamboji 3 and Madhyamavati 2 (agreeing), but **Hamsadhvani has 1
audio file and 0 extracted features**. Raw audio counts differ (Kamboji 4,
Madhyamavati 4). Confidence High. Resolution: define "clips" as *extracted,
eligible* clips and reconcile the Hamsadhvani row. **Do not change the numbers
without deciding the definition.**

### F-3 · LOW — `requirements.txt` header is version-stale

`requirements.txt:1` reads "Swarag v1.3 -- Python Dependencies"; current version
is **v1.3.2**. Dependency ranges themselves are satisfied by the installed stack
(numpy 2.2.6 ≥ 1.23, librosa 0.11.0 ≥ 0.10.0). Confidence High.

### F-4 · INFORMATIONAL — confidence thresholds agree everywhere

`MARGIN_STRICT = 0.003`, `MIN_MARGIN_FINAL = 0.001`, `ALPHA = 0.01`,
`N_BINS = 72`, `PCD_WEIGHT = 0.8`, `DYAD_WEIGHT = 0.2`,
`MIN_CLIPS_PER_RAGA = 5` are consistent across `recognize_raga_v12.py`,
`DEVELOPMENT.md` §8, and `PROJECT_STATUS.md`. **No drift.**

---

## G. Methodology inconsistencies

### G-1 · MEDIUM — no document records that the dyad channel is unweighted and unnormalised

| | |
|---|---|
| **Location** | Absent from `.ai-memory/feature-registry.md`, `docs/ARCHITECTURE.md`, `PROJECT_STATUS.md` |
| **Observed** | Nothing states that the dyad channel receives neither IDF×Variance weighting nor L2 normalisation, while PCD receives weighting |
| **Canonical** | `recognize_raga_v12.py:210-214`; established by Q-003 Phase 1-C and recorded only in `docs/research/Q-003/PHASE_LOG.md` |
| **Confidence** | High |
| **Resolution** | Record it as a live representation fact where features are described — it is not a rejected feature, so `feature-registry.md`'s rejected-features table is not the right home without a new row type |
| **Files affected** | `.ai-memory/feature-registry.md`, `docs/ARCHITECTURE.md` |

Methodology otherwise verified accurate: 72-bin PCD at 16.67 cents/bin
(README says "17 cents", a rounding, acceptable), pYIN via librosa, tonic
normalisation, directional dyads with up/down stored separately, LOO as the
trust standard (ADR-011), `sandbox_loo_v131_canonical.py` present.

---

## H. Documentation inconsistencies

### H-1 · MEDIUM — the Phase 1-C authorisation gate is untracked

`docs/research/Q-003/PHASE_1C_PRECHECK.md` exists on disk but is **not in
version control**. The verification gate that authorised Phase 1-C is therefore
not reconstructible from the repository. Confidence High. Resolution: commit it,
or record why it is deliberately excluded. **Files affected:** repository index.

### H-2 · MEDIUM — Q-003 has no research plan

`CLAUDE.md` §4a places "the active research plan" at level 3 of the
source-of-truth hierarchy. `.ai-memory/Q-001B_Research_Plan.md` exists;
**there is no Q-003 equivalent**. The active gate's plan has lived entirely in
successive external directives. Confidence High. Resolution: create
`docs/research/Q-003/RESEARCH_PLAN.md` — the Phase 1-D pre-registration is the
natural first entry. **Files affected:** `docs/research/Q-003/`.

### H-3 · LOW — navigation links verified

All README links resolve: `DEVELOPMENT.md`, `CONTRIBUTING.md`, `LICENSE`,
`PROJECT_STATUS.md`, `docs/research/Q-003/PHASE_LOG.md`. **No broken links.**
`CODE_OF_CONDUCT.md` is absent but is also **not referenced** — no defect.

---

## I. Duplicate-authority findings

### I-1 · HIGH — the canonical accuracy figures exist in four places

| | |
|---|---|
| **Copies** | `README.md:82-95` · `PROJECT_STATUS.md` (Current Accuracy) · `.ai-memory/architecture.md:80-88` · `datasets/README.md:43` |
| **Canonical owner** | `PROJECT_STATUS.md`, per `CLAUDE.md` §4b ("volatile project state") |
| **Currently consistent?** | **Yes — all four agree today** |
| **Intentional?** | Partly. README needs a summary; `.ai-memory/` and `datasets/README.md` are working copies |
| **Safe to consolidate?** | Not fully. A README with no numbers is unusable. **Safest form:** README keeps the table and adds a one-line pointer naming `PROJECT_STATUS.md` as canonical; the `.ai-memory/` copy is reduced to a pointer |
| **Risk if left** | This exact duplication class produced the fabricated 67.4% figure, which stood for three months and drove ADR-006 |

### I-2 · MEDIUM — scoring constants duplicated in documentation and code

`DEVELOPMENT.md` §8 table + `recognize_raga_v12.py` + `aggregate_all_v12.py`.
Canonical owner: `recognize_raga_v12.py` (ADR-015). Values currently agree.
Consolidation is safe for the **documentation** copy (reframe as
"sourced from"); the **code** copy is C-4 and needs authorisation.

### I-3 · LOW — the pipeline diagram exists twice and the copies disagree

`README.md:49-78` and `docs/ARCHITECTURE.md:28-37`. They disagree precisely at
the IDF claim (C-1/C-2). Canonical owner: `docs/ARCHITECTURE.md` ("stable
conceptual architecture", `CLAUDE.md` §4b). Resolution: fix both, and keep the
README copy shorter and explicitly derivative.

---

## J. Governance conflicts

### J-1 · HIGH — `DEVELOPMENT.md` §8 versus ADR-015

Cross-listed with C-3. A locked ADR mandates importing constants; an active
workflow document instructs contributors to keep copies identical. A contributor
following `DEVELOPMENT.md` would reintroduce the exact failure ADR-015 closed.
**Flagged, not resolved.**

### J-2 · LOW — sandbox naming convention drift

`DEVELOPMENT.md:33,54-58` and `CONTRIBUTING.md:33` prescribe `test_*.py`;
`CLAUDE.md`'s quick reference prescribes `scripts/sandbox_*.py`. **ADR-010
sanctions both** ("a `test_*.py` / `sandbox_*.py` script"), so this is cosmetic
drift, not a contradiction. Recent Q-003 work used `sandbox_*.py`.

### J-3 · INFORMATIONAL — pre-commit hook depends on `python3`

`.githooks/pre-commit` invokes `python3 -m py_compile`, while `CLAUDE.md` §9
warns the bare interpreter lacks numpy. No actual conflict — the hook only
compiles and does not import numpy, and it has run clean on commits `9b1dd6d`
and `0bf39cb`. Worth documenting as an undeclared dependency.

---

## K. Severity classification

| Severity | Entries | Findings |
|---|---|---|
| CRITICAL | 1 | B-1 |
| HIGH | 8 | C-1, C-2, C-3, D-1, D-2, E-1, I-1, J-1 *(J-1 cross-lists C-3 — 7 distinct issues)* |
| MEDIUM | 10 | C-4, C-5, D-3, D-5, E-2, E-3, G-1, H-1, H-2, I-2 |
| LOW | 6 | D-4, F-2, F-3, H-3, I-3, J-2 |
| INFORMATIONAL | 5 | B-2, D-6, F-1, F-4, J-3 |
| **Total** | **30 entries / 29 distinct** | |

---

## L. Disposition

### L1 · Must fix before the README redesign

1. **B-1** — the naming decision. Everything in the README hero depends on it.
2. **C-1 + C-2** — the IDF claim. Rewriting the README around a false technical
   statement would propagate it into the redesigned document.
3. **D-1** — the run commands, since the redesign rewrites that section anyway.

### L2 · Should fix before the README redesign

4. **E-1** — research gates. The redesign's stated purpose is to reflect research
   status; omitting the gates would defeat it.
5. **E-3** — limitations, for the same reason.
6. **D-3** — repository structure, since the redesign rewrites it.
7. **I-1** — add the canonical pointer while the table is being touched.

### L3 · Safe to defer

8. **C-3 / J-1** — `DEVELOPMENT.md` §8 vs ADR-015. Real and HIGH, but outside the
   README. Should become its own task, not a rider.
9. **C-4** — production constant duplication. Requires sandbox validation.
10. **D-2, D-4, D-5, F-2, F-3, G-1, H-1, H-2, I-2, I-3, J-2** — none blocks the README.
11. **C-5, D-6, B-2, F-1, F-4, J-3** — no action; recorded.

### L4 · Decisions required from you

1. **Naming architecture** — Option 1 (display/slug split), 2 (full rename),
   3 (standardise on `Swarag`), or 4 (also rename filesystem paths). *Not decided
   here.*
2. **Authorise the C-1/C-2 correction** — it changes a stated technical claim in
   two documents. Per `CLAUDE.md` §4, flagged rather than silently corrected.
3. **Scope of the README redesign** — L1 only, or L1 + L2.
4. **Whether `PHASE_1C_PRECHECK.md` should be committed** (H-1).
5. **Whether `DEVELOPMENT.md` §8 vs ADR-015 becomes its own task** (C-3/J-1).

---

*Read-only audit. No file was modified, renamed, deleted, committed, or pushed.
No unresolved question was decided.*
