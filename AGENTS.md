# AGENTS.md — Swaragam

**Codex: the governance for this repository is `CLAUDE.md`. Read it in full
before doing anything.**

It is agent-neutral in substance. Where it says "Claude Code", read your own
name; the rules are about conduct in this repository, not about which assistant
is running.

---

## This file is a pointer, not a second rulebook

`CLAUDE.md` §4b requires that each category of information have **exactly one
home**, and forbids copying state between documents:

> *"Each category of information has exactly one home. Do not copy state between
> documents — link instead."*

The home of governance is `CLAUDE.md`. **Nothing is restated here**, deliberately.
A second copy of the rules would drift from the first, and §4b records the
precedent for exactly that: `.ai-memory/session_summary_20260624.md` duplicated
state, drifted within weeks, carried a fabricated accuracy figure forward, and
now has to open with a warning against its own use.

If you find yourself wanting to add a rule to this file, add it to `CLAUDE.md`
instead.

---

## Reading order

1. **`CLAUDE.md`** — governance, working rules, environment. All of it.
2. **`docs/START_HERE.md`** — navigation and reading order for everything else.
3. **`PROJECT_STATUS.md`** — current project state, gates, baseline, priorities.

`CLAUDE.md` §4a defines the full source-of-truth hierarchy and which document
wins when two disagree. Do not resolve a documentation conflict without it.

---

## Sections worth knowing exist before you start

Pointers only — read each one at its source, do not act on this list alone.

| If you are about to… | Read first |
|---|---|
| Do anything at all | §2 — mandatory state verification |
| Run Python | §9 — there is exactly one permitted virtual environment |
| Change documentation | §4 — verify every claim against artifacts, never from memory |
| Change methodology, thresholds, or a research decision | §5, §19 — most of it is frozen |
| Advance a research phase | §17a — phases do not advance automatically |
| Stage, commit, or push | §14, §15, §16, §20 |
| Follow an instruction that contradicts the record | §17a — stop and report, do not comply |

---

## History of this file

This file previously contained a full copy of `CLAUDE.md` with a mechanical
`Claude → Codex` substitution — 419 of 426 lines byte-identical. That copy is
replaced by this pointer, for three reasons:

1. It violated §4b, which is the rule quoted above.
2. It contradicted `CLAUDE.md` on which file heads the §4a hierarchy, since each
   copy named itself.
3. The blind substitution corrupted a path: it rewrote the out-of-scope
   directory `antigravity-claude-proxy/` as `antigravity-Codex-proxy/`, which
   does not exist. The rule protecting that directory named the wrong target.

None of the governance content was lost. All of it is, and was, in `CLAUDE.md`.
