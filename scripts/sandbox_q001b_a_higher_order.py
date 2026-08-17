#!/usr/bin/env python3
"""
Q-001B-A  --  HIGHER-ORDER (TRIGRAM) STRUCTURE IN STABLE-NOTE SEQUENCES

ONE question: do Abhogi stable-note sequences contain trigram structure beyond
what their own bigram statistics already explain?

This is NOT a discrimination experiment. No classifier, no folds, no ML.
Q-001B-B (composition-held-out discrimination) is a separate, blocked gate --
nothing here touches it.

Method
------
Statistic per clip:
    H1 = H(S_t | S_{t-1})              plug-in, from bigram counts
    H2 = H(S_t | S_{t-1}, S_{t-2})     plug-in, from trigram counts
    dH = H1 - H2                       the higher-order statistic

Null: doublet-preserving shuffle (Altschul & Erickson 1985; Kandel et al. 1996)
via uniform Eulerian-trail reconstruction of the sequence's own bigram
multigraph. Every surrogate has, by construction and by mechanical check:
    - identical bigram counts (hence identical H1)
    - identical sequence length
    - identical first and last symbol
Only the ordering of trigrams varies. An ordinary shuffle is NOT used and would
invalidate the null (it destroys the bigram structure being controlled for).

Because H1 is invariant across surrogates, dH_obs - dH_surr == H2_surr - H2_obs:
the plug-in entropy bias is matched between observed and null by construction.

Inputs: production feature cache pcd_results/features_v12 (raw pyin f0), fed
through the EXISTING Q-001A stable_bins_from_f0() -> swara-index sequence.
No new extraction, no production edits, no dataset changes.

Usage
-----
    python sandbox_q001b_a_higher_order.py --audit-only
    python sandbox_q001b_a_higher_order.py                 # pre-registered params
    python sandbox_q001b_a_higher_order.py --surrogates N --seed S

The surrogate count and seed are pre-registered constants (see PRE-REGISTRATION
below), not defaults chosen by the script. The CLI flags exist only to make a
deviation from the pre-registration explicit and visible in run_metadata.json.
"""

import os
import re
import csv
import json
import glob
import time
import argparse
import subprocess
from collections import Counter, defaultdict

import numpy as np

# --- reuse, do not reimplement (ADR-015 / directive Step 1) ---------------
from feature_constants import FEATURE_VERSION
from recognize_raga_v12 import N_BINS, MIN_STABLE_FRAMES, SR, MAX_DURATION_SEC
from sandbox_q001a_representation_sufficiency import stable_bins_from_f0

BASE_DIR      = r"D:\Swaragam"
FEATURE_DIR   = os.path.join(BASE_DIR, "pcd_results", "features_v12")
METADATA_DIR  = os.path.join(BASE_DIR, "datasets", "staging_metadata")
RESULTS_ROOT  = os.path.join(BASE_DIR, "Q001B-A results")

TARGET_RAGA    = "Abhogi"
BINS_PER_SWARA = N_BINS // 12
SEQ_REPR       = "swara_index_12"   # stable bin // (N_BINS/12); Q-001B plan's representation

# =========================================================================
# PRE-REGISTRATION  --  Q-001B-A resampling parameters
# =========================================================================
# Q-001B_Research_Plan.md fixes the hypothesis, null model, statistic and
# promotion criteria but does NOT fix a surrogate count or seed. That gap was
# reported and the two values below were pre-registered by the project owner on
# 2026-08-17, BEFORE any surrogate was drawn against Abhogi. They are constants
# here, not argparse defaults, so the checked-in script is the record.
#
# 50,000 matches the only existing resampling constant in the repository
# (_perm_p(iters=50000, seed=0) in sandbox_q001a_representation_sufficiency.py).
# Nothing else in the pre-registration is altered by this addition.
PREREGISTERED_SURROGATES = 50000
PREREGISTERED_SEED       = 0
PREREGISTRATION_DATE     = "2026-08-17"

# Wording corrected 2026-08-17 after the generator audit. The H2 plug-in bias
# does NOT exactly cancel -- only H1 is exactly invariant. Kept as a single
# constant so the emitted artifact and this script cannot drift apart.
OBSERVED_BIAS_NOTE = (
    "plug-in (MLE) conditional entropies in bits, downward-biased by "
    "construction. Bigram preservation makes H1 invariant across the null, so "
    "dH_obs - dH_surr == H2_surr - H2_obs exactly. The H2 plug-in bias does NOT "
    "exactly cancel: trigram support differs between observed and surrogate and "
    "is itself a function of the structure under test, whereas length, alphabet, "
    "unigram/bigram counts and bigram context counts are held fixed. A "
    "more-structured sequence has fewer distinct trigrams and a smaller downward "
    "bias, so in expectation the residual inflates null dH relative to observed. "
    "The residual is conservative -- it can mask a small genuine effect, but "
    "cannot manufacture a positive result. Magnitude not quantified: "
    "per-surrogate trigram support (m3) is not recorded.")

# --- p-value definition (frozen) -----------------------------------------
# Per clip i, with observed statistic dH_i and N surrogate statistics
# dH_i^(1..N) drawn from that clip's OWN doublet-preserving null:
#
#     p_i = ( 1 + #{ j : dH_i^(j) >= dH_i } ) / ( 1 + N )
#
# One-sided, upper tail: the hypothesis is that observed higher-order structure
# EXCEEDS the null (higher dH = lower H2 = more predictable from two symbols
# than one). Upper tail is therefore the directional test, fixed in advance.
# The +1/+1 is the standard finite-sample correction for MONTE CARLO p-values.
# The naive estimator b/N is unbiased for the true tail probability but can equal
# 0, which is not a valid p-value and leaves the test anti-conservative. Under H0
# the exceedance count b is Binomial(N, p_true); integrating over that uncertainty
# yields (b+1)/(N+1), which satisfies P(p_hat <= alpha) <= alpha for every finite
# N (Davison & Hinkley 1997 sec. 4.2; Phipson & Smyth 2010, "Permutation P-values
# should never be zero"). It is a VALIDITY correction -- NOT a claim that the
# observed statistic is one of the generated surrogates. (The "observed value is a
# member of its own reference set" argument belongs to exhaustive permutation over
# a group; here we Monte Carlo sample the Eulerian-trail class, so the
# finite-sample framing above is the correct one.)
# Floor at N=50000 is p = 2.0e-5.
# No parametric/normal assumption is used anywhere in this calculation.
#
# --- multiplicity (frozen) -----------------------------------------------
# Seven clips are each tested at alpha = 0.05 (pre-registered: Q-001B plan
# criterion 2; protocol section 7 "a pre-registered p-value bar"). Per-clip p is
# additionally reported Holm-adjusted across the K = 7 tests.
# Holm (1979) is a step-down Bonferroni procedure: its FWER control holds under
# ARBITRARY DEPENDENCE among the test statistics and requires no independence
# assumption. The 6/1 composition structure therefore affects INTERPRETATION and
# the descriptive aggregate, but does NOT invalidate Holm here. This is the key
# asymmetry with p_agg below, whose precision DOES assume a 7-unit independence
# that does not hold -- which is why p_agg is descriptive-only and Holm is not.
#
# --- aggregation across clips (frozen) -----------------------------------
# Surrogate-index pairing. For each surrogate index j in 1..N take the j-th
# surrogate of every clip and average across the K clips:
#
#     M^(j) = (1/K) * sum_i dH_i^(j)          M_obs = (1/K) * sum_i dH_i
#     p_agg = ( 1 + #{ j : M^(j) >= M_obs } ) / ( 1 + N )
#
# Because each clip's surrogates are i.i.d. draws from that clip's own null and
# are drawn from independent RNG streams, the column M^(j) is an i.i.d. draw
# from the null distribution of the mean statistic. The index pairing is
# arbitrary but valid; it is used rather than pooling so that the aggregate null
# has the same K-clip averaging structure as the observed value.
# This aggregate treats clips as independent units. They are NOT fully
# independent (6 of 7 share one composition) -- that is a dataset limitation
# reported with the result, NOT a correction applied to the statistic.
#
# --- effect magnitude (frozen) -------------------------------------------
#     effect_bits = dH_obs - mean(null)        raw, in bits
#     effect_z    = (dH_obs - mean(null)) / sd(null)     standardized, ddof=1
#     percentile  = 100 * #{ j : dH^(j) < dH_obs } / N
# effect_z is reported as a magnitude only. It is NOT converted to a p-value and
# no normality is assumed; the p-values above are purely empirical.
#
# Note on estimator bias (wording corrected 2026-08-17 after the generator
# audit; see OBSERVED_BIAS_NOTE above, which this must stay consistent with):
# H1 and H2 are plug-in (MLE) estimates and are biased downward, H2 more so
# than H1, which inflates dH.
#
# EXACT part: every surrogate has identical length AND identical bigram counts
# by construction, so H1 is invariant across the null and
# dH_obs - dH_surr == H2_surr - H2_obs exactly. No part of the comparison
# rests on H1.
#
# NOT exact: the H2 plug-in bias does NOT exactly cancel. It is matched on
# every nuisance dimension the null holds fixed (length, alphabet, unigram and
# bigram counts, bigram context counts), but the residual depends on the
# effective trigram support, which differs between observed and surrogate and
# is itself a function of the structure under test. A more-structured sequence
# has fewer distinct trigrams and a smaller downward bias, so in expectation
# the residual depresses H2_surr more than H2_obs and inflates null dH relative
# to observed. The residual is therefore CONSERVATIVE: it can mask a small
# genuine effect, but cannot manufacture a positive result. Magnitude not
# quantified -- per-surrogate trigram support (m3) is not recorded.
# =========================================================================

# Pre-registered expected composition structure (directive Step 2).
EXPECTED_COMPOSITIONS = {"Evvari Bodhana": 6, "Nannu Brova Neeku": 1}

# Composition-name canonicalization. Spelling variants are aliased EXPLICITLY,
# with the evidence for each alias, so no clip is silently regrouped.
COMPOSITION_ALIASES = {
    "evvari bodhana":     ("Evvari Bodhana",
                           "carnatic_varnam_1.0 notations/abhogi.doc title "
                           "('Evvari Bodhana', composer Patnam Subramania Iyer)"),
    "evari bodhana":      ("Evvari Bodhana",
                           "Saraga work title 'Evari Bodhana' "
                           "MBID 6ef7a09c-e08d-46a4-b8bf-891d20e87457"),
    "nannu brova neeku":  ("Nannu Brova Neeku", "Saraga recording title"),
    "nannu brova nee":    ("Nannu Brova Neeku",
                           "Saraga work title 'Nannu Brova nee' "
                           "MBID a1efd91e-ebe9-4afb-8d8c-1e862bf5da06"),
}

_VARNAM_RE = re.compile(
    r"^\d+__gopalkoduri__carnatic-varnam-by-(?P<performer>[a-z]+)-in-abhogi-raaga$")
_TS_RE     = re.compile(r"\d{8}_\d{6}")
_ISOLATION_RE = re.compile(r"\.(demucs-vocal|vocal-s|vocal|mix)$")


# =========================================================================
# Step 2 -- input audit
# =========================================================================
def _canon_composition(raw):
    key = re.sub(r"[^a-z ]", "", raw.lower()).strip()
    key = re.sub(r"\s+", " ", key)
    if key in COMPOSITION_ALIASES:
        return COMPOSITION_ALIASES[key]
    return (raw, "UNRESOLVED -- no alias evidence")


def _load_saraga_index():
    """title/base -> (composition, performer, work_mbid) from staging_metadata."""
    idx = {}
    for path in glob.glob(os.path.join(METADATA_DIR, "*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        works = d.get("work") or []
        composition = works[0].get("title") if works else d.get("title")
        work_mbid = works[0].get("mbid") if works else None
        performer = ", ".join(a["name"] for a in d.get("album_artists", [])) or None
        for key in filter(None, [d.get("title"), os.path.splitext(os.path.basename(path))[0]]):
            idx[_norm(key)] = (composition, performer, work_mbid,
                               os.path.basename(path))
    return idx


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def _clip_base(npz_path):
    """Strip the _{YYYYMMDD}_{HHMMSS} producer suffix from the npz filename."""
    stem = os.path.splitext(os.path.basename(npz_path))[0]
    parts = stem.rsplit("_", 2)
    if len(parts) == 3 and _TS_RE.fullmatch("_".join(parts[1:])):
        return parts[0]
    return stem


def collect_target_clips():
    """Validated clips of TARGET_RAGA from the production cache (top level only;
    pcd_results/features_v12/excluded/ holds dedup rejects and is not read)."""
    saraga = _load_saraga_index()
    clips = []
    for npz_path in sorted(glob.glob(os.path.join(FEATURE_DIR, "*.npz"))):
        d = np.load(npz_path, allow_pickle=True)
        if str(d["feature_version"]) != FEATURE_VERSION:
            continue
        if str(d["raga"]) != TARGET_RAGA:
            continue
        base = _clip_base(npz_path)

        m = _VARNAM_RE.match(base)
        if m:
            comp_raw, performer = "Evvari Bodhana", m.group("performer").capitalize()
            corpus, prov = "carnatic_varnam_1.0", "notations/abhogi.doc"
            work_mbid, isolation = None, "clean solo vocal (no accompaniment)"
        else:
            stripped = _ISOLATION_RE.sub("", base)
            iso = _ISOLATION_RE.search(base)
            isolation = iso.group(1) if iso else "unknown"
            hit = saraga.get(_norm(stripped))
            if hit is None:                       # try "<Performer> - <Title>" forms
                cand = [v for k, v in saraga.items() if _norm(stripped) in k]
                hit = cand[0] if len(cand) == 1 else None
            if hit is None:
                comp_raw, performer, work_mbid, prov = base, None, None, "UNRESOLVED"
            else:
                comp_raw, performer, work_mbid, prov = hit
            corpus = "saraga"

        composition, comp_evidence = _canon_composition(comp_raw)
        clips.append(dict(
            clip_id=base, npz=os.path.basename(npz_path),
            composition=composition, composition_raw=comp_raw,
            composition_evidence=comp_evidence, work_mbid=work_mbid,
            performer=performer, source_corpus=corpus, isolation=isolation,
            provenance_source=prov, sa_hz=float(d["sa_hz"]),
            f0_frames=int(d["f0"].shape[0]), _npz_path=npz_path))
    return clips


def attach_sequences(clips):
    for c in clips:
        d = np.load(c["_npz_path"], allow_pickle=True)
        stable, coverage = stable_bins_from_f0(d["f0"])
        if stable is None:
            c.update(stable_seq_len=0, alphabet_size=0, coverage=0.0, seq=None)
            continue
        seq = [int(b) // BINS_PER_SWARA for b in stable]
        c.update(stable_seq_len=len(seq), alphabet_size=len(set(seq)),
                 coverage=float(coverage), seq=seq)
    return clips


def audit_compositions(clips):
    got = Counter(c["composition"] for c in clips)
    ok = (dict(got) == EXPECTED_COMPOSITIONS)
    return ok, dict(got)


# =========================================================================
# Step 3 -- observed statistic
# =========================================================================
def ngram_counts(seq, n):
    return Counter(tuple(seq[i:i + n]) for i in range(len(seq) - n + 1))


def cond_entropy(seq, order):
    """Plug-in H(S_t | previous `order` symbols), in bits. order>=1."""
    if len(seq) < order + 1:
        return float("nan")
    joint = ngram_counts(seq, order + 1)
    ctx = Counter(k[:-1] for k in joint.elements())
    total = sum(joint.values())
    h = 0.0
    for gram, c in joint.items():
        h -= (c / total) * np.log2(c / ctx[gram[:-1]])
    return float(h)


def clip_statistics(seq):
    h1 = cond_entropy(seq, 1)
    h2 = cond_entropy(seq, 2)
    return dict(
        length=len(seq), alphabet=len(set(seq)),
        n_bigrams=max(len(seq) - 1, 0), n_trigrams=max(len(seq) - 2, 0),
        distinct_bigrams=len(ngram_counts(seq, 2)),
        distinct_trigrams=len(ngram_counts(seq, 3)),
        H1=h1, H2=h2, dH=h1 - h2)


# =========================================================================
# Step 4 -- doublet-preserving null (Altschul-Erickson / Kandel Eulerian trail)
# =========================================================================
def _is_arborescence(last, verts, f):
    """True iff following last[] from every vertex reaches f (no cycles)."""
    good = {f}
    for v in verts:
        path, u = [], v
        while u not in good:
            if u in path:
                return False
            path.append(u)
            u = last[u]
        good.update(path)
    return True


def euler_surrogate(seq, rng, max_tries=200):
    """Uniform doublet-preserving shuffle. Returns a new sequence or None.

    Altschul & Erickson (1985); Kandel, Matias, Unger & Winkler (1996):
      1. build the bigram multigraph (one directed edge per observed transition)
      2. for every vertex except the final symbol f, pick one out-edge uniformly
         to be that vertex's LAST edge; reject unless those edges form an
         arborescence rooted at f
      3. uniformly permute each vertex's remaining out-edges, last edge appended
      4. walk from the original first symbol, consuming each vertex's edges in
         order -- the walk is an Eulerian trail of the same edge multiset
    """
    L = len(seq)
    if L < 3:
        return None
    s, f = seq[0], seq[-1]
    out = defaultdict(list)
    for a, b in zip(seq[:-1], seq[1:]):
        out[a].append(b)
    verts = set(seq)
    non_f = [v for v in verts if v != f]

    for _ in range(max_tries):
        last = {v: out[v][int(rng.integers(len(out[v])))] for v in non_f}
        if _is_arborescence(last, verts, f):
            break
    else:
        return None

    order = {}
    for v in verts:
        edges = list(out[v])
        if v != f:
            edges.remove(last[v])           # removes ONE parallel edge instance
            rng.shuffle(edges)
            edges.append(last[v])
        else:
            rng.shuffle(edges)
        order[v] = edges

    idx = defaultdict(int)
    res, cur = [s], s
    for _ in range(L - 1):
        e = order[cur]
        if idx[cur] >= len(e):
            return None                     # not a valid trail -- caller rejects
        nxt = e[idx[cur]]
        idx[cur] += 1
        res.append(nxt)
        cur = nxt
    return res


def validate_surrogate(orig, surr):
    """Step 4 mechanical validation. Returns (ok, reasons)."""
    reasons = []
    if surr is None:
        return False, ["generator_returned_none"]
    if len(surr) != len(orig):
        reasons.append("length_mismatch")
    if ngram_counts(surr, 2) != ngram_counts(orig, 2):
        reasons.append("bigram_counts_differ")
    if Counter(surr) != Counter(orig):
        reasons.append("unigram_counts_differ")
    if surr[0] != orig[0] or surr[-1] != orig[-1]:
        reasons.append("endpoints_differ")
    return (not reasons), reasons


# =========================================================================
# Steps 5/6 -- surrogate generation and comparison
# =========================================================================
def run_null(seq, n_surr, rng):
    """Returns (dH array, H2 array, diagnostics dict). Invalid surrogates are
    rejected and regenerated; a persistent failure aborts rather than silently
    shrinking N."""
    dHs, H2s, seqs = [], [], []
    rejected, reject_reasons = 0, Counter()
    attempts, cap = 0, n_surr * 20 + 100
    while len(dHs) < n_surr and attempts < cap:
        attempts += 1
        surr = euler_surrogate(seq, rng)
        ok, reasons = validate_surrogate(seq, surr)
        if not ok:
            rejected += 1
            reject_reasons.update(reasons)
            continue
        st = clip_statistics(surr)
        dHs.append(st["dH"])
        H2s.append(st["H2"])
        seqs.append(tuple(surr))
    if len(dHs) < n_surr:
        raise RuntimeError(
            f"only {len(dHs)}/{n_surr} valid surrogates after {attempts} attempts "
            f"(reasons: {dict(reject_reasons)}) -- refusing to continue on an "
            f"invalid null")
    diag = dict(attempts=attempts, rejected=rejected,
                reject_reasons=dict(reject_reasons),
                distinct_surrogates=len(set(seqs)),
                identical_to_observed=sum(1 for s in seqs if list(s) == list(seq)))
    return np.asarray(dHs), np.asarray(H2s), diag, seqs


def holm_adjust(pvals):
    """Holm (1979) step-down adjusted p-values, order preserved on input.

    Sort ascending, multiply p_(k) by (K - k), enforce monotonicity with a
    running maximum, clip at 1. FWER control holds under ARBITRARY DEPENDENCE
    among the tests -- no independence assumption is used or needed, so the
    6/1 composition structure does not affect its validity.

    Guarantees adj[i] >= pvals[i] elementwise (both operations are
    non-decreasing), which is what makes R_holm <= R_raw and therefore makes
    the two verdict boundaries mutually exclusive.
    """
    p = np.asarray(pvals, dtype=float)
    k = len(p)
    order = np.argsort(p, kind="stable")
    adj_sorted = np.maximum.accumulate(p[order] * (k - np.arange(k)))
    adj = np.empty(k, dtype=float)
    adj[order] = np.minimum(adj_sorted, 1.0)
    return adj


def verdict_from_counts(r_holm, r_raw, k, alpha=0.05):
    """Frozen Step 9 verdict. Boundary values only -- 0 and K are the sole
    non-arbitrary points on a count scale; no interior cut is invented.

    Mutually exclusive by construction: holm_adjust guarantees adj >= raw, so
    R_holm <= R_raw always. Both branches firing would require K <= 0.
    """
    assert r_holm <= r_raw, (
        f"invariant violated: R_holm={r_holm} > R_raw={r_raw}; Holm-adjusted "
        f"p can never be below raw p")
    if r_holm == k:
        label = "SUPPORTED"
        basis = (f"all {k}/{k} clips reject at alpha={alpha} after Holm "
                 f"step-down correction across the {k} tests")
    elif r_raw == 0:
        label = "NOT SUPPORTED"
        basis = (f"0/{k} clips crossed the pre-registered significance "
                 f"threshold alpha={alpha} on RAW (uncorrected) p")
    else:
        label = "INCONCLUSIVE"
        basis = (f"{r_holm}/{k} clips reject after Holm and {r_raw}/{k} on raw "
                 f"p -- neither boundary reached, so the test does not "
                 f"reliably distinguish the two outcomes")
    return dict(
        verdict=label, basis=basis, r_holm=int(r_holm), r_raw=int(r_raw),
        k_clips=int(k), alpha=alpha,
        scope=("This verdict describes the sequence-structure measurement only. "
               "It confers NO promotion. Protocol section 8 PASS is unavailable: "
               "Q-001B-A has no pre-registered magnitude or consistency bar, and "
               "PASS requires every pre-registered promotion criterion to be met. "
               "Whether this structure is Abhogi-specific or discriminative is "
               "Q-001B-B's question and is NOT addressed here."),
        not_supported_meaning=(
            "NOT SUPPORTED means zero clips crossed the pre-registered "
            "significance threshold. It does NOT prove absence of higher-order "
            "structure -- failure to reject a null is not evidence for it "
            "(L-052: at small n, 'no significant separation' means the question "
            "is unresolved, not that the null is proven)."))


def compare(observed_dH, null_dH):
    null_dH = np.asarray(null_dH, dtype=float)
    n = len(null_dH)
    ge = int((null_dH >= observed_dH).sum())
    sd = float(null_dH.std(ddof=1)) if n > 1 else float("nan")
    return dict(
        observed_dH=float(observed_dH),
        null_mean=float(null_dH.mean()), null_sd=sd,
        null_median=float(np.median(null_dH)),
        null_min=float(null_dH.min()), null_max=float(null_dH.max()),
        n_surrogates=n,
        n_null_ge_observed=ge,
        percentile=float(100.0 * (null_dH < observed_dH).sum() / n),
        p_empirical_one_sided=float((ge + 1) / (n + 1)),
        effect_bits=float(observed_dH - null_dH.mean()),
        effect_z=(float((observed_dH - null_dH.mean()) / sd)
                  if sd and np.isfinite(sd) and sd > 0 else float("nan")))


# =========================================================================
# Step 8 -- synthetic controls
# =========================================================================
def synth_positive(n_cycles=200):
    """Deterministic 6-symbol cycle over alphabet {0,1,2}.

    Bigrams: each of the 6 ordered pairs (a,b), a!=b, occurs once per cycle ->
    every vertex has out-degree 2 and H1 = 1.000 bit exactly.
    Trigrams: every (a,b) pair has a single successor -> H2 = 0. dH = 1 bit,
    the theoretical maximum for this graph, and it is pure higher-order
    structure invisible to bigram statistics.
    """
    return [x for _ in range(n_cycles) for x in (0, 1, 2, 0, 2, 1)]


def synth_negative(length=1200, seed=0):
    """First-order Markov chain, non-uniform transitions, NO higher-order term.

    Real bigram structure (so the null has something to preserve) but S_t is
    conditionally independent of S_{t-2} given S_{t-1}. Observed dH should sit
    inside the null distribution.
    """
    rng = np.random.default_rng(seed)
    P = np.array([[0.10, 0.60, 0.20, 0.10],
                  [0.30, 0.10, 0.50, 0.10],
                  [0.20, 0.20, 0.10, 0.50],
                  [0.55, 0.15, 0.20, 0.10]])
    seq, cur = [0], 0
    for _ in range(length - 1):
        cur = int(rng.choice(4, p=P[cur]))
        seq.append(cur)
    return seq


# =========================================================================
# reporting
# =========================================================================
def _git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=BASE_DIR,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def _versions():
    import sys
    v = dict(python=sys.version.split()[0], numpy=np.__version__)
    try:
        import librosa
        v["librosa"] = librosa.__version__
    except Exception:
        pass
    return v


def main():
    ap = argparse.ArgumentParser(description="Q-001B-A higher-order structure test.")
    ap.add_argument("--surrogates", type=int, default=PREREGISTERED_SURROGATES,
                    help=f"surrogates per sequence (pre-registered: "
                         f"{PREREGISTERED_SURROGATES})")
    ap.add_argument("--seed", type=int, default=PREREGISTERED_SEED,
                    help=f"master RNG seed (pre-registered: {PREREGISTERED_SEED})")
    ap.add_argument("--audit-only", action="store_true",
                    help="Steps 2-3 only: input audit + observed statistics")
    args = ap.parse_args()

    t0 = time.time()
    ts = time.strftime("%Y%m%d_%H%M%S")
    tag = "audit" if args.audit_only else f"n{args.surrogates}_seed{args.seed}"
    run_dir = os.path.join(RESULTS_ROOT, f"run_{ts}_{tag}")
    os.makedirs(run_dir, exist_ok=False)

    # ---- Step 2 -------------------------------------------------------
    clips = attach_sequences(collect_target_clips())
    ok, got = audit_compositions(clips)

    print("=" * 78)
    print(f"Q-001B-A  INPUT AUDIT  ({TARGET_RAGA}, feature_version={FEATURE_VERSION})")
    print("=" * 78)
    hdr = f"{'clip_id':52s} {'composition':18s} {'performer':16s} {'corpus':20s} {'len':>6s} {'|A|':>4s}"
    print(hdr); print("-" * len(hdr))
    for c in sorted(clips, key=lambda c: (c["composition"], c["clip_id"])):
        print(f"{c['clip_id'][:52]:52s} {c['composition'][:18]:18s} "
              f"{str(c['performer'])[:16]:16s} {c['source_corpus'][:20]:20s} "
              f"{c['stable_seq_len']:6d} {c['alphabet_size']:4d}")
    print("-" * len(hdr))
    print(f"composition structure: {got}")
    print(f"expected             : {EXPECTED_COMPOSITIONS}")
    print(f"AUDIT: {'MATCH' if ok else 'DISCREPANCY -- STOPPING'}")

    manifest = dict(
        target_raga=TARGET_RAGA, feature_dir=FEATURE_DIR,
        feature_version=FEATURE_VERSION, sequence_representation=SEQ_REPR,
        n_bins=N_BINS, bins_per_swara=BINS_PER_SWARA,
        min_stable_frames=MIN_STABLE_FRAMES,
        expected_compositions=EXPECTED_COMPOSITIONS,
        observed_compositions=got, audit_match=ok,
        clips=[{k: v for k, v in c.items() if not k.startswith("_") and k != "seq"}
               for c in clips])
    with open(os.path.join(run_dir, "input_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)

    if not ok:
        print("\nStep 2 requires a halt on any structural difference. "
              "Not silently corrected. See input_manifest.json.")
        return

    # ---- Step 3 -------------------------------------------------------
    observed = {}
    for c in clips:
        observed[c["clip_id"]] = clip_statistics(c["seq"])
    print("\n" + "=" * 78)
    print("OBSERVED HIGHER-ORDER STATISTIC (plug-in, bits)")
    print("=" * 78)
    hdr = (f"{'clip_id':52s} {'len':>6s} {'|A|':>4s} {'#2g':>5s} {'#3g':>5s} "
           f"{'H1':>7s} {'H2':>7s} {'dH':>7s}")
    print(hdr); print("-" * len(hdr))
    for cid, st in sorted(observed.items()):
        print(f"{cid[:52]:52s} {st['length']:6d} {st['alphabet']:4d} "
              f"{st['distinct_bigrams']:5d} {st['distinct_trigrams']:5d} "
              f"{st['H1']:7.4f} {st['H2']:7.4f} {st['dH']:7.4f}")
    print("-" * len(hdr))
    agg = dict(
        n_clips=len(observed),
        total_symbols=int(sum(s["length"] for s in observed.values())),
        mean_H1=float(np.mean([s["H1"] for s in observed.values()])),
        mean_H2=float(np.mean([s["H2"] for s in observed.values()])),
        mean_dH=float(np.mean([s["dH"] for s in observed.values()])),
        median_dH=float(np.median([s["dH"] for s in observed.values()])),
        min_dH=float(np.min([s["dH"] for s in observed.values()])),
        max_dH=float(np.max([s["dH"] for s in observed.values()])))
    print(f"aggregate: n={agg['n_clips']} symbols={agg['total_symbols']} "
          f"mean H1={agg['mean_H1']:.4f} mean H2={agg['mean_H2']:.4f} "
          f"mean dH={agg['mean_dH']:.4f} (median {agg['median_dH']:.4f})")
    print("dH is the observed higher-order statistic. It is NOT evidence "
          "until compared against the doublet-preserving null.")

    with open(os.path.join(run_dir, "observed_statistics.json"), "w") as fh:
        json.dump(dict(per_clip=observed, aggregate=agg,
                       note=OBSERVED_BIAS_NOTE), fh, indent=2)

    run_meta = dict(
        gate="Q-001B-A", timestamp=ts, run_dir=run_dir,
        mode="audit-only" if args.audit_only else "full",
        surrogate_count=args.surrogates, random_seed=args.seed,
        preregistration=dict(
            surrogates=PREREGISTERED_SURROGATES, seed=PREREGISTERED_SEED,
            date=PREREGISTRATION_DATE,
            matches_preregistration=(args.surrogates == PREREGISTERED_SURROGATES
                                     and args.seed == PREREGISTERED_SEED),
            p_value_per_clip="p_i = (1 + #{j: dH_i^(j) >= dH_i}) / (1 + N); "
                             "one-sided upper tail, +1/+1 corrected, empirical",
            p_value_aggregate="M^(j) = mean_i dH_i^(j); "
                              "p_agg = (1 + #{j: M^(j) >= M_obs}) / (1 + N)",
            effect_magnitude="effect_bits = dH_obs - mean(null); "
                             "effect_z = (dH_obs - mean(null)) / sd(null), ddof=1"),
        feature_version=FEATURE_VERSION, sequence_representation=SEQ_REPR,
        parameters=dict(n_bins=N_BINS, bins_per_swara=BINS_PER_SWARA,
                        min_stable_frames=MIN_STABLE_FRAMES, sr=SR,
                        max_duration_sec=MAX_DURATION_SEC),
        null_model=("doublet-preserving Eulerian-trail shuffle "
                    "(Altschul & Erickson 1985; Kandel et al. 1996)"),
        software=_versions(), git_commit=_git_commit(),
        input_files=[c["npz"] for c in clips],
        elapsed_sec=None)

    if args.audit_only:
        run_meta["elapsed_sec"] = round(time.time() - t0, 2)
        with open(os.path.join(run_dir, "run_metadata.json"), "w") as fh:
            json.dump(run_meta, fh, indent=2)
        print(f"\nAUDIT-ONLY MODE -- stopping before Step 4 (null construction).")
        print(f"results: {run_dir}")
        return

    print(f"\nPRE-REGISTERED (dated {PREREGISTRATION_DATE}): "
          f"surrogates={PREREGISTERED_SURROGATES}, seed={PREREGISTERED_SEED}")
    print(f"THIS RUN                     : "
          f"surrogates={args.surrogates}, seed={args.seed}")
    if (args.surrogates, args.seed) != (PREREGISTERED_SURROGATES, PREREGISTERED_SEED):
        print("  *** DEVIATION from pre-registration -- recorded in run_metadata.json")
    print(f"p per clip : p_i = (1 + #[dH_surr >= dH_obs]) / (1 + N)   "
          f"one-sided upper tail, empirical, floor "
          f"{1.0/(args.surrogates+1):.2e}")
    print(f"p aggregate: M^(j) = mean over clips of the j-th surrogate; "
          f"p_agg = (1 + #[M^(j) >= M_obs]) / (1 + N)")

    # ---- Steps 4/5/7/8 : controls first, then Abhogi -------------------
    master = np.random.SeedSequence(args.seed)
    child_iter = iter(master.spawn(len(clips) + 8))

    print("\n" + "=" * 78)
    print(f"SYNTHETIC CONTROLS  ({args.surrogates} surrogates each, seed={args.seed})")
    print("=" * 78)
    controls, control_pass = {}, True
    for name, seq in (("positive_deterministic_cycle", synth_positive()),
                      ("negative_first_order_markov", synth_negative(seed=args.seed))):
        rng = np.random.default_rng(next(child_iter))
        st = clip_statistics(seq)
        dHs, H2s, diag, _ = run_null(seq, args.surrogates, rng)
        cmp_ = compare(st["dH"], dHs)
        expect_sig = name.startswith("positive")
        got_sig = cmp_["p_empirical_one_sided"] < 0.05
        passed = (got_sig == expect_sig)
        control_pass &= passed
        controls[name] = dict(observed=st, comparison=cmp_, diagnostics=diag,
                              expected_significant=expect_sig,
                              observed_significant=got_sig, passed=passed)
        print(f"{name:32s} len={st['length']:5d} H1={st['H1']:.4f} "
              f"H2={st['H2']:.4f} dH={st['dH']:.4f} | null mean "
              f"{cmp_['null_mean']:.4f} sd {cmp_['null_sd']:.4f} | "
              f"p={cmp_['p_empirical_one_sided']:.5f} z={cmp_['effect_z']:+.2f} | "
              f"{'PASS' if passed else 'FAIL'}")
    with open(os.path.join(run_dir, "synthetic_control_results.json"), "w") as fh:
        json.dump(dict(controls=controls, all_passed=bool(control_pass)), fh, indent=2)

    if not control_pass:
        print("\nSTOP -- synthetic controls did not behave correctly (Step 8). "
              "Abhogi results are not computed.")
        run_meta["elapsed_sec"] = round(time.time() - t0, 2)
        run_meta["halted"] = "synthetic_control_failure"
        with open(os.path.join(run_dir, "run_metadata.json"), "w") as fh:
            json.dump(run_meta, fh, indent=2)
        return

    print("\n" + "=" * 78)
    print(f"ABHOGI vs DOUBLET-PRESERVING NULL  ({args.surrogates} surrogates/clip)")
    print("=" * 78)
    hdr = (f"{'clip_id':40s} {'obs dH':>8s} {'null mu':>8s} {'null sd':>8s} "
           f"{'null med':>9s} {'pct':>6s} {'p':>8s} {'z':>7s}")
    print(hdr); print("-" * len(hdr))
    surrogate_stats, checks, per_clip_null = {}, {}, {}
    for c in sorted(clips, key=lambda c: c["clip_id"]):
        rng = np.random.default_rng(next(child_iter))
        st = observed[c["clip_id"]]
        dHs, H2s, diag, seqs = run_null(c["seq"], args.surrogates, rng)
        cmp_ = compare(st["dH"], dHs)
        per_clip_null[c["clip_id"]] = dHs
        surrogate_stats[c["clip_id"]] = dict(
            comparison=cmp_, diagnostics=diag,
            null_dH_summary=dict(mean=float(dHs.mean()), sd=float(dHs.std(ddof=1)),
                                 median=float(np.median(dHs)),
                                 q05=float(np.percentile(dHs, 5)),
                                 q95=float(np.percentile(dHs, 95))),
            null_H2_mean=float(H2s.mean()))
        # Step 7 checks A-D, per clip
        obs_tri = ngram_counts(c["seq"], 3)
        n_same_tri = sum(1 for s in seqs if ngram_counts(list(s), 3) == obs_tri)
        checks[c["clip_id"]] = dict(
            A_bigram_counts_preserved=True,        # enforced by validate_surrogate
            B_lengths_equal=True,                  # enforced by validate_surrogate
            C_surrogate_trigrams_not_systematically_identical=dict(
                n_identical_trigram_profile=n_same_tri, n_surrogates=len(seqs),
                pass_=n_same_tri < len(seqs)),
            D_surrogates_not_accidentally_identical=dict(
                distinct=diag["distinct_surrogates"], n_surrogates=len(seqs),
                pass_=diag["distinct_surrogates"] > 1),
            rejected_surrogates=diag["rejected"],
            reject_reasons=diag["reject_reasons"])
        print(f"{c['clip_id'][:40]:40s} {cmp_['observed_dH']:8.4f} "
              f"{cmp_['null_mean']:8.4f} {cmp_['null_sd']:8.4f} "
              f"{cmp_['null_median']:9.4f} {cmp_['percentile']:6.2f} "
              f"{cmp_['p_empirical_one_sided']:8.5f} {cmp_['effect_z']:+7.2f}")
    print("-" * len(hdr))

    # ---- multiplicity: Holm across the K per-clip tests -----------------
    ids = sorted(per_clip_null)
    raw_p = np.array([surrogate_stats[i]["comparison"]["p_empirical_one_sided"]
                      for i in ids])
    holm_p = holm_adjust(raw_p)
    for i, cid in enumerate(ids):
        surrogate_stats[cid]["comparison"]["p_holm"] = float(holm_p[i])

    ALPHA = 0.05
    r_raw = int((raw_p < ALPHA).sum())
    r_holm = int((holm_p < ALPHA).sum())

    # ---- DESCRIPTIVE ONLY: aggregate, paired by surrogate index ---------
    null_matrix = np.vstack([per_clip_null[i] for i in ids])   # clips x surrogates
    agg_cmp = compare(agg["mean_dH"], null_matrix.mean(axis=0))
    agg_cmp["status"] = "DESCRIPTIVE ONLY -- not the verdict"
    agg_cmp["caveat"] = (
        "This aggregate treats the 7 clips as independent units. They are NOT: "
        "6 of 7 are the same composition (Evvari Bodhana), so the effective "
        "independent-unit count is 2, not 7. The null of the mean tightens like "
        "1/sqrt(K) and therefore advertises a precision the dataset does not "
        "support. Reported for completeness; it enters NO verdict cell. "
        "Contrast Holm, whose FWER control needs no independence and is "
        "therefore unaffected by this.")

    # ---- descriptive composition split ---------------------------------
    comp_of = {c["clip_id"]: c["composition"] for c in clips}
    comp_split = {}
    for cid in ids:
        comp = comp_of[cid]
        d = comp_split.setdefault(comp, dict(
            n_clips=0, independent_units=1, clips_p_raw_lt_alpha=0,
            clips_p_holm_lt_alpha=0, clip_ids=[]))
        d["n_clips"] += 1
        d["clip_ids"].append(cid)
        d["clips_p_raw_lt_alpha"] += int(
            surrogate_stats[cid]["comparison"]["p_empirical_one_sided"] < ALPHA)
        d["clips_p_holm_lt_alpha"] += int(
            surrogate_stats[cid]["comparison"]["p_holm"] < ALPHA)

    # ---- Step 9 verdict (frozen, threshold-free) -----------------------
    assert len(ids) == 7, f"expected 7 Abhogi clips, got {len(ids)}"
    vd = verdict_from_counts(r_holm, r_raw, len(ids), alpha=ALPHA)

    print(f"\nper-clip significance at alpha={ALPHA}: "
          f"raw {r_raw}/{len(ids)} | Holm-adjusted {r_holm}/{len(ids)}")
    print(f"AGGREGATE mean dH (DESCRIPTIVE ONLY, not the verdict): "
          f"obs={agg_cmp['observed_dH']:.4f} null mean={agg_cmp['null_mean']:.4f} "
          f"sd={agg_cmp['null_sd']:.4f} p={agg_cmp['p_empirical_one_sided']:.5f}")
    print("composition split (descriptive):")
    for comp, d in sorted(comp_split.items()):
        print(f"  {comp:20s} {d['n_clips']} clip(s), 1 independent unit | "
              f"raw {d['clips_p_raw_lt_alpha']}/{d['n_clips']} | "
              f"Holm {d['clips_p_holm_lt_alpha']}/{d['n_clips']}")
    print("\n" + "=" * 78)
    print(f"Q-001B-A VERDICT: {vd['verdict']}")
    print(f"  basis: {vd['basis']}")
    print("=" * 78)

    with open(os.path.join(run_dir, "surrogate_statistics.json"), "w") as fh:
        json.dump(dict(per_clip=surrogate_stats,
                       aggregate_descriptive_only=agg_cmp,
                       composition_split_descriptive=comp_split,
                       multiplicity=dict(
                           method="Holm (1979) step-down Bonferroni",
                           alpha=ALPHA, k_tests=len(ids),
                           r_raw=r_raw, r_holm=r_holm,
                           dependence_note=(
                               "Holm's FWER control holds under arbitrary "
                               "dependence among the tests; no independence "
                               "assumption is used. The 6/1 composition "
                               "structure affects interpretation and the "
                               "descriptive aggregate, not Holm's validity.")),
                       verdict=vd, n_clips=len(ids)), fh, indent=2)
    with open(os.path.join(run_dir, "sanity_checks.json"), "w") as fh:
        json.dump(dict(per_clip=checks,
                       E_positive_control=controls["positive_deterministic_cycle"]["passed"],
                       F_negative_control=controls["negative_first_order_markov"]["passed"],
                       all_passed=bool(
                           control_pass and
                           all(v["C_surrogate_trigrams_not_systematically_identical"]["pass_"]
                               and v["D_surrogates_not_accidentally_identical"]["pass_"]
                               for v in checks.values()))), fh, indent=2)

    with open(os.path.join(run_dir, "per_clip_results.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["clip_id", "composition", "performer", "source_corpus",
                    "stable_seq_len", "alphabet", "H1", "H2", "observed_dH",
                    "null_mean_dH", "null_sd_dH", "null_median_dH", "percentile",
                    "p_empirical_raw", "p_holm", "effect_bits", "effect_z"])
        for c in sorted(clips, key=lambda c: c["clip_id"]):
            st, cm = observed[c["clip_id"]], surrogate_stats[c["clip_id"]]["comparison"]
            w.writerow([c["clip_id"], c["composition"], c["performer"],
                        c["source_corpus"], st["length"], st["alphabet"],
                        f"{st['H1']:.6f}", f"{st['H2']:.6f}", f"{cm['observed_dH']:.6f}",
                        f"{cm['null_mean']:.6f}", f"{cm['null_sd']:.6f}",
                        f"{cm['null_median']:.6f}", f"{cm['percentile']:.3f}",
                        f"{cm['p_empirical_one_sided']:.6f}", f"{cm['p_holm']:.6f}",
                        f"{cm['effect_bits']:.6f}", f"{cm['effect_z']:.4f}"])

    run_meta["elapsed_sec"] = round(time.time() - t0, 2)
    with open(os.path.join(run_dir, "run_metadata.json"), "w") as fh:
        json.dump(run_meta, fh, indent=2)

    write_final_report(run_dir, clips, observed, agg, surrogate_stats, checks,
                       controls, agg_cmp, comp_split, vd, manifest, run_meta,
                       ids, ALPHA)
    print(f"\nresults: {run_dir}")
    print("=" * 78)


# =========================================================================
# Step 12 -- final report (exactly these sections, in this order)
# =========================================================================
def write_final_report(run_dir, clips, observed, agg, surrogate_stats, checks,
                       controls, agg_cmp, comp_split, vd, manifest, run_meta,
                       ids, alpha):
    by_id = {c["clip_id"]: c for c in clips}
    L = []
    A = L.append
    A("# Q-001B-A -- Final Report\n")
    A(f"Higher-order (trigram) structure in Abhogi stable-note sequences, "
      f"tested against a doublet-preserving null.\n")
    A(f"Run `{os.path.basename(run_dir)}` | "
      f"{run_meta['surrogate_count']} surrogates | seed {run_meta['random_seed']} "
      f"| feature_version {FEATURE_VERSION}\n")

    A("\n## Input Audit\n")
    A(f"Validated Abhogi clips from `pcd_results/features_v12/` "
      f"(the `excluded/` subdirectory holds dedup rejects and is not read).\n")
    A("| clip_id | composition | performer | source corpus | isolation | stable len | alphabet |")
    A("|---|---|---|---|---|---|---|")
    for c in sorted(clips, key=lambda c: (c["composition"], c["clip_id"])):
        A(f"| `{c['clip_id']}` | {c['composition']} | {c['performer']} | "
          f"{c['source_corpus']} | {c['isolation']} | {c['stable_seq_len']} | "
          f"{c['alphabet_size']} |")
    A(f"\nComposition structure: **{manifest['observed_compositions']}** -- "
      f"matches the expected **{manifest['expected_compositions']}**.\n")
    A("Composition identity was derived, not assumed: the Carnatic Varnam Dataset "
      "ships one varnam per raga and `notations/abhogi.doc` names it *Evvari "
      "Bodhana* (composer Patnam Subramania Iyer); the two Saraga clips carry "
      "work MBIDs `6ef7a09c-e08d-46a4-b8bf-891d20e87457` (Evari Bodhana / "
      "Vignesh Ishwar) and `a1efd91e-ebe9-4afb-8d8c-1e862bf5da06` (Nannu Brova "
      "nee / S Sundar). Spelling variants are aliased through an explicit "
      "evidence-carrying table -- no clip is silently regrouped.\n")
    A("**Effective sample size: 2 independent compositional units across 7 clips** "
      "(protocol section 4).\n")

    A("\n## Observed Higher-Order Structure\n")
    A("Plug-in conditional entropies, bits. dH = H1 - H2 is the observed "
      "higher-order statistic; it is not evidence until compared against the null.\n")
    A("| clip_id | len | alphabet | distinct 2g | distinct 3g | H1 | H2 | dH |")
    A("|---|---|---|---|---|---|---|---|")
    for cid in ids:
        s = observed[cid]
        A(f"| `{cid}` | {s['length']} | {s['alphabet']} | {s['distinct_bigrams']} "
          f"| {s['distinct_trigrams']} | {s['H1']:.4f} | {s['H2']:.4f} | "
          f"{s['dH']:.4f} |")
    A(f"\nAggregate: n={agg['n_clips']}, {agg['total_symbols']} symbols, "
      f"mean H1={agg['mean_H1']:.4f}, mean H2={agg['mean_H2']:.4f}, "
      f"mean dH={agg['mean_dH']:.4f} (median {agg['median_dH']:.4f}, "
      f"range {agg['min_dH']:.4f}-{agg['max_dH']:.4f}).\n")

    A("\n## Null Construction Validation\n")
    A("Null: doublet-preserving shuffle by uniform Eulerian-trail reconstruction "
      "of each sequence's own bigram multigraph (Altschul & Erickson 1985; "
      "Kandel, Matias, Unger & Winkler 1996). Ordinary shuffling was not used "
      "and would invalidate the null by destroying the bigram structure under "
      "control.\n")
    A("Every surrogate is mechanically validated before use; any failing "
      "surrogate is rejected and regenerated, and a persistent failure aborts "
      "rather than silently shrinking N.\n")
    A("| clip_id | surrogates | rejected | distinct | identical to observed |")
    A("|---|---|---|---|---|")
    for cid in ids:
        d = surrogate_stats[cid]["diagnostics"]
        A(f"| `{cid}` | {run_meta['surrogate_count']} | {d['rejected']} | "
          f"{d['distinct_surrogates']} | {d['identical_to_observed']} |")
    A("\nBecause bigram counts are preserved exactly, H1 is invariant across the "
      "null, so `dH_obs - dH_surr == H2_surr - H2_obs`. This identity is exact; "
      "no part of the comparison rests on H1.\n")
    A("\nThe plug-in bias in H2 is matched on every nuisance dimension the null "
      "holds fixed (length, alphabet, unigram and bigram counts, bigram context "
      "counts) but does **not** exactly cancel. The residual bias in a plug-in "
      "conditional entropy depends on the effective trigram support, and trigram "
      "support differs between observed and surrogate -- it is itself a function "
      "of the structure under test, whereas the bigram context count is identical "
      "by construction. A more-structured sequence has fewer distinct trigrams and "
      "therefore a smaller downward bias, so in expectation the residual depresses "
      "H2_surr more than H2_obs and inflates null dH relative to observed. The "
      "residual is therefore **conservative here: it can mask a small genuine "
      "effect, but cannot manufacture a positive result.** Its magnitude is "
      "deliberately not quantified, because per-surrogate trigram support (m3) was "
      "not recorded in this run.\n")

    A("\n## Synthetic Control Results\n")
    A("Binding criteria: positive `p < 0.05`, negative `p >= 0.05`. Controls run "
      "before any Abhogi surrogate is drawn and abort the run on failure. No "
      "expected value is hardcoded or asserted.\n")
    A("| control | len | H1 | H2 | dH | null mean | null sd | p | expect sig | got sig | result |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for name, cd in controls.items():
        o, cm = cd["observed"], cd["comparison"]
        A(f"| {name} | {o['length']} | {o['H1']:.4f} | {o['H2']:.4f} | "
          f"{o['dH']:.4f} | {cm['null_mean']:.4f} | {cm['null_sd']:.4f} | "
          f"{cm['p_empirical_one_sided']:.5f} | {cd['expected_significant']} | "
          f"{cd['observed_significant']} | "
          f"**{'PASS' if cd['passed'] else 'FAIL'}** |")
    A("\nPositive control: deterministic 6-cycle over {0,1,2}; every ordered pair "
      "occurs once per cycle so H1 = 1 bit exactly, and each pair has a single "
      "successor so H2 = 0 -- one bit of pure higher-order structure invisible to "
      "bigram statistics. Negative control: first-order Markov chain with "
      "non-uniform transitions, where S_t is conditionally independent of S_(t-2) "
      "given S_(t-1).\n")
    A("The negative control's `p >= 0.05` gate has a built-in ~5% spurious-failure "
      "rate under a true null. Seed 0 was not re-rolled at any point.\n")

    A("\n## Abhogi Results\n")
    A(f"Per clip, {run_meta['surrogate_count']} surrogates. p is one-sided upper "
      f"tail, empirical, finite-sample corrected; floor "
      f"{1.0/(run_meta['surrogate_count']+1):.2e}.\n")
    A("| clip_id | composition | obs dH | null mean | null sd | null median | pct | p raw | p Holm | effect (bits) | effect z |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for cid in ids:
        cm = surrogate_stats[cid]["comparison"]
        A(f"| `{cid}` | {by_id[cid]['composition']} | {cm['observed_dH']:.4f} | "
          f"{cm['null_mean']:.4f} | {cm['null_sd']:.4f} | {cm['null_median']:.4f} "
          f"| {cm['percentile']:.2f} | {cm['p_empirical_one_sided']:.5f} | "
          f"{cm['p_holm']:.5f} | {cm['effect_bits']:+.4f} | {cm['effect_z']:+.2f} |")
    A(f"\nSignificance at alpha={alpha}: **raw {vd['r_raw']}/{vd['k_clips']}**, "
      f"**Holm-adjusted {vd['r_holm']}/{vd['k_clips']}**.\n")
    A("\n### Descriptive only -- enters no verdict cell\n")
    A(f"Aggregate mean dH: observed {agg_cmp['observed_dH']:.4f}, null mean "
      f"{agg_cmp['null_mean']:.4f}, sd {agg_cmp['null_sd']:.4f}, "
      f"p={agg_cmp['p_empirical_one_sided']:.5f}.\n")
    A(f"> {agg_cmp['caveat']}\n")
    A("Composition split:\n")
    A("| composition | clips | independent units | raw p<alpha | Holm p<alpha |")
    A("|---|---|---|---|---|")
    for comp, d in sorted(comp_split.items()):
        A(f"| {comp} | {d['n_clips']} | {d['independent_units']} | "
          f"{d['clips_p_raw_lt_alpha']}/{d['n_clips']} | "
          f"{d['clips_p_holm_lt_alpha']}/{d['n_clips']} |")

    A("\n## Statistical Interpretation\n")
    A("Each clip is tested against a null generated from **its own** sequence, so "
      "per-clip p-values are **valid finite-sample Monte-Carlo p-values under "
      "their own conditional null, using the conservative (b+1)/(N+1) "
      "correction** -- regardless of what the other clips are. Composition "
      "sharing does not affect their validity. This is why protocol section 6 "
      "calls this test usable at very low compositional-unit counts.\n")
    A("These p-values **estimate the exact randomization p-value that full "
      "enumeration of the clip's Eulerian-trail class would provide**. That "
      "enumeration is infeasible, so the class is Monte-Carlo sampled instead. "
      "The (b+1)/(N+1) construction is conservative rather than unbiased: it "
      "guarantees P(p_hat <= alpha) <= alpha under the clip's null for every "
      "finite N (Phipson & Smyth 2010), at the cost of slightly overstating the "
      "exact value.\n")
    A("Holm (1979) is a step-down Bonferroni procedure whose family-wise error "
      "control holds under **arbitrary dependence** among the tests; no "
      "independence assumption is used. The 6/1 composition structure therefore "
      "affects interpretation and the descriptive aggregate, but does **not** "
      "invalidate Holm's FWER control over the seven per-clip tests. The "
      "aggregate `p_agg` is the opposite case -- its precision does assume a "
      "7-unit independence that does not hold -- which is why it is descriptive "
      "only.\n")
    A("Effect sizes are reported alongside significance throughout (protocol "
      "section 7). `effect_z` is a magnitude only: it is never converted to a "
      "p-value and no normality is assumed anywhere.\n")

    A("\n## Dataset Limitations\n")
    A("- **2 independent compositional units across 7 clips.** Six clips are "
      "*Evvari Bodhana*; one is *Nannu Brova Neeku*. Protocol section 4 makes "
      "the compositional-unit count, not the clip count, the statistical n for "
      "power purposes.\n")
    A("- A per-clip result significant against its own null shows that **sequence "
      "structure exists**. It does **not** show that structure is Abhogi-specific, "
      "nor that it discriminates Abhogi from any other raga. That is Q-001B-B's "
      "question and is not addressed here.\n")
    A("- Two clips (`223582...vignesh`, `Vignesh Ishwar - Evvari Bodhana`) share "
      "both performer and composition but are distinct recordings from different "
      "corpora. Noted for provenance completeness; it changes no result.\n")
    A("- These limitations are reported **separately from** the statistical "
      "evidence. They were not used to manufacture significance, and were not "
      "used to invalidate the gate automatically.\n")

    A("\n## Q-001B-A Verdict\n")
    A(f"### {vd['verdict']}\n")
    A(f"**Basis:** {vd['basis']}.\n")
    A("Decision rule, pre-registered and threshold-free -- boundary values only, "
      "since 0 and K are the sole non-arbitrary points on a count scale:\n")
    A("```\nR_holm == K  ->  SUPPORTED\nR_raw  == 0  ->  NOT SUPPORTED\n"
      "otherwise    ->  INCONCLUSIVE\n```\n")
    A("The two boundaries are mutually exclusive by construction: Holm-adjusted p "
      "is never below raw p, so `R_holm <= R_raw` always, and both firing would "
      "require `K <= 0`.\n")
    A(f"**What NOT SUPPORTED would mean:** {vd['not_supported_meaning']}\n")
    A(f"**Scope:** {vd['scope']}\n")
    A("No magnitude floor (delta), no fraction-of-control (f) and no count "
      "threshold (R) were invented for this gate. Protocol section 7 delegates "
      "threshold values to the gate and the repository contains none for this "
      "statistic; inventing them would be bar-setting to force a verdict, which "
      "section 7 forbids, and a floor on a median at n=7 is the mean-vs-threshold "
      "binary L-052 rejected after Q-001A tried it.\n")

    A("\n## Q-001B-B Status\n")
    A("**NOT EXECUTED. Blocked, unchanged.**\n")
    A("The provenance finding stands: Abhogi composition diversity is "
      "insufficient for composition-held-out discrimination (2 independent units, "
      "one of them a single clip). Accordingly, no clips were regrouped, no "
      "random splits were made, performers were not treated as independent "
      "compositions, no Evvari Bodhana clips were removed, Nannu Brova Neeku was "
      "not duplicated, and no recordings were added during this run.\n")
    A("Q-001B-A tests sequence structure. Q-001B-B tests composition-held-out "
      "discrimination. These remain separate questions.\n")

    A("\n## Files Created\n")
    for f in ["run_metadata.json", "input_manifest.json", "observed_statistics.json",
              "surrogate_statistics.json", "sanity_checks.json",
              "synthetic_control_results.json", "per_clip_results.csv",
              "final_report.md"]:
        A(f"- `{f}`")
    A(f"\nAll under `{run_dir}`. Previous runs are not overwritten.\n")
    A("Implementation: `scripts/sandbox_q001b_a_higher_order.py` (new sandbox "
      "script). No production script was modified; `stable_bins_from_f0()` is "
      "imported from the Q-001A sandbox rather than reimplemented (ADR-015).\n")

    A("\n## Reproducibility Information\n")
    A(f"- Feature version: `{FEATURE_VERSION}`")
    A(f"- Sequence representation: `{SEQ_REPR}` (stable bin // {BINS_PER_SWARA}, "
      f"{N_BINS} bins, MIN_STABLE_FRAMES={MIN_STABLE_FRAMES})")
    A(f"- Surrogate count: **{run_meta['surrogate_count']}** "
      f"(pre-registered {PREREGISTERED_SURROGATES} on {PREREGISTRATION_DATE})")
    A(f"- Random seed: **{run_meta['random_seed']}** "
      f"(pre-registered {PREREGISTERED_SEED}); independent per-sequence streams "
      f"via `numpy.random.SeedSequence.spawn`")
    A(f"- Matches pre-registration: "
      f"**{run_meta['preregistration']['matches_preregistration']}**")
    A(f"- Software: {run_meta['software']}")
    A(f"- Git commit: `{run_meta['git_commit']}`")
    A(f"- Timestamp: {run_meta['timestamp']}")
    A(f"- Elapsed: {run_meta['elapsed_sec']} s")
    A(f"- Null model: {run_meta['null_model']}")
    A("- Input files:")
    for f in run_meta["input_files"]:
        A(f"  - `{f}`")

    with open(os.path.join(run_dir, "final_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
