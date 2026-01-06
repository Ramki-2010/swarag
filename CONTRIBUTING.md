# Contributing to Swarag

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
