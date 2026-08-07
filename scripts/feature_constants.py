"""Single source of truth for the feature-cache schema version.

FEATURE_VERSION is stamped into every .npz by extract_pitch_batch_v12.py and
checked by every consumer (aggregate_all_v12.py, sandbox_q001a_*). Bump it ONCE
here when the extracted feature format changes; all readers follow automatically.
Prevents the three-copy drift that silently breaks cache lookup (ADR-015).
"""

FEATURE_VERSION = "v1.2"
