#!/usr/bin/env python3
"""
Q-003 PHASE 1-A  --  PCD CONFUSION DIAGNOSTIC (Bhairavi)

ONE question: does PCD similarity explain Bhairavi's actual confusion pattern?

DIAGNOSTIC ONLY. Read-only against datasets and feature caches. No production
script, dataset, feature cache, weight or threshold is modified. No clip is
added or removed. No ML. No feature is invented.

Established before this run (Q-003 Phase 0, commit 908dbaa):
  - Bhairavi 11 clips, 1C / 6W / 4U = 14% decided
  - Bhairavi errors: Saveri 4, Thodi 2
  - Current mean-PCD overlap Bhairavi-Thodi   = 0.7840
  - Current mean-PCD overlap Bhairavi-Kalyani = 0.7487
  - Bhairavi-Saveri overlap: NEVER MEASURED

Why this script exists (existing tooling cannot produce the required output):
  - scripts/_diag_weak_ragas.py computes the overlap metric but ONLY for
    Bhairavi-Thodi and Bhairavi-Kalyani. It has no Saveri comparison.
  - scripts/confusion_matrix_audit.py computes per-fold margin/tier/prediction
    (its lines 151-155) but aggregates them into a matrix and RETURNS NOTHING
    per clip. Per-clip margins cannot be recovered from it without modifying
    it, and it is canonical audit tooling.

Reuse, not duplication (CLAUDE.md, ADR-015):
  - load_clips / compute_features / idf_var_weights are IMPORTED from
    confusion_matrix_audit.py, not reimplemented.
  - MARGIN_STRICT / MIN_MARGIN_FINAL / PCD_WEIGHT / DYAD_WEIGHT / EPS come from
    production recognize_raga_v12.py. NO THRESHOLD IS INVENTED HERE.
  - The overlap metric is the definition recovered in Phase 0 from
    _diag_weak_ragas.py: histogram intersection sum(min(mean_a, mean_b)).

The LOO fold loop is replicated (not imported) solely because run_loo_cm does
not return per-clip detail. It mirrors that function's arithmetic line for
line, and the script VALIDATES itself against the canonical baseline before any
diagnostic output is trusted -- evaluation-protocol.md section 7b.

    python sandbox_q003_bhairavi_pcd_diagnostic.py
"""

import os
import re
import io
import csv
import json
import glob
import time
import hashlib
import contextlib
from collections import defaultdict, Counter

import numpy as np

BASE_DIR     = r"D:\Swaragam"
FEATURE_DIR  = os.path.join(BASE_DIR, "pcd_results", "features_v12")
METADATA_DIR = os.path.join(BASE_DIR, "datasets", "staging_metadata")
RESULTS_ROOT = os.path.join(BASE_DIR, "Q003 Bhairavi Diagnosis results")

TARGET     = "Bhairavi"
COMPARATOR = ["Saveri", "Thodi", "Kalyani"]   # Kalyani = contrast control
# Shankarabharanam deliberately excluded: 0 Bhairavi confusions, no overlap
# evidence. Including it would add noise, not signal.

# --- canonical constants: imported, never redefined -----------------------
from recognize_raga_v12 import (
    N_BINS, EPS, PCD_WEIGHT, DYAD_WEIGHT, MARGIN_STRICT, MIN_MARGIN_FINAL,
)

# confusion_matrix_audit.py has no __main__ guard: importing it runs its three
# LOO scenarios. Suppress that output; we want only its functions.
with contextlib.redirect_stdout(io.StringIO()):
    from confusion_matrix_audit import (
        load_clips, compute_features, idf_var_weights, MIN_CLIPS,
    )

# Canonical values this run must reproduce before its output is trusted.
CANON = dict(total=70, correct=25, wrong=14, unknown=31,
             bhairavi=dict(clips=11, c=1, w=6, u=4),
             bhairavi_confusers={"Saveri": 4, "Thodi": 2})


# =========================================================================
# Part 1 -- PCD overlap (metric recovered in Phase 0, unmodified)
# =========================================================================
def mean_pcds(processed):
    by_raga = defaultdict(list)
    for c in processed:
        by_raga[c["raga"]].append(c["pcd"])
    return {r: np.mean(v, axis=0) for r, v in by_raga.items()}


def histogram_intersection(a, b):
    """sum(min(a, b)) over normalized PCD bins -- the Phase 0 definition,
    identical to scripts/_diag_weak_ragas.py."""
    return float(np.sum(np.minimum(a, b)))


# =========================================================================
# Part 2 -- LOO with per-clip capture (mirrors run_loo_cm's arithmetic)
# =========================================================================
def loo_per_clip(processed):
    """Returns one record per clip. Arithmetic mirrors confusion_matrix_audit.
    run_loo_cm lines 111-168; that function aggregates and returns nothing."""
    rows = []
    for i, held in enumerate(processed):
        train = processed[:i] + processed[i + 1:]

        raga_data = defaultdict(list)
        for c in train:
            raga_data[c["raga"]].append(c)

        models = {
            raga: {"pcd":  np.mean([c["pcd"]  for c in rc], axis=0),
                   "up":   np.mean([c["up"]   for c in rc], axis=0),
                   "down": np.mean([c["down"] for c in rc], axis=0)}
            for raga, rc in raga_data.items()
        }
        weights = idf_var_weights(models)

        pcd_w = held["pcd"] * weights
        pcd_w = pcd_w / (np.sum(pcd_w) + EPS)

        scores, pcd_sims, dyad_sims = {}, {}, {}
        for raga, m in models.items():
            model_w = m["pcd"] * weights
            model_w = model_w / (np.sum(model_w) + EPS)
            pcd_sim  = float(np.dot(pcd_w, model_w))
            dyad_sim = float(0.5 * (np.dot(held["up"],   m["up"]) +
                                    np.dot(held["down"], m["down"])))
            pcd_sims[raga], dyad_sims[raga] = pcd_sim, dyad_sim
            scores[raga] = PCD_WEIGHT * pcd_sim + DYAD_WEIGHT * dyad_sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0.0

        if   margin >= MARGIN_STRICT:    tier, pred = "HIGH", ranked[0][0]
        elif margin >= MIN_MARGIN_FINAL: tier, pred = "MOD",  ranked[0][0]
        else:                            tier, pred = "UNK",  "UNKNOWN"

        true_raga = held["raga"]
        outcome = ("correct" if pred == true_raga
                   else "unknown" if tier == "UNK" else "wrong")

        rows.append(dict(
            fname=held["fname"], true_raga=true_raga, predicted=pred,
            tier=tier, outcome=outcome, margin=float(margin),
            top1=ranked[0][0], top1_score=float(ranked[0][1]),
            top2=ranked[1][0] if len(ranked) > 1 else None,
            top2_score=float(ranked[1][1]) if len(ranked) > 1 else None,
            scores={k: float(v) for k, v in scores.items()},
            pcd_sims=pcd_sims, dyad_sims=dyad_sims))
    return rows


def tally(rows):
    stats = defaultdict(lambda: {"t": 0, "c": 0, "w": 0, "u": 0})
    tot = {"c": 0, "w": 0, "u": 0}
    for r in rows:
        s = stats[r["true_raga"]]
        s["t"] += 1
        s[r["outcome"][0]] += 1
        tot[r["outcome"][0]] += 1
    return dict(stats), tot


# =========================================================================
# Part 3 -- provenance (evidence only; never inferred from filenames)
# =========================================================================
_ISO_RE = re.compile(r"\.(demucs-vocal|vocal-s|vocal|mix)$")
_TS_RE  = re.compile(r"\d{8}_\d{6}")


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def _clip_base(npz_name):
    stem = os.path.splitext(npz_name)[0]
    parts = stem.rsplit("_", 2)
    if len(parts) == 3 and _TS_RE.fullmatch("_".join(parts[1:])):
        return parts[0]
    return stem


def saraga_index():
    idx = {}
    for path in glob.glob(os.path.join(METADATA_DIR, "*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        works = d.get("work") or []
        rec = dict(
            composition=(works[0].get("title") if works else d.get("title")),
            work_mbid=(works[0].get("mbid") if works else None),
            performer=", ".join(a["name"] for a in d.get("album_artists", [])) or None,
            length_ms=d.get("length"),
            source_file=os.path.basename(path))
        for key in filter(None, [d.get("title"),
                                 os.path.splitext(os.path.basename(path))[0]]):
            idx[_norm(key)] = rec
    return idx


def provenance_for(npz_name, idx):
    """Evidence-backed metadata only. Unknown fields are reported as
    NOT ESTABLISHED -- never inferred from the filename."""
    base = _clip_base(npz_name)
    stripped = _ISO_RE.sub("", base)
    iso = _ISO_RE.search(base)
    hit = idx.get(_norm(stripped))
    if hit is None:
        cand = [v for k, v in idx.items() if _norm(stripped) and _norm(stripped) in k]
        hit = cand[0] if len(cand) == 1 else None
    if hit is None:
        return dict(clip_id=base, composition="NOT ESTABLISHED",
                    work_mbid=None, performer="NOT ESTABLISHED",
                    recording="NOT ESTABLISHED",
                    isolation=(iso.group(1) if iso else "NOT ESTABLISHED"),
                    provenance_source="none found")
    return dict(clip_id=base, composition=hit["composition"],
                work_mbid=hit["work_mbid"], performer=hit["performer"],
                recording=hit["source_file"],
                isolation=(iso.group(1) if iso else "NOT ESTABLISHED"),
                provenance_source=hit["source_file"])


def clip_shape(npz_name):
    d = np.load(os.path.join(FEATURE_DIR, npz_name), allow_pickle=True)
    return dict(sa_hz=float(d["sa_hz"]), f0_frames=int(d["f0"].shape[0]),
                gated_frames=int(d["cents_gated"].shape[0]),
                gating_ratio=float(d["gating_ratio"]))


# =========================================================================
def _versions():
    import sys
    v = dict(python=sys.version.split()[0], numpy=np.__version__)
    try:
        import librosa
        v["librosa"] = librosa.__version__
    except Exception:
        pass
    return v


def _git_commit():
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE_DIR,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def main():
    t0 = time.time()
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_ROOT, f"run_{ts}")
    os.makedirs(run_dir, exist_ok=False)

    print("=" * 78)
    print("Q-003 PHASE 1-A  --  PCD CONFUSION DIAGNOSTIC (Bhairavi)")
    print("=" * 78)

    # Mirrors confusion_matrix_audit.py's main block (lines 215-227) exactly:
    # load, apply the MIN_CLIPS eligibility filter, precompute features once.
    with contextlib.redirect_stdout(io.StringIO()):
        all_clips = load_clips()
    raga_counts = Counter(c["raga"] for c in all_clips)
    eligible = {r for r, n in raga_counts.items() if n >= MIN_CLIPS}
    clips = [c for c in all_clips if c["raga"] in eligible]
    processed = []
    for c in clips:
        pcd, up, down = compute_features(c["cents"])
        processed.append({"fname": c["fname"], "raga": c["raga"],
                          "pcd": pcd, "up": up, "down": down})

    print(f"eligible clips: {len(processed)} | ragas: "
          f"{len(set(c['raga'] for c in processed))}")

    # ---- Part 1: overlap ------------------------------------------------
    means = mean_pcds(processed)
    overlaps = {}
    for other in COMPARATOR:
        overlaps[other] = histogram_intersection(means[TARGET], means[other])
    all_overlaps = {r: histogram_intersection(means[TARGET], means[r])
                    for r in sorted(means) if r != TARGET}

    print("\n" + "-" * 78)
    print("PART 1 -- mean-PCD overlap, histogram intersection sum(min(a,b))")
    print("-" * 78)
    for r in sorted(all_overlaps, key=lambda k: -all_overlaps[k]):
        mark = "  <- comparator" if r in COMPARATOR else ""
        print(f"  {TARGET}-{r:20s} {all_overlaps[r]:.4f}{mark}")

    # ---- Part 2: LOO with per-clip capture ------------------------------
    rows = loo_per_clip(processed)
    stats, tot = tally(rows)
    decided = tot["c"] + tot["w"]
    acc = tot["c"] / decided if decided else 0.0

    # ---- Part 3: self-validation against canonical (protocol 7b) --------
    b = stats[TARGET]
    conf = Counter(r["predicted"] for r in rows
                   if r["true_raga"] == TARGET and r["outcome"] == "wrong")
    checks = {
        "total_clips":        (len(rows), CANON["total"]),
        "correct":            (tot["c"],  CANON["correct"]),
        "wrong":              (tot["w"],  CANON["wrong"]),
        "unknown":            (tot["u"],  CANON["unknown"]),
        "bhairavi_clips":     (b["t"],    CANON["bhairavi"]["clips"]),
        "bhairavi_correct":   (b["c"],    CANON["bhairavi"]["c"]),
        "bhairavi_wrong":     (b["w"],    CANON["bhairavi"]["w"]),
        "bhairavi_unknown":   (b["u"],    CANON["bhairavi"]["u"]),
        "bhairavi_to_saveri": (conf.get("Saveri", 0), CANON["bhairavi_confusers"]["Saveri"]),
        "bhairavi_to_thodi":  (conf.get("Thodi", 0),  CANON["bhairavi_confusers"]["Thodi"]),
    }
    print("\n" + "-" * 78)
    print("PART 2 -- baseline validation against canonical (protocol 7b)")
    print("-" * 78)
    all_ok = True
    for k, (got, want) in checks.items():
        ok = (got == want)
        all_ok &= ok
        print(f"  {k:22s} got={got:>4} canonical={want:>4}  {'OK' if ok else '*** MISMATCH ***'}")
    print(f"  overall: {tot['c']}C / {tot['w']}W / {tot['u']}U = {acc*100:.1f}%")
    if not all_ok:
        raise SystemExit("STOP -- replicated LOO does not reproduce the canonical "
                         "baseline. Diagnostic output is NOT trustworthy.")
    print("  BASELINE REPRODUCED -- diagnostic output may be interpreted.")

    # ---- Part 4: the six Bhairavi errors --------------------------------
    idx = saraga_index()
    errs = [r for r in rows if r["true_raga"] == TARGET and r["outcome"] == "wrong"]
    print("\n" + "-" * 78)
    print(f"PART 3 -- Bhairavi misclassified clips (n={len(errs)})")
    print("-" * 78)
    err_records = []
    for r in sorted(errs, key=lambda x: -x["margin"]):
        prov = provenance_for(r["fname"], idx)
        shape = clip_shape(r["fname"])
        rec = dict(r, **{f"prov_{k}": v for k, v in prov.items()},
                   **{f"shape_{k}": v for k, v in shape.items()})
        err_records.append(rec)
        print(f"  {prov['clip_id'][:46]:46s}")
        print(f"    predicted={r['predicted']:<10s} tier={r['tier']:<5s} "
              f"margin={r['margin']:.6f}")
        print(f"    top1={r['top1']}({r['top1_score']:.6f})  "
              f"top2={r['top2']}({r['top2_score']:.6f})  true={TARGET}"
              f"({r['scores'][TARGET]:.6f})")
        print(f"    PCD sim  true={r['pcd_sims'][TARGET]:.6f}  "
              f"pred={r['pcd_sims'][r['predicted']]:.6f}")
        print(f"    dyad sim true={r['dyad_sims'][TARGET]:.6f}  "
              f"pred={r['dyad_sims'][r['predicted']]:.6f}")
        print(f"    composition={prov['composition']} | performer={prov['performer']}")
        print(f"    Sa={shape['sa_hz']:.1f}Hz gated={shape['gated_frames']} "
              f"gating={shape['gating_ratio']:.3f}")

    print(f"\n  confuser distribution: {dict(conf)}")

    # ---- artifacts ------------------------------------------------------
    bh_rows = [r for r in rows if r["true_raga"] == TARGET]
    with open(os.path.join(run_dir, "error_analysis.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["clip_id", "outcome", "predicted", "tier", "margin",
                    "score_true", "score_pred", "pcd_sim_true", "pcd_sim_pred",
                    "dyad_sim_true", "dyad_sim_pred", "composition", "performer",
                    "isolation", "provenance_source", "sa_hz", "gated_frames",
                    "gating_ratio"])
        for r in sorted(bh_rows, key=lambda x: (x["outcome"], -x["margin"])):
            p = provenance_for(r["fname"], idx)
            s = clip_shape(r["fname"])
            pred = r["predicted"]
            w.writerow([p["clip_id"], r["outcome"], pred, r["tier"],
                        f"{r['margin']:.8f}", f"{r['scores'][TARGET]:.8f}",
                        f"{r['scores'][pred]:.8f}" if pred in r["scores"] else "",
                        f"{r['pcd_sims'][TARGET]:.8f}",
                        f"{r['pcd_sims'][pred]:.8f}" if pred in r["pcd_sims"] else "",
                        f"{r['dyad_sims'][TARGET]:.8f}",
                        f"{r['dyad_sims'][pred]:.8f}" if pred in r["dyad_sims"] else "",
                        p["composition"], p["performer"], p["isolation"],
                        p["provenance_source"], f"{s['sa_hz']:.2f}",
                        s["gated_frames"], f"{s['gating_ratio']:.4f}"])

    with open(os.path.join(run_dir, "pcd_overlap.json"), "w") as fh:
        json.dump(dict(
            metric="histogram intersection: sum(min(mean_PCD_a, mean_PCD_b))",
            metric_source="recovered Phase 0 from scripts/_diag_weak_ragas.py",
            n_bins=N_BINS, normalization="hist / sum(hist)",
            target=TARGET, comparators=COMPARATOR,
            comparator_overlaps=overlaps, all_overlaps=all_overlaps,
            note="Descriptive similarity. NOT an established cause of "
                 "Bhairavi's errors."), fh, indent=2)

    with open(os.path.join(run_dir, "baseline_validation.json"), "w") as fh:
        json.dump(dict(checks={k: dict(got=v[0], canonical=v[1], ok=v[0] == v[1])
                               for k, v in checks.items()},
                       all_passed=bool(all_ok),
                       overall=dict(correct=tot["c"], wrong=tot["w"],
                                    unknown=tot["u"], accuracy=acc),
                       per_raga=stats), fh, indent=2)

    with open(os.path.join(run_dir, "error_analysis.json"), "w") as fh:
        json.dump(dict(n_errors=len(errs), confuser_distribution=dict(conf),
                       errors=err_records), fh, indent=2)

    meta = dict(
        gate="Q-003", phase="1-A", timestamp=ts, run_dir=run_dir,
        question="Does PCD similarity explain Bhairavi's actual confusion pattern?",
        target=TARGET, comparators=COMPARATOR,
        excluded_comparator=dict(raga="Shankarabharanam",
                                 reason="0 Bhairavi confusions, no overlap evidence"),
        constants=dict(n_bins=N_BINS, pcd_weight=PCD_WEIGHT,
                       dyad_weight=DYAD_WEIGHT, margin_strict=MARGIN_STRICT,
                       min_margin_final=MIN_MARGIN_FINAL,
                       source="recognize_raga_v12.py -- imported, none invented"),
        reused=dict(functions="load_clips, compute_features, idf_var_weights "
                              "imported from confusion_matrix_audit.py",
                    metric="histogram intersection from _diag_weak_ragas.py"),
        feature_dir=FEATURE_DIR, n_clips=len(processed),
        software=_versions(), git_commit=_git_commit(),
        elapsed_sec=round(time.time() - t0, 2),
        read_only=True, modifies_production=False, modifies_dataset=False)
    with open(os.path.join(run_dir, "run_metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    print(f"\nresults: {run_dir}")
    print("=" * 78)


if __name__ == "__main__":
    main()
