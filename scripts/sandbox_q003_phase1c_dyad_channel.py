"""
Q-003 PHASE 1-C  --  DYAD-CHANNEL DIAGNOSTIC (Bhairavi)
========================================================================

Authorised 2026-08-25 against the verified Phase 1-C precheck
(docs/research/Q-003/PHASE_1C_PRECHECK.md).

QUESTION
    Why does the dyad channel fail weak ragas?

HYPOTHESES -- kept strictly separate, none selected by this script:
    H_DATA             insufficient or redundant transition data
    H_REP              representation cannot express discrimination
    H_SHARED-measured  observed dyads overlap because of extraction
    H_SHARED-intrinsic true musical dyads genuinely overlap
    H_SCORE            scoring interaction degrades useful dyad signal

MEASUREMENTS, in the authorised order:
    M1  per-channel dyad rank and margin
    M3  ascending vs descending dyad analysis
    M2  Bhairavi vs Thodi matched control (n = 11 both)
    M5  raw vs L2-normalised dyad sharing
    M4  stability curve -- DESCRIPTIVE EVIDENCE ONLY, no plateau threshold

CONSTRAINTS OBSERVED
    - No production code modified. Scoring arithmetic is imported or mirrored
      line-for-line from recognize_raga_v12.py:210-216 and
      confusion_matrix_audit.py:129-148.
    - No dataset or feature cache modified. Read-only.
    - No subset search of any kind.
    - No weight, threshold, scoring or methodology change.
    - The three stale 2026-01-05 *_dyad_stats.npz artifacts are IGNORED;
      all models are built in memory from pcd_results/features_v12/.
    - M4 introduces no numeric plateau criterion and does not determine any
      diagnosis.

KNOWN LIMITATION, pre-registered
    6 of Bhairavi's 11 clips (Bhairavi_clean_1..6) have no recoverable
    composition, performer or source identity. Composition and performer
    diversity therefore CANNOT be controlled. Every conclusion touching data
    sufficiency or redundancy is limited on that ground. Scope was not
    expanded to recover provenance.
"""

import os
import io
import csv
import json
import time
import contextlib
from collections import defaultdict, Counter

import numpy as np

# --- canonical constants, imported (never re-declared) --------------------
from recognize_raga_v12 import (
    N_BINS, EPS, PCD_WEIGHT, DYAD_WEIGHT, MARGIN_STRICT, MIN_MARGIN_FINAL,
)

with contextlib.redirect_stdout(io.StringIO()):
    from confusion_matrix_audit import (
        load_clips, compute_features, idf_var_weights, MIN_CLIPS, ALPHA,
    )

from sandbox_q003_bhairavi_pcd_diagnostic import (
    BASE_DIR, RESULTS_ROOT, TARGET, _versions, _git_commit,
)

MIN_STABLE_FRAMES = 5          # aggregate_all_v12.py:16 / confusion_matrix_audit
MATCHED_CONTROL   = "Thodi"    # n = 11, matches Bhairavi exactly (precheck S5)
STABILITY_DRAWS   = 100
STABILITY_SEED    = 0

# Canonical baseline -- the gate this run must pass before interpretation.
CANON = dict(total=70, correct=25, wrong=14, unknown=31,
             bhairavi=dict(clips=11, c=1, w=6, u=4),
             bhairavi_confusers={"Saveri": 4, "Thodi": 2})


# =========================================================================
# Raw (pre-smoothing) dyads -- replicates aggregate_all_v12.py:53-105 and
# confusion_matrix_audit.py:58-92 exactly, but returns the counts BEFORE
# `+= ALPHA`. Verified byte-equivalent downstream in verify_raw_replication().
# =========================================================================
def raw_dyads(cents):
    bin_edges  = np.linspace(0, 1200, N_BINS + 1)
    pitch_bins = np.digitize(cents, bin_edges) - 1
    pitch_bins = pitch_bins[(pitch_bins >= 0) & (pitch_bins < N_BINS)]

    stable_bins = []
    current, count = pitch_bins[0], 1
    for b in pitch_bins[1:]:
        if b == current:
            count += 1
        else:
            if count >= MIN_STABLE_FRAMES:
                stable_bins.append(current)
            current, count = b, 1
    if count >= MIN_STABLE_FRAMES:
        stable_bins.append(current)

    raw_up   = np.zeros((N_BINS, N_BINS))
    raw_down = np.zeros((N_BINS, N_BINS))
    for i in range(len(stable_bins) - 1):
        frm, to = stable_bins[i], stable_bins[i + 1]
        if to > frm:
            raw_up[frm, to]   += 1
        elif to < frm:
            raw_down[frm, to] += 1
    return raw_up, raw_down, stable_bins


def smooth_like_production(raw):
    m = raw + ALPHA
    return (m / (np.sum(m) + EPS)).flatten()


def build_processed():
    """Mirrors confusion_matrix_audit.py's main block, plus raw counts."""
    with contextlib.redirect_stdout(io.StringIO()):
        all_clips = load_clips()
    counts   = Counter(c["raga"] for c in all_clips)
    eligible = {r for r, n in counts.items() if n >= MIN_CLIPS}

    processed = []
    for c in (x for x in all_clips if x["raga"] in eligible):
        pcd, up, down = compute_features(c["cents"])
        raw_up, raw_down, stable = raw_dyads(c["cents"])
        processed.append({
            "fname": c["fname"], "raga": c["raga"],
            "pcd": pcd, "up": up, "down": down,
            "raw_up": raw_up, "raw_down": raw_down,
            "n_stable": len(stable),
            "n_transitions": int(raw_up.sum() + raw_down.sum()),
            "support_up": int((raw_up > 0).sum()),
            "support_down": int((raw_down > 0).sum()),
        })
    return processed


def verify_raw_replication(processed):
    """Every raw count matrix must reproduce the production up/down vector
    after smoothing + normalisation. Guards against silent divergence."""
    bad = []
    for c in processed:
        if not (np.allclose(smooth_like_production(c["raw_up"]),   c["up"]) and
                np.allclose(smooth_like_production(c["raw_down"]), c["down"])):
            bad.append(c["fname"])
    return bad


# =========================================================================
# LOO with full per-channel capture. Arithmetic mirrors
# confusion_matrix_audit.py:129-148 exactly; only the capture is added.
# =========================================================================
def _l2(v):
    return float(np.sqrt(np.dot(v, v)))


def _unit(v):
    n = np.sqrt(np.dot(v, v))
    return v / (n + EPS)


def loo_full(processed):
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
        up_sims, down_sims, cos_dyad = {}, {}, {}

        hu, hd = _unit(held["up"]), _unit(held["down"])

        for raga, m in models.items():
            model_w = m["pcd"] * weights
            model_w = model_w / (np.sum(model_w) + EPS)

            pcd_sim  = float(np.dot(pcd_w, model_w))
            up_sim   = float(np.dot(held["up"],   m["up"]))
            down_sim = float(np.dot(held["down"], m["down"]))
            dyad_sim = 0.5 * (up_sim + down_sim)          # production line 214

            # L2-normalised (cosine) variant -- M5. Measurement only; the
            # production score below is untouched.
            cos_dyad[raga] = float(0.5 * (np.dot(hu, _unit(m["up"])) +
                                          np.dot(hd, _unit(m["down"]))))

            pcd_sims[raga], dyad_sims[raga] = pcd_sim, dyad_sim
            up_sims[raga],  down_sims[raga] = up_sim, down_sim
            scores[raga] = PCD_WEIGHT * pcd_sim + DYAD_WEIGHT * dyad_sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        margin = ranked[0][1] - ranked[1][1] if len(ranked) >= 2 else 0.0

        if   margin >= MARGIN_STRICT:    tier, pred = "HIGH", ranked[0][0]
        elif margin >= MIN_MARGIN_FINAL: tier, pred = "MOD",  ranked[0][0]
        else:                            tier, pred = "UNK",  "UNKNOWN"

        true_raga = held["raga"]
        outcome = ("correct" if pred == true_raga
                   else "unknown" if tier == "UNK" else "wrong")

        def rank_of(d, r):
            return sorted(d, key=lambda k: d[k], reverse=True).index(r) + 1

        def top_of(d):
            return max(d, key=lambda k: d[k])

        def gap_to_top(d, r):
            """Deficit of the true raga behind the channel leader.
            0.0 exactly when the true raga leads that channel."""
            return float(max(d.values()) - d[r])

        rows.append(dict(
            fname=held["fname"], true_raga=true_raga, predicted=pred,
            tier=tier, outcome=outcome,
            margin=float(margin),
            full_rank=rank_of(scores, true_raga),
            pcd_rank=rank_of(pcd_sims, true_raga),
            dyad_rank=rank_of(dyad_sims, true_raga),
            up_rank=rank_of(up_sims, true_raga),
            down_rank=rank_of(down_sims, true_raga),
            cos_dyad_rank=rank_of(cos_dyad, true_raga),
            pcd_top=top_of(pcd_sims), dyad_top=top_of(dyad_sims),
            up_top=top_of(up_sims),   down_top=top_of(down_sims),
            cos_dyad_top=top_of(cos_dyad),
            dyad_gap=gap_to_top(dyad_sims, true_raga),
            dyad_top_val=float(max(dyad_sims.values())),
            dyad_true_val=float(dyad_sims[true_raga]),
            cos_gap=gap_to_top(cos_dyad, true_raga),
            pcd_gap=gap_to_top(pcd_sims, true_raga),
            scores=scores, pcd_sims=pcd_sims, dyad_sims=dyad_sims,
            up_sims=up_sims, down_sims=down_sims, cos_dyad=cos_dyad,
        ))
    return rows


def tally(rows):
    stats = defaultdict(lambda: {"t": 0, "c": 0, "w": 0, "u": 0})
    tot = {"c": 0, "w": 0, "u": 0}
    for r in rows:
        s = stats[r["true_raga"]]
        s["t"] += 1
        k = {"correct": "c", "wrong": "w", "unknown": "u"}[r["outcome"]]
        s[k] += 1
        tot[k] += 1
    return stats, tot


def gate(rows):
    """Canonical baseline must reproduce before any interpretation."""
    stats, tot = tally(rows)
    checks = []
    checks.append(("total clips", len(rows), CANON["total"]))
    checks.append(("correct", tot["c"], CANON["correct"]))
    checks.append(("wrong",   tot["w"], CANON["wrong"]))
    checks.append(("unknown", tot["u"], CANON["unknown"]))
    b = stats[TARGET]
    checks.append(("Bhairavi clips", b["t"], CANON["bhairavi"]["clips"]))
    checks.append(("Bhairavi correct", b["c"], CANON["bhairavi"]["c"]))
    checks.append(("Bhairavi wrong",   b["w"], CANON["bhairavi"]["w"]))
    checks.append(("Bhairavi unknown", b["u"], CANON["bhairavi"]["u"]))
    conf = Counter(r["predicted"] for r in rows
                   if r["true_raga"] == TARGET and r["outcome"] == "wrong")
    for k, v in CANON["bhairavi_confusers"].items():
        checks.append(("Bhairavi -> %s" % k, conf.get(k, 0), v))
    return checks, all(a == b for _, a, b in checks)


# =========================================================================
# M4 -- stability curve. Descriptive only. No plateau criterion.
# =========================================================================
def stability_curve(processed):
    rng = np.random.default_rng(STABILITY_SEED)
    by_raga = defaultdict(list)
    for c in processed:
        by_raga[c["raga"]].append(c)

    out = {}
    for raga, clips in sorted(by_raga.items()):
        n = len(clips)
        ups   = np.array([c["up"]   for c in clips])
        downs = np.array([c["down"] for c in clips])
        curve = {}
        for k in range(2, n + 1):
            mods = []
            for _ in range(STABILITY_DRAWS):
                idx = rng.choice(n, size=k, replace=False)
                mods.append(np.concatenate([ups[idx].mean(axis=0),
                                            downs[idx].mean(axis=0)]))
            mods = np.array(mods)
            cent = _unit(mods.mean(axis=0))
            # mean cosine distance of each draw's model to the centroid
            d = [1.0 - float(np.dot(_unit(m), cent)) for m in mods]
            curve[k] = float(np.mean(d))
        out[raga] = curve
    return out


# =========================================================================
def main():
    t0 = time.time()
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_ROOT, "run_%s_phase1c" % ts)
    os.makedirs(run_dir, exist_ok=True)

    print("=" * 74)
    print("Q-003 PHASE 1-C  --  DYAD-CHANNEL DIAGNOSTIC")
    print("=" * 74)

    processed = build_processed()
    print("\nclips processed: %d" % len(processed))

    bad = verify_raw_replication(processed)
    print("raw-count replication check: %s" %
          ("PASS (all %d clips)" % len(processed) if not bad
           else "FAIL on %d clips" % len(bad)))
    if bad:
        raise SystemExit("Raw dyad replication diverged; aborting.")

    rows = loo_full(processed)
    checks, ok = gate(rows)
    print("\n--- CANONICAL BASELINE GATE ---")
    for name, got, want in checks:
        print("  %-22s got=%-5s want=%-5s %s" %
              (name, got, want, "OK" if got == want else "MISMATCH"))
    print("  RESULT: %s" % ("REPRODUCED" if ok else "NOT REPRODUCED"))
    if not ok:
        raise SystemExit("Baseline not reproduced; refusing to interpret.")

    by_raga = defaultdict(list)
    for r in rows:
        by_raga[r["true_raga"]].append(r)
    ragas = sorted(by_raga)

    # ---------------- M1: per-channel dyad rank and margin ---------------
    print("\n" + "=" * 74)
    print("M1 -- PER-CHANNEL DYAD RANK AND MARGIN")
    print("=" * 74)
    print("\n  %-18s %5s %8s %8s %10s %10s" %
          ("raga", "clips", "dyad#1", "medRank", "medGap", "medGap/top"))
    m1 = {}
    for r in ragas:
        rs = by_raga[r]
        ranks = [x["dyad_rank"] for x in rs]
        gaps  = [x["dyad_gap"] for x in rs]
        rel   = [x["dyad_gap"] / (x["dyad_top_val"] + EPS) for x in rs]
        m1[r] = dict(clips=len(rs), first=sum(1 for v in ranks if v == 1),
                     med_rank=float(np.median(ranks)),
                     med_gap=float(np.median(gaps)),
                     med_rel=float(np.median(rel)))
        print("  %-18s %5d %8d %8.1f %10.6f %10.4f" %
              (r, m1[r]["clips"], m1[r]["first"], m1[r]["med_rank"],
               m1[r]["med_gap"], m1[r]["med_rel"]))

    print("\n  Bhairavi per-clip dyad detail:")
    print("  %-42s %7s %6s %6s %10s %10s" %
          ("clip", "outcome", "pcd#", "dyad#", "dyadGap", "dyadTop"))
    for x in by_raga[TARGET]:
        print("  %-42s %7s %6d %6d %10.6f %10s" %
              (x["fname"][:42], x["outcome"], x["pcd_rank"], x["dyad_rank"],
               x["dyad_gap"], x["dyad_top"]))

    # error decomposition: which channel drove each wrong/unknown outcome
    print("\n  Error decomposition (Bhairavi non-correct clips):")
    print("  %-42s %12s %12s %10s" %
          ("clip", "0.8*dPCD", "0.2*dDYAD", "driver"))
    decomp = []
    for x in by_raga[TARGET]:
        if x["outcome"] == "correct":
            continue
        # rival = highest-scoring raga other than the true one
        rival = max((k for k in x["scores"] if k != TARGET),
                    key=lambda k: x["scores"][k])
        dp = PCD_WEIGHT  * (x["pcd_sims"][rival]  - x["pcd_sims"][TARGET])
        dd = DYAD_WEIGHT * (x["dyad_sims"][rival] - x["dyad_sims"][TARGET])
        driver = "dyad" if dd > dp else "pcd"
        if dp > 0 and dd > 0:
            driver += " (both +)"
        decomp.append(dict(clip=x["fname"], rival=rival, d_pcd=float(dp),
                           d_dyad=float(dd), driver=driver))
        print("  %-42s %12.6f %12.6f %10s" %
              (x["fname"][:42], dp, dd, driver))

    # ---------------- M3: ascending vs descending ------------------------
    print("\n" + "=" * 74)
    print("M3 -- ASCENDING VS DESCENDING")
    print("=" * 74)
    print("\n  %-18s %5s %7s %7s %7s" %
          ("raga", "clips", "up#1", "down#1", "dyad#1"))
    m3 = {}
    for r in ragas:
        rs = by_raga[r]
        u = sum(1 for x in rs if x["up_rank"] == 1)
        d = sum(1 for x in rs if x["down_rank"] == 1)
        y = sum(1 for x in rs if x["dyad_rank"] == 1)
        m3[r] = dict(clips=len(rs), up_first=u, down_first=d, dyad_first=y,
                     med_up=float(np.median([x["up_rank"] for x in rs])),
                     med_down=float(np.median([x["down_rank"] for x in rs])))
        print("  %-18s %5d %7d %7d %7d" % (r, len(rs), u, d, y))

    # model-level directional asymmetry: how different are mean_up, mean_down
    print("\n  Model directional asymmetry (1 - cosine(mean_up, mean_down)):")
    asym = {}
    for r in ragas:
        cl = [c for c in processed if c["raga"] == r]
        mu = np.mean([c["up"] for c in cl], axis=0)
        md = np.mean([c["down"] for c in cl], axis=0)
        asym[r] = 1.0 - float(np.dot(_unit(mu), _unit(md)))
        print("    %-18s %.6f" % (r, asym[r]))

    # ---------------- M2: Bhairavi vs Thodi matched control --------------
    print("\n" + "=" * 74)
    print("M2 -- MATCHED CONTROL: %s vs %s" % (TARGET, MATCHED_CONTROL))
    print("=" * 74)
    m2 = {}
    for r in (TARGET, MATCHED_CONTROL):
        rs = by_raga[r]
        cl = [c for c in processed if c["raga"] == r]
        mu = np.mean([c["up"] for c in cl], axis=0)
        md = np.mean([c["down"] for c in cl], axis=0)
        m2[r] = dict(
            clips=len(rs),
            correct=sum(1 for x in rs if x["outcome"] == "correct"),
            wrong=sum(1 for x in rs if x["outcome"] == "wrong"),
            unknown=sum(1 for x in rs if x["outcome"] == "unknown"),
            dyad_first=sum(1 for x in rs if x["dyad_rank"] == 1),
            up_first=sum(1 for x in rs if x["up_rank"] == 1),
            down_first=sum(1 for x in rs if x["down_rank"] == 1),
            pcd_first=sum(1 for x in rs if x["pcd_rank"] == 1),
            cos_first=sum(1 for x in rs if x["cos_dyad_rank"] == 1),
            med_transitions=float(np.median([c["n_transitions"] for c in cl])),
            med_stable=float(np.median([c["n_stable"] for c in cl])),
            med_support_up=float(np.median([c["support_up"] for c in cl])),
            med_support_down=float(np.median([c["support_down"] for c in cl])),
            model_l2_up=_l2(mu), model_l2_down=_l2(md),
            asymmetry=asym[r],
        )
    keys = ["clips", "correct", "wrong", "unknown", "pcd_first", "dyad_first",
            "up_first", "down_first", "cos_first", "med_transitions",
            "med_stable", "med_support_up", "med_support_down",
            "model_l2_up", "model_l2_down", "asymmetry"]
    print("\n  %-20s %14s %14s" % ("metric", TARGET, MATCHED_CONTROL))
    for k in keys:
        print("  %-20s %14.4f %14.4f" %
              (k, m2[TARGET][k], m2[MATCHED_CONTROL][k]))

    # ---------------- M5: raw vs L2-normalised sharing -------------------
    print("\n" + "=" * 74)
    print("M5 -- RAW VS L2-NORMALISED DYAD SHARING")
    print("=" * 74)
    print("\n  %-18s %5s %10s %12s %12s" %
          ("raga", "clips", "dyad#1", "cosDyad#1", "delta"))
    m5 = {}
    for r in ragas:
        rs = by_raga[r]
        a = sum(1 for x in rs if x["dyad_rank"] == 1)
        b = sum(1 for x in rs if x["cos_dyad_rank"] == 1)
        m5[r] = dict(clips=len(rs), raw_first=a, cos_first=b, delta=b - a)
        print("  %-18s %5d %10d %12d %+12d" % (r, len(rs), a, b, b - a))

    print("\n  Dyad model concentration (L2 of L1-normalised model):")
    conc = {}
    for r in ragas:
        cl = [c for c in processed if c["raga"] == r]
        mu = np.mean([c["up"] for c in cl], axis=0)
        md = np.mean([c["down"] for c in cl], axis=0)
        conc[r] = dict(up=_l2(mu), down=_l2(md))
        print("    %-18s up=%.5f down=%.5f" % (r, conc[r]["up"], conc[r]["down"]))

    print("\n  Bhairavi dyad overlap (histogram intersection, L1 models):")
    bcl = [c for c in processed if c["raga"] == TARGET]
    b_up = np.mean([c["up"] for c in bcl], axis=0)
    b_dn = np.mean([c["down"] for c in bcl], axis=0)
    share = {}
    for r in ragas:
        if r == TARGET:
            continue
        cl = [c for c in processed if c["raga"] == r]
        mu = np.mean([c["up"] for c in cl], axis=0)
        md = np.mean([c["down"] for c in cl], axis=0)
        share[r] = dict(up=float(np.sum(np.minimum(b_up, mu))),
                        down=float(np.sum(np.minimum(b_dn, md))))
        print("    %-18s up=%.4f down=%.4f" % (r, share[r]["up"], share[r]["down"]))

    # ---------------- M4: stability curve (descriptive) ------------------
    print("\n" + "=" * 74)
    print("M4 -- STABILITY CURVE  (DESCRIPTIVE EVIDENCE ONLY)")
    print("=" * 74)
    print("  Mean cosine distance of a k-clip model to the k-clip centroid.")
    print("  %d draws, seed %d. Lower = more stable." %
          (STABILITY_DRAWS, STABILITY_SEED))
    print("  NO plateau criterion is applied. This does not determine the")
    print("  diagnosis and is not evidence for or against H_DATA on its own.")
    curves = stability_curve(processed)
    ks = list(range(2, 15))
    print("\n  %-18s %s" % ("raga", " ".join("k=%-2d" % k for k in ks)))
    for r in ragas:
        cells = []
        for k in ks:
            v = curves[r].get(k)
            cells.append("%.4f" % v if v is not None else "  -  ")
        print("  %-18s %s" % (r, " ".join(cells)))

    # ---------------- artifacts ------------------------------------------
    with open(os.path.join(run_dir, "per_clip.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["clip", "true_raga", "outcome", "predicted", "margin",
                    "full_rank", "pcd_rank", "dyad_rank", "up_rank",
                    "down_rank", "cos_dyad_rank", "pcd_top", "dyad_top",
                    "up_top", "down_top", "cos_dyad_top",
                    "dyad_gap", "dyad_true_val", "dyad_top_val", "pcd_gap"])
        for x in rows:
            w.writerow([x["fname"], x["true_raga"], x["outcome"],
                        x["predicted"], "%.8f" % x["margin"],
                        x["full_rank"], x["pcd_rank"], x["dyad_rank"],
                        x["up_rank"], x["down_rank"], x["cos_dyad_rank"],
                        x["pcd_top"], x["dyad_top"], x["up_top"],
                        x["down_top"], x["cos_dyad_top"],
                        "%.8f" % x["dyad_gap"], "%.8f" % x["dyad_true_val"],
                        "%.8f" % x["dyad_top_val"], "%.8f" % x["pcd_gap"]])

    payload = dict(m1=m1, m3=m3, m2=m2, m5=m5,
                   model_asymmetry=asym, concentration=conc,
                   bhairavi_dyad_overlap=share,
                   error_decomposition=decomp,
                   stability_curves={r: {str(k): v for k, v in c.items()}
                                     for r, c in curves.items()})
    with open(os.path.join(run_dir, "phase1c_measurements.json"), "w",
              encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)

    meta = dict(gate="Q-003", phase="1-C", timestamp=ts, run_dir=run_dir,
                baseline_reproduced=bool(ok),
                raw_replication_pass=not bad,
                measurements_executed=["M1", "M3", "M2", "M5", "M4"],
                execution_order="M1 -> M3 -> M2 -> M5 -> M4",
                constants=dict(pcd_weight=PCD_WEIGHT, dyad_weight=DYAD_WEIGHT,
                               alpha=ALPHA, n_bins=N_BINS,
                               min_stable_frames=MIN_STABLE_FRAMES,
                               margin_strict=MARGIN_STRICT,
                               min_margin_final=MIN_MARGIN_FINAL,
                               source="recognize_raga_v12.py, imported"),
                stability=dict(draws=STABILITY_DRAWS, seed=STABILITY_SEED,
                               role="descriptive only, no plateau threshold"),
                stale_artifacts_ignored=[
                    "pcd_results/aggregation/stats/Bhairavi_dyad_stats.npz",
                    "pcd_results/aggregation/stats/Kalyani_dyad_stats.npz",
                    "pcd_results/aggregation/stats/Shankarabharanam_dyad_stats.npz"],
                limitation=("6 of 11 Bhairavi clips (Bhairavi_clean_1..6) have no "
                            "recoverable composition/performer identity; "
                            "composition and performer diversity are NOT controlled"),
                software=_versions(), git_commit=_git_commit(),
                elapsed_sec=round(time.time() - t0, 2),
                read_only=True, modified_production_code=False,
                modified_datasets=False, subset_search=False)
    with open(os.path.join(run_dir, "run_metadata.json"), "w",
              encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)

    print("\n" + "=" * 74)
    print("artifacts: %s" % run_dir)
    print("elapsed: %.2fs" % (time.time() - t0))
    print("=" * 74)


if __name__ == "__main__":
    main()
