import os
import numpy as np

# sandbox_abhogi_ratio.py  --  BUG-015: Abhogi vs Kalyani Quantitative Swara Energy Ratio
# ========================================================================================
# DEAD ENDS (do not re-attempt):
#   - Per-raga weight overrides (L-044): 0% Abhogi at all weights
#   - Binary absent-swara penalty (L-046): gamakas leak 6-19% Pa energy
#
# THIS APPROACH: quantitative Pa / N3 energy ratio comparison.
#   Instead of asking 'Is Pa present?' we ask:
#   'How much Pa energy does this clip have vs what this raga EXPECTS?'
#
#   Kalyani model -> HIGH Pa (Pa is a core swara, sung frequently)
#   Abhogi  model -> LOW  Pa (only gamaka spillover, ~6% typical)
#
#   ratio_sim = 0.5 * (pa_match + n3_match)
#   pa_match  = max(0,  1 - |test_pa - model_pa| / (model_pa + EPS))
#   final_score = base_score * (1.0 + ratio_weight * ratio_sim)
#
# STRUCTURE:
#   Phase 1 -- DIAGNOSTIC  : print Pa/N3 ratios per clip, check separation
#   Phase 2 -- LOO SWEEP   : baseline vs ratio-augmented at 6 weights
#   Phase 3 -- DECISION    : BETTER -> production patch | SAME/WORSE -> dead end
# ========================================================================================

FEATURES_DIR = r'D:\Swaragam\pcd_results\features_v12'
AGG_FOLDER   = r'D:\Swaragam\pcd_results\aggregation\v1.2\run_20260331_232228'

N_BINS = 72
ALPHA  = 0.01
EPS    = 1e-8
PCD_WEIGHT        = 0.8
DYAD_WEIGHT       = 0.2
PER_RAGA_WEIGHTS  = {'Bhairavi': (0.5, 0.5)}   # v1.3.1 frozen
MARGIN_STRICT     = 0.003
MIN_MARGIN_FINAL  = 0.001
MIN_STABLE_FRAMES = 5

# Swara bin positions  (72 bins, 1200/72 = 16.67 cents/bin)
# Pa  = 702 cents  -> bin 42    N3 = 1088 cents -> bin 65
BIN_WIDTH = 1200.0 / N_BINS
PA_CENTRE = int(702  / BIN_WIDTH)   # 42
N3_CENTRE = int(1088 / BIN_WIDTH)   # 65
WINDOW    = 2                        # +/-2 bins to capture gamaka approach notes
PA_BINS   = slice(max(0, PA_CENTRE - WINDOW), min(N_BINS, PA_CENTRE + WINDOW + 1))
N3_BINS   = slice(max(0, N3_CENTRE - WINDOW), min(N_BINS, N3_CENTRE + WINDOW + 1))


# =============================================================================
# DATA LOADING
# =============================================================================

def load_features(features_dir):
    """Load all .npz feature files. Returns {raga: [(fname, pcd), ...]}"""
    raga_pcds = {}
    for fname in sorted(os.listdir(features_dir)):
        if not fname.endswith('.npz'):
            continue
        fpath = os.path.join(features_dir, fname)
        try:
            d           = np.load(fpath, allow_pickle=True)
            raga        = str(d['raga'])
            cents_gated = d['cents_gated']
            if len(cents_gated) < 200:
                continue
            hist, _ = np.histogram(cents_gated, bins=N_BINS, range=(0, 1200))
            if np.sum(hist) == 0:
                continue
            pcd = hist / (np.sum(hist) + EPS)
            raga_pcds.setdefault(raga, []).append((fname, pcd))
        except Exception as e:
            print(f'  [SKIP] {fname}: {e}')
    return raga_pcds


def load_models(agg_folder):
    """Load aggregated raga models from aggregation run."""
    models   = {}
    pcd_dir  = os.path.join(agg_folder, 'pcd_stats')
    dyad_dir = os.path.join(agg_folder, 'dyad_stats')
    for fname in os.listdir(pcd_dir):
        if not fname.endswith('_pcd_stats.npz'):
            continue
        raga   = fname.replace('_pcd_stats.npz', '')
        pcd_d  = np.load(os.path.join(pcd_dir,  fname), allow_pickle=True)
        dyad_d = np.load(os.path.join(dyad_dir, f'{raga}_dyad_stats.npz'), allow_pickle=True)
        models[raga] = {
            'pcd':       pcd_d['mean_pcd'],
            'mean_up':   dyad_d['mean_up'],
            'mean_down': dyad_d['mean_down'],
        }
    return models


# =============================================================================
# FEATURE HELPERS
# =============================================================================

def swara_ratios(pcd):
    """Return (Pa_energy, N3_energy) as fractions of total PCD energy."""
    return np.sum(pcd[PA_BINS]), np.sum(pcd[N3_BINS])


def compute_pcd_weights(models):
    """IDF x variance weights -- identical to production recognize_raga_v12.py."""
    all_pcds  = np.array([m['pcd'] for m in models.values()])
    threshold = 1.0 / N_BINS
    doc_freq  = np.sum(all_pcds > threshold, axis=0)
    idf       = np.log(len(models) / (doc_freq + 1)) + 1
    bin_std   = np.std(all_pcds, axis=0)
    weights   = idf / (bin_std + EPS)
    return weights / (np.sum(weights) + EPS) * N_BINS


def compute_directional_dyads(cents):
    """Identical to production recognize_raga_v12.py."""
    bins       = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bins) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]
    if len(pitch_bins) < MIN_STABLE_FRAMES:
        return np.zeros(N_BINS * N_BINS), np.zeros(N_BINS * N_BINS)
    stable_bins = []
    current = pitch_bins[0]
    count   = 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current = b
            count   = 1
    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)
    mat_up   = np.zeros((N_BINS, N_BINS))
    mat_down = np.zeros((N_BINS, N_BINS))
    for i in range(len(stable_bins) - 1):
        frm, to = stable_bins[i], stable_bins[i + 1]
        if to > frm:
            mat_up[frm, to]   += 1
        elif to < frm:
            mat_down[frm, to] += 1
    mat_up   += ALPHA;  mat_down += ALPHA
    mat_up   /= (np.sum(mat_up)   + EPS)
    mat_down /= (np.sum(mat_down) + EPS)
    return mat_up.flatten(), mat_down.flatten()


# =============================================================================
# SCORING
# =============================================================================

def score_baseline(pcd, up, down, models, pcd_weights):
    """Production scoring -- no ratio term. Used as the LOO baseline."""
    scores    = {}
    pcd_w_arr = pcd * pcd_weights
    pcd_w_arr /= (np.sum(pcd_w_arr) + EPS)
    for raga, model in models.items():
        r_pcd_w, r_dyad_w = PER_RAGA_WEIGHTS.get(raga, (PCD_WEIGHT, DYAD_WEIGHT))
        model_w  = model['pcd'] * pcd_weights
        model_w /= (np.sum(model_w) + EPS)
        pcd_sim  = np.dot(pcd_w_arr, model_w)
        dyad_sim = 0.5 * (np.dot(up,   model['mean_up']) +
                          np.dot(down, model['mean_down']))
        scores[raga] = r_pcd_w * pcd_sim + r_dyad_w * dyad_sim
    return scores


def score_with_ratio(pcd, up, down, models, pcd_weights, ratio_weight=0.1):
    """
    Ratio-augmented scoring.

    For every raga model, compare the test clip's Pa and N3 energy fractions
    against the model's own Pa and N3 fractions.

      pa_match  = max(0,  1 - |test_pa  - model_pa|  / (model_pa  + EPS))
      n3_match  = max(0,  1 - |test_n3  - model_n3|  / (model_n3  + EPS))
      ratio_sim = 0.5 * (pa_match + n3_match)

    This is purely QUANTITATIVE -- not binary present/absent.
    A clip with low Pa (Abhogi) scores LOWER against Kalyani (high model Pa)
    and HIGHER against Abhogi (low model Pa).

      final_score = base_score * (1.0 + ratio_weight * ratio_sim)
    """
    scores    = {}
    test_pa, test_n3 = swara_ratios(pcd)
    pcd_w_arr = pcd * pcd_weights
    pcd_w_arr /= (np.sum(pcd_w_arr) + EPS)
    for raga, model in models.items():
        r_pcd_w, r_dyad_w = PER_RAGA_WEIGHTS.get(raga, (PCD_WEIGHT, DYAD_WEIGHT))
        model_w  = model['pcd'] * pcd_weights
        model_w /= (np.sum(model_w) + EPS)
        pcd_sim  = np.dot(pcd_w_arr, model_w)
        dyad_sim = 0.5 * (np.dot(up,   model['mean_up']) +
                          np.dot(down, model['mean_down']))
        base      = r_pcd_w * pcd_sim + r_dyad_w * dyad_sim
        model_pa, model_n3 = swara_ratios(model['pcd'])
        pa_match  = max(0.0, 1.0 - abs(test_pa  - model_pa)  / (model_pa  + EPS))
        n3_match  = max(0.0, 1.0 - abs(test_n3  - model_n3)  / (model_n3  + EPS))
        ratio_sim = 0.5 * (pa_match + n3_match)
        scores[raga] = base * (1.0 + ratio_weight * ratio_sim)
    return scores


# =============================================================================
# LOO CROSS-VALIDATION
# =============================================================================

def run_loo(all_features, models, scorer_fn, label):
    """Leave-One-Out cross-validation across all 7 modelled ragas."""
    correct = wrong = unknown = 0
    details = []
    raga_clips = {r: c for r, c in all_features.items() if r in models}
    for true_raga, clips in raga_clips.items():
        for i, (fname, test_pcd) in enumerate(clips):
            # Build LOO model set
            loo_models = {}
            for raga, rclips in raga_clips.items():
                remaining = ([p for j, (_, p) in enumerate(rclips) if j != i]
                             if raga == true_raga
                             else [p for _, p in rclips])
                if not remaining:
                    continue
                mean_pcd  = np.mean(remaining, axis=0)
                mean_pcd /= (np.sum(mean_pcd) + EPS)
                loo_models[raga] = {
                    'pcd':       mean_pcd,
                    'mean_up':   models[raga]['mean_up'],
                    'mean_down': models[raga]['mean_down'],
                }
            pcd_weights = compute_pcd_weights(loo_models)
            d  = np.load(os.path.join(FEATURES_DIR, fname), allow_pickle=True)
            up, down = compute_directional_dyads(d['cents_gated'])
            scores = scorer_fn(test_pcd, up, down, loo_models, pcd_weights)
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            margin = (ranked[0][1] - ranked[1][1]) if len(ranked) >= 2 else 0.0
            pred   = ranked[0][0] if margin >= MIN_MARGIN_FINAL else 'UNKNOWN'
            if pred == 'UNKNOWN':
                unknown += 1;  outcome = 'UNKNOWN'
            elif pred == true_raga:
                correct += 1;  outcome = 'CORRECT'
            else:
                wrong   += 1;  outcome = f'WRONG->{pred}'
            details.append((true_raga, fname[:38], outcome, round(margin, 6)))
    decided = correct + wrong
    acc     = correct / decided * 100 if decided > 0 else 0.0
    print(f'  [{label}]')
    print(f'  C={correct}  W={wrong}  U={unknown}  Total={decided + unknown}  '
          f'Acc(decided)={acc:.1f}%')
    return details, acc


def per_raga_breakdown(details, label):
    stats = {}
    for true_raga, fname, outcome, margin in details:
        stats.setdefault(true_raga, {'c': 0, 'w': 0, 'u': 0})
        if   outcome == 'CORRECT': stats[true_raga]['c'] += 1
        elif outcome == 'UNKNOWN': stats[true_raga]['u'] += 1
        else:                      stats[true_raga]['w'] += 1
    print(f'  Per-raga [{label}]:')
    for raga, s in sorted(stats.items()):
        d   = s['c'] + s['w']
        acc = s['c'] / d * 100 if d > 0 else 0
        print(f'    {raga:20s}  C={s["c"]}  W={s["w"]}  U={s["u"]}  Acc={acc:.0f}%')
    return stats


# =============================================================================
# PHASE 1 -- DIAGNOSTIC
# =============================================================================

def phase1_diagnostic(all_features, models):
    print()
    print('=' * 70)
    print('PHASE 1 -- SWARA ENERGY RATIO DIAGNOSTIC')
    print('=' * 70)
    print(f'  Bin width : {BIN_WIDTH:.2f} cents/bin')
    print(f'  Pa centre : bin {PA_CENTRE} ({PA_CENTRE * BIN_WIDTH:.0f} cents)  '
          f'window bins {PA_BINS.start}-{PA_BINS.stop - 1}')
    print(f'  N3 centre : bin {N3_CENTRE} ({N3_CENTRE * BIN_WIDTH:.0f} cents)  '
          f'window bins {N3_BINS.start}-{N3_BINS.stop - 1}')
    for raga in ['Abhogi', 'Kalyani']:
        if raga not in all_features:
            print(f'  {raga}: NOT FOUND in features')
            continue
        clips = all_features[raga]
        pa_vals, n3_vals = [], []
        print(f'\n  --- {raga} ({len(clips)} clips) ---')
        for fname, pcd in clips:
            pa, n3 = swara_ratios(pcd)
            pa_vals.append(pa);  n3_vals.append(n3)
            print(f'    {fname[:48]:48s}  Pa={pa:.4f}  N3={n3:.4f}')
        if raga in models:
            m_pa, m_n3 = swara_ratios(models[raga]['pcd'])
            print(f'    {"MODEL":48s}  Pa={m_pa:.4f}  N3={m_n3:.4f}')
        print(f'    Pa: mean={np.mean(pa_vals):.4f}  std={np.std(pa_vals):.4f}  '
              f'range=[{min(pa_vals):.4f}, {max(pa_vals):.4f}]')
        print(f'    N3: mean={np.mean(n3_vals):.4f}  std={np.std(n3_vals):.4f}  '
              f'range=[{min(n3_vals):.4f}, {max(n3_vals):.4f}]')
    # Separation check
    if 'Abhogi' in all_features and 'Kalyani' in all_features:
        ab_pa = [swara_ratios(p)[0] for _, p in all_features['Abhogi']]
        ka_pa = [swara_ratios(p)[0] for _, p in all_features['Kalyani']]
        print()
        print('  SEPARATION CHECK (Pa ratio):')
        print(f'    Abhogi  mean={np.mean(ab_pa):.4f}  '
              f'Kalyani mean={np.mean(ka_pa):.4f}  '
              f'ratio={np.mean(ka_pa) / (np.mean(ab_pa) + EPS):.2f}x')
        overlap = sum(1 for v in ab_pa if v >= min(ka_pa))
        print(f'    Abhogi clips overlapping Kalyani Pa-range: {overlap}/{len(ab_pa)}')
        if np.mean(ka_pa) >= np.mean(ab_pa) * 1.3:
            print('    >> GOOD SEPARATION: Kalyani Pa-mean >= 30% above Abhogi')
            print('       Ratio scoring should provide useful signal -- proceed to Phase 2.')
        else:
            print('    >> WEAK SEPARATION: distributions overlap too much.')
            print('       Ratio scoring is unlikely to help. Consider phrase n-grams instead.')


# =============================================================================
# PHASE 2 -- LOO SWEEP
# =============================================================================

def phase2_loo_sweep(all_features, models):
    print()
    print('=' * 70)
    print('PHASE 2 -- LOO SWEEP: BASELINE vs RATIO-AUGMENTED')
    print('=' * 70)
    # Baseline
    base_det, base_acc = run_loo(
        all_features, models,
        lambda p, u, d, m, w: score_baseline(p, u, d, m, w),
        'BASELINE (production)')
    per_raga_breakdown(base_det, 'BASELINE')
    # Ratio sweep
    best_acc = base_acc
    best_w   = 0.0
    best_det = base_det
    for rw in [0.05, 0.10, 0.15, 0.20, 0.30, 0.40]:
        det, acc = run_loo(
            all_features, models,
            lambda p, u, d, m, w, rw=rw: score_with_ratio(p, u, d, m, w, ratio_weight=rw),
            f'ratio_weight={rw}')
        if acc > best_acc:
            best_acc = acc;  best_w = rw;  best_det = det
    # Summary
    print()
    print('=' * 70)
    print('PHASE 2 SUMMARY')
    print('=' * 70)
    print(f'  Baseline  : {base_acc:.1f}%')
    print(f'  Best ratio: {best_acc:.1f}%  (ratio_weight={best_w})')
    delta = best_acc - base_acc
    print(f'  Delta     : {delta:+.1f}%')
    if delta > 0:
        print(f'  VERDICT: IMPROVEMENT')
        print(f'  ACTION : Apply ratio_weight={best_w} to production sandbox, run full LOO.')
        per_raga_breakdown(best_det, f'BEST rw={best_w}')
    elif delta == 0:
        print('  VERDICT: NO CHANGE -- ratio term adds no signal at any weight.')
        print('  ACTION : Add to proven dead ends. Next: phrase n-gram detection.')
    else:
        print('  VERDICT: REGRESSION -- ratio term hurts overall accuracy.')
        print('  ACTION : Add to proven dead ends. Next: phrase n-gram detection.')


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print()
    print('Swarag -- Abhogi Ratio Sandbox (BUG-015)')
    print('=' * 42)
    print('Loading features...')
    all_features = load_features(FEATURES_DIR)
    for raga, clips in sorted(all_features.items()):
        print(f'  {raga:20s}: {len(clips)} clips')
    print('Loading models...')
    models = load_models(AGG_FOLDER)
    print(f'  Models: {sorted(models.keys())}')
    phase1_diagnostic(all_features, models)
    phase2_loo_sweep(all_features, models)
    print()
    print('Done.')
