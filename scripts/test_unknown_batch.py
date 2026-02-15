import os
import csv
import random
from recognize_raga import recognize_raga

# =========================
# CONFIG
# =========================
AUDIO_DIR = r"D:\Swagaram\datasets\audio test"
OUT_DIR = r"D:\Swagaram\pcd_results\inference"

TOP_K = 3
SHUFFLE_AUDIO = True   # set False if you want fixed order

os.makedirs(OUT_DIR, exist_ok=True)


# =========================
# INFERENCE RUNNER
# =========================
def run_inference():
    audio_files = [
        f for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(".wav")
    ]

    if not audio_files:
        print("No audio files found in inference directory.")
        return

    if SHUFFLE_AUDIO:
        random.shuffle(audio_files)

    results = []

    print("\n--- Swarag 1.0 | Inference Mode ---\n")

    for fname in audio_files:
        audio_path = os.path.join(AUDIO_DIR, fname)

        try:
            verdict, ranked, best_dist = recognize_raga(audio_path)
        except KeyboardInterrupt:
            print("\nInterrupted by user. Saving partial results...")
            break
        except Exception as e:
            print(f"ERROR processing {fname}: {e}")
            continue

        top_ragas = ranked[:TOP_K]

        results.append([
            fname,
            verdict,
            best_dist,
            [r[0] for r in top_ragas],
            [round(r[1], 4) for r in top_ragas],
            [round(r[2], 4) for r in top_ragas],
        ])

        # ---- Console output ----
        print(f"File: {fname}")
        for raga, dist, conf in top_ragas:
            print(
                f"  {raga:18s} | "
                f"Distance: {dist:.3f} | "
                f"Confidence: {conf*100:.1f}%"
            )
        print(f"  → Final Verdict: {verdict}")
        print("-" * 50)

        # ---- Incremental save ----
        save_partial(results)

    save_final(results)


# =========================
# SAVE HELPERS
# =========================
def save_partial(rows):
    path = os.path.join(OUT_DIR, "inference_results_partial.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename",
            "final_verdict",
            "best_distance",
            f"top_{TOP_K}_ragas",
            f"top_{TOP_K}_distances",
            f"top_{TOP_K}_confidence_scores"
        ])
        writer.writerows(rows)


def save_final(rows):
    path = os.path.join(OUT_DIR, "inference_results.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename",
            "final_verdict",
            "best_distance",
            f"top_{TOP_K}_ragas",
            f"top_{TOP_K}_distances",
            f"top_{TOP_K}_confidence_scores"
        ])
        writer.writerows(rows)

    print("\nInference results saved to:")
    print(OUT_DIR)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    run_inference()
