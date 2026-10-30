# Experiment V: portable tail diagnostics

These files reproduce the October 29 YearPredictionMSD tail checks used to qualify the finite-repetition summaries in the paper. They leave the frozen experimental protocols, draws and scientific conclusions unchanged. [The parent evidence guide](../README.md) covers the saved empirical comparisons; [data acquisition](../../../docs/DATA_SOURCES.md) describes the official raw inputs.

## 1. Lightweight verification (no raw download)

From the repository root, with Python 3.11 or later:

```text
python -m pip install mpmath==1.3.0
python evidence/experiment5/tail_diagnostics/verify_witnesses.py
python evidence/experiment5/tail_diagnostics/verify_stability.py
```

The first command checks four single-atom witnesses with 80-digit arithmetic and 60-digit outward interval arithmetic: Landweber UNI/OPT, Showalter UNI, and Nesterov UNI. It verifies the stored restored Landweber target vector has norm below 8, checks the historical target-norm premises, and reproduces the archived scalar logarithmic bounds. `--output PATH.json` saves its report instead of printing it. The input file contains only two 90-coordinate standardized rows, their responses, a 90-coordinate target and the scalar probabilities/parameters, encoded as hexadecimal binary64 strings. It does not require NumPy or the large original arrays.

At budget 50,000, the conservative integer exponents for Landweber UNI and OPT are respectively 2,059,934 and 2,885,997: conditional relative MSE exceeds 10 raised to the indicated exponent, subject to the input and target premises. Showalter's UNI witness is also large at this budget. Nesterov's same-event bound is large at smaller budgets but tiny at 50,000; **a tiny lower bound does not establish negligible tails**. The calculation does not establish a complete conditional-MSE ordering among rules.

For a row atom `z_i`, squared norm `s_i`, response `y_i` and probability `pi_i`, the event that all `N` draws select this row has probability `pi_i**N`. Its sampled Gram has positive eigenvalue `s_i/pi_i`. If `r` is the residual of the actual finite-step numerical map, the estimator is

```text
beta(E_i) = (y_i/s_i) * (1-r(s_i/pi_i)) * z_i
RelMSE(N) >= pi_i**N * max(||beta(E_i)||/8 - 1, 0)**2
```

The last inequality uses `0 < ||beta_target|| <= 8`. Landweber uses `r=(1-h*lambda)**k`; Showalter uses the RK4 polynomial to the power `k`; Nesterov uses the frozen omega=1 recurrence. The verifier handles the residual's sign explicitly. It uses the full-precision parameters, not rounded table entries.

Probability conventions are preserved explicitly: Landweber uses the stored binary64 UNI/OPT probabilities; the archived Showalter/Nesterov check uses mathematical UNI=`1/463715`. They differ slightly in the uniform case. This package does not silently identify those numbers, or assert that an exact-real scalar recurrence is a certificate for the entire floating-point matrix trajectory.

`verify_stability.py` checks the supplied HBF/SOAR support-bound premises from `reference/hbf_soar_values.json`. For SOAR, the exact RK4 identity `|R(i sqrt(q))|^2 = 1 + q^3(q-8)/576` controls the full interval `0 <= q <= h^2 B <= 8`. For HBF the archived sufficient interval is `0 < h*eta <= .01` and `0 <= h^2 B <= 2`; the complex-root bound is `|R|^2-1 <= a*(-5/6+7*a/12+a^3/24)<0`, with `a=h*eta`, while the real roots lie in `[-a,0]`. This excludes the specific exponentially amplified homogeneous mode only. Year HBF/SOAR OPT bounds come from saved target summaries; those probability arrays were not rebuilt. GDSC uses standardized column norms, the probability floor and the recorded step counts. This scalar premise check does not add an input-regeneration certificate or prove Monte Carlo accuracy.

## 2. Full Year/Landweber restoration and scan

Use the pinned numerical environment in the repository's `requirements.txt`; the full path additionally needs NumPy, SciPy, pandas and Numba. It replays the original native recurrences and checkpointed derivatives, without eigenvalue/SVD trajectory shortcuts. It may require several minutes and approximately 1 GB of generated arrays, plus transient memory. The examples place generated outputs under the repository's ignored `runs/` directory, outside this tracked evidence directory.

```text
python -m pip install -r requirements.txt
python run.py data download --dataset year
python evidence/experiment5/tail_diagnostics/restore_year.py --raw-year Data/real_data_20261016/raw/yearpredictionmsd/yearpredictionmsd/YearPredictionMSD.txt --output runs/tail_year_restore
python evidence/experiment5/tail_diagnostics/scan_year.py --restored runs/tail_year_restore --output runs/tail_year_scan
```

The raw-text path above matches `files.year.path` in [`provenance/data_sources.json`](../../../provenance/data_sources.json). `--raw-year` also accepts the official ZIP at `Data/real_data_20261016/raw/yearpredictionmsd/yearpredictionmsd.zip`, reading its `YearPredictionMSD.txt` member without extraction. All locations are supplied by CLI or resolved relative to this repository; neither command relies on a developer's absolute filesystem path. Both output directories must be new. `--repository-root PATH` overrides repository detection, making it possible to run the scripts from any working directory.

Restoration verifies the raw text SHA-256, `source_hashes.json` and the frozen saved-records archive hash before using the frozen code. It reconstructs training-only normalization, Gram/cross-product, the three baseline probability arrays, the Landweber target, checkpointed influences and OPT probabilities. It compares full-target metrics, first-order constants, minimum OPT probability and maximum atom/probability ratio against the historical summary in `../saved_records.tar.gz`, requiring relative errors below `1e-8`.

The scan verifies regenerated-array hashes, rescans the full row support, recomputes the saved empirical Landweber means from the archive, and writes `support_stability.csv`, `event_bounds.csv`, `event_witnesses.csv`, `diagnosis.json` and `recomputed_saved_means.csv`. It also regenerates compact inputs for all four witnesses and reruns the high-precision/interval verifier. The Showalter/Nesterov scalar parameters are rebuilt from the regenerated Gram using their frozen formulas; their full targets are not replayed here, and their norm-8 premise continues to use the saved historical target summaries. Rebuilding the complete Experiment V runs is separate from this diagnostic workflow.

## Provenance and limits

The required raw text hash is `4b6f8e50235b359e01689ae7fb33ad0f89677e9a15f25f3d6259327a6bb927bb`. The official ZIP hash recorded in the original audit is `06f801af323bb7798e800583acce4ea1ed2697ac12c23f4424aea0a7a3d09e11`. A ZIP with identical text but different container bytes is acceptable: the raw text hash is the reconstruction prerequisite and the supplied container hash is recorded separately.

- `source_hashes.json`: frozen native sources and protocol used for restoration.
- `witness_inputs.json`: compact exact inputs for independent scalar arithmetic.
- `reference/array_manifest.json`: hashes of the October 29 **reconstructed** arrays; not hashes of the unavailable original historical arrays.
- `reference/restoration_validation.json`: original summary comparisons, environment versions and reconstruction qualifications; the local raw-file path is replaced by a portable description.
- `reference/independent_check.json` and `reference/showalter_nesterov_witness.json`: October 29 scalar checks.
- `reference/verified_witnesses.json`: portable high-precision/interval verification of all four witnesses.
- `reference/portable_validation.json`: October 30 end-to-end check from the hash-matched raw ZIP, including independent restoration, full-support rescanning, all four regenerated scalar witnesses and the lightweight changed-step rejection check. All 16 reconstructed-array hashes and all five scan-output hashes matched the October 29 reconstruction in the tested environment.
- Remaining reference CSV/JSON files preserve the full-support scan, event bounds, historical target summary and saved means. `reference/hbf_soar_values.json` preserves the separate stability-screen inputs and source descriptions.

The original historical input/probability arrays and their byte-level manifests are unavailable. Frozen source plus hash-matched raw data and agreement with historical summaries support a tolerance-based reconstruction, **not historical array-byte identity**. Different numerical library builds can alter low-order bits; fresh array hashes are recorded, and the immutable reference hashes are not silently treated as universal cross-platform expectations. Interval arithmetic encloses scalar computations on the supplied rows and parameters only. It does not certify normalization, all native trajectories or unknown historical bits. No new random subsamples are drawn by these diagnostics.
