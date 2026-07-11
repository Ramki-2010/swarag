import os
from datetime import datetime
from recognize_raga_v12 import recognize_raga

# =========================
# CONFIG
# =========================

DATASET_FOLDER = r"D:\Swaragam\datasets\seed_carnatic"
AGG_FOLDER = r"D:\Swaragam\pcd_results\aggregation\v1.2\run_20260215_113720"
OUTPUT_BASE = r"D:\Swaragam\pcd_results\evaluation"

SUPPORTED_EXTS = (".wav", ".mp3", ".flac")


# =========================
# MAIN EVALUATION
# =========================

def evaluate():

    print("\nStarting Swarag v1.2 Batch Evaluation")
    print("======================================\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(OUTPUT_BASE, f"run_{timestamp}")
    os.makedirs(run_folder, exist_ok=True)

    total = 0
    correct = 0

    for raga in os.listdir(DATASET_FOLDER):

        raga_path = os.path.join(DATASET_FOLDER, raga)

        if not os.path.isdir(raga_path):
            continue

        for file in os.listdir(raga_path):

            if not file.lower().endswith(SUPPORTED_EXTS):
                continue

            audio_path = os.path.join(raga_path, file)

            print(f"Analyzing: {file}")

            try:
                result = recognize_raga(audio_path, AGG_FOLDER)

                predicted = result["final"]
                ranking = result["ranking"]
                margin = result["margin"]

                total += 1

                if predicted == raga:
                    correct += 1

                print(f"True: {raga}")
                print(f"Predicted: {predicted}")
                print(f"Margin: {round(margin, 4)}\n")

            except Exception as e:
                print(f"Error processing {file}: {e}\n")

    if total > 0:
        accuracy = correct / total
    else:
        accuracy = 0.0

    print("===================================")
    print(f"Overall accuracy: {round(accuracy, 4)}")
    print("Results saved to:")
    print(run_folder)


if __name__ == "__main__":
    evaluate()