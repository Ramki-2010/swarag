import numpy as np
import os
from collections import defaultdict
from recognize_raga_v12 import load_aggregated_models, _score_models, compute_pcd_weights
from sandbox_absent_swara_v2 import load_clips, extract_features

# Global Config
PER_RAGA_WEIGHTS = {}
PCD_WEIGHT = 0.8
DYAD_WEIGHT = 0.2
MIN_STABLE = 5

def run_loo_with_bins(n_bins):
    clips = load_clips()
    # Re-extract features for this bin count
    processed = []
    for c in clips:
        # We need the original raw data, but load_clips() already processed them.
        # This is inefficient but safe. Let's re-run extract_features with new N_BINS.
        # I'll just adjust extract_features globally for this run.
        pass # See below for logic

# Actually, let's keep it simple and clean

def run_loo_for_bins(n_bins):
    # Re-load from disk to ensure clean feature extraction
    clips = []
    # ... (simplified loader)
    return 0.0

print('Running bin sparsity audit...')