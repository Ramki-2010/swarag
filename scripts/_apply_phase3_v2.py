"""Apply Method E (IDF x Variance) to recognize_raga_v12.py - v2"""
import os

filepath = os.path.join(os.path.dirname(__file__), 'recognize_raga_v12.py')

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find key locations
score_fn_start = None
score_fn_end = None
for i, line in enumerate(lines):
    if 'def _score_models(' in line:
        score_fn_start = i
    if score_fn_start and line.strip() == 'return scores' and score_fn_end is None and i > score_fn_start:
        score_fn_end = i

header_start = score_fn_start
for i in range(score_fn_start - 1, max(0, score_fn_start - 6), -1):
    if '# =========================' in lines[i]:
        header_start = i
        break

print("Found: header={}, fn={}-{}, fn_end={}".format(
    header_start + 1, score_fn_start + 1, score_fn_end + 1, score_fn_end + 1))

# New function text
new_fn_text = """# =========================
# IDF x VARIANCE PCD WEIGHTS (Phase 3 fix: BUG-008 Thodi sink)
# =========================

def compute_pcd_weights(models):
    \"\"\"
    Compute IDF x variance weights from loaded raga models.
    Downweights common bins, upweights distinctive bins.
    Formula: weight = idf / (std + eps)  [safer form]
    Normalized so weights sum to N_BINS.
    \"\"\"
    all_pcds = np.array([m["pcd"] for m in models.values()])

    # IDF: bins used by many ragas get low weight
    threshold = 1.0 / N_BINS
    doc_freq = np.sum(all_pcds > threshold, axis=0)
    idf = np.log(len(models) / (doc_freq + 1)) + 1

    # Variance: bins where models agree get low weight
    bin_std = np.std(all_pcds, axis=0)

    # Combined: IDF / (std + eps)
    weights = idf / (bin_std + EPS)
    weights = weights / (np.sum(weights) + EPS) * N_BINS

    return weights


# =========================
# SCORE ONE PASS
# =========================

def _score_models(pcd, test_up, test_down, models, pcd_w, dyad_w,
                  pcd_weights=None):
    \"\"\"IDF x variance weighted dot-product scoring for all ragas.\"\"\"
    scores = {}

    # Apply PCD weights if provided (Phase 3 BUG-008 fix)
    if pcd_weights is not None:
        pcd_w_arr = pcd * pcd_weights
        pcd_w_arr = pcd_w_arr / (np.sum(pcd_w_arr) + EPS)
    else:
        pcd_w_arr = pcd

    for raga, model in models.items():

        if pcd_weights is not None:
            model_w = model["pcd"] * pcd_weights
            model_w = model_w / (np.sum(model_w) + EPS)
        else:
            model_w = model["pcd"]

        pcd_sim  = np.dot(pcd_w_arr, model_w)
        up_sim   = np.dot(test_up,  model["mean_up"])
        down_sim = np.dot(test_down, model["mean_down"])

        dyad_sim = 0.5 * (up_sim + down_sim)

        scores[raga] = pcd_w * pcd_sim + dyad_w * dyad_sim

    return scores
"""

# Build result: before header + new function + after old function
result = lines[:header_start]
result.append(new_fn_text)
result.extend(lines[score_fn_end + 1:])

# Fix the scoring call
for i in range(len(result)):
    line = result[i] if isinstance(result[i], str) else ""
    if 'scores = _score_models(pcd' in line:
        # Check if next line is continuation
        next_line = result[i + 1] if i + 1 < len(result) else ""
        if 'PCD_WEIGHT, DYAD_WEIGHT)' in next_line:
            result[i] = "        pcd_weights = compute_pcd_weights(models)\n\n        scores = _score_models(pcd, test_up, test_down, models,\n                               PCD_WEIGHT, DYAD_WEIGHT,\n                               pcd_weights=pcd_weights)\n"
            result[i + 1] = ""
        break

# Fix the Step 1 comment
for i in range(len(result)):
    line = result[i] if isinstance(result[i], str) else ""
    if '# Step 1' in line and 'scoring' in line.lower():
        result[i] = "        # Step 1 -- IDF x Variance weighted scoring (Phase 3 BUG-008 fix)\n"
        break

with open(filepath, 'w', encoding='utf-8') as f:
    for item in result:
        f.write(item)

# Verify
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('compute_pcd_weights exists', 'def compute_pcd_weights' in content),
    ('safer formula', 'idf / (bin_std + EPS)' in content),
    ('pcd_weights param', 'pcd_weights=None' in content),
    ('pcd_weights passed', 'pcd_weights=pcd_weights' in content),
    ('genericness removed from scoring', 'GENERICNESS_WEIGHT * genericness' not in content),
    ('IDF x Variance in comment', 'IDF x Variance' in content),
]

print()
print("=== VERIFICATION ===")
all_ok = True
for name, ok in checks:
    status = "OK" if ok else "FAIL"
    print("  {}: {}".format(status, name))
    if not ok:
        all_ok = False

if all_ok:
    print()
    print("ALL CHECKS PASSED")
else:
    print()
    print("SOME CHECKS FAILED")
