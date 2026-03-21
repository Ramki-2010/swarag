# Contributing to Swarag

Thank you for your interest in **Swarag**.

Swarag is a research-driven project focused on **Carnatic raga identification using signal-derived statistical features**, not rule-based systems.

We welcome collaborators who value correctness, interpretability, and musical validity.

---

## Project Philosophy

Before contributing, please understand the core principles:

- **Tonic-relative analysis only** — Absolute pitch is meaningless across singers.
- **Data-first, not rule-first** — No hand-coded arohanam / avarohanam rules.
- **Interpretability over black-box models** — Every feature should be explainable musically.
- **Incremental complexity** — Baselines are stabilized before adding new features.
- **Vocal-only audio** — Instrument contamination degrades pitch extraction. Always use isolated vocals.

---

## The Development Loop (Mandatory)

Every change to Swarag must follow this 4-step loop. No exceptions.

```
STEP 1: PLAN
    What are we changing? Why? What could break?
    Check .ai-memory/bugs.md and architecture.md first.

STEP 2: IMPLEMENT (sandbox-first)
    Apply fix in a test_*.py sandbox script first.
    Run sandbox, capture output, compare before/after.
    Only apply to production if results are BETTER.

STEP 3: VERIFY
    Run batch_evaluate.py or batch_evaluate_random.py.
    Compare results against previous run.
    Log results in .ai-memory/datasets.md.

STEP 4: LEARN & DOCUMENT
    Update: bugs.md, lessons.md, architecture.md, datasets.md.
    Extract at least one lesson per session.
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full development workflow.

---

## Code Principles

- No silent parameter changes
- No mixing version artifacts
- No dataset commits (datasets/ is gitignored)
- All changes must be testable via `batch_evaluate.py`
- Shared constants must match across all scripts:
  - `N_BINS=72`, `ALPHA=0.01`, `MIN_STABLE_FRAMES=5`, `EPS=1e-8`
  - `PCD_WEIGHT=0.7`, `DYAD_WEIGHT=0.3`
  - `MIN_CLIPS_PER_RAGA=5` (aggregation guardrail)
- Never modify production scripts without sandbox validation first
- Always cross-reference raga labels against authoritative sources (Saraga, Dunya)

---

## Areas Where Contributions Are Welcome

### Signal Processing / MIR
- Pitch tracking robustness
- Tonic estimation and validation
- Transition (dyad) statistics
- Windowed / temporal feature aggregation

### Evaluation & Analysis
- Similarity metrics
- Error analysis tooling
- Visualization improvements

### Dataset Expansion
- Curated Carnatic vocal recordings (vocal-only or with multitrack stems)
- Clear raga labeling (cross-referenced against Saraga/Dunya metadata)
- Minimum 5 clips per raga to pass the MIN_CLIPS guardrail
- Beware parent vs janya raga confusion (e.g., Harikambhoji vs Kamboji)
- Performance context documentation

### Engineering
- Modularization
- Config-driven pipelines
- Performance optimizations

---

## What We Are Not Accepting (Yet)

- End-to-end deep learning models without interpretability
- Heavily heuristic raga rules
- UI / application layers (planned later)

---

## How to Contribute

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Read [DEVELOPMENT.md](DEVELOPMENT.md) and `.ai/agent_spec.md` for workflow rules
4. Make changes with clear commits
5. Run evaluation and capture results
6. Open a Pull Request describing:
   - What problem you addressed
   - Why the change is musically valid
   - Before/after evaluation results

---

**Swarag values depth over speed.**
