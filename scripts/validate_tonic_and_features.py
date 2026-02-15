import os
import numpy as np

RAW_DIR = r"D:\Swagaram\pcd_results\features_raw"
VALIDATED_DIR = r"D:\Swagaram\pcd_results\features_validated"

os.makedirs(VALIDATED_DIR, exist_ok=True)


def tonic_score(f0, voiced_flag, sa_hz):
    """
    Score a tonic candidate based on internal structure.
    Higher is better.
    """
    f0v = f0[voiced_flag]
    f0v = f0v[~np.isnan(f0v)]

    if len(f0v) < 100:
        return -np.inf

    cents = 1200 * np.log2(f0v / sa_hz)
    cents = cents[(cents > -1200) & (cents < 1200)]

    if len(cents) == 0:
        return -np.inf

    # 1. Density near Sa
    sa_density = np.mean(np.abs(cents) < 50)

    # 2. Continuity (how often pitch stays near Sa across frames)
    near_sa = np.abs(cents) < 50
    continuity = np.mean(near_sa[:-1] & near_sa[1:])

    # Weighted score
    return 0.7 * sa_density + 0.3 * continuity


def validate_file(npz_path):
    data = np.load(npz_path, allow_pickle=True)

    f0 = data["f0"]
    voiced_flag = data["voiced_flag"]
    candidates = data["tonic_candidates"]
    original_sa = float(data["sa_hz"])

    scores = {}
    for sa in candidates:
        scores[float(sa)] = tonic_score(f0, voiced_flag, float(sa))

    best_sa = max(scores, key=scores.get)

    # Copy everything, override only Sa if needed
    out_data = dict(data)

    out_data["sa_hz_raw"] = original_sa
    out_data["sa_hz_validated"] = best_sa
    out_data["tonic_scores"] = scores
    out_data["schema_version"] = "2.0"

    fname = os.path.basename(npz_path)
    out_path = os.path.join(VALIDATED_DIR, fname)

    np.savez(out_path, **out_data)

    print(f"Validated: {fname}")
    if abs(np.log2(best_sa / original_sa)) > 0.5:
        print(f"  Octave adjustment: {original_sa:.2f} → {best_sa:.2f}")


def run():
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".npz")]

    for f in files:
        validate_file(os.path.join(RAW_DIR, f))


if __name__ == "__main__":
    run()
