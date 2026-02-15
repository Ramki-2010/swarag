import librosa

audio_path = "test.wav"  # we'll fix this path later

y, sr = librosa.load(audio_path, sr=None)

print("Audio loaded successfully")
print("Sample rate:", sr)
print("Number of samples:", len(y))
