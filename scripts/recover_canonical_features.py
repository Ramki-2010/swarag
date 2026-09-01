"""
Canonical feature-population recovery + duplicate cleanup.

DRY RUN BY DEFAULT. Nothing moves unless you pass --execute.

Purpose (one-time, reversible):
  A. Restore 6 Bhairavi_clean_*.npz  excluded/ -> features_v12/
  B. Retire 4 July Abhogi duplicate re-extractions   features_v12/ -> excluded/
  C. Retire 1 July Kamakshi duplicate re-extraction  features_v12/ -> excluded/

Every operation is a MOVE (shutil.move). Nothing is deleted, nothing is
overwritten, nothing is regenerated. Matches the March 2026 precedent set by
scripts/_cleanup_duplicates.py, which moved rather than deleted so provenance
stayed recoverable.

WHY RETIREMENT FILENAMES ARE RESOLVED, NOT HARDCODED
----------------------------------------------------
The July timestamps were never transcribed into this script, so hardcoding them
would mean guessing. Instead each duplicate is resolved from the directory
itself: for each of the 5 known duplicated SOURCES, the script finds every .npz
whose basename matches that source prefix, requires EXACTLY 2 matches, and
retires the one with the later timestamp (March < July lexicographically in
YYYYMMDD_HHMMSS). Anything other than exactly 2 matches aborts.

The resolved pairing is printed in full during dry run. READ IT and confirm the
KEEP/RETIRE assignment matches your verified inventory before using --execute.

VERIFICATION MODEL
------------------
Post-flight checks are FILENAME-BASED, not count-based. excluded/ holds
unrelated historical artifacts, so its total is not a valid invariant. The
script asserts, per file:
  - each of the 6 restored files is PRESENT in features_v12/ and ABSENT from excluded/
  - each of the 5 retired  files is PRESENT in excluded/     and ABSENT from features_v12/
plus per-raga active counts and the seven-raga modeled total.

Completing all moves is NOT success. The script exits non-zero and prints
VERIFICATION FAILED if any assertion fails, even when every move succeeded.

Usage:
    python recover_canonical_features.py            # dry run, verify only
    python recover_canonical_features.py --execute  # perform the moves
"""

import os
import sys
import shutil
from collections import Counter

import numpy as np

FEAT_DIR = r"D:\Swaragam\pcd_results\features_v12"
EXCL_DIR = os.path.join(FEAT_DIR, "excluded")

EXECUTE = "--execute" in sys.argv

# ---------------------------------------------------------------- A. RESTORE
# excluded/ -> features_v12/ . Required by the frozen dataset definition
# (datasets.md: Bhairavi = 11 = 6 clean wav + 1 stem + 4 demucs).
# These filenames were verified in the local excluded/ listing.
RESTORE_FROM_EXCLUDED = [
    "Bhairavi_clean_1_20260309_005922.npz",
    "Bhairavi_clean_2_20260309_010008.npz",
    "Bhairavi_clean_3_20260309_010240.npz",
    "Bhairavi_clean_4_20260309_010506.npz",
    "Bhairavi_clean_5_20260309_010733.npz",
    "Bhairavi_clean_6_20260309_011001.npz",
]

# ---------------------------------------------------------------- B/C. RETIRE
# Sources with a confirmed duplicate re-extraction. Filenames resolved at
# runtime from these prefixes; exactly 2 matches required per source.
DUPLICATE_SOURCE_PREFIXES = [
    "223578__gopalkoduri__carnatic-varnam-by-dharini-in-abhogi-raaga",
    "223579__gopalkoduri__carnatic-varnam-by-prasanna-in-abhogi-raaga",
    "223580__gopalkoduri__carnatic-varnam-by-ramakrishnamurthy-in-abhogi-raaga",
    "223581__gopalkoduri__carnatic-varnam-by-sreevidya-in-abhogi-raaga",
    "Sanjay Subrahmanyan - Kamakshi",
]

EXPECTED_ACTIVE_TOTAL = 75
EXPECTED_SEVEN_RAGA_TOTAL = 70
EXPECTED_PER_RAGA = {
    "Abhogi": 7,
    "Bhairavi": 11,
    "Kalyani": 14,
    "Mohanam": 10,
    "Saveri": 8,
    "Shankarabharanam": 9,
    "Thodi": 11,
}
EXPECTED_STAGED = {"Kamboji": 3, "Madhyamavati": 2}
MODELED_RAGAS = set(EXPECTED_PER_RAGA)


# --------------------------------------------------------------- inventory
def raga_counts(directory):
    """Per-raga .npz counts read from each file's own metadata, not filenames."""
    counts = Counter()
    unreadable = []
    if not os.path.isdir(directory):
        return counts, unreadable
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".npz"):
            continue
        try:
            d = np.load(os.path.join(directory, fname), allow_pickle=True)
            counts[str(d["raga"])] += 1
        except Exception as exc:
            unreadable.append((fname, str(exc)))
    return counts, unreadable


def show_inventory(title, directory):
    counts, unreadable = raga_counts(directory)
    total = sum(counts.values())
    print("\n{}  ({})".format(title, directory))
    print("-" * 76)
    if not counts:
        print("  (no readable .npz files)")
    for raga in sorted(counts):
        mark = "  <- modeled" if raga in MODELED_RAGAS else ""
        print("  {:22s} {:3d}{}".format(raga, counts[raga], mark))
    print("  {:22s} {:3d}".format("TOTAL .npz", total))
    if unreadable:
        print("  !! UNREADABLE:")
        for fname, exc in unreadable:
            print("     {} -- {}".format(fname[:58], exc))
    return counts, total


# ------------------------------------------------- duplicate name resolution
def resolve_duplicates():
    """Resolve the 5 duplicate filenames from FEAT_DIR. Returns (retire, keep, problems)."""
    retire, keep, problems = [], [], []

    if not os.path.isdir(FEAT_DIR):
        return retire, keep, ["FEAT_DIR does not exist: {}".format(FEAT_DIR)]

    all_npz = [f for f in sorted(os.listdir(FEAT_DIR)) if f.endswith(".npz")]

    for prefix in DUPLICATE_SOURCE_PREFIXES:
        matches = [f for f in all_npz if f.startswith(prefix)]
        if len(matches) != 2:
            problems.append(
                "Source '{}' matched {} file(s), expected exactly 2:{}".format(
                    prefix[:52], len(matches),
                    "".join("\n        - " + m for m in matches) or " (none)"))
            continue
        ordered = sorted(matches)          # timestamps sort chronologically
        keep.append(ordered[0])            # March  -> canonical, stays active
        retire.append(ordered[1])          # July   -> duplicate, retired

    return retire, keep, problems


# ------------------------------------------------------------------ preflight
def preflight(retire_list):
    """Verify every planned move is safe. Returns list of (src, dst, kind) or None."""
    problems, planned = [], []

    if not os.path.isdir(FEAT_DIR):
        problems.append("FEAT_DIR does not exist: {}".format(FEAT_DIR))
    if not os.path.isdir(EXCL_DIR):
        problems.append("EXCL_DIR does not exist: {}".format(EXCL_DIR))

    if len(retire_list) != 5:
        problems.append(
            "Resolved {} duplicates, expected 5. Not proceeding.".format(len(retire_list)))

    for fname in RESTORE_FROM_EXCLUDED:
        src, dst = os.path.join(EXCL_DIR, fname), os.path.join(FEAT_DIR, fname)
        if not os.path.exists(src):
            problems.append("RESTORE source missing in excluded/: {}".format(fname))
        elif os.path.exists(dst):
            problems.append("RESTORE would overwrite existing active file: {}".format(fname))
        else:
            planned.append((src, dst, "RESTORE"))

    for fname in retire_list:
        src, dst = os.path.join(FEAT_DIR, fname), os.path.join(EXCL_DIR, fname)
        if not os.path.exists(src):
            problems.append("RETIRE source missing in features_v12/: {}".format(fname))
        elif os.path.exists(dst):
            problems.append("RETIRE would overwrite existing excluded file: {}".format(fname))
        else:
            planned.append((src, dst, "RETIRE"))

    if problems:
        print("\nPRE-FLIGHT FAILED -- no files touched:")
        for p in problems:
            print("  X {}".format(p))
        return None

    print("\nPRE-FLIGHT PASSED. {} planned moves:".format(len(planned)))
    for src, _dst, kind in planned:
        print("  {:8s} {}".format(kind, os.path.basename(src)[:64]))
    return planned


# ------------------------------------------------------------- verification
def verify_post(retire_list):
    """Filename-based invariants. excluded/ total is NOT used as an invariant."""
    counts, active_total = show_inventory("POST-MOVE ACTIVE INVENTORY", FEAT_DIR)
    show_inventory("POST-MOVE EXCLUDED INVENTORY (informational only)", EXCL_DIR)

    failures = []

    print("\nFILE PLACEMENT CHECKS")
    print("-" * 76)
    for fname in RESTORE_FROM_EXCLUDED:
        in_active = os.path.exists(os.path.join(FEAT_DIR, fname))
        in_excl = os.path.exists(os.path.join(EXCL_DIR, fname))
        ok = in_active and not in_excl
        if not ok:
            failures.append("RESTORED file misplaced: {} (active={}, excluded={})".format(
                fname, in_active, in_excl))
        print("  {} RESTORED {}".format("OK  " if ok else "FAIL", fname[:58]))

    for fname in retire_list:
        in_active = os.path.exists(os.path.join(FEAT_DIR, fname))
        in_excl = os.path.exists(os.path.join(EXCL_DIR, fname))
        ok = in_excl and not in_active
        if not ok:
            failures.append("RETIRED file misplaced: {} (active={}, excluded={})".format(
                fname, in_active, in_excl))
        print("  {} RETIRED  {}".format("OK  " if ok else "FAIL", fname[:58]))

    print("\nPER-RAGA ACTIVE COUNTS")
    print("-" * 76)
    for raga in sorted(EXPECTED_PER_RAGA):
        want, got = EXPECTED_PER_RAGA[raga], counts.get(raga, 0)
        if got != want:
            failures.append("{}: expected {}, got {}".format(raga, want, got))
        print("  {} {:22s} expected {:3d}  got {:3d}  (modeled)".format(
            "OK  " if got == want else "FAIL", raga, want, got))
    for raga in sorted(EXPECTED_STAGED):
        want, got = EXPECTED_STAGED[raga], counts.get(raga, 0)
        if got != want:
            failures.append("{}: expected {}, got {}".format(raga, want, got))
        print("  {} {:22s} expected {:3d}  got {:3d}  (staged)".format(
            "OK  " if got == want else "FAIL", raga, want, got))

    print("\nTOTALS")
    print("-" * 76)
    seven = sum(counts.get(r, 0) for r in MODELED_RAGAS)
    for label, want, got in [
        ("seven-raga modeled", EXPECTED_SEVEN_RAGA_TOTAL, seven),
        ("active total", EXPECTED_ACTIVE_TOTAL, active_total),
    ]:
        if got != want:
            failures.append("{}: expected {}, got {}".format(label, want, got))
        print("  {} {:22s} expected {:3d}  got {:3d}".format(
            "OK  " if got == want else "FAIL", label, want, got))

    print("\n" + "=" * 76)
    if failures:
        print("VERIFICATION FAILED -- {} problem(s). The moves completed, but the".format(len(failures)))
        print("resulting state is NOT the canonical population. Do not run")
        print("confusion_matrix_audit.py until these are resolved:")
        for f in failures:
            print("  X {}".format(f))
        print("=" * 76)
        return False
    print("VERIFICATION PASSED -- canonical population restored.")
    print("=" * 76)
    return True


# ------------------------------------------------------------------- driver
def main():
    print("=" * 76)
    print("CANONICAL FEATURE RECOVERY  --  {}".format(
        "EXECUTE MODE" if EXECUTE else "DRY RUN (no files will move)"))
    print("=" * 76)

    show_inventory("CURRENT ACTIVE INVENTORY", FEAT_DIR)
    show_inventory("CURRENT EXCLUDED INVENTORY (informational only)", EXCL_DIR)

    retire_list, keep_list, problems = resolve_duplicates()

    print("\nDUPLICATE RESOLUTION  --  CONFIRM THIS PAIRING BEFORE --execute")
    print("-" * 76)
    for k, r in zip(keep_list, retire_list):
        print("  KEEP   {}".format(k[:66]))
        print("  RETIRE {}".format(r[:66]))
        print()
    if problems:
        print("  RESOLUTION PROBLEMS:")
        for p in problems:
            print("  X {}".format(p))

    planned = preflight(retire_list)
    if planned is None:
        sys.exit(1)

    if not EXECUTE:
        print("\nDRY RUN COMPLETE. Nothing moved.")
        print("Confirm the KEEP/RETIRE pairing above, then re-run with --execute")
        print("to perform the {} moves.".format(len(planned)))
        return

    print("\nEXECUTING")
    print("-" * 76)
    done = []
    try:
        for src, dst, kind in planned:
            shutil.move(src, dst)
            done.append((dst, src))
            print("  {:8s} {}".format(kind, os.path.basename(src)[:64]))
    except Exception as exc:
        print("\nERROR mid-run: {}".format(exc))
        print("Rolling back {} completed move(s)...".format(len(done)))
        for dst, src in reversed(done):
            try:
                shutil.move(dst, src)
                print("  REVERTED {}".format(os.path.basename(dst)[:60]))
            except Exception as rexc:
                print("  ROLLBACK FAILED {} -- {}".format(os.path.basename(dst)[:48], rexc))
        sys.exit(1)

    print("\nAll {} moves completed. Completion is not success -- verifying...".format(len(done)))
    sys.exit(0 if verify_post(retire_list) else 1)


if __name__ == "__main__":
    main()