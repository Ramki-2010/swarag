import numpy as np


def _choose_best_tonic(peaks_hz, pitch_values):
    """
    Identical to choose_best_tonic() in extract_pitch_batch_v12.py.
    Expands each peak across octaves (x0.5, x1.0, x2.0), filters to
    the vocal Sa range (80-400 Hz), then scores each candidate by how
    many pitch frames fall within 50 cents of it.
    """
    candidates = []

    for hz in peaks_hz:
        for mult in (0.5, 1.0, 2.0):
            cand = hz * mult
            if 80 <= cand <= 400:
                candidates.append(cand)

    scores = []
    for cand in candidates:
        cents = 1200 * np.log2(pitch_values / cand)
        cents = cents[(cents > -1200) & (cents < 1200)]
        score = np.sum(np.abs(cents) < 50)
        scores.append(score)

    return candidates[np.argmax(scores)]


def estimate_tonic(f0):
    """
    Canonical tonic (Sa) estimator -- mirrors extract_pitch_batch_v12.py exactly.

    Previously used argmax on a log-Hz histogram (120 bins), which returned
    the most frequently occurring pitch -- not necessarily Sa.

    Now uses the same two-step logic as the extraction pipeline:
      1. Linear-Hz histogram (200 bins) -> top 5 peaks
      2. Octave-aware candidate scoring via _choose_best_tonic()
    """
    f0 = f0[~np.isnan(f0)]

    if len(f0) < 200:
        raise ValueError("Not enough voiced frames for tonic estimation")

    hist, bin_edges = np.histogram(f0, bins=200)
    top_idx  = np.argsort(hist)[-5:]
    peaks_hz = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in top_idx]

    return _choose_best_tonic(peaks_hz, f0)
