"""Apply Method E (IDF x Variance) edits to recognize_raga_v12.py"""

with open('recognize_raga_v12.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find key line numbers
score_fn_start = None
score_fn_end = None
scoring_call_line = None
step1_comment_line = None

for i, line in enumerate(lines):
    if 'def _score_models(' in line:
        score_fn_start = i
    if score_fn_start and line.strip() == 'return scores' and score_fn_end is None and i > score_fn_start:
        score_fn_end = i
    if '# Step 1' in line and 'Standard scoring' in line:
        step1_comment_line = i
    if '_score_models(pcd, test_up, test_down, models,' in line and 'PCD_WEIGHT' in line:
        scoring_call_line = i

print(f"_score_models function: lines {score_fn_start+1}-{score_fn_end+1}")
print(f"Step 1 comment: line {step1_comment_line+1}")
print(f"Scoring call: line {scoring_call_line+1}")

# Also find the section header before _score_models (# SCORE ONE PASS)
header_start = score_fn_start
for i in range(score_fn_start - 1, max(0, score_fn_start - 6), -1):
    if '# =========================' in lines[i]:
        header_start = i
        break

print(f"Section header starts: line {header_start+1}")

# BUILD NEW FUNCTION
new_section = """# =========================
# IDF x VARIANCE PCD WEIGHTS (Phase 3 fix: BUG-008 Thodi sink)
# =========================

def compute_pcd_weights(models):
    \"\"\"
    Compute IDF x variance weights from loaded raga models.
    Downweights bins shared by all ragas (Sa, Pa) and upweights
    bins where ragas actually differ (distinctive swaras).

    Formula: weight_i = idf_i / (std_i + eps)   [safer form]
    Then normalized so weights sum to N_BINS (preserves score scale).
    \"\"\"
    all_pcds = np.array([m["pcd"] for m in models.values()])

    # IDF component: bins used by many ragas get low weight
    threshold = 1.0 / N_BINS
    doc_freq  = np.sum(all_pcds > threshold, axis=0)
    idf       = np.log(len(models) / (doc_freq + 1)) + 1

    # Variance component: bins where models agree get low weight
    bin_std = np.std(all_pcds, axis=0)

    # Combined: IDF / (std + eps) -- safer than IDF * (1/std)
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

        # Weighted PCD similarity
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

# Replace the function section
new_lines = lines[:header_start] + [new_section + "\n"] + lines[score_fn_end + 1:]

# Now fix the scoring call — find it in the new lines
for i, line in enumerate(new_lines):
    if '# Step 1' in line:
        # Replace the comment and the next scoring call
        new_lines[i] = "        # Step 1 -- IDF x Variance weighted scoring (Phase 3 BUG-008 fix)\n"
        break

# Find and update the scoring call
for i, line in enumerate(new_lines):
    if '_score_models(pcd, test_up, test_down, models,' in line and 'PCD_WEIGHT' in line:
        # Insert pcd_weights computation before the call
        indent = "        "
        new_call = (
            indent + "pcd_weights = compute_pcd_weights(models)\n"
            "\n"
            + indent + "scores = _score_models(pcd, test_up, test_down, models,\n"
            + indent + "                       PCD_WEIGHT, DYAD_WEIGHT,\n"
            + indent + "                       pcd_weights=pcd_weights)\n"
        )
        # Check if next line is continuation
        if i + 1 < len(new_lines) and 'PCD_WEIGHT, DYAD_WEIGHT)' in new_lines[i + 1]:
            new_lines[i] = new_call
            new_lines[i + 1] = ""  # remove continuation line
        else:
            new_lines[i] = new_call
        break

with open('recognize_raga_v12.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\nEdits applied successfully!")
print("Verifying...")

with open('recognize_raga_v12.py', 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('compute_pcd_weights', 'compute_pcd_weights' in content),
    ('idf / (bin_std + EPS)', 'idf / (bin_std + EPS)' in content),
    ('pcd_weights=None', 'pcd_weights=None' in content),
    ('pcd_weights=pcd_weights', 'pcd_weights=pcd_weights' in content),
    ('GENERICNESS_WEIGHT removed from scoring', 'GENERICNESS_WEIGHT * genericness' not in content),
]

for name, ok in checks:
    print(f"  {'OK' if ok else 'FAIL'}: {name}")
