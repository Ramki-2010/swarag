# =============================================================================
# DIAGNOSTIC SCRATCH SCRIPT -- not part of any pipeline
# Inspects keys and contents of a single raw features .npz file.
# Hardcoded to a specific file path -- update path before running.
# =============================================================================

import numpy as np

# Print everything
print("Keys:", list(data.keys()))
print("\nSchema version:", data.get('schema_version'))
print("Raga:", data.get('raga'))
print("Sa (Hz):", data['sa_hz'])
print("Tonic candidates:", data['tonic_candidates'])
print("Min/Max pitch:", data['min_pitch'], data['max_pitch'])
print("\nPCD shape:", data['pcd'].shape)
print("PCD (first 10 bins):", data['pcd'][:10])
print("\nf0 shape:", data['f0'].shape)
print("f0 (first 20):", data['f0'][:20])
print("Voiced flag (first 20):", data['voiced_flag'][:20])