# =============================================================================
# DEPRECATED -- early test phase script
# Used during initial project setup to verify librosa could load audio.
# Superseded by the full extraction pipeline in extract_pitch_batch_v12.py.
# Hardcoded to "test.wav" -- was never updated beyond this placeholder.
#
# Do not use.
# =============================================================================

import librosa

audio_path = "test.wav"  # we'll fix this path later

y, sr = librosa.load(audio_path, sr=None)

print("Audio loaded successfully")
print("Sample rate:", sr)
print("Number of samples:", len(y))
