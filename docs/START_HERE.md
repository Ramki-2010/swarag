# START HERE — Swarag navigation

This is a **navigation document**. It tells you where truth lives; it does not
restate it.

It deliberately contains almost no project facts. Accuracy figures, gate status,
constants and open blockers are **not** duplicated here, because a second copy
drifts from the first. Every factual question below is answered by following a
link, not by reading this page.

If you find a project fact stated here, that is a defect — remove it and link
instead.

---

## Source-of-truth hierarchy

When two documents disagree, the higher entry wins:

| # | Source | Authority |
|---|--------|-----------|
| 1 | `CLAUDE.md` | Governance, working rules, environment |
| 2 | `PROJECT_STATUS.md` | Current project state, gates, baseline, priorities |
| 3 | Active research plan | Methodology for the active gate |
| 4 | `docs/research/<GATE>/PHASE_LOG.md` | Detailed research history and reasoning |
| 5 | `adr.md`, frozen protocols | Settled decisions and frozen methodology |
| 6 | Datasets and experiment artifacts | Measured evidence |
| 7 | Historical summaries | Records of what was believed at the time |
| 8 | General repository documentation | Everything else |

Two standing qualifications:

- **More recent evidence does not automatically override frozen methodology.**
  A frozen protocol is frozen for a reason; changing it is a decision, not an
  inference.
- **Never resolve a contradiction by guessing.** Use each document's declared
  authority and scope. If the conflict is genuine, stop and report it.

---

## Reading order for a fresh session

1. **`CLAUDE.md`** — governance and working rules. Read first, always.
2. **`PROJECT_STATUS.md`** — current baseline, active gates, current phase,
   blockers, immediate priorities.
3. **Git state** — `git status`, `git log --oneline -20`. Never assume the
   documentation is current, and never assume an experiment has or has not run;
   check the artifacts on disk and the history (`CLAUDE.md` §2).
4. **Identify the active research gate** from `PROJECT_STATUS.md` → Research
   Gates. Do not infer the active gate from conversation or from this file.
5. **Read that gate's research plan**, if one exists.
6. **Read that gate's phase log** — `docs/research/<GATE>/PHASE_LOG.md`. This is
   where detailed experimental reasoning lives.
7. **Read the relevant ADRs and frozen protocols** — `adr.md`,
   `.ai-memory/phrase-evaluation-protocol.md`,
   `.ai-memory/evaluation-protocol.md`.
8. **Inspect the experiment artifacts before making any claim about results.**
   A number that is not in an artifact, a commit, or a reproducible measurement
   does not get stated.

A fresh session should be able to reconstruct context from this path alone. It
must not depend on conversational memory from a previous session.

---

## Document map — what belongs where

| Category | Home | Changes |
|---|---|---|
| Governance, rules, environment | `CLAUDE.md` | Rarely |
| **Volatile project state** | `PROJECT_STATUS.md` | Every gate/phase transition |
| **Detailed research reasoning** | `docs/research/<GATE>/PHASE_LOG.md` | Append-only, per phase |
| **Active gate methodology** | `docs/research/<GATE>/RESEARCH_PLAN.md` | Per phase design |
| Phase authorisation gates | `docs/research/<GATE>/PHASE_*_PRECHECK.md` | Historical, never edited |
| Repository consistency audits | `docs/repository-consistency-audit.md` (+ `.json`) | Dated snapshots |
| Stable conceptual architecture | `docs/ARCHITECTURE.md` | Rarely |
| Volatile architectural state | `.ai-memory/architecture.md` | Often |
| Settled decisions | `adr.md` | Append-only |
| Frozen methodology | `.ai-memory/*-protocol.md` | Only by explicit decision |
| Lessons | `.ai-memory/lessons.md` | Append-only |
| Dataset facts and run logs | `.ai-memory/datasets.md`, `datasets/README.md` | Per run |
| Historical session records | `.ai-memory/session_summary_*.md` | Never — historical |

**Do not merge these categories without explicit approval.** Stable architecture
and volatile state are separated on purpose.

---

## Rules that constrain what you may write

- **Do not copy detailed state between documents.** Link instead.
- **Phase logs are append-oriented.** Do not silently rewrite an earlier phase.
  If an earlier statement was wrong, **append a correction that preserves the
  original reasoning.** Do not erase history.
- **Never manufacture a missing number.** Never convert inference into fact, or
  hypothesis into diagnosis.
- **Never remove historical context for cleanliness.** Documentation exists to
  preserve evidence, not to make the project look tidy.
- When uncertain, mark the uncertainty. When unestablished, write
  **"not established."** When a phase is incomplete, leave it incomplete.

---

## Phase transitions

The required sequence is:

```
research → verification → decision → documentation → commit
```

A phase does **not** advance automatically. A finished experiment is not
approval to begin the next phase, and the existence of a completed phase does
not create the next one. **The next phase requires explicit approval.**

If a proposed next step conflicts with the established trail, stop and state:
what conflicts, which prior decision is affected, why it matters, and what would
change if approved. Then ask.

---

## Git

Follow `CLAUDE.md` §14–§16 and §20. In short: verify the intended files, verify
the diff, run `git diff --check`, confirm no experiment artifacts or unrelated
source files are staged. **Never `git add -A` without authorisation. Never
commit automatically. Never push automatically.**
