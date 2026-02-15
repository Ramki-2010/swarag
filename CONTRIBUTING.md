# Contributing to Swarag

<<<<<<< HEAD
Thank you for your interest in **Swarag**.

Swarag is a research-driven project focused on **Carnatic raga identification using signal-derived statistical features**, not rule-based systems.

We welcome collaborators who value correctness, interpretability, and musical validity.

---

## Project Philosophy

Before contributing, please understand the core principles:

- **Tonic-relative analysis only**  
  Absolute pitch is meaningless across singers.

- **Data-first, not rule-first**  
  No hand-coded arohanam / avarohanam rules.

- **Interpretability over black-box models**  
  Every feature should be explainable musically.

- **Incremental complexity**  
  Baselines are stabilized before adding new features.

---

## Areas Where Contributions Are Welcome

### 🎵 Signal Processing / MIR
- Pitch tracking robustness
- Tonic estimation and validation
- Transition (dyad) statistics
- Windowed / temporal feature aggregation

### 📊 Evaluation & Analysis
- Similarity metrics
- Error analysis tooling
- Visualization improvements

### 🧪 Dataset Expansion
- Curated Carnatic vocal samples
- Clear raga labeling
- Performance context documentation

### 🛠 Engineering
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
2. Create a feature branch  

```bash
git checkout -b feature/your-feature-name
```

3. Make changes with clear commits
4. Open a Pull Request describing:
- What problem you addressed
- Why the change is musically valid
- How it was tested

---

**Swarag values depth over speed.**
=======
Swarag follows a deterministic DSP-based architecture.

Before contributing:

1. Do not introduce deep learning models without discussion.
2. Maintain version isolation (v1.1, v1.2, etc.).
3. Preserve reproducibility and metadata logging.
4. Avoid dataset inclusion in repository.
5. All changes must be testable via batch_evaluate.py.

## Workflow

- Create a feature branch
- Make isolated changes
- Run evaluation
- Compare against previous version
- Submit PR with diagnostic summary

## Code Principles

- No silent parameter changes
- No mixing version artifacts
- No dataset commits
>>>>>>> 3507cb62bb7d7c0b60c944ec3e1be532bc9d8c3b
