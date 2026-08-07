#!/usr/bin/env python3
"""
Q-001A  --  REPRESENTATION SUFFICIENCY EXPERIMENT

ONE question: does the production extraction pipeline convert audio into stable,
meaningful swara sequences -- enough to make phrase modelling (Q-001B) possible?
No phrases, no n-grams. "Meaningful" is measured against each raga's KNOWN scale.

Method -- identical to production, imported not reimplemented (ADR-015):
  librosa.pyin -> estimate_tonic() (utils.py canonical Sa) ->
  cents = 1200*log2(f0/Sa) % 1200 -> N_BINS digitize ->
  stable-region collapse (MIN_STABLE_FRAMES) -> swara index = bin // (N_BINS/12)

Metrics: coverage, prec_raw, prec_corrected (chance = |scale|/12), recall,
residual_cents. Threshold derived from reference ragas.

--- PERFORMANCE DIAGNOSTICS (added; experiment logic/metrics UNCHANGED) ---
Prints filename before extraction, per-clip elapsed, cumulative N/total progress,
a slowest-clips summary, and a pyin-vs-total timing breakdown. pyin is expected
to dominate: production caches it in .npz; this sandbox re-runs it live.

    python sandbox_q001a_representation_sufficiency.py <audio_root>
    # <audio_root>/<Raga>/*.wav
"""

import os
import re
import csv
import glob
import time
import argparse
import numpy as np
import librosa

from recognize_raga_v12 import SR, N_BINS, MAX_DURATION_SEC, MIN_STABLE_FRAMES
from utils import estimate_tonic

TARGET_RAGA     = "Abhogi"
REFERENCE_RAGAS = ["Kalyani", "Shankarabharanam"]

SCALES = {
    "Abhogi":            {0, 2, 3, 5, 9},
    "Kalyani":           {0, 2, 4, 6, 7, 9, 11},
    "Shankarabharanam":  {0, 2, 4, 5, 7, 9, 11},
}

BINS_PER_SWARA = N_BINS // 12
CENTS_PER_BIN  = 1200.0 / N_BINS

# Accepted formats -- mirrors extract_pitch_batch_v12.py exactly (production set).
AUDIO_EXTS = (".wav", ".mp3", ".flac")

# Production feature cache (extract_pitch_batch_v12.py). f0 is the raw pyin
# output; reusing it skips the ONLY expensive step. Set via --feature-dir.
from feature_constants import FEATURE_VERSION   # single source of truth (ADR-015)
FEATURE_DIR = None                       # None -> always live pyin
_TS_RE = re.compile(r"\d{8}_\d{6}")      # {base}_{YYYYMMDD}_{HHMMSS}.npz

# --- diagnostics accumulators (do not affect metrics) ---
_PYIN_SECONDS = []              # per-clip pyin wall time
_CLIP_TIMES   = []              # (elapsed_seconds, "raga/clip")
_SOURCES      = []              # "cache" | "live" per clip


def _find_cached_npz(audio_path):
    """Newest version-matching .npz for this clip, or None. Mirrors producer naming."""
    if not FEATURE_DIR:
        return None
    base = os.path.splitext(os.path.basename(audio_path))[0]
    hits = []
    for cand in glob.glob(os.path.join(FEATURE_DIR, f"{base}_*.npz")):
        tail = os.path.basename(cand)[len(base) + 1:-4]     # strip "{base}_" and ".npz"
        if not _TS_RE.fullmatch(tail):
            continue                                        # different clip sharing a prefix
        try:
            fv = str(np.load(cand, allow_pickle=True)["feature_version"])
        except Exception:
            continue
        if fv == FEATURE_VERSION:
            hits.append((tail, cand))                       # tail sorts lexically by timestamp
    return max(hits)[1] if hits else None


def get_f0(audio_path):
    """Return (f0, source). Prefers cached raw pyin output; falls back to live pyin."""
    npz = _find_cached_npz(audio_path)
    if npz is not None:
        _SOURCES.append("cache")
        return np.load(npz, allow_pickle=True)["f0"], "cache"
    y, _ = librosa.load(audio_path, sr=SR, duration=MAX_DURATION_SEC)
    _t = time.time()
    f0, _, _ = librosa.pyin(y, sr=SR,
                            fmin=librosa.note_to_hz("C1"),
                            fmax=librosa.note_to_hz("C6"))
    _PYIN_SECONDS.append(time.time() - _t)   # diagnostic only (live path)
    _SOURCES.append("live")
    return f0, "live"


def stable_bins_from_f0(f0):
    """Downstream of pyin -- UNCHANGED logic. f0 in (cache or live) -> (stable, coverage)."""
    valid = f0[~np.isnan(f0)]
    if len(valid) < 200:
        return None, 0.0
    sa_hz = estimate_tonic(valid)                # recompute tonic from f0 (proven == cached sa_hz)
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


def stable_bins_from_audio(audio_path):
    f0, source = get_f0(audio_path)
    stable, coverage = stable_bins_from_f0(f0)
    return stable, coverage, source


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


def _audio_files(folder):
    return [f for f in sorted(os.listdir(folder)) if f.lower().endswith(AUDIO_EXTS)]


def eval_raga(root, raga, writer, counter, total):
    folder = os.path.join(root, raga)
    scale = SCALES[raga]
    rows = []
    for fn in _audio_files(folder):
        counter[0] += 1
        codec = os.path.splitext(fn)[1].lstrip(".").lower()
        # (1) filename + (3) cumulative progress, printed BEFORE pyin runs
        print(f"[{counter[0]:>3}/{total}] {raga}/{fn} -- extracting...", flush=True)
        t_clip = time.time()
        try:
            stable, coverage, source = stable_bins_from_audio(os.path.join(folder, fn))
        except Exception as e:                          # decode/other failure -> skip, do not crash
            dt = time.time() - t_clip
            _CLIP_TIMES.append((dt, f"{raga}/{fn}"))
            print(f"           LOAD_FAILED ({type(e).__name__}: {e})  [{dt:.1f}s]")
            writer.writerow([raga, fn, codec, "", "", "", "", "", f"LOAD_FAILED:{type(e).__name__}"])
            continue
        dt = time.time() - t_clip                       # (2) per-clip elapsed
        _CLIP_TIMES.append((dt, f"{raga}/{fn}"))
        m = clip_metrics(stable, scale)
        if m is None:
            print(f"           SKIPPED (insufficient voiced frames)  [{source}] [{dt:.1f}s]")
            writer.writerow([raga, fn, codec, "", "", "", "", "", f"SKIPPED({source})"])
            continue
        rows.append((coverage, m["prec_raw"], m["prec_corr"], m["recall"], m["residual"]))
        print(f"           cov={coverage:.2f} prec={m['prec_raw']:.2f} "
              f"corr={m['prec_corr']:+.2f} rec={m['recall']:.2f} "
              f"resid={m['residual']:5.1f}c  [{codec}|{source}]  [{dt:.1f}s]")
        writer.writerow([raga, fn, codec, f"{coverage:.4f}", f"{m['prec_raw']:.4f}",
                         f"{m['prec_corr']:.4f}", f"{m['recall']:.4f}",
                         f"{m['residual']:.2f}", ""])
    if not rows:
        return None
    a = np.array(rows)
    return dict(coverage=a[:,0].mean(), prec_raw=a[:,1].mean(),
                prec_corr=a[:,2].mean(), recall=a[:,3].mean(),
                residual=a[:,4].mean(), n=len(rows),
                pc=a[:,2].tolist(), rc=a[:,4].tolist())   # per-clip, for the separation test


def _cohens_d(a, b):
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    sp = np.sqrt(((na-1)*a.var(ddof=1) + (nb-1)*b.var(ddof=1)) / (na+nb-2))
    return (a.mean() - b.mean()) / sp if sp else float("nan")


def _perm_p(a, b, iters=50000, seed=0):
    """Two-sided permutation test on the difference of means."""
    a, b = np.asarray(a), np.asarray(b)
    rng = np.random.default_rng(seed)
    obs = abs(a.mean() - b.mean())
    pool = np.concatenate([a, b]); na = len(a); hit = 0
    for _ in range(iters):
        rng.shuffle(pool)
        if abs(pool[:na].mean() - pool[na:].mean()) >= obs:
            hit += 1
    return (hit + 1) / (iters + 1)


def run(root):
    t0 = time.time()
    results_dir = r"D:\Swaragam\Q001A sufficiency results"
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(
        results_dir,
        f"q001a_per_clip_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    )

    all_ragas = REFERENCE_RAGAS + [TARGET_RAGA]
    total = sum(len(_audio_files(os.path.join(root, r))) for r in all_ragas)
    print(f"Q-001A diagnostics | SR={SR} Hz | duration cap={MAX_DURATION_SEC}s "
          f"(~{MAX_DURATION_SEC//60} min) | formats {AUDIO_EXTS} | {total} clips\n")

    counter = [0]
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["raga", "clip", "codec", "coverage", "prec_raw",
                         "prec_corrected", "recall", "residual_cents", "note"])
        ref_stats = {}
        for r in REFERENCE_RAGAS:
            print(f"\n[REFERENCE] {r}")
            s = eval_raga(root, r, writer, counter, total)
            if s: ref_stats[r] = s
        print(f"\n[TARGET] {TARGET_RAGA}")
        tgt = eval_raga(root, TARGET_RAGA, writer, counter, total)

    if not ref_stats or tgt is None:
        raise SystemExit("Insufficient data to establish band or evaluate target.")

    prec_floor    = min(s["prec_corr"] for s in ref_stats.values())
    resid_ceiling = max(s["residual"]  for s in ref_stats.values())

    print("\n" + "=" * 70)
    print("REFERENCE BAND")
    for r, s in ref_stats.items():
        print(f"  {r:18s} prec_raw={s['prec_raw']:.2f} prec_corr={s['prec_corr']:+.2f} "
              f"resid={s['residual']:5.1f}c cov={s['coverage']:.2f} (n={s['n']})")
    print(f"  (min-of-references band prec>={prec_floor:+.2f} resid<={resid_ceiling:.1f}c "
          "-- DESCRIPTIVE ONLY, not the verdict)")
    print("-" * 70)
    print(f"TARGET  {TARGET_RAGA}")
    print(f"  prec_raw={tgt['prec_raw']:.2f} prec_corr={tgt['prec_corr']:+.2f} "
          f"resid={tgt['residual']:5.1f}c cov={tgt['coverage']:.2f} (n={tgt['n']})")
    print("-" * 70)

    # Verdict = distribution separation of TARGET vs pooled references, NOT a
    # mean-vs-threshold binary (which is verdict-fragile at small n; see L-052).
    ref_pc = [v for s in ref_stats.values() for v in s["pc"]]
    ref_rc = [v for s in ref_stats.values() for v in s["rc"]]
    tgt_pc, tgt_rc = tgt["pc"], tgt["rc"]
    p_prec, d_prec = _perm_p(ref_pc, tgt_pc), _cohens_d(ref_pc, tgt_pc)
    p_res,  d_res  = _perm_p(ref_rc, tgt_rc), _cohens_d(ref_rc, tgt_rc)
    ref_med, tgt_med = float(np.median(ref_pc)), float(np.median(tgt_pc))
    beats = int((np.asarray(tgt_pc) > ref_med).sum())

    print("SEPARATION TEST (target vs pooled references)")
    print(f"  corrected precision: ref median {ref_med:+.2f} | {TARGET_RAGA} median "
          f"{tgt_med:+.2f} | perm p={p_prec:.3f} | Cohen's d={d_prec:+.2f}")
    print(f"  residual cents:      perm p={p_res:.3f} | Cohen's d={d_res:+.2f}")
    print(f"  {TARGET_RAGA} clips above reference median: {beats}/{len(tgt_pc)}")
    print("-" * 70)

    worse_sig = p_prec < 0.05 and np.mean(tgt_pc) < np.mean(ref_pc)
    if worse_sig:
        print(f"Q-001A: TARGET SIGNIFICANTLY WORSE -- representation degrades on "
              f"{TARGET_RAGA} (p={p_prec:.3f}). Q-001B likely futile.")
    elif tgt_med >= ref_med:
        print(f"Q-001A: NO DEGRADATION -- {TARGET_RAGA} matches references "
              f"(p={p_prec:.3f}). Representation sufficient; Q-001B viable.")
    else:
        print(f"Q-001A: INCONCLUSIVE -- no significant separation (p={p_prec:.3f}, "
              f"d={d_prec:+.2f}). Representation NOT shown to be the bottleneck; "
              f"Q-001B remains viable. Underpowered at n={len(tgt_pc)}.")

    # ---- (4) slowest clips + (5) pyin-vs-total timing evidence ----
    total_rt = time.time() - t0
    pyin_total = sum(_PYIN_SECONDS)
    print("-" * 70)
    print("PERFORMANCE")
    nc = _SOURCES.count("cache"); nl = _SOURCES.count("live")
    print(f"  total runtime: {total_rt:.1f}s over {len(_CLIP_TIMES)} clips "
          f"({total_rt/max(len(_CLIP_TIMES),1):.1f}s/clip avg)")
    print(f"  f0 source: {nc} cache-hit, {nl} live-pyin")
    if _PYIN_SECONDS:
        print(f"  librosa.pyin: {pyin_total:.1f}s "
              f"({100*pyin_total/max(total_rt,1e-9):.0f}% of runtime) -- the bottleneck")
    print("  slowest clips:")
    for dt, label in sorted(_CLIP_TIMES, reverse=True)[:5]:
        print(f"    {dt:6.1f}s  {label}")
    print(f"per-clip data: {csv_path}")
    print("=" * 70)


def _metrics_from_f0(f0, scale):
    """Full Q-001A metric tuple from an f0 array (used by validation)."""
    stable, coverage = stable_bins_from_f0(f0)
    m = clip_metrics(stable, scale)
    if m is None:
        return None
    return (round(coverage, 6), round(m["prec_raw"], 6), round(m["prec_corr"], 6),
            round(m["recall"], 6), round(m["residual"], 6))


def run_validation(root):
    """One-time proof: for every clip with a cache, compare cached-f0 vs live-pyin.
    Passes only if f0 arrays match AND all five metrics are identical."""
    if not FEATURE_DIR:
        raise SystemExit("--validate requires --feature-dir (the cache to check).")
    print("VALIDATION MODE -- cached f0 vs live pyin (metrics must be identical)\n")
    checked = mism = nocache = 0
    for raga in REFERENCE_RAGAS + [TARGET_RAGA]:
        scale = SCALES[raga]
        folder = os.path.join(root, raga)
        if not os.path.isdir(folder):
            continue
        for fn in _audio_files(folder):
            path = os.path.join(folder, fn)
            npz = _find_cached_npz(path)
            if npz is None:
                nocache += 1
                print(f"  {raga}/{fn}: no cache -- skipped")
                continue
            f0_cache = np.load(npz, allow_pickle=True)["f0"]
            y, _ = librosa.load(path, sr=SR, duration=MAX_DURATION_SEC)
            f0_live, _, _ = librosa.pyin(y, sr=SR,
                                         fmin=librosa.note_to_hz("C1"),
                                         fmax=librosa.note_to_hz("C6"))
            same_shape = f0_cache.shape == f0_live.shape
            f0_equal = same_shape and np.allclose(f0_cache, f0_live, equal_nan=True)
            f0_maxdiff = (float(np.nanmax(np.abs(f0_cache - f0_live)))
                          if same_shape else float("nan"))
            m_cache = _metrics_from_f0(f0_cache, scale)
            m_live = _metrics_from_f0(f0_live, scale)
            metrics_equal = (m_cache == m_live)
            ok = f0_equal and metrics_equal
            checked += 1
            mism += 0 if ok else 1
            flag = "OK  " if ok else "FAIL"
            print(f"  [{flag}] {raga}/{fn}  f0_equal={f0_equal} "
                  f"maxdiff={f0_maxdiff:.2e}  metrics_equal={metrics_equal}")
            if not ok:
                print(f"          cache={m_cache}")
                print(f"          live ={m_live}")
    print("\n" + "=" * 64)
    print(f"validated {checked} clips | {nocache} without cache | mismatches: {mism}")
    if checked and mism == 0:
        print("RESULT: cache is a faithful substitute -- metrics identical. Safe to use.")
    elif mism:
        print("RESULT: MISMATCH -- do NOT use cache. Likely librosa/version skew "
              "(check FEATURE_VERSION and librosa version vs when cache was built).")
    else:
        print("RESULT: no cached clips found to validate.")
    print("=" * 64)


def main():
    ap = argparse.ArgumentParser(description="Q-001A representation sufficiency experiment.")
    ap.add_argument("audio_root", help="folder with one subfolder per raga of audio clips")
    ap.add_argument("--feature-dir", default=None,
                    help="production feature cache dir (features_v12). Enables cached f0.")
    ap.add_argument("--validate", action="store_true",
                    help="compare cached f0 vs live pyin and prove metrics are identical")
    args = ap.parse_args()

    global FEATURE_DIR
    FEATURE_DIR = args.feature_dir

    if args.validate:
        run_validation(args.audio_root)
    else:
        run(args.audio_root)


if __name__ == "__main__":
    main()