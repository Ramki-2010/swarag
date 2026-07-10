import numpy as np
import os
from collections import defaultdict
from recognize_raga_v12 import compute_pcd_weights

FEAT_DIR = r'D:\Swaragam\pcd_results\features_v12'
MIN_STABLE = 5
ALPHA = 0.01
EPS = 1e-8

def extract_for_bins(data, n_bins):
    cents = data['cents_gated']
    hist, _ = np.histogram(cents, bins=n_bins, range=(0, 1200))
    pcd = hist / (np.sum(hist) + EPS)
    bins = np.floor(cents / (1200.0 / n_bins)).astype(int)
    bins = np.clip(bins, 0, n_bins - 1)
    up = np.zeros((n_bins, n_bins))
    down = np.zeros((n_bins, n_bins))
    i = 0
    while i < len(bins):
        j = i + 1
        while j < len(bins) and bins[j] == bins[i]: j += 1
        if (j - i) >= MIN_STABLE and i > 0:
            prev, curr = bins[i - 1], bins[i]
            if curr > prev: up[prev, curr] += 1
            elif curr < prev: down[prev, curr] += 1
        i = j
    up_flat = (up + ALPHA).flatten() / (np.sum(up + ALPHA) + EPS)
    down_flat = (down + ALPHA).flatten() / (np.sum(down + ALPHA) + EPS)
    return pcd, up_flat, down_flat

for n_bins in [36, 48, 72]:
    print(f'\n--- Testing {n_bins} BINS ---')
    clips = []
    for f in os.listdir(FEAT_DIR):
        if not f.endswith('.npz'): continue
        d = np.load(os.path.join(FEAT_DIR, f), allow_pickle=True)
        if d.get('feature_version') != 'v1.2': continue
        pcd, up, down = extract_for_bins(d, n_bins)
        clips.append({'raga': str(d['raga']), 'pcd': pcd, 'up': up, 'down': down})
    
    correct = wrong = unknown = 0
    for i, held in enumerate(clips):
        train = [c for j, c in enumerate(clips) if j != i]
        r_pcds = defaultdict(list)
        for c in train: r_pcds[c['raga']].append(c['pcd'])
        loo_models = {r: {'pcd': np.mean(v, axis=0)} for r, v in r_pcds.items()}
        weights = compute_pcd_weights(loo_models)
        
        scores = {}
        for r, m in loo_models.items():
            pcd_sim = np.dot(held['pcd']*weights, m['pcd']*weights)
            scores[r] = pcd_sim
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = (ranked[0][1] - (ranked[1][1] if len(ranked)>1 else 0))
        pred = ranked[0][0] if margin > 0.001 else 'UNK'
        
        if pred == held['raga']: correct += 1
        elif pred == 'UNK': unknown += 1
        else: wrong += 1
    print(f'Acc={correct/(correct+wrong) if (correct+wrong)>0 else 0:.1%} (C={correct} W={wrong} U={unknown})')