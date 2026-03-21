"""Patch aggregate_all_v12.py to add MIN_CLIPS_PER_RAGA guardrail."""
import re

with open("aggregate_all_v12.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add MIN_CLIPS_PER_RAGA constant (idempotent)
if "MIN_CLIPS_PER_RAGA" not in content:
    content = content.replace(
        "MIN_STABLE_FRAMES = 5\nALPHA",
        "MIN_STABLE_FRAMES = 5\nMIN_CLIPS_PER_RAGA = 5  # Ragas with fewer clips excluded (unstable models)\nALPHA"
    )
    print("Added MIN_CLIPS_PER_RAGA constant")

# 2. Add exclusion logic before SAVE PER RAGA (idempotent)
if "FILTER: exclude ragas" not in content:
    old = "    # =========================\n    # SAVE PER RAGA\n    # =========================\n    for raga in raga_pcds.keys():"
    new = """    # =========================
    # FILTER: exclude ragas with too few clips (BUG-011)
    # =========================
    excluded_ragas = []
    for raga in list(raga_pcds.keys()):
        if clip_counts[raga] < MIN_CLIPS_PER_RAGA:
            excluded_ragas.append((raga, clip_counts[raga]))
            del raga_pcds[raga]
            del raga_up[raga]
            del raga_down[raga]
            del raga_gating[raga]
            del raga_transitions[raga]
            del clip_counts[raga]

    if excluded_ragas:
        print()
        print("[EXCLUDED] Ragas with < {} clips:".format(MIN_CLIPS_PER_RAGA))
        for raga, count in excluded_ragas:
            print("  {} ({} clips) -- needs {} more".format(raga, count, MIN_CLIPS_PER_RAGA - count))
        print()

    # =========================
    # SAVE PER RAGA
    # =========================
    for raga in raga_pcds.keys():"""
    content = content.replace(old, new)
    print("Added exclusion logic")

# 3. Update metadata (idempotent)
if "min_clips_per_raga" not in content:
    content = content.replace(
        '        "skipped_files": skipped_files\n    }',
        '        "skipped_files": skipped_files,\n'
        '        "excluded_ragas": {r: c for r, c in excluded_ragas} if excluded_ragas else {},\n'
        '        "included_ragas": list(clip_counts.keys()),\n'
        '        "included_clips": sum(clip_counts.values()),\n'
        '        "min_clips_per_raga": MIN_CLIPS_PER_RAGA\n    }'
    )
    print("Updated metadata")

# 4. Update final print (idempotent)
if "Ragas included" not in content:
    old_print = '    print(f"Files seen: {total_files_seen} | Skipped: {skipped_files}")'
    new_print = (
        '    print(f"Files seen: {total_files_seen} | Skipped: {skipped_files}")\n'
        '    print(f"Ragas included: {len(clip_counts)} | Clips: {sum(clip_counts.values())}")\n'
        '    if excluded_ragas:\n'
        '        print(f"Ragas excluded: {len(excluded_ragas)} (need >= {MIN_CLIPS_PER_RAGA} clips)")'
    )
    content = content.replace(old_print, new_print)
    print("Updated final print")

with open("aggregate_all_v12.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone. aggregate_all_v12.py patched successfully.")
