# Swarag Continue slash-command prompts

Version-controlled copies of the three Continue slash commands the project's
tracked documentation depends on.

## Why these are here

`.ai-memory/workflow.md` §12, `.ai/agent_spec.md` RULE 13 and `adr.md` ADR-012
(Status: ACTIVE, locked) all instruct the user to invoke `/analyze-swarag`,
`/debug-swarag` and `/capture-lesson`. Until 2026-08-21 those commands existed
**only** at `C:\Users\ramki\.continue\prompts\` — outside the repository,
untracked and unbacked-up. A fresh clone, or a new machine, had the
documentation telling it to run commands that did not exist.

The repository's own `.continue/` directory is gitignored (`.gitignore:45`), so
copying them there would have left them equally unprotected. `.ai/` is tracked
and already holds `agent_spec.md`, so these live here instead.

## Provenance

Copied byte-exact on 2026-08-21 from `C:\Users\ramki\.continue\prompts\`.
Verified identical by sha256 at copy time:

| File | sha256 (first 16) |
|---|---|
| `analyze-swarag.prompt` | `f328aac50ff40e81` |
| `capture-lesson.prompt` | `f575969ec5eeafa9` |
| `debug-swarag.prompt`   | `b7c4bdd881f12997` |

Nothing was edited, reformatted, or re-encoded. The byte-order marks present in
the originals are preserved.

## These are copies, not the live commands

Continue reads slash commands from `~/.continue/prompts/`, **not** from here.
These are a backup and a version-controlled record. If a prompt is edited, edit
the live copy and re-copy it here, or the two will drift — the same
single-source-of-truth problem ADR-015/ADR-017 addressed for `FEATURE_VERSION`.

## What each contains

- **`analyze-swarag.prompt`** — the 5-agent engineering team (Audio DSP
  Engineer, MIR Researcher, ML Engineer, Software Architect, Debug
  Investigator). Note it specifies an **AGREEMENTS / DISAGREEMENTS** output
  section that `agent_spec.md` RULE 13 does not mention; RULE 13's format stops
  at a single `UNIFIED:` line. The prompt is the fuller specification.
- **`debug-swarag.prompt`** — the 8-step debugging hierarchy (environment →
  paths → data loading → pitch → tonic → features → scoring → guardrails), each
  step reported PASS / FAIL / NEEDS INVESTIGATION, then a diagnosis against the
  5-level fix priority order.
- **`capture-lesson.prompt`** — extracts an L-NNN lesson in the actionable
  Context / Rule / Impact form `workflow.md` §8 requires.

Governed by ADR-012: multi-agent analysis is **on-demand only**, never routine.
