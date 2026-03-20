"""
SANDBOX: Phase 1 — PCD-only scoring (DYAD_WEIGHT = 0.0)
FAST VERSION: Uses cached features for seed dataset, only extracts 4 test files.
"""
import sys, os, numpy as np, librosa
sys.path.insert(0, ".")
from utils import estimate_tonic

SR = 22050
MAX_DURATION_SEC = 360
N_BINS = 36
MIN_STABLE_FRAMES = 5
ALPHA = 0.5
EPS = 1e-8

AGG = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260310_063600"
TEST_DIR = r"D:\Swaragam\datasets\audio test"
FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"


def load_aggregated_models(folder):
    models = {}
    pcd_folder = os.path.join(folder, "pcd_stats")
    dyad_folder = os.path.join(folder, "dyad_stats")
    for fname in os.listdir(pcd_folder):
        if fname.endswith("_pcd_stats.npz"):
            raga = fname.replace("_pcd_stats.npz", "")
            dyad_path = os.path.join(dyad_folder, "{}_dyad_stats.npz".format(raga))
            if not os.path.exists(dyad_path):
                continue
            pcd_data = np.load(os.path.join(pcd_folder, fname), allow_pickle=True)
            dyad_data = np.load(dyad_path, allow_pickle=True)
            models[raga] = {
                "pcd": pcd_data["mean_pcd"],
                "mean_up": dyad_data["mean_up"],
                "mean_down": dyad_data["mean_down"],
            }
    return models


def compute_directional_dyads(cents):
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
    mat_up += ALPHA
    mat_down += ALPHA
    mat_up /= (np.sum(mat_up) + EPS)
    mat_down /= (np.sum(mat_down) + EPS)
    return mat_up.flatten(), mat_down.flatten()


def features_from_audio(audio_path):
    y, sr = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)
    f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C1"),
                            fmax=librosa.note_to_hz("C6"), sr=SR)
    valid = f0[~np.isnan(f0)]
    if len(valid) < 200:
        return None, None, None
    sa_hz = estimate_tonic(valid)
    cents = (1200 * np.log2(valid / sa_hz)) % 1200
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    if np.sum(hist) == 0:
        return None, None, None
    pcd = hist / np.sum(hist)
    test_up, test_down = compute_directional_dyads(cents)
    return pcd, test_up, test_down


def features_from_cached(npz_path):
    """Load pre-extracted features from .npz and compute PCD + dyads."""
    data = np.load(npz_path, allow_pickle=True)
    cents = data["cents_gated"]
    raga = str(data["raga"])
    if len(cents) < 200:
        return None, None, None, raga
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    if np.sum(hist) == 0:
        return None, None, None, raga
    pcd = hist / np.sum(hist)
    test_up, test_down = compute_directional_dyads(cents)
    return pcd, test_up, test_down, raga


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
# LOAD MODELS
# ============================================================
models = load_aggregated_models(AGG)
print("Loaded {} raga models: {}".format(len(models), ", ".join(sorted(models.keys()))))
print()

# ============================================================
# PART 1: RANDOM TEST FILES (4 files, extract from audio)
# ============================================================
print("=" * 80)
print("RANDOM TEST FILES: PCD-ONLY (1.0/0.0) vs CURRENT (0.6/0.4)")
print("=" * 80)
print()

test_files = [
    ("Alapana_HAM_Test.wav", "OOD_Hamsadwani"),
    ("Alapana_Moha_Test.wav", "OOD_Mohanam"),
    ("Balap_Test.wav", "Bhairavi"),
    ("Kalap_Test.wav", "Kalyani"),
]

for fname, expected in test_files:
    fpath = os.path.join(TEST_DIR, fname)
    print(">> Extracting: {} ...".format(fname))
    pcd, test_up, test_down = features_from_audio(fpath)
    if pcd is None:
        print("   FAILED")
        continue

    # Current (0.6/0.4)
    sc_cur = score_all(pcd, test_up, test_down, models, 0.6, 0.4)
    rk_cur = sorted(sc_cur.items(), key=lambda x: x[1], reverse=True)
    mg_cur = rk_cur[0][1] - rk_cur[1][1]

    # PCD-only (1.0/0.0)
    sc_pcd = score_all(pcd, test_up, test_down, models, 1.0, 0.0)
    rk_pcd = sorted(sc_pcd.items(), key=lambda x: x[1], reverse=True)
    mg_pcd = rk_pcd[0][1] - rk_pcd[1][1]
    top_score = rk_pcd[0][1]
    mean_score = np.mean([s for _, s in rk_pcd])
    ood_conf = top_score - mean_score

    # Tier
    if mg_pcd >= 0.003:
        tier = "HIGH"
    elif mg_pcd >= 0.001:
        tier = "MODERATE"
    else:
        tier = "UNKNOWN"

    print("   Expected: {}".format(expected))
    print("   Current (0.6/0.4): #1={:20} margin={:.6f}".format(rk_cur[0][0], mg_cur))
    print("   PCD-only (1.0/0.0): #1={:20} margin={:.6f} tier={} OOD_conf={:.4f}".format(
        rk_pcd[0][0], mg_pcd, tier, ood_conf))
    print("   Margin improvement: {:.1f}x".format(mg_pcd / mg_cur if mg_cur > 0 else 0))
    print()

# ============================================================
# PART 2: SEED DATASET (50 files, use cached features)
# ============================================================
print("=" * 80)
print("SEED DATASET: PCD-ONLY SELF-RECOGNITION (from cached features)")
print("=" * 80)
print()

feat_files = sorted([f for f in os.listdir(FEAT_DIR) if f.endswith(".npz")])
correct_high = 0
correct_mod = 0
ranking_correct_unknown = 0
wrong = 0
total = 0
wrong_list = []
raga_stats = {}

for feat_file in feat_files:
    pcd, test_up, test_down, true_raga = features_from_cached(
        os.path.join(FEAT_DIR, feat_file))
    if pcd is None:
        continue

    total += 1
    sc = score_all(pcd, test_up, test_down, models, 1.0, 0.0)
    rk = sorted(sc.items(), key=lambda x: x[1], reverse=True)
    mg = rk[0][1] - rk[1][1]
    pred = rk[0][0]
    top_s = rk[0][1]
    mean_s = np.mean([s for _, s in rk])
    ood_conf = top_s - mean_s

    if mg >= 0.003:
        tier = "HIGH"
    elif mg >= 0.001:
        tier = "MODERATE"
    else:
        tier = "UNKNOWN"

    if true_raga not in raga_stats:
        raga_stats[true_raga] = {"high": 0, "mod": 0, "unk": 0, "wrong": 0, "margins": []}

    if pred == true_raga and tier == "HIGH":
        correct_high += 1
        raga_stats[true_raga]["high"] += 1
    elif pred == true_raga and tier == "MODERATE":
        correct_mod += 1
        raga_stats[true_raga]["mod"] += 1
    elif pred == true_raga and tier == "UNKNOWN":
        ranking_correct_unknown += 1
        raga_stats[true_raga]["unk"] += 1
    elif tier == "UNKNOWN":
        ranking_correct_unknown += 1
        raga_stats[true_raga]["unk"] += 1
    else:
        wrong += 1
        raga_stats[true_raga]["wrong"] += 1
        wrong_list.append((feat_file[:40], true_raga, pred, mg))

    raga_stats[true_raga]["margins"].append(mg)

# Print per-raga results
for raga in sorted(raga_stats.keys()):
    s = raga_stats[raga]
    n = s["high"] + s["mod"] + s["unk"] + s["wrong"]
    mm = np.mean(s["margins"])
    print("  {:20} n={:2d}  HIGH={:2d}  MOD={:2d}  UNK={:2d}  WRONG={:2d}  mean_margin={:.4f}".format(
        raga, n, s["high"], s["mod"], s["unk"], s["wrong"], mm))

if wrong_list:
    print()
    print("MISCLASSIFICATIONS:")
    for f, true, pred, mg in wrong_list:
        print("  {} true={} pred={} margin={:.4f}".format(f, true, pred, mg))

print()
print("TOTALS (PCD-only, 1.0/0.0):")
print("  Total:     {}".format(total))
print("  HIGH:      {} ({:.0f}%)".format(correct_high, 100*correct_high/max(1,total)))
print("  MODERATE:  {} ({:.0f}%)".format(correct_mod, 100*correct_mod/max(1,total)))
print("  UNKNOWN:   {} ({:.0f}%)".format(ranking_correct_unknown, 100*ranking_correct_unknown/max(1,total)))
print("  WRONG:     {} ({:.0f}%)".format(wrong, 100*wrong/max(1,total)))
print("  Classified correctly: {} / {} ({:.0f}%)".format(
    correct_high + correct_mod, total - ranking_correct_unknown,
    100*(correct_high+correct_mod)/max(1, total-ranking_correct_unknown)))

