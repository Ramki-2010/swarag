import numpy as np

def estimate_tonic(f0):
    """
    Histogram-based tonic (Sa) estimation.
    Must match extraction logic exactly.
    """
    f0 = f0[~np.isnan(f0)]

    if len(f0) < 200:
        raise ValueError("Not enough voiced frames for tonic estimation")

    log_f0 = np.log2(f0)
    hist, bins = np.histogram(log_f0, bins=120)

    sa_log = bins[np.argmax(hist)]
    sa_hz = 2 ** sa_log

    return sa_hz
