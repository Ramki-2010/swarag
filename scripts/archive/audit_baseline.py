import numpy as np
import os
from collections import defaultdict
from recognize_raga_v12 import load_aggregated_models, _score_models, compute_pcd_weights, recognize_raga

# Force Global Baseline (No Override)
PER_RAGA_WEIGHTS = {}
PCD_WEIGHT = 0.8
DYAD_WEIGHT = 0.2

# Load data (using recognize_raga_v12 loader)
AGG_FOLDER = r'D:\Swaragam\pcd_results\aggregation\v1.2\run_20260331_232228'
models = load_aggregated_models(AGG_FOLDER)
pcd_weights = compute_pcd_weights(models)

# Re-run LOO with Forced Baseline
# (We need the actual clip data, let's load clips using the same loader from the previous sandbox)
# Actually, I can just use the clips list from a previous sandbox session if available,
# but to be rigorous, I will re-load from FEAT_DIR.
from sandbox_absent_swara_v2 import load_clips
clips = load_clips()

def run_loo_audit(clips, models, pcd_weights):
    correct = 0
    wrong = 0
    unknown = 0
    raga_stats = defaultdict(lambda: {'c':0, 'w':0, 'u':0})
    
    for i, held in enumerate(clips):
        # Build LOO models
        train = [c for j, c in enumerate(clips) if j != i]
        raga_pcds = defaultdict(list)
        raga_ups = defaultdict(list)
        raga_downs = defaultdict(list)
        for c in train:
            raga_pcds[c['raga']].append(c['pcd'])
            raga_ups[c['raga']].append(c['up'])
            raga_downs[c['raga']].append(c['down'])
            
        loo_models = {r: {'pcd': np.mean(v, axis=0), 
                          'mean_up': np.mean(raga_ups[r], axis=0), 
                          'mean_down': np.mean(raga_downs[r], axis=0)} 
                      for r, v in raga_pcds.items()}
        
        # Score
        scores = _score_models(held['pcd'], held['up'], held['down'], 
                               loo_models, PCD_WEIGHT, DYAD_WEIGHT, pcd_weights=pcd_weights)
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = (ranked[0][1] - ranked[1][1]) if len(ranked) >= 2 else 0.0
        
        # Use existing confidence tiers
        if margin >= 0.003: # HIGH
            pred = ranked[0][0]
        elif margin >= 0.001: # MODERATE
            pred = ranked[0][0]
        else:
            pred = 'UNKNOWN'
            
        if pred == held['raga']:
            correct += 1
            raga_stats[held['raga']]['c'] += 1
        elif pred == 'UNKNOWN':
            unknown += 1
            raga_stats[held['raga']]['u'] += 1
        else:
            wrong += 1
            raga_stats[held['raga']]['w'] += 1
            
    return correct, wrong, unknown, raga_stats

c, w, u, stats = run_loo_audit(clips, models, pcd_weights)
print(f'LOO AUDIT (Forced Global Baseline): C={c} W={w} U={u} Acc={c/(c+w)*100 if (c+w)>0 else 0:.1f}%')
for r in sorted(stats.keys()):
    print(f'{r}: {stats[r]}')
