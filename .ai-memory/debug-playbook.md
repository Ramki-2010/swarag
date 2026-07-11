# Swarag — Debug Playbook

## Debugging Priority Order

Always investigate problems in this exact sequence.
Most failures occur in data pipelines, not algorithms.

```
1. FILE PATHS
   - Does the audio file exist?
   - Does the aggregation folder exist?
     Current: pcd_results/aggregation/v1.2/run_20260331_232228/
     Scoring: IDF x Variance weighted, 72 bins, MIN_CLIPS=5, PCD=0.8/Dyad=0.2, no per-raga overrides (v1.3.2)
   - Are pcd_stats/ and dyad_stats/ subfolders present?
   - Are .npz files loadable?

2. ENVIRONMENT
   - Is the virtual environment activated?
     Path: scripts/my_virtual_env_swarag/
   - Are all dependencies installed? (numpy, librosa, scipy)
   - Demucs has its OWN venv: demucs_env/

3. AUDIO QUALITY
   - Is the audio vocal-only? (instruments contaminate pYIN)
   - Check for violin/mridangam in the recording
   - Saraga multitrack stems preferred over mix files
   - Use Demucs (--two-stems vocals) for mix-only recordings
   - Is the audio longer than 6 minutes?
     (MAX_DURATION_SEC=360 caps at 6 min — should be enough)

4. DATA LOADING
   - Do .npz files contain expected keys? (mean_pcd, mean_up, mean_down)
   - Are array shapes correct? (PCD: 72, Dyads: 5184)
   - Are values non-zero and non-NaN?

5. PITCH EXTRACTION
   - Does pYIN return enough voiced frames? (min 200)
   - Is the audio too short / too noisy / polyphonic?
   - Is f0 mostly NaN? (check voiced_flag ratio)
   - Is gating ratio reasonable? (>0.6 is good, <0.5 is suspect)

6. TONIC ESTIMATION
   - Is estimate_tonic() returning a plausible Sa? (80-400 Hz)
   - Does the tonic match across extraction and recognition?
   - Are extraction and recognition using the SAME tonic logic?
     (Both must use utils.py -> estimate_tonic)

7. FEATURE COMPUTATION
   - Are PCD bins summing to 1.0?
   - Are dyad matrices non-zero after Laplace smoothing?
   - Do recognition-time features use the SAME constants as
     aggregation-time features? (MIN_STABLE_FRAMES, ALPHA, EPS)

8. SCORING LOGIC
   - Are all scores in a reasonable range?
   - Is genericness penalty dominating? (all scores negative = BUG-004)
   - Is score compression present? (total spread < margin threshold)
   - Is escalation crushing margins? (BUG-007)
   - Is a janya raga being absorbed by its parent? (BUG-015, L-044)

9. GUARDRAILS
   - Are margin thresholds appropriate for the score range?
     Current: MARGIN_STRICT=0.003 (HIGH), MIN_MARGIN_FINAL=0.001 (MODERATE)
     (BUG-006 resolved: was 0.05, recalibrated 2026-03-09)
   - Is the except-Exception hiding real errors?
   - Does UNKNOWN mean "genuinely ambiguous" or "crash swallowed"?

10. POST-EDIT VERIFICATION (after modifying any production script)
   - Run: python -m py_compile <script>.py        (syntax OK?)
   - Run: python -c "import <module>; ..."         (constants correct?)
   - Run: git diff <script>.py                     (only expected changes?)
   - Check for duplicate def/class/import statements (no corruption?)
   - See L-047: BUG-016 was caused by skipping this step.
```

## Common Failure Patterns

| Symptom | Likely Cause |
|---|---|
| Everything returns UNKNOWN | Thresholds too high (BUG-006), or silent exception |
| Shankarabharanam always wins | Too few ragas trained — add more ragas to crowd out attractor |
| All scores are negative | GENERICNESS_WEIGHT too high (BUG-004, confirmed inert) |
| Margin is always tiny | Score compression — features lack discriminative power |
| Kalyani/Shankarabharanam tied | Sibling raga problem — need phrase-level features |
| Kalyani margin crushed | Escalation path (BUG-007) — dyad-heavy reweighting hurts |
| Thodi absorbs everything | Thodi PCD concentrated on Sa/Pa/Ma (universal swaras) — BUG-008 |
| Dyad similarities all ~0.001 | ALPHA too high (was 0.5, should be 0.01) — Phase 2 fix |
| OOD false positives on mix audio | Instrument noise inflates scores -- must vocal-isolate first (BUG-009) |
| Noisy PCD with extra peaks | Instrument contamination — use vocal-only audio |
| Very slow processing | Missing MAX_DURATION_SEC=360 cap, or processing full concerts |
| ModuleNotFoundError | Virtual environment not activated |
| Sandbox accuracy much higher than LOO | Self-evaluation bias -- use LOO for true accuracy |
| Accuracy drops when adding scoring layer | Feature too weak for current dataset size (see BUG-010) |
| && syntax error | Using PowerShell -- use `;` instead. Never use `&&` in PS commands |
| New raga tanks accuracy | Thin-data raga sink (need 5+ clips) -- BUG-011 |
| UnicodeEncodeError (checkmark) | aggregate_all_v12.py print statement -- cosmetic, aggregation completed |
| Production script has duplicate function defs | Prepended corruption block -- run py_compile + git diff (BUG-016, L-047) |
| Janya raga always classified as parent | PCD subset overlap -- need phrase/ratio features, not weight overrides (BUG-015, L-044) |
| Absent-swara penalty hurts self-recognition | Gamaka leakage makes swaras never truly absent -- use energy ratios, not binary (L-046) |
| Quoting errors in terminal commands | PowerShell uses different quoting than bash. Use single quotes for simple strings, double quotes for variable interpolation. Never use `&&` |

## Quick Diagnostic Commands

```powershell
# Activate environment
Set-Location D:\Swaragam\scripts
.\my_virtual_env_swarag\Scripts\Activate.ps1

# Run random/unknown evaluation (4 test files)
python batch_evaluate_random.py

# Run seed evaluation (50 training files)
python batch_evaluate.py

# Run Demucs vocal isolation on a file
D:\Swaragam\demucs_env\Scripts\python.exe -m demucs --two-stems vocals -o D:\Swaragam\demucs_outputs\vocal_separation "path\to\file.mp3"

# Check feature file contents
python -c "import numpy as np; d=np.load('file.npz',allow_pickle=True); print(list(d.keys())); print(d['raga'])"

# Check current aggregation models
python -c "import os; print(sorted(os.listdir(r'D:\Swaragam\pcd_results\aggregation\v1.2'))[-1])"

# --- POST-EDIT VERIFICATION (run after ANY production script change) ---

# Syntax check
python -m py_compile recognize_raga_v12.py

# Constants check (verify key values match architecture.md)
python -c "import recognize_raga_v12 as r; print('PCD_WEIGHT:', r.PCD_WEIGHT); print('DYAD_WEIGHT:', r.DYAD_WEIGHT); print('ALPHA:', r.ALPHA); print('N_BINS:', r.N_BINS)"

# Git integrity check (should show ONLY your intended changes)
git diff recognize_raga_v12.py

# Check for duplicate function definitions (corruption canary)
python -c "import ast; tree=ast.parse(open('recognize_raga_v12.py').read()); defs=[n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]; dupes=set(d for d in defs if defs.count(d)>1); print('DUPLICATES:', dupes) if dupes else print('OK: no duplicate defs')"
```

**NOTE on PowerShell quoting**: When running Python one-liners with `-c`,
use double quotes for the outer string and single quotes inside, or
vice versa. PowerShell does NOT handle bash-style quoting.
If in doubt, write a small .py script instead of a one-liner.

## Audio Source Quality Checklist

| Source | Vocal Quality | Action Needed |
|---|---|---|
| Original seed (*_clean_*.wav) | Clean vocal | None |
| Carnatic Varnam (223*gopalkoduri*) | Solo vocal + drone | None |
| Saraga *.vocal.mp3 (stem) | Multitrack stem | None (already isolated) |
| Saraga *.vocal.mp3 (Demucs) | AI-separated vocal | Check for artifacts |
| Saraga mix (concert recording) | Vocal + violin + mridangam | MUST isolate vocals first |
