"""Analyze actual transition counts and simulate different ALPHA values"""
import numpy as np
import os, sys
sys.path.insert(0, ".")

N_BINS = 36
feat_dir = r"D:\Swaragam\pcd_results\features_v12"
MIN_STABLE_FRAMES = 5

print("=" * 70)
print("TRANSITION COUNT ANALYSIS")
print("=" * 70)

files = sorted([f for f in os.listdir(feat_dir) if f.endswith(".npz")])
transition_counts = []

for f in files:
    data = np.load(os.path.join(feat_dir, f), allow_pickle=True)
    cents = data["cents_gated"]
    raga = str(data["raga"])
    
    # Reproduce stable region detection
    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]
    
    stable_bins = []
    current = pitch_bins[0]
    count = 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current = b
            count = 1
    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)
    
    n_transitions = max(0, len(stable_bins) - 1)
    transition_counts.append(n_transitions)
    
    # Count unique bin pairs actually used
    unique_pairs = set()
    for i in range(len(stable_bins) - 1):
        unique_pairs.add((stable_bins[i], stable_bins[i+1]))
    
    print("{:50} {:15} stable={:4d} transitions={:4d} unique_pairs={:3d}".format(
        f[:50], raga, len(stable_bins), n_transitions, len(unique_pairs)))

print()
print("SUMMARY:")
print("  Total files: {}".format(len(transition_counts)))
print("  Mean transitions per file: {:.1f}".format(np.mean(transition_counts)))
print("  Min: {}, Max: {}, Median: {:.0f}".format(
    min(transition_counts), max(transition_counts), np.median(transition_counts)))

print()
print("=" * 70)
print("LAPLACE ALPHA IMPACT ANALYSIS")
print("=" * 70)

# For a typical file with ~200 transitions spread over a 36x36 matrix:
typical_transitions = int(np.median(transition_counts))
matrix_cells = N_BINS * N_BINS  # 1296

for alpha in [0.5, 0.1, 0.01, 0.001, 0.0001]:
    total_laplace = matrix_cells * alpha
    signal_ratio = typical_transitions / (typical_transitions + total_laplace)
    noise_ratio = total_laplace / (typical_transitions + total_laplace)
    
    # Typical cell values
    laplace_floor = alpha / (typical_transitions + total_laplace)
    signal_cell = (1 + alpha) / (typical_transitions + total_laplace)  # cell with 1 transition
    
    print()
    print("ALPHA = {}:".format(alpha))
    print("  Total Laplace mass: {:.1f} vs signal mass: {}".format(total_laplace, typical_transitions))
    print("  Signal ratio: {:.1%}  Noise ratio: {:.1%}".format(signal_ratio, noise_ratio))
    print("  Laplace floor per cell: {:.6f}".format(laplace_floor))
    print("  Cell with 1 transition: {:.6f}  (ratio over floor: {:.1f}x)".format(
        signal_cell, signal_cell / laplace_floor if laplace_floor > 0 else 0))
    
    # Simulate dot product between two similar matrices
    # Assume 50% overlap in transition patterns
    shared_cells = 30  # cells with transitions in both
    sim = shared_cells * signal_cell**2 + (matrix_cells - shared_cells) * laplace_floor**2
    print("  Estimated dot-product (similar ragas): {:.6f}".format(sim))
    
    # Dissimilar 
    diff_cells = 5
    sim_diff = diff_cells * signal_cell**2 + (matrix_cells - diff_cells) * laplace_floor**2
    print("  Estimated dot-product (different ragas): {:.6f}".format(sim_diff))
    print("  Discrimination ratio: {:.2f}x".format(sim / sim_diff if sim_diff > 0 else 0))
