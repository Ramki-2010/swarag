import librosa
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Load audio
# -----------------------------
audio_path = r"D:\Swagaram\datasets\seed_carnatic\Bhairavi\Bhairavi_clean_1.wav"
y, sr = librosa.load(audio_path, sr=22050)

# -----------------------------
# Pitch extraction (pYIN)
# -----------------------------
f0, voiced_flag, _ = librosa.pyin(
    y,
    fmin=librosa.note_to_hz("G2"),
    fmax=librosa.note_to_hz("E5")
)

# Keep only voiced frames
valid_f0 = f0[~np.isnan(f0)]

print("Min pitch (Hz):", round(np.min(valid_f0), 2))
print("Max pitch (Hz):", round(np.max(valid_f0), 2))

# -----------------------------
# Estimate Sa (tonic) using histogram
# -----------------------------
hist, bin_edges = np.histogram(
    valid_f0,
    bins=200
)

max_bin = np.argmax(hist)
sa_estimate = (bin_edges[max_bin] + bin_edges[max_bin + 1]) / 2

print("Estimated Sa (Hz):", round(sa_estimate, 2))

# -----------------------------
# Convert pitch → cents relative to Sa
# -----------------------------
cents = 1200 * np.log2(valid_f0 / sa_estimate)

# Fold into one octave (0–1200)
cents_mod = np.mod(cents, 1200)

# -----------------------------
# Visualization (optional, diagnostic)
# -----------------------------
plt.figure(figsize=(10, 4))
plt.hist(cents_mod, bins=36, range=(0, 1200))
plt.xlabel("Cents (Sa = 0)")
plt.ylabel("Count")
plt.title("Pitch-Class Distribution (Tonic-normalized)")
plt.show()
