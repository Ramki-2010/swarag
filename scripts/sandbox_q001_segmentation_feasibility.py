#!/usr/bin/env python3
"""
Q-001 FEASIBILITY SPIKE  --  Can the current pitch representation be reliably
quantized into swara sequences despite gamaka smearing?

This does NOT build a classifier. It answers one question: after the existing
stable-region collapse, does a target raga's characteristic swara subsequence
recur in its clips, and is it discriminative against a confuser raga?

Design (per workflow.md Promotion Rule, step 3: pre-register before running):
  - Reuses production extraction: librosa.pyin -> cents -> N_BINS digitize ->
    stable-region collapse (MIN_STABLE_FRAMES), imported from recognize_raga_v12
    so it cannot drift (ADR-015).
  - Maps each stable bin to a 12-TET swara index (bin // (N_BINS // 12)).
  - Collapses consecutive identical swaras into a symbol string per clip.
  - Counts the TARGET n-gram in target-raga clips vs confuser-raga clips.

Outcome is a PASS/FAIL against a line YOU set below, before looking at results.

    python sandbox_q001_segmentation_feasibility.py <audio_root>

<audio_root> should contain one subfolder per raga, each holding that raga's
.wav clips, e.g. <audio_root>/Abhogi/*.wav, <audio_root>/Kalyani/*.wav
"""

import os
import sys
import numpy as np
import librosa

# Import production constants -- do not redefine (ADR-015).
from recognize_raga_v12 import SR, N_BINS, MAX_DURATION_SEC, MIN_STABLE_FRAMES

# ============================================================================
# PRE-REGISTRATION  --  fill these in BEFORE running. The script refuses to run
# until they are set. Once set, do not change them after seeing results.
# ============================================================================

TARGET_RAGA   = None   # e.g. "Abhogi"   (research focus) or "Bhairavi" (accuracy focus)
CONFUSER_RAGA = None   # e.g. "Kalyani"  -- the raga it is most confused with

# Characteristic subsequence as 12-TET swara INDICES (Sa=0, R1=1, R2/G1=2,
# G2=3, G3=4, M1=5, M2=6, P=7, D1=8, D2/N1=9, N2=10, N3=11).
# NOTE: confirm these against the raga's actual scale before trusting a result.
# The docs' "M2-D2-M2 for Abhogi" is musicologically suspect (Abhogi has no M2).
TARGET_NGRAM   = None  # e.g. (5, 9, 5) for M1-D2-M1  -- CONFIRM with musicology
CONFUSER_NGRAM = None  # e.g. (7, 9, 11) for Pa-D2-N3 -- the confuser's signature

# The pass line. Q-001 PASSES only if BOTH hold:
PASS_MIN_TARGET_RECALL = None   # e.g. 0.60 : target n-gram present in >= 60% of target clips
PASS_MIN_DISCRIMINATION = None  # e.g. 3.0  : target-clip rate >= 3x confuser-clip rate

# ============================================================================

SWARAS_PER_OCTAVE = 12
BINS_PER_SWARA = N_BINS // SWARAS_PER_OCTAVE


def _check_preregistration():
    missing = [k for k, v in {
        "TARGET_RAGA": TARGET_RAGA, "CONFUSER_RAGA": CONFUSER_RAGA,
        "TARGET_NGRAM": TARGET_NGRAM, "CONFUSER_NGRAM": CONFUSER_NGRAM,
        "PASS_MIN_TARGET_RECALL": PASS_MIN_TARGET_RECALL,
        "PASS_MIN_DISCRIMINATION": PASS_MIN_DISCRIMINATION,
    }.items() if v is None]
    if missing:
        sys.exit("PRE-REGISTRATION INCOMPLETE. Set these first: " + ", ".join(missing))


def audio_to_swara_string(audio_path):
    """Production extraction -> stable held bins -> collapsed swara-index string."""
    y, _ = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)
    f0, _, _ = librosa.pyin(
        y, sr=SR,
        fmin=librosa.note_to_hz("C1"), fmax=librosa.note_to_hz("C6"),
    )
    f0 = f0[~np.isnan(f0)]
    if len(f0) == 0:
        return []

    # Tonic-relative cents. Tonic estimated as the median pitch (Sa reference).
    # If the pipeline uses an explicit tonic, substitute it here.
    tonic_hz = np.median(f0)
    cents = 1200.0 * np.log2(f0 / tonic_hz)
    cents = np.mod(cents, 1200.0)

    bins = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]
    if len(pitch_bins) < MIN_STABLE_FRAMES:
        return []

    # Stable-region detection -- identical logic to compute_directional_dyads().
    stable = []
    current, count = pitch_bins[0], 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable.append(current)
            current, count = b, 1
    if count >= MIN_STABLE_FRAMES:
        stable.append(current)

    # Bin -> swara index, then collapse consecutive duplicates.
    swaras = [int(b) // BINS_PER_SWARA for b in stable]
    collapsed = [swaras[0]] if swaras else []
    for s in swaras[1:]:
        if s != collapsed[-1]:
            collapsed.append(s)
    return collapsed


def count_ngram(seq, ngram):
    n = len(ngram)
    return sum(1 for i in range(len(seq) - n + 1) if tuple(seq[i:i + n]) == tuple(ngram))


def clip_rate(folder, ngram):
    """Returns (per-clip presence list, mean occurrences per clip)."""
    presence, occurrences = [], []
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".wav"):
            continue
        seq = audio_to_swara_string(os.path.join(folder, fn))
        c = count_ngram(seq, ngram)
        presence.append(1 if c > 0 else 0)
        occurrences.append(c)
        print(f"  {fn:40s} len={len(seq):3d}  target_ngram x{c}")
    return presence, occurrences


def main():
    _check_preregistration()
    if len(sys.argv) < 2:
        sys.exit("usage: sandbox_q001_segmentation_feasibility.py <audio_root>")
    root = sys.argv[1]

    print(f"\n[TARGET] {TARGET_RAGA}  ngram={TARGET_NGRAM}")
    tgt_presence, tgt_occ = clip_rate(os.path.join(root, TARGET_RAGA), TARGET_NGRAM)

    print(f"\n[CONFUSER] {CONFUSER_RAGA}  (same target ngram, expected rare)")
    conf_presence, _ = clip_rate(os.path.join(root, CONFUSER_RAGA), TARGET_NGRAM)

    tgt_recall = np.mean(tgt_presence) if tgt_presence else 0.0
    tgt_mean = np.mean(tgt_occ) if tgt_occ else 0.0
    conf_recall = np.mean(conf_presence) if conf_presence else 0.0
    discrimination = (tgt_recall / conf_recall) if conf_recall > 0 else float("inf")

    print("\n" + "=" * 60)
    print(f"Target n-gram recall in {TARGET_RAGA}:   {tgt_recall:.2%} "
          f"(mean {tgt_mean:.2f} / clip)")
    print(f"Target n-gram recall in {CONFUSER_RAGA}: {conf_recall:.2%}")
    print(f"Discrimination ratio:               {discrimination:.2f}x")
    print("-" * 60)
    passed = (tgt_recall >= PASS_MIN_TARGET_RECALL
              and discrimination >= PASS_MIN_DISCRIMINATION)
    print(f"Pre-registered line: recall >= {PASS_MIN_TARGET_RECALL:.0%} "
          f"AND discrimination >= {PASS_MIN_DISCRIMINATION:.1f}x")
    print(f"Q-001 RESULT: {'PASS -> proceed to Q-002' if passed else 'FAIL -> representation is the bottleneck'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
