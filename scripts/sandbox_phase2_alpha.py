"""
SANDBOX: Phase 2 — ALPHA fix for dyads (0.5 -> 0.01)

Tests the full pipeline:
1. Re-aggregate with ALPHA=0.01 (in memory, no file changes)
2. Compare dyad discrimination: ALPHA=0.5 vs ALPHA=0.01
3. Test scoring at multiple weight combos: PCD-only, 0.8/0.2, 0.7/0.3, 0.6/0.4
4. Run on 4 random test files + 53 seed files

NO production files are modified. All aggregation is done in-memory.
"""
import sys, os, numpy as np, librosa
sys.path.insert(0, ".")
from utils import estimate_tonic

# ============================================================
# CONFIG
# ============================================================
SR = 22050
MAX_DURATION_SEC = 360
N_BINS = 36
MIN_STABLE_FRAMES = 5
EPS = 1e-8

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
TEST_DIR = r"D:\Swaragam\datasets\audio test"


# ============================================================
# AGGREGATION (in-memory, parameterized ALPHA)
# ============================================================
def aggregate_in_memory(feat_dir, alpha):
    """Aggregate all features with given ALPHA. Returns model dict."""
    raga_pcds = {}
    raga_up = {}
    raga_down = {}

    for fname in os.listdir(feat_dir):
        if not fname.endswith(".npz"):
            continue
        data = np.load(os.path.join(feat_dir, fname), allow_pickle=True)
        if "feature_version" not in data or str(data["feature_version"]) != "v1.2":
            continue
        raga = str(data["raga"])
        cents = data["cents_gated"]
        if float(data["gating_ratio"]) < 0.05:
            continue

        # PCD
        hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
        pcd = hist / (np.sum(hist) + EPS)

        # Directional dyads with given ALPHA
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

        mat_up = np.zeros((N_BINS, N_BINS))
        mat_down = np.zeros((N_BINS, N_BINS))
        for i in range(len(stable_bins) - 1):
            frm, to = stable_bins[i], stable_bins[i + 1]
            if to > frm:
                mat_up[frm, to] += 1
            elif to < frm:
                mat_down[frm, to] += 1

        mat_up += alpha
        mat_down += alpha
        mat_up /= (np.sum(mat_up) + EPS)
        mat_down /= (np.sum(mat_down) + EPS)

        raga_pcds.setdefault(raga, []).append(pcd)
        raga_up.setdefault(raga, []).append(mat_up.flatten())
        raga_down.setdefault(raga, []).append(mat_down.flatten())

    models = {}
    for raga in raga_pcds:
        models[raga] = {
            "pcd": np.mean(raga_pcds[raga], axis=0),
            "mean_up": np.mean(raga_up[raga], axis=0),
            "mean_down": np.mean(raga_down[raga], axis=0),
            "n_clips": len(raga_pcds[raga]),
        }
    return models


def compute_dyads_for_test(cents, alpha):
    """Compute directional dyads for a test sample with given ALPHA."""
    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]
    if len(pitch_bins) < MIN_STABLE_FRAMES:
        return np.zeros(N_BINS * N_BINS), np.zeros(N_BINS * N_BINS)

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

    mat_up = np.zeros((N_BINS, N_BINS))
    mat_down = np.zeros((N_BINS, N_BINS))
    for i in range(len(stable_bins) - 1):
        frm, to = stable_bins[i], stable_bins[i + 1]
        if to > frm:
            mat_up[frm, to] += 1
        elif to < frm:
            mat_down[frm, to] += 1

    mat_up += alpha
    mat_down += alpha
    mat_up /= (np.sum(mat_up) + EPS)
    mat_down /= (np.sum(mat_down) + EPS)
    return mat_up.flatten(), mat_down.flatten()


def score_all(pcd, test_up, test_down, models, pcd_w, dyad_w):
    scores = {}
    for raga, model in models.items():
        pcd_sim = np.dot(pcd, model["pcd"])
        up_sim = np.dot(test_up, model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])
        dyad_sim = 0.5 * (up_sim + down_sim)
        scores[raga] = pcd_w * pcd_sim + dyad_w * dyad_sim
    return scores


# ============================================================
# PART 1: AGGREGATE WITH BOTH ALPHAS
# ============================================================
print("=" * 80)
print("PHASE 2 SANDBOX: ALPHA=0.5 vs ALPHA=0.01")
print("=" * 80)
print()

print("Aggregating with ALPHA=0.5 ...")
models_05 = aggregate_in_memory(FEAT_DIR, alpha=0.5)
print("  Ragas: {}".format(", ".join("{} ({})".format(r, m["n_clips"]) for r, m in sorted(models_05.items()))))

print("Aggregating with ALPHA=0.01 ...")
models_001 = aggregate_in_memory(FEAT_DIR, alpha=0.01)
print("  Ragas: {}".format(", ".join("{} ({})".format(r, m["n_clips"]) for r, m in sorted(models_001.items()))))

# ============================================================
# PART 2: DYAD DISCRIMINATION COMPARISON
# ============================================================
print()
print("=" * 80)
print("DYAD SIMILARITY: ALPHA=0.5 vs ALPHA=0.01")
print("=" * 80)
print()

# Cross-raga dyad similarity matrix for both alphas
ragas = sorted(models_05.keys())
print("ALPHA=0.5 — Dyad similarities (up+down avg):")
header = "  {:15}".format("")
for r in ragas:
    header += " {:>7}".format(r[:7])
print(header)

for r1 in ragas:
    row = "  {:15}".format(r1[:15])
    for r2 in ragas:
        up_sim = np.dot(models_05[r1]["mean_up"], models_05[r2]["mean_up"])
        dn_sim = np.dot(models_05[r1]["mean_down"], models_05[r2]["mean_down"])
        sim = 0.5 * (up_sim + dn_sim)
        row += " {:7.5f}".format(sim)
    print(row)

print()
print("ALPHA=0.01 — Dyad similarities (up+down avg):")
header = "  {:15}".format("")
for r in ragas:
    header += " {:>7}".format(r[:7])
print(header)

for r1 in ragas:
    row = "  {:15}".format(r1[:15])
    for r2 in ragas:
        up_sim = np.dot(models_001[r1]["mean_up"], models_001[r2]["mean_up"])
        dn_sim = np.dot(models_001[r1]["mean_down"], models_001[r2]["mean_down"])
        sim = 0.5 * (up_sim + dn_sim)
        row += " {:7.5f}".format(sim)
    print(row)

# Discrimination ratio
print()
print("DISCRIMINATION RATIO (self-sim / mean-other-sim):")
for alpha_label, models in [("ALPHA=0.5", models_05), ("ALPHA=0.01", models_001)]:
    print("  {}:".format(alpha_label))
    for r1 in ragas:
        self_sim_up = np.dot(models[r1]["mean_up"], models[r1]["mean_up"])
        self_sim_dn = np.dot(models[r1]["mean_down"], models[r1]["mean_down"])
        self_sim = 0.5 * (self_sim_up + self_sim_dn)
        other_sims = []
        for r2 in ragas:
            if r2 == r1:
                continue
            up_sim = np.dot(models[r1]["mean_up"], models[r2]["mean_up"])
            dn_sim = np.dot(models[r1]["mean_down"], models[r2]["mean_down"])
            other_sims.append(0.5 * (up_sim + dn_sim))
        mean_other = np.mean(other_sims)
        ratio = self_sim / mean_other if mean_other > 0 else 0
        print("    {:20} self={:.5f} mean_other={:.5f} ratio={:.2f}x".format(
            r1, self_sim, mean_other, ratio))

# ============================================================
# PART 3: TEST ON RANDOM FILES — MULTIPLE WEIGHT COMBOS
# ============================================================
print()
print("=" * 80)
print("RANDOM TEST FILES: WEIGHT COMBOS WITH ALPHA=0.01")
print("=" * 80)

test_files = [
    ("Alapana_HAM_Test.wav", "OOD_Hamsadwani"),
    ("Alapana_Moha_Test.wav", "OOD_Mohanam"),
    ("Balap_Test.wav", "Bhairavi"),
    ("Kalap_Test.wav", "Kalyani"),
]

weight_combos = [
    (1.0, 0.0, "PCD-only"),
    (0.8, 0.2, "0.8/0.2"),
    (0.7, 0.3, "0.7/0.3"),
    (0.6, 0.4, "0.6/0.4"),
]

for fname, expected in test_files:
    fpath = os.path.join(TEST_DIR, fname)
    y, sr = librosa.load(fpath, sr=SR, duration=MAX_DURATION_SEC)
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C1"),
                            fmax=librosa.note_to_hz("C6"), sr=SR)
    valid = f0[~np.isnan(f0)]
    sa_hz = estimate_tonic(valid)
    cents = (1200 * np.log2(valid / sa_hz)) % 1200
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / np.sum(hist)
    test_up, test_down = compute_dyads_for_test(cents, alpha=0.01)

    print()
    print(">> {} (expected: {})".format(fname, expected))
    for pcd_w, dyad_w, label in weight_combos:
        sc = score_all(pcd, test_up, test_down, models_001, pcd_w, dyad_w)
        rk = sorted(sc.items(), key=lambda x: x[1], reverse=True)
        mg = rk[0][1] - rk[1][1]
        tier = "HIGH" if mg >= 0.003 else ("MODERATE" if mg >= 0.001 else "UNKNOWN")
        top_s = rk[0][1]
        mean_s = np.mean([s for _, s in rk])
        ood = top_s - mean_s
        print("   {:10} #1={:20} margin={:.6f} tier={:8} OOD_conf={:.4f}".format(
            label, rk[0][0], mg, tier, ood))

# ============================================================
# PART 4: SEED DATASET WITH BEST WEIGHT COMBO (ALPHA=0.01)
# ============================================================
print()
print("=" * 80)
print("SEED DATASET: ALPHA=0.01, MULTIPLE WEIGHTS")
print("=" * 80)

feat_files = sorted([f for f in os.listdir(FEAT_DIR) if f.endswith(".npz")])

for pcd_w, dyad_w, label in weight_combos:
    correct_high = 0
    correct_mod = 0
    unknown = 0
    wrong = 0
    total = 0

    for feat_file in feat_files:
        fpath = os.path.join(FEAT_DIR, feat_file)
        data = np.load(fpath, allow_pickle=True)
        if "feature_version" not in data or str(data["feature_version"]) != "v1.2":
            continue
        if float(data["gating_ratio"]) < 0.05:
            continue

        true_raga = str(data["raga"])
        cents = data["cents_gated"]
        if len(cents) < 200:
            continue

        total += 1
        hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
        pcd = hist / np.sum(hist)
        t_up, t_down = compute_dyads_for_test(cents, alpha=0.01)
        sc = score_all(pcd, t_up, t_down, models_001, pcd_w, dyad_w)
        rk = sorted(sc.items(), key=lambda x: x[1], reverse=True)
        mg = rk[0][1] - rk[1][1]
        pred = rk[0][0]

        if mg >= 0.003:
            tier = "HIGH"
        elif mg >= 0.001:
            tier = "MODERATE"
        else:
            tier = "UNKNOWN"

        if pred == true_raga and tier in ("HIGH", "MODERATE"):
            if tier == "HIGH":
                correct_high += 1
            else:
                correct_mod += 1
        elif tier == "UNKNOWN":
            unknown += 1
        else:
            wrong += 1

    classified = total - unknown
    correct = correct_high + correct_mod
    acc = 100 * correct / max(1, classified)
    print("  {:10}  total={:2d}  HIGH={:2d}  MOD={:2d}  UNK={:2d}  WRONG={:2d}  acc={:.0f}%".format(
        label, total, correct_high, correct_mod, unknown, wrong, acc))

print()
print("Done. Compare results above to decide best weight combo.")
