import os
import csv
import time
from datetime import datetime

from recognize_raga import recognize_raga

# =========================
# CONFIG
# =========================
AUDIO_DIR = r"D:\Swaragam\datasets\audio test"
OUTPUT_BASE_DIR = r"D:\Swaragam\pcd_results\randomevaluations"

SUPPORTED_EXTS = (".wav", ".mp3", ".flac")

# =========================
# SETUP OUTPUT DIR (NO OVERWRITE)
# =========================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = os.path.join(OUTPUT_BASE_DIR, f"run_{timestamp}")
os.makedirs(RUN_DIR, exist_ok=True)

PER_FILE_CSV = os.path.join(RUN_DIR, "per_file_results.csv")
SUMMARY_TXT = os.path.join(RUN_DIR, "summary.txt")

# =========================
# MAIN
# =========================
def main():
    print("\nStarting Swarag random batch evaluation")
    print("--------------------------------------\n")

    audio_files = [
        f for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(SUPPORTED_EXTS)
    ]

    if not audio_files:
        print("No audio files found.")
        return

    results = []

    for fname in audio_files:
        audio_path = os.path.join(AUDIO_DIR, fname)

        print(f"▶ Analyzing: {fname}")
        try:
            pred, ranking = recognize_raga(audio_path)

            top1 = ranking[0][0]
            top3 = [r for r, _ in ranking[:3]]

            results.append({
                "file": fname,
                "prediction": pred,
                "top1": top1,
                "top3": ", ".join(top3)
            })

            print(f"    ✓ Prediction → {pred}\n")

        except Exception as e:
            print(f"    ✗ Error processing {fname}: {e}\n")
            results.append({
                "file": fname,
                "prediction": "ERROR",
                "top1": "",
                "top3": ""
            })

    # =========================
    # SAVE CSV
    # =========================
    with open(PER_FILE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "prediction", "top1", "top3"]
        )
        writer.writeheader()
        writer.writerows(results)

    # =========================
    # SAVE SUMMARY
    # =========================
    total = len(results)
    unknown = sum(1 for r in results if r["prediction"] == "UNKNOWN / LOW CONFIDENCE")
    errors = sum(1 for r in results if r["prediction"] == "ERROR")

    with open(SUMMARY_TXT, "w", encoding="utf-8") as f:
        f.write("Swarag Random Evaluation Summary\n")
        f.write("--------------------------------\n")
        f.write(f"Total files: {total}\n")
        f.write(f"UNKNOWN / LOW CONFIDENCE: {unknown}\n")
        f.write(f"Errors: {errors}\n")

    print("Batch evaluation completed.\n")
    print("Results saved to:")
    print(RUN_DIR)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()
