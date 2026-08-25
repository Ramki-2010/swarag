#!/usr/bin/env python3
"""
Q-003 PHASE 1-B  --  WEIGHTED-CHANNEL DIAGNOSTIC (Bhairavi)

Phase 1-A established (FACT): unweighted mean-PCD overlap does NOT explain
Bhairavi's confusion pattern. Saveri has the LOWEST comparator overlap (0.6782)
yet absorbs 4 of 6 Bhairavi errors; Thodi (0.7840) takes 2; Kalyani (0.7487)
takes 0.

Phase 1-B measures what the scorer ACTUALLY consults, which is not the
unweighted overlap:
  1. IDF x Variance-WEIGHTED PCD similarity
  2. WEIGHTED PCD L2 norms (magnitude, per raga model)
  3. Dyad similarity, measured SEPARATELY from PCD
  4. Relationship of each to incoming error counts
  5. Saveri's rank against the other ragas on each channel

DIAGNOSTIC ONLY. Read-only. No production script, dataset, feature cache,
weight or threshold is modified. No threshold is invented. No fix is applied.
BUG-010 (hubness) is NOT reopened here -- magnitude is measured, not corrected.

Reuse (CLAUDE.md, ADR-015): the LOO fold loop, feature loading and constants
all come from scripts/sandbox_q003_bhairavi_pcd_diagnostic.py (Phase 1-A,
commit 1ef479f), which in turn imports from confusion_matrix_audit.py and
recognize_raga_v12.py. Nothing is reimplemented here; this module only
AGGREGATES and RANKS quantities that pipeline already computes.

    python sandbox_q003_phase1b_weighted_channels.py
"""

import os
import io
import csv
import json
import time
import contextlib
from collections import defaultdict, Counter

import numpy as np

# Phase 1-A module: has a __main__ guard, so importing runs nothing.
from sandbox_q003_bhairavi_pcd_diagnostic import (
    BASE_DIR, RESULTS_ROOT, TARGET, COMPARATOR,
    loo_per_clip, mean_pcds, histogram_intersection,
    _versions, _git_commit,
)
from recognize_raga_v12 import EPS, PCD_WEIGHT, DYAD_WEIGHT
with contextlib.redirect_stdout(io.StringIO()):
    from confusion_matrix_audit import (
        load_clips, compute_features, idf_var_weights, MIN_CLIPS,
    )

# Canonical incoming-error counts, recomputed and corrected 2026-08-21 (C-6).
# Documented as 6/3/2 before that; those summed to 11, not 14.
INCOMING_ERRORS = {"Saveri": 8, "Thodi": 4, "Kalyani": 2,
                   "Abhogi": 0, "Bhairavi": 0, "Mohanam": 0,
                   "Shankarabharanam": 0}


def build_processed():
    """Mirrors confusion_matrix_audit.py's main block exactly."""
    with contextlib.redirect_stdout(io.StringIO()):
        all_clips = load_clips()
    counts = Counter(c["raga"] for c in all_clips)
    eligible = {r for r, n in counts.items() if n >= MIN_CLIPS}
    processed = []
    for c in (x for x in all_clips if x["raga"] in eligible):
        pcd, up, down = compute_features(c["cents"])
        processed.append({"fname": c["fname"], "raga": c["raga"],
                          "pcd": pcd, "up": up, "down": down})
    return processed


def weighted_model_norms(processed):
    """L2 norm of each raga's WEIGHTED, renormalized model vector -- the exact
    vector the scorer dots against. Computed per LOO fold and averaged, because
    idf_var_weights is recomputed every fold."""
    acc = defaultdict(list)
    for i, _ in enumerate(processed):
        train = processed[:i] + processed[i + 1:]
        by = defaultdict(list)
        for c in train:
            by[c["raga"]].append(c)
        models = {r: {"pcd": np.mean([c["pcd"] for c in v], axis=0)}
                  for r, v in by.items()}
        w = idf_var_weights(models)
        for r, m in models.items():
            mw = m["pcd"] * w
            mw = mw / (np.sum(mw) + EPS)
            acc[r].append(float(np.linalg.norm(mw)))
    return {r: dict(mean_l2=float(np.mean(v)), sd_l2=float(np.std(v, ddof=1)))
            for r, v in acc.items()}


def dyad_model_norms(processed):
    """L2 norm of each raga's dyad model (up/down concatenated). Dyads are NOT
    renormalized by the scorer, so magnitude enters directly."""
    acc = defaultdict(list)
    for i, _ in enumerate(processed):
        train = processed[:i] + processed[i + 1:]
        by = defaultdict(list)
        for c in train:
            by[c["raga"]].append(c)
        for r, v in by.items():
            up = np.mean([c["up"] for c in v], axis=0)
            dn = np.mean([c["down"] for c in v], axis=0)
            acc[r].append(float(np.linalg.norm(np.concatenate([up, dn]))))
    return {r: float(np.mean(v)) for r, v in acc.items()}


def channel_ranks(rows):
    """For every clip: rank of the TRUE raga under full / PCD-only / dyad-only,
    and which raga each channel would pick. Rank 1 = channel favours truth."""
    out = []
    for r in rows:
        t = r["true_raga"]
        full = sorted(r["scores"].items(), key=lambda x: -x[1])
        pcd = sorted(r["pcd_sims"].items(), key=lambda x: -x[1])
        dyd = sorted(r["dyad_sims"].items(), key=lambda x: -x[1])
        out.append(dict(
            fname=r["fname"], true_raga=t, outcome=r["outcome"],
            predicted=r["predicted"], margin=r["margin"],
            full_rank=[k for k, _ in full].index(t) + 1, full_top=full[0][0],
            pcd_rank=[k for k, _ in pcd].index(t) + 1,  pcd_top=pcd[0][0],
            dyad_rank=[k for k, _ in dyd].index(t) + 1, dyad_top=dyd[0][0]))
    return out


def spearman(x, y):
    """Rank correlation without scipy. Returns (rho, n)."""
    n = len(x)
    def rk(v):
        s = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[s[j + 1]] == v[s[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[s[k]] = avg
            i = j + 1
        return r
    rx, ry = rk(x), rk(y)
    mx, my = np.mean(rx), np.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return (num / den if den else float("nan")), n


def main():
    t0 = time.time()
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_ROOT, f"run_{ts}_phase1b")
    os.makedirs(run_dir, exist_ok=False)

    print("=" * 78)
    print("Q-003 PHASE 1-B  --  WEIGHTED-CHANNEL DIAGNOSTIC")
    print("=" * 78)

    processed = build_processed()
    rows = loo_per_clip(processed)
    ragas = sorted(set(c["raga"] for c in processed))
    print(f"clips: {len(processed)} | ragas: {len(ragas)}")

    # -- validation gate: same canonical baseline as Phase 1-A ------------
    tot = Counter(r["outcome"] for r in rows)
    bh = Counter(r["outcome"] for r in rows if r["true_raga"] == TARGET)
    conf = Counter(r["predicted"] for r in rows
                   if r["true_raga"] == TARGET and r["outcome"] == "wrong")
    ok = (tot["correct"] == 25 and tot["wrong"] == 14 and tot["unknown"] == 31
          and bh["correct"] == 1 and bh["wrong"] == 6 and bh["unknown"] == 4
          and conf.get("Saveri") == 4 and conf.get("Thodi") == 2)
    print(f"baseline: {tot['correct']}C/{tot['wrong']}W/{tot['unknown']}U | "
          f"Bhairavi {bh['correct']}/{bh['wrong']}/{bh['unknown']} | "
          f"confusers {dict(conf)} | {'REPRODUCED' if ok else '*** MISMATCH ***'}")
    if not ok:
        raise SystemExit("STOP -- canonical baseline not reproduced.")

    # -- (1) weighted PCD similarity, Bhairavi clips -> each raga ---------
    bh_rows = [r for r in rows if r["true_raga"] == TARGET]
    wpcd = {r: float(np.mean([x["pcd_sims"][r] for x in bh_rows])) for r in ragas}
    wdyd = {r: float(np.mean([x["dyad_sims"][r] for x in bh_rows])) for r in ragas}

    # -- (2) weighted model L2 norms --------------------------------------
    l2w = weighted_model_norms(processed)
    l2d = dyad_model_norms(processed)

    # -- unweighted overlap, for the Phase 1-A contrast --------------------
    means = mean_pcds(processed)
    overlap = {r: histogram_intersection(means[TARGET], means[r])
               for r in ragas if r != TARGET}

    print("\n" + "-" * 78)
    print("MEASUREMENTS (Bhairavi clips, averaged over LOO folds)")
    print("-" * 78)
    hdr = (f"  {'raga':20s} {'wPCD sim':>10s} {'dyad sim':>10s} "
           f"{'wPCD L2':>9s} {'dyad L2':>9s} {'unw ovlp':>9s} {'in-err':>7s}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for r in sorted(ragas, key=lambda k: -wpcd[k]):
        print(f"  {r:20s} {wpcd[r]:10.6f} {wdyd[r]:10.6f} "
              f"{l2w[r]['mean_l2']:9.5f} {l2d[r]:9.5f} "
              f"{overlap.get(r, float('nan')):9.4f} "
              f"{INCOMING_ERRORS.get(r, 0):7d}")

    # -- (4) relationship with incoming errors ----------------------------
    others = [r for r in ragas]
    err = [INCOMING_ERRORS.get(r, 0) for r in others]
    print("\n" + "-" * 78)
    print("RANK CORRELATION vs INCOMING ERROR COUNT (n=7 ragas)")
    print("-" * 78)
    corrs = {}
    for name, vals in (("weighted PCD sim to Bhairavi", [wpcd[r] for r in others]),
                       ("dyad sim to Bhairavi",         [wdyd[r] for r in others]),
                       ("weighted PCD L2 norm",         [l2w[r]["mean_l2"] for r in others]),
                       ("dyad model L2 norm",           [l2d[r] for r in others]),
                       ("unweighted overlap",           [overlap.get(r, 0.0) for r in others])):
        rho, n = spearman(vals, err)
        corrs[name] = rho
        print(f"  {name:32s} rho = {rho:+.3f}  (n={n}, NOT a significance test)")

    # -- (5) Saveri ranking on each channel -------------------------------
    def rank_of(d, key, reverse=True):
        order = sorted(d, key=lambda k: d[k], reverse=reverse)
        return order.index(key) + 1, order
    print("\n" + "-" * 78)
    print("SAVERI'S RANK (1 = most similar / largest)")
    print("-" * 78)
    saveri_ranks = {}
    for name, d in (("weighted PCD sim", wpcd), ("dyad sim", wdyd),
                    ("weighted PCD L2", {k: v["mean_l2"] for k, v in l2w.items()}),
                    ("dyad model L2", l2d)):
        rk, order = rank_of(d, "Saveri")
        saveri_ranks[name] = rk
        print(f"  {name:20s} rank {rk}/{len(d)}   order: {' > '.join(order[:4])} ...")
    rk_o, order_o = rank_of(overlap, "Saveri")
    saveri_ranks["unweighted overlap"] = rk_o
    print(f"  {'unweighted overlap':20s} rank {rk_o}/{len(overlap)}   "
          f"order: {' > '.join(order_o[:4])} ...")

    # -- (3) channel separation: which channel misleads? -------------------
    cr = channel_ranks(rows)
    bh_cr = [c for c in cr if c["true_raga"] == TARGET]
    print("\n" + "-" * 78)
    print("CHANNEL SEPARATION -- Bhairavi clips: rank of the TRUE raga")
    print("-" * 78)
    print(f"  {'clip':44s} {'outcome':9s} {'full':>5s} {'PCD':>5s} {'dyad':>5s}  pcd_top / dyad_top")
    for c in sorted(bh_cr, key=lambda x: (x["outcome"], x["fname"])):
        print(f"  {c['fname'][:44]:44s} {c['outcome']:9s} "
              f"{c['full_rank']:5d} {c['pcd_rank']:5d} {c['dyad_rank']:5d}  "
              f"{c['pcd_top']} / {c['dyad_top']}")
    wrongs = [c for c in bh_cr if c["outcome"] == "wrong"]
    pcd_mis = sum(1 for c in wrongs if c["pcd_top"] != TARGET)
    dyd_mis = sum(1 for c in wrongs if c["dyad_top"] != TARGET)
    both = sum(1 for c in wrongs if c["pcd_top"] != TARGET and c["dyad_top"] != TARGET)
    print(f"\n  of {len(wrongs)} errors: PCD channel favours a wrong raga in {pcd_mis}, "
          f"dyad in {dyd_mis}, BOTH in {both}")

    # -- artifacts --------------------------------------------------------
    with open(os.path.join(run_dir, "phase1b_measurements.json"), "w") as fh:
        json.dump(dict(
            weighted_pcd_sim_to_bhairavi=wpcd, dyad_sim_to_bhairavi=wdyd,
            weighted_pcd_model_l2=l2w, dyad_model_l2=l2d,
            unweighted_overlap_to_bhairavi=overlap,
            incoming_errors=INCOMING_ERRORS,
            rank_correlations_vs_incoming_errors=corrs,
            saveri_ranks=saveri_ranks,
            channel_misdirection=dict(n_errors=len(wrongs), pcd_favours_wrong=pcd_mis,
                                      dyad_favours_wrong=dyd_mis, both=both),
            note="Descriptive measurements. No threshold, no fix, no correction. "
                 "Rank correlations at n=7 are directional only, NOT significance "
                 "tests."), fh, indent=2)

    with open(os.path.join(run_dir, "channel_ranks.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["clip", "true_raga", "outcome", "predicted", "margin",
                    "full_rank_of_true", "pcd_rank_of_true", "dyad_rank_of_true",
                    "pcd_top", "dyad_top"])
        for c in cr:
            w.writerow([c["fname"], c["true_raga"], c["outcome"], c["predicted"],
                        f"{c['margin']:.8f}", c["full_rank"], c["pcd_rank"],
                        c["dyad_rank"], c["pcd_top"], c["dyad_top"]])

    with open(os.path.join(run_dir, "run_metadata.json"), "w") as fh:
        json.dump(dict(gate="Q-003", phase="1-B", timestamp=ts, run_dir=run_dir,
                       baseline_reproduced=bool(ok),
                       constants=dict(pcd_weight=PCD_WEIGHT, dyad_weight=DYAD_WEIGHT,
                                      source="recognize_raga_v12.py, imported"),
                       reused="sandbox_q003_bhairavi_pcd_diagnostic.py (Phase 1-A) "
                              "+ confusion_matrix_audit.py",
                       incoming_errors_source="recomputed 2026-08-21, C-6 correction",
                       software=_versions(), git_commit=_git_commit(),
                       elapsed_sec=round(time.time() - t0, 2),
                       read_only=True, modifies_production=False), fh, indent=2)

    print(f"\nresults: {run_dir}")
    print("=" * 78)


if __name__ == "__main__":
    main()
