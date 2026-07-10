import numpy as np
import os
from collections import defaultdict
from recognize_raga_v12 import load_aggregated_models, _score_models, compute_pcd_weights
from sandbox_absent_swara_v2 import load_clips

# Configuration
AGG_FOLDER = r'D:\Swaragam\pcd_results\aggregation\v1.2\run_20260331_232228'
PCD_WEIGHT = 0.8
DYAD_WEIGHT = 0.2

def run_audit(clips, exclude_ragas=set()):
    # Filter clips
    active_clips = [c for c in clips if c['raga'] not in exclude_ragas]
    
    # Re-calculate models based on included ragas only
    raga_pcds = defaultdict(list)
    raga_ups = defaultdict(list)
    raga_downs = defaultdict(list)
    for c in active_clips:
        raga_pcds[c['raga']].append(c['pcd'])
        raga_ups[c['raga']].append(c['up'])
        raga_downs[c['raga']].append(c['down'])
    
    loo_models = {r: {'pcd': np.mean(v, axis=0), 
                      'mean_up': np.mean(raga_ups[r], axis=0), 
                      'mean_down': np.mean(raga_downs[r], axis=0)} 
                  for r, v in raga_pcds.items()}
    
    pcd_weights = compute_pcd_weights(loo_models)
    
    correct = 0
    wrong = 0
    unknown = 0
    conf_matrix = defaultdict(lambda: defaultdict(int))
    
    for i, held in enumerate(active_clips):
        train = [c for j, c in enumerate(active_clips) if j != i]
        # (Re-calculate models per LOO fold)
        r_pcds, r_ups, r_downs = defaultdict(list), defaultdict(list), defaultdict(list)
        for c in train:
            r_pcds[c['raga']].append(c['pcd'])
            r_ups[c['raga']].append(c['up'])
            r_downs[c['raga']].append(c['down'])
        fold_models = {r: {'pcd': np.mean(v, axis=0), 'mean_up': np.mean(r_ups[r], axis=0), 'mean_down': np.mean(r_downs[r], axis=0)} for r, v in r_pcds.items()}
        
        scores = _score_models(held['pcd'], held['up'], held['down'], fold_models, PCD_WEIGHT, DYAD_WEIGHT, pcd_weights=pcd_weights)
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = (ranked[0][1] - ranked[1][1]) if len(ranked) >= 2 else 0.0
        
        pred = ranked[0][0] if margin >= 0.001 else 'UNKNOWN'
        
        if pred == held['raga']: correct += 1
        elif pred == 'UNKNOWN': unknown += 1
        else: wrong += 1
        
        conf_matrix[held['raga']][pred] += 1
        
    return correct, wrong, unknown, conf_matrix

clips = load_clips()

print('--- 7-RAGA BASELINE ---')
c, w, u, cm = run_audit(clips)
print(f'C={c} W={w} U={u} Acc={c/(c+w)*100:.1f}%')
for tr in sorted(cm.keys()):
    print(f'True {tr:15s}: {dict(cm[tr])}')

print('\n--- 5-RAGA EXCLUSION (Bhairavi/Abhogi out) ---')
c, w, u, cm = run_audit(clips, exclude_ragas={'Bhairavi', 'Abhogi'})
print(f'C={c} W={w} U={u} Acc={c/(c+w)*100:.1f}%')
for tr in sorted(cm.keys()):
    print(f'True {tr:15s}: {dict(cm[tr])}')