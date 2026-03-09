import os
import csv
import numpy as np
from datetime import datetime
from recognize_raga_v12 import recognize_raga, load_aggregated_models

# =========================
# CONFIG
# =========================
BASE_DIR     = r"D:\Swaragam"
DATASET_DIR  = os.path.join(BASE_DIR, "datasets", "seed_carnatic")
AGG_FOLDER   = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260309_082638"  # B2: was missing

EVAL_BASE_DIR = os.path.join(BASE_DIR, "pcd_results", "evaluation")
timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR       = os.path.join(EVAL_BASE_DIR, f"run_{timestamp}")

os.makedirs(RUN_DIR, exist_ok=True)

PER_FILE_CSV = os.path.join(RUN_DIR, "per_file_results.csv")
PER_RAGA_CSV = os.path.join(RUN_DIR, "per_raga_results.csv")
SUMMARY_TXT  = os.path.join(RUN_DIR, "summary.txt")

SUPPORTED_EXTS = (".wav", ".mp3", ".flac")


# =========================
# EVALUATION
# =========================
def evaluate():

    # Pre-load model once — avoid re-loading for every file
    models = load_aggregated_models(AGG_FOLDER)
    if not models:
        print(f"✗ No models found in: {AGG_FOLDER}")
        return

    print(f"\nSwarag v1.2 — Seed Dataset Evaluation")
    print(f"AGG folder : {AGG_FOLDER}")
    print(f"Dataset    : {DATASET_DIR}")
    print(f"Run output : {RUN_DIR}\n")
    print("=" * 60)

    per_file_rows = []
    raga_stats    = {}

    total_files = 0
    correct     = 0
    unknown_count = 0

    for raga_folder in sorted(os.listdir(DATASET_DIR)):

        raga_path = os.path.join(DATASET_DIR, raga_folder)
        if not os.path.isdir(raga_path):
            continue

        for file in sorted(os.listdir(raga_path)):

            if not file.lower().endswith(SUPPORTED_EXTS):
                continue

            total_files += 1
            audio_path  = os.path.join(raga_path, file)

            # C2: use v1.2 API — (audio_path, aggregation_folder, models)
            result = recognize_raga(audio_path, AGG_FOLDER, models=models)

            final           = result["final"]
            ranking         = result["ranking"]
            margin          = result["margin"]
            confidence_tier = result.get("confidence_tier", "UNKNOWN")

            top1_score = ranking[0][1] if len(ranking) >= 1 else 0.0
            top2_score = ranking[1][1] if len(ranking) >= 2 else 0.0
            top3_score = ranking[2][1] if len(ranking) >= 3 else 0.0

            is_correct = (final == raga_folder)

            if final == "UNKNOWN / LOW CONFIDENCE":
                unknown_count += 1
            elif is_correct:
                correct += 1

            per_file_rows.append([
                file,
                raga_folder,
                final,
                confidence_tier,
                round(margin,    6),
                round(top1_score, 4),
                round(top2_score, 4),
                round(top3_score, 4),
                is_correct
            ])

            stats = raga_stats.setdefault(raga_folder, {"total": 0, "correct": 0, "unknown": 0})
            stats["total"] += 1
            if is_correct:
                stats["correct"] += 1
            if final == "UNKNOWN / LOW CONFIDENCE":
                stats["unknown"] += 1

            status_sym = "✔" if is_correct else ("?" if "UNKNOWN" in final else "✗")
            print(f"{status_sym} {file:<35} | True={raga_folder:<20} | Pred={final:<25} "
                  f"| Tier={confidence_tier:<10} | Margin={round(margin, 4)}")

    # =========================
    # SAVE PER FILE CSV
    # =========================
    with open(PER_FILE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file", "true_raga", "predicted_raga",
            "confidence_tier", "margin",
            "top1_score", "top2_score", "top3_score",
            "correct"
        ])
        writer.writerows(per_file_rows)

    # =========================
    # SAVE PER RAGA CSV
    # =========================
    per_raga_rows = []
    for raga, stats in sorted(raga_stats.items()):
        decided = stats["total"] - stats["unknown"]
        acc_all     = stats["correct"] / stats["total"]          if stats["total"] > 0 else 0
        acc_decided = stats["correct"] / decided                 if decided > 0 else 0
        per_raga_rows.append([
            raga, stats["total"], stats["correct"],
            stats["unknown"], round(acc_all, 4), round(acc_decided, 4)
        ])

    with open(PER_RAGA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["raga", "total", "correct", "unknown", "acc_all", "acc_decided"])
        writer.writerows(per_raga_rows)

    # =========================
    # SAVE SUMMARY
    # =========================
    decided_total    = total_files - unknown_count
    overall_acc_all  = correct / total_files      if total_files > 0 else 0
    overall_acc_dec  = correct / decided_total    if decided_total > 0 else 0
    unknown_rate     = unknown_count / total_files if total_files > 0 else 0

    summary_lines = [
        f"Swarag v1.2 Evaluation — {timestamp}",
        f"AGG Folder  : {AGG_FOLDER}",
        f"",
        f"Total files  : {total_files}",
        f"Correct      : {correct}",
        f"Unknown      : {unknown_count}  ({unknown_rate:.1%})",
        f"Decided      : {decided_total}",
        f"",
        f"Accuracy (all)     : {overall_acc_all:.4f}",
        f"Accuracy (decided) : {overall_acc_dec:.4f}",
    ]

    with open(SUMMARY_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print("\n" + "=" * 60)
    print(f"Total        : {total_files}")
    print(f"Correct      : {correct}")
    print(f"Unknown      : {unknown_count}  ({unknown_rate:.1%})")
    print(f"Acc (all)    : {overall_acc_all:.4f}")
    print(f"Acc (decided): {overall_acc_dec:.4f}")
    print(f"\nResults saved to: {RUN_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    evaluate()
