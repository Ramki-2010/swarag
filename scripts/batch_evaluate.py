import os
import csv
import numpy as np
from datetime import datetime
from recognize_raga_v12 import recognize_raga

# =========================
# CONFIG
# =========================
BASE_DIR = r"D:\Swaragam"
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "seed_carnatic")

EVAL_BASE_DIR = os.path.join(BASE_DIR, "pcd_results", "evaluation")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = os.path.join(EVAL_BASE_DIR, f"run_{timestamp}")

os.makedirs(RUN_DIR, exist_ok=True)

PER_FILE_CSV = os.path.join(RUN_DIR, "per_file_results.csv")
PER_RAGA_CSV = os.path.join(RUN_DIR, "per_raga_results.csv")
SUMMARY_TXT = os.path.join(RUN_DIR, "summary.txt")


# =========================
# EVALUATION
# =========================
def evaluate():

    per_file_rows = []
    raga_stats = {}

    total_files = 0
    correct = 0

    for raga_folder in os.listdir(DATASET_DIR):

        raga_path = os.path.join(DATASET_DIR, raga_folder)
        if not os.path.isdir(raga_path):
            continue

        for file in os.listdir(raga_path):

            if not file.endswith(".wav"):
                continue

            total_files += 1
            audio_path = os.path.join(raga_path, file)

            # Load stored extraction for inference
            # IMPORTANT: you must load f0, sa_hz, voiced_flag
            # from your feature file logic (adapt if needed)

            from extract_pitch_batch_v12 import process_file  # reuse logic

            # Re-extract features live for evaluation
            # (alternatively load stored .npz if you prefer)
            # For now we assume extraction returns f0 etc.
            import librosa
            SR = 22050
            FMIN = librosa.note_to_hz("C1")
            FMAX = librosa.note_to_hz("C6")

            y, sr = librosa.load(audio_path, sr=SR)
            f0, voiced_flag, _ = librosa.pyin(
                y, fmin=FMIN, fmax=FMAX, sr=sr
            )

            valid_f0 = f0[~np.isnan(f0)]
            if len(valid_f0) == 0:
                continue

            # Simple tonic estimation (reuse extraction logic)
            hist, bin_edges = np.histogram(valid_f0, bins=200)
            top_idx = np.argsort(hist)[-5:]
            top_peaks = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in top_idx]

            from extract_pitch_batch_v12 import choose_best_tonic
            sa_hz = choose_best_tonic(top_peaks, valid_f0)

            predictions = recognize_raga(f0, sa_hz, voiced_flag)

            if predictions is None:
                continue

            top_raga, top_data = predictions[0]
            second_raga, second_data = predictions[1]

            margin = top_data["final"] - second_data["final"]

            is_correct = (top_raga == raga_folder)
            if is_correct:
                correct += 1

            # Store per-file
            per_file_rows.append([
                file,
                raga_folder,
                top_raga,
                round(top_data["raw"], 4),
                round(top_data["final"], 4),
                round(top_data["genericness"], 4),
                top_data["transitions"],
                round(margin, 4),
                is_correct
            ])

            # Aggregate per-raga stats
            stats = raga_stats.setdefault(raga_folder, {
                "total": 0,
                "correct": 0
            })

            stats["total"] += 1
            if is_correct:
                stats["correct"] += 1

            print(f"{file} | True={raga_folder} | Pred={top_raga} "
                  f"| Raw={top_data['raw']:.3f} "
                  f"| Final={top_data['final']:.3f} "
                  f"| Gen={top_data['genericness']:.3f} "
                  f"| Trans={top_data['transitions']} "
                  f"| Margin={margin:.3f}")

    # =========================
    # SAVE PER FILE CSV
    # =========================
    with open(PER_FILE_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file",
            "true_raga",
            "predicted_raga",
            "raw_score",
            "final_score",
            "genericness",
            "transitions",
            "top2_margin",
            "correct"
        ])
        writer.writerows(per_file_rows)

    # =========================
    # SAVE PER RAGA CSV
    # =========================
    per_raga_rows = []
    for raga, stats in raga_stats.items():
        acc = stats["correct"] / stats["total"]
        per_raga_rows.append([raga, stats["total"], stats["correct"], round(acc, 4)])

    with open(PER_RAGA_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["raga", "total", "correct", "accuracy"])
        writer.writerows(per_raga_rows)

    # =========================
    # SAVE SUMMARY
    # =========================
    overall_accuracy = correct / total_files if total_files > 0 else 0

    with open(SUMMARY_TXT, "w") as f:
        f.write(f"Total files: {total_files}\n")
        f.write(f"Correct: {correct}\n")
        f.write(f"Overall accuracy: {overall_accuracy:.4f}\n")

    print("\n===================================")
    print(f"Overall accuracy: {overall_accuracy:.4f}")
    print("Results saved to:", RUN_DIR)
    print("===================================")


if __name__ == "__main__":
    evaluate()
