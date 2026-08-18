# CLAUDE.md — Swarag Research & Repository Governance

Guidance for Claude Code when working in this repository.

**Scope: this file governs `D:\Swaragam` only.** It says nothing about any other
repository, and nothing here authorises acting outside this project directory.

**Relationship to existing instructions.** This file is the operative
project-level instruction set. It does not replace:

- `.ai/agent_spec.md` — the older CODE ARBITER spec (RULE 0–14). Still valid for
  development-loop, debugging-order and architecture-guardian guidance. Where the
  two overlap, **this file governs research and Git conduct**; agent_spec governs
  engineering workflow.
- `.ai-memory/*.md` — the project's living memory (bugs, lessons, architecture,
  datasets, workflow, evaluation protocols). These are **evidence**, not advice.
- `.ai-memory/phrase-evaluation-protocol.md` and `adr.md` — frozen methodology and
  recorded decisions. Read-only unless explicitly reopened.

Nothing in this file overrides Claude Code's own system rules or the user's direct
instructions in a session. Where this file and a live instruction conflict, ask.

---

## 1. Project context

Swarag is a **scientific research project** that identifies Carnatic ragas from
audio. Scientific validity, reproducibility, provenance and documentation take
priority over speed or convenience.

Never optimise for producing a desired result. Never manufacture certainty.
Scientific correctness takes priority over task completion.

## 2. Mandatory state verification

Before any substantive task, establish the actual current state. Inspect, as
relevant: `git status`, current branch, current commit, `PROJECT_STATUS.md`, the
`.ai-memory/` documents, research plans, protocols, experiment artifacts, scripts
and dataset definitions.

Never assume documentation is current. Never assume an experiment has or has not
run — **check the artifacts on disk and the Git history.** Both directions of that
assumption have been wrong in this repository.

## 3. Research-first requirement

For substantive scientific decisions: inspect repository evidence first, then
prior experiments, then relevant literature and established methodology. Compare
approaches before choosing one.

Distinguish evidence from inference, and inference from speculation.

Do not invent methodology, statistical thresholds, provenance, or dataset
membership. Do not fabricate citations. When evidence is missing, say so.

## 4. Documentation cross-check

Before changing documentation, verify every claim against experiment artifacts,
source manifests, scripts, Git history, dataset records and committed evidence.

**Never copy remembered values into documentation.** Read them from the
authoritative artifact and quote the file you read.

If documentation conflicts with code or data: **STOP and report the contradiction
before editing.**

Precedent: a 67.4% accuracy figure stood as canonical for three months while its
per-raga rows never summed to its own stated total, and it drove a real
architectural decision the whole time. `.ai-memory/evaluation-protocol.md` §4
requires the row-sum check *before* committing.

## 5. Frozen research decisions

Treat as frozen unless explicitly reopened: hypotheses, null hypotheses, dataset
definitions, pre-registration, evaluation protocols, statistical thresholds,
seeds, surrogate counts, promotion criteria, experiment scope, methodological
decisions.

Never change methodology because results are inconvenient. Never introduce a
threshold after seeing results. Never remove difficult samples because they hurt
results. Never reinterpret an INCONCLUSIVE result as success.

If a required threshold does not exist in the frozen documents, **say so and
pause** — do not supply one. Quote the passage that delegates it.

## 6. Provenance standard

Never establish provenance from filename similarity alone.

Preference order: committed manifests → source records → dataset metadata →
extraction records → Git history → reproducible measurement.

Label inference as inference. Never present inference as established fact.

## 7. Duplicate-data rule

**Same composition does not automatically mean duplicate audio.** Different
performers produce legitimate variations; different performances can contain
different structures.

Treat recordings as duplicates only where evidence supports shared
recording/performance identity. Weigh composition, performance, performer,
recording, isolation method, source dataset, extraction timestamp and committed
cleanup rules together.

When retiring an artifact, retain its provenance. Prefer moving to `excluded/`
over deletion — the March 2026 precedent (`scripts/_cleanup_duplicates.py`) moved
rather than deleted so provenance stayed recoverable.

## 8. Change-scope control

Before modifying anything, determine which files may change, which must not,
which datasets are read versus modified, which artifacts are generated, and which
directories are out of scope.

Modify only what the task requires. No opportunistic cleanup, no reformatting of
unrelated files, no folder reorganisation.

Do not modify production code during sandbox research unless explicitly required.
Do not modify datasets without explicit authorisation. **Do not delete
experimental evidence.**

## 9. Python environment

All Swarag Python execution uses **`my_virtual_env_swarag`**. Never create another
virtual environment without authorisation.

Canonical interpreter:

```
D:\Swaragam\my_virtual_env_swarag\Scripts\python.exe    # numpy 2.2.6, librosa 0.11.0
```

Notes verified in-repo:
- This is the **sole canonical environment**. A second environment previously
  existed at `scripts/my_virtual_env_swarag/`; it was **retired on 2026-08-17**
  (renamed `scripts/my_virtual_env_swarag.RETIRED_20260817`, **not deleted**)
  because it was no longer required by active Swarag workflows. Its 77-package
  manifest is preserved at `docs/retired_scripts_venv_packages.txt`. Deletion is
  a separate future decision. **Do not create a third environment.**
- The bare `python` on PATH is a separate install **without numpy** and will fail.
- Add `PYTHONIOENCODING=utf-8` when output may contain non-ASCII — Saraga metadata
  carries transliterated raga names (e.g. `Ābhōgi`) and cp1252 raises
  `UnicodeEncodeError`.

Verify the interpreter before consequential execution. Do not change environment
silently.

## 10. Experiment pre-flight

Before running an experiment, verify: branch, commit, virtual environment, script
version, dataset, feature directory, exclusions, parameters, seed, surrogate
count, output directory, pre-registration and methodology.

**If the implementation differs materially from the pre-registration, STOP and
report it** before running.

## 11. Experiment reproducibility

Preserve with every run: Git commit, script version, parameters, seed, dataset
population, feature version, output path, environment, provenance and methodology
version.

Never overwrite a previous run. Use timestamped output directories. A canonical
number must trace to a checked-in script, never to a hand-typed table.

## 12. Result interpretation

Keep these four distinct, and label which one you are asserting:

**Observed fact** · **Statistical inference** · **Scientific interpretation** ·
**Hypothesis**

- A significant result does not automatically establish the research hypothesis.
- A non-significant result does not prove absence.
- A sequence-level result does not automatically establish raga-level knowledge.
- A dataset limitation is not automatically a model failure.

Report effect size alongside significance, always. Prefer separation tests over
mean-versus-threshold verdicts at small n (L-052).

## 13. Documentation after gates

After a completed research gate, determine whether
`.ai-memory/phrase-evaluation-protocol.md` §9 requires updates. Candidates:

- `PROJECT_STATUS.md`
- `.ai-memory/datasets.md`
- `.ai-memory/lessons.md`
- `adr.md` — **repository root**, not `.ai-memory/`

Before updating, verify exact result values, dataset population, interpretation,
limitations, provenance and the scientific claims being made. Do not overclaim.

**Do not modify an ADR unless an actual architectural decision was made.** A
result alone is not an ADR.

## 14. Git safety

Run `git status` before staging. Then verify: only intended files changed, no
datasets changed accidentally, no experiment artifacts staged, no secrets, no
temporary files, no unrelated formatting.

Run `git diff --check`.

**Never use `git add -A` unless explicitly authorised.** Stage explicit file paths.

This repository sets `core.hooksPath=.githooks`; `.githooks/pre-commit` audits
staged Python for syntax corruption, editor placeholders, merge markers and
duplicated top-level defs. Never bypass it with `--no-verify` unless the user
explicitly asks.

## 15. Commit safety

Before committing, inspect the staged file list and the staged diff, and verify
scope, tests, research status and documentation accuracy.

Commit messages must describe the actual change. **Never claim a verification that
did not occur.**

## 16. Push safety

Before pushing, verify commit, branch, remote, commit scope and that no unintended
commits are included. Push only when the user asks.

**Never force-push. Never rewrite remote history.**

After pushing, verify local HEAD, origin HEAD, ahead/behind status and
working-tree status.

## 17. Decision escalation

**Do not ask unnecessary approval questions.** When a task is explicit and
unambiguous: verify, execute, audit, report. This section exists to prevent
repetitive approval loops.

Ask only when: scientific interpretation is ambiguous; evidence conflicts;
methodology must change; a frozen decision must reopen; dataset modification is
required; scope is unclear; a destructive action is proposed; or commit/push
authorisation is absent.

This refines `.ai/agent_spec.md` RULE 1 (Founder Mode): keep explanations clear
and jargon-light, but clarity of explanation is not a licence to ask for approval
that has already been given.

## 18. Anti-hallucination

Before documenting any factual claim, identify its evidence: a repository file, an
experiment artifact, a Git commit, a dataset manifest, a reproducible measurement,
or an authoritative external source.

**If evidence cannot be established, write "not established."** Never fill a gap
with a plausible assumption.

## 19. No retroactive reasoning

An unexpected result triggers investigation. It does **not** justify changing
thresholds, exclusions, dataset membership, scoring rules, seeds or null models,
nor removing inconvenient samples.

Any methodology change requires explicit justification, authorisation and
documentation — in that order.

## 20. Final pre-commit audit

- [ ] Correct branch
- [ ] Correct project state
- [ ] Correct research scope
- [ ] Correct documentation
- [ ] Correct dataset
- [ ] Correct experiment artifacts
- [ ] No unsupported claims
- [ ] No unsupported provenance
- [ ] No frozen-protocol changes
- [ ] No unrelated files
- [ ] No accidental dataset changes
- [ ] No accidental artifacts
- [ ] `git diff --check` passes
- [ ] Staged diff reviewed
- [ ] Commit message accurate

**If any item fails: STOP.**

## 21. Final principle

When uncertain, preserve evidence. When unsupported, say unknown. When
conflicting, investigate. When consequential, verify. When methodology changes,
document it. When data changes, preserve provenance. When code changes, minimise
scope. When interpreting results, avoid overclaiming.

**Scientific correctness takes priority over task completion.**

---

## Repository quick reference (verified)

| Item | Value |
|---|---|
| Project root | `D:\Swaragam` |
| Interpreter | `my_virtual_env_swarag\Scripts\python.exe` |
| Production scripts | `scripts/recognize_raga_v12.py`, `aggregate_all_v12.py`, `extract_pitch_batch_v12.py`, `batch_evaluate*.py`, `utils.py` |
| Sandbox convention | `scripts/sandbox_*.py` — checked in, never a notebook or manual calculation |
| Feature cache | `pcd_results/features_v12/` (gitignored); `excluded/` holds dedup rejects and is not read |
| Feature version owner | `scripts/feature_constants.py` (`FEATURE_VERSION`) — single source, never re-declare (ADR-015/017) |
| Living memory | `.ai-memory/` |
| Decisions | `adr.md` (repository root) |
| Gate status | `PROJECT_STATUS.md` |
| Generated results | gitignored under `# Generated experiment outputs` in `.gitignore` |
| Hooks | `core.hooksPath=.githooks` |

**Out of scope for this file:** `antigravity-claude-proxy/` is a gitignored,
untracked vendored subproject with its own `CLAUDE.md`. Do not modify it, and do
not treat its instructions as Swarag's.
