import os
import csv
from datetime import datetime
from recognize_raga_v12 import recognize_raga, load_aggregated_models

# =========================
# CONFIG
# =========================

RANDOM_TEST_FOLDER = r"D:\Swaragam\datasets\audio test"
AGG_FOLDER   = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260331_232228"  # v1.3.1: 7 ragas, 70 clips
OUTPUT_BASE        = r"D:\Swaragam\pcd_results\random_evaluations_v12"

SUPPORTED_EXTS = (".wav", ".mp3", ".flac")


# =========================
# MAIN
# =========================

def main():

    print("\nStarting Swarag v1.2 Random Batch Evaluation")
    print("=============================================\n")

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(OUTPUT_BASE, f"run_{timestamp}")
    os.makedirs(run_folder, exist_ok=True)

    files = [
        f for f in os.listdir(RANDOM_TEST_FOLDER)
        if f.lower().endswith(SUPPORTED_EXTS)
    ]

    if not files:
        print("⚠ No audio files found.")
        return

    # Pre-load models once for efficiency
    models = load_aggregated_models(AGG_FOLDER)
    if not models:
        print(f"✗ No models found in: {AGG_FOLDER}")
        return

    print(f"Loaded {len(models)} raga model(s): {', '.join(sorted(models.keys()))}")
    print(f"Run output: {run_folder}\n")

    # C3: collect rows for CSV output
    csv_rows = []

    for file in files:

        print(f">> Analyzing: {file}\n")

        try:
            audio_path = os.path.join(RANDOM_TEST_FOLDER, file)

            result = recognize_raga(audio_path, AGG_FOLDER, models=models)

            final           = result["final"]
            ranking         = result["ranking"]
            margin          = result["margin"]
            confidence_tier = result.get("confidence_tier", "UNKNOWN")

            top1_score = ranking[0][1] if len(ranking) >= 1 else 0.0
            top2_score = ranking[1][1] if len(ranking) >= 2 else 0.0
            top3_name  = ranking[2][0] if len(ranking) >= 3 else ""
            top3_score = ranking[2][1] if len(ranking) >= 3 else 0.0

            print(f"Final Prediction : {final}")
            print(f"Confidence Tier  : {confidence_tier}")
            print(f"Margin           : {round(margin, 4)}")

            print("\nRanking:")
            for raga, score in ranking:
                print(f"  {raga:20} | {round(score, 4)}")

            print()

            # C3: accumulate CSV data
            csv_rows.append([
                file,
                final,
                confidence_tier,
                round(margin, 6),
                ranking[0][0] if len(ranking) >= 1 else "",
                round(top1_score, 4),
                ranking[1][0] if len(ranking) >= 2 else "",
                round(top2_score, 4),
                top3_name,
                round(top3_score, 4),
            ])

        except Exception as e:
            print(f"✗ Error processing {file}: {e}\n")
            csv_rows.append([file, "ERROR", "UNKNOWN", 0.0, "", 0.0, "", 0.0, "", 0.0])

    # C3: Write CSV
    csv_path = os.path.join(run_folder, "results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file",
            "predicted_raga", "confidence_tier", "margin",
            "top1_raga", "top1_score",
            "top2_raga", "top2_score",
            "top3_raga", "top3_score",
        ])
        writer.writerows(csv_rows)

    print("Random batch evaluation completed.")
    print(f"Results saved to: {csv_path}")


if __name__ == "__main__":
    main()

