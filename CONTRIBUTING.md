# Contributing to Swarag

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
