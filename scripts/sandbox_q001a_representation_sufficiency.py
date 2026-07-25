#!/usr/bin/env python3
"""
Q-001A  --  REPRESENTATION SUFFICIENCY EXPERIMENT

ONE question: does the production extraction pipeline convert audio into stable,
meaningful swara sequences -- enough to make phrase modelling (Q-001B) possible?
No phrases, no n-grams. "Meaningful" is measured against each raga's KNOWN scale
(a musicological fact).

Method -- identical to production, imported not reimplemented (ADR-015):
  librosa.pyin -> estimate_tonic() (utils.py canonical Sa) ->
  cents = 1200*log2(f0/Sa) % 1200 -> N_BINS digitize ->
  stable-region collapse (MIN_STABLE_FRAMES) -> swara index = bin // (N_BINS/12)

Per-clip metrics:
  coverage        voiced frames retained by the stability filter (printed, NOT gated)
  prec_raw        held swaras belonging to the raga scale (token-weighted)
  prec_corrected  chance-corrected: (raw - chance)/(1 - chance), chance = |scale|/12
                  -> neutralises the pentatonic-vs-heptatonic bias (first-order:
                     assumes uniform smearing; real gamaka smearing is local)
  recall          scale swaras that actually appear
  residual_cents  mean distance of held pitches to nearest 12-TET grid centre
                  (grid-alignment / gamaka-smear magnitude; not scale membership)

Threshold is DERIVED from the reference ragas, not chosen. Abhogi passes only if
its CHANCE-CORRECTED precision >= the reference floor AND residual <= ceiling.

    python sandbox_q001a_representation_sufficiency.py <audio_root>
    # <audio_root>/<Raga>/*.wav
"""

import os
import sys
import csv
import time
import numpy as np
import librosa

from recognize_raga_v12 import SR, N_BINS, MAX_DURATION_SEC, MIN_STABLE_FRAMES
from utils import estimate_tonic

TARGET_RAGA     = "Abhogi"
REFERENCE_RAGAS = ["Kalyani", "Shankarabharanam"]  # easy/high-accuracy -> set the band

# Known scales as 12-TET pitch positions (Sa=0). Raga definitions, not guesses.
SCALES = {
    "Abhogi":            {0, 2, 3, 5, 9},          # S R2 G2 M1 D2
    "Kalyani":           {0, 2, 4, 6, 7, 9, 11},   # S R2 G3 M2 P D2 N3
    "Shankarabharanam":  {0, 2, 4, 5, 7, 9, 11},   # S R2 G3 M1 P D2 N3
}

BINS_PER_SWARA = N_BINS // 12
CENTS_PER_BIN  = 1200.0 / N_BINS


def stable_bins_from_audio(audio_path):
    y, _ = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)
    f0, _, _ = librosa.pyin(y, sr=SR,
                            fmin=librosa.note_to_hz("C1"),
                            fmax=librosa.note_to_hz("C6"))
    valid = f0[~np.isnan(f0)]
    if len(valid) < 200:
        return None, 0.0
    sa_hz = estimate_tonic(valid)
    cents = (1200 * np.log2(valid / sa_hz)) % 1200
    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]
    if len(pitch_bins) < MIN_STABLE_FRAMES:
        return None, 0.0
    stable, retained = [], 0
    current, count = pitch_bins[0], 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable.append(current); retained += count
            current, count = b, 1
    if count >= MIN_STABLE_FRAMES:
        stable.append(current); retained += count
    return stable, retained / len(pitch_bins)


def clip_metrics(stable_bins, scale):
    if not stable_bins:
        return None
    swaras = [int(b) // BINS_PER_SWARA for b in stable_bins]
    prec_raw = sum(1 for s in swaras if s in scale) / len(swaras)
    chance = len(scale) / 12.0
    prec_corr = (prec_raw - chance) / (1 - chance) if chance < 1 else 0.0
    recall = len(set(swaras) & scale) / len(scale)
    residual = float(np.mean([
        min(b % BINS_PER_SWARA, BINS_PER_SWARA - (b % BINS_PER_SWARA)) * CENTS_PER_BIN
        for b in stable_bins
    ]))
    return dict(prec_raw=prec_raw, prec_corr=prec_corr, chance=chance,
                recall=recall, residual=residual)


def eval_raga(root, raga, writer):
    folder = os.path.join(root, raga)
    scale = SCALES[raga]
    rows = []
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".wav"):
            continue
        stable, coverage = stable_bins_from_audio(os.path.join(folder, fn))
        m = clip_metrics(stable, scale)
        if m is None:
            print(f"  {fn:38s} SKIPPED (insufficient voiced frames)")
            writer.writerow([raga, fn, "", "", "", "", "", "SKIPPED"])
            continue
        rows.append((coverage, m["prec_raw"], m["prec_corr"], m["recall"], m["residual"]))
        print(f"  {fn:38s} cov={coverage:.2f} prec={m['prec_raw']:.2f} "
              f"corr={m['prec_corr']:+.2f} rec={m['recall']:.2f} resid={m['residual']:5.1f}c")
        writer.writerow([raga, fn, f"{coverage:.4f}", f"{m['prec_raw']:.4f}",
                         f"{m['prec_corr']:.4f}", f"{m['recall']:.4f}",
                         f"{m['residual']:.2f}", ""])
    if not rows:
        return None
    a = np.array(rows)
    return dict(coverage=a[:,0].mean(), prec_raw=a[:,1].mean(),
                prec_corr=a[:,2].mean(), recall=a[:,3].mean(),
                residual=a[:,4].mean(), n=len(rows))


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: sandbox_q001a_representation_sufficiency.py <audio_root>")
    root = sys.argv[1]
    t0 = time.time()
    csv_path = f"q001a_per_clip_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["raga", "clip", "coverage", "prec_raw",
                         "prec_corrected", "recall", "residual_cents", "note"])
        ref_stats = {}
        for r in REFERENCE_RAGAS:
            print(f"\n[REFERENCE] {r}")
            s = eval_raga(root, r, writer)
            if s: ref_stats[r] = s
        print(f"\n[TARGET] {TARGET_RAGA}")
        tgt = eval_raga(root, TARGET_RAGA, writer)

    if not ref_stats or tgt is None:
        sys.exit("Insufficient data to establish band or evaluate target.")

    prec_floor    = min(s["prec_corr"] for s in ref_stats.values())
    resid_ceiling = max(s["residual"]  for s in ref_stats.values())

    print("\n" + "=" * 70)
    print("REFERENCE BAND")
    for r, s in ref_stats.items():
        print(f"  {r:18s} prec_raw={s['prec_raw']:.2f} prec_corr={s['prec_corr']:+.2f} "
              f"resid={s['residual']:5.1f}c cov={s['coverage']:.2f} (n={s['n']})")
    print(f"  Derived threshold: prec_corrected >= {prec_floor:+.2f} "
          f"AND residual <= {resid_ceiling:.1f}c")
    print("-" * 70)
    print(f"TARGET  {TARGET_RAGA}")
    print(f"  prec_raw={tgt['prec_raw']:.2f} prec_corr={tgt['prec_corr']:+.2f} "
          f"resid={tgt['residual']:5.1f}c cov={tgt['coverage']:.2f} (n={tgt['n']})")
    print("-" * 70)
    passed = tgt["prec_corr"] >= prec_floor and tgt["residual"] <= resid_ceiling
    if passed:
        print(f"Q-001A: PASS -- representation is sufficient for {TARGET_RAGA}. "
              "Define Q-001B (phrase-candidate discovery).")
    else:
        print(f"Q-001A: FAIL -- representation degrades on {TARGET_RAGA} vs easy "
              "ragas. The bottleneck is the representation, not phrase modelling.")
    print(f"per-clip data: {csv_path}   runtime: {time.time()-t0:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
