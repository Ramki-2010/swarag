"""Diagnostic: Score breakdown per raga per test file"""
import sys, os, numpy as np, librosa
sys.path.insert(0, '.')
from recognize_raga_v12 import *
from utils import estimate_tonic

AGG = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260309_082638"
TEST_DIR = r"D:\Swaragam\datasets\audio test"
models = load_aggregated_models(AGG)

test_files = ["Alapana_HAM_Test.wav", "Alapana_Moha_Test.wav", "Balap_Test.wav", "Kalap_Test.wav"]
expected = ["OOD (Hamsadwani)", "OOD (Mohanam)", "Bhairavi", "Kalyani"]

for fname, exp in zip(test_files, expected):
    fpath = os.path.join(TEST_DIR, fname)
    y, sr = librosa.load(fpath, sr=SR, duration=MAX_DURATION_SEC)
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C1"), fmax=librosa.note_to_hz("C6"), sr=SR)
    valid = f0[~np.isnan(f0)]
    sa_hz = estimate_tonic(valid)
    cents = (1200 * np.log2(valid / sa_hz)) % 1200
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / np.sum(hist)
    test_up, test_down = compute_directional_dyads(cents)

    print("=" * 70)
    print("{} (expected: {})".format(fname, exp))
    print("  voiced frames: {}, tonic: {:.1f} Hz".format(len(valid), sa_hz))
    print()

    # Score breakdown
    header = "  {:20} {:>8} {:>9} {:>9} {:>9} {:>9}".format(
        "Raga", "PCD_sim", "Dyad_sim", "0.6/0.4", "0.3/0.7", "PCD-only")
    print(header)

    results = {}
    for raga in sorted(models.keys()):
        model = models[raga]
        pcd_sim = np.dot(pcd, model["pcd"])
        up_sim = np.dot(test_up, model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])
        dyad_sim = 0.5 * (up_sim + down_sim)
        std = 0.6 * pcd_sim + 0.4 * dyad_sim
        esc = 0.3 * pcd_sim + 0.7 * dyad_sim
        results[raga] = {"pcd": pcd_sim, "dyad": dyad_sim, "std": std, "esc": esc}
        print("  {:20} {:8.5f} {:9.5f} {:9.5f} {:9.5f} {:9.5f}".format(
            raga, pcd_sim, dyad_sim, std, esc, pcd_sim))

    # Margins comparison
    print()
    for label, key in [("0.6/0.4 (current)", "std"), ("0.3/0.7 (old esc)", "esc"), ("PCD-only", "pcd")]:
        ranked = sorted(results.items(), key=lambda x: x[1][key], reverse=True)
        margin = ranked[0][1][key] - ranked[1][1][key]
        print("  {:20} #1={:20} margin={:.6f}".format(label, ranked[0][0], margin))

    print()
