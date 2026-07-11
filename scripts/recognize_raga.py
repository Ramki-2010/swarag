import os
import numpy as np

EPS = 1e-8

# Weights
BASE_PCD_WEIGHT = 0.6
BASE_DYAD_WEIGHT = 0.4
ESCALATED_PCD_WEIGHT = 0.2
ESCALATED_DYAD_WEIGHT = 0.8

GENERICNESS_LAMBDA = 0.05


# =========================================
# LOAD AGGREGATED MODELS (v1.2)
# =========================================

def load_aggregated_models(agg_folder):

    models = {}

    for fname in os.listdir(agg_folder):

        if not fname.endswith("_stats.npz"):
            continue

        raga = fname.replace("_stats.npz", "")

        data = np.load(os.path.join(agg_folder, fname), allow_pickle=True)

        models[raga] = {
            "mean_pcd": data["mean_pcd"],
            "mean_dyad_up": data["mean_dyad_up"],
            "mean_dyad_down": data["mean_dyad_down"],
            "alpha": float(data["alpha"]),
            "mean_gating": float(data["mean_gating"])
        }

    return models


# =========================================
# UTILS
# =========================================

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + EPS)


def compute_genericness_index(pcd):
    entropy = -np.sum(pcd * np.log(pcd + EPS))
    return entropy


# =========================================
# MAIN RECOGNITION
# =========================================

def recognize_raga(test_pcd,
                   test_dyad_up,
                   test_dyad_down,
                   models):

    results = {}

    for raga, stats in models.items():

        pcd_sim = cosine_similarity(test_pcd, stats["mean_pcd"])

        dyad_up_sim = cosine_similarity(test_dyad_up, stats["mean_dyad_up"])
        dyad_down_sim = cosine_similarity(test_dyad_down, stats["mean_dyad_down"])

        dyad_sim = 0.5 * dyad_up_sim + 0.5 * dyad_down_sim

        raw_score = (
            BASE_PCD_WEIGHT * pcd_sim +
            BASE_DYAD_WEIGHT * dyad_sim
        )

        genericness = compute_genericness_index(test_pcd)
        final_score = raw_score * (1 - GENERICNESS_LAMBDA * genericness)

        results[raga] = {
            "pcd_sim": pcd_sim,
            "dyad_sim": dyad_sim,
            "raw": raw_score,
            "final": final_score
        }

    # Sort by final score
    ranking = sorted(
        results.items(),
        key=lambda x: x[1]["final"],
        reverse=True
    )

    best_raga = ranking[0][0]

    margin = 0.0
    if len(ranking) > 1:
        margin = ranking[0][1]["final"] - ranking[1][1]["final"]

    diagnostics = {
        "margin": margin,
        "genericness": compute_genericness_index(test_pcd)
    }

    return best_raga, ranking, diagnostics
