"""Extract features for the 5 new Thodi vocal-isolated clips only."""
import os, sys, numpy as np, librosa
sys.path.insert(0, ".")
from utils import estimate_tonic

SR = 22050
MAX_DURATION_SEC = 360
N_BINS = 36
FEATURE_VERSION = "v1.2"
FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"

new_files = [
    r"D:\Swaragam\datasets\seed_carnatic\Thodi\05-Koluvamaregada-MalladiBros.vocal.wav",
    r"D:\Swaragam\datasets\seed_carnatic\Thodi\19b_FILLER_gajavadana_thodi_krithi-ssi-c09.vocal.wav",
    r"D:\Swaragam\datasets\seed_carnatic\Thodi\kamalambike.vocal.wav",
    r"D:\Swaragam\datasets\seed_carnatic\Thodi\MS Subbulakshmi-Dasharathi Ni Runamu-Adi-Todi-Thyagaraja.vocal.wav",
    r"D:\Swaragam\datasets\seed_carnatic\Thodi\nI-vantidaivamu-HydBros.vocal.wav",
]

for fpath in new_files:
    fname = os.path.basename(fpath)
    print(">> Extracting: {} ...".format(fname))
    
    y, sr = librosa.load(fpath, sr=SR, duration=MAX_DURATION_SEC)
    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C1"),
                                       fmax=librosa.note_to_hz("C6"), sr=SR)
    valid = f0[~np.isnan(f0)]
    
    if len(valid) < 200:
        print("   SKIPPED: only {} voiced frames".format(len(valid)))
        continue
    
    sa_hz = estimate_tonic(valid)
    cents = (1200 * np.log2(valid / sa_hz)) % 1200
    
    # Gating ratio
    gating_ratio = len(valid) / len(f0)
    
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = "{}_{}.npz".format(fname.replace(".vocal.wav", "").replace(".wav", ""), ts)
    out_path = os.path.join(FEAT_DIR, out_name)
    
    np.savez(out_path,
             feature_version=FEATURE_VERSION,
             raga="Thodi",
             sa_hz=sa_hz,
             f0=f0,
             voiced_flag=voiced_flag,
             cents_gated=cents,
             gating_ratio=gating_ratio,
             window_size=0,
             drift_threshold=0,
             voiced_ratio_threshold=0)
    
    # Quick PCD check
    hist, _ = np.histogram(cents, bins=N_BINS, range=(0, 1200))
    pcd = hist / np.sum(hist)
    entropy = -np.sum(pcd * np.log(pcd + 1e-10))
    
    print("   frames={} tonic={:.1f}Hz gating={:.2f} entropy={:.3f}".format(
        len(valid), sa_hz, gating_ratio, entropy))
    print("   Saved: {}".format(out_name))
    print()

print("Done! Now re-aggregate.")
