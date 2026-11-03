# Experiment V: full-support stable run

Reported results, collected November 1, 2026. This directory supplies the full-support stable Experiment V evidence used by the manuscript. These results are included in submission source version v2026.11.02.1; the v2026.10.30.2 data archive supplies the historical protocol comparison.

The versioned protocol is `experiment-V-support-stable-20261031-v1`. It retains the real-data preprocessing, full-model calibration constants, budgets, repetitions and UNI/NORM/LEV/OPT definitions. The fresh sampling seed is 202610310501. Landweber, Showalter and Nesterov use a common full-support step bound for each dataset, with recomputed numerical targets, algorithmic influences and OPT. Ridge/HBF/SOAR retain hash-verified historical full-data targets and probabilities; all six methods use fresh subsamples.

For a rule with probabilities pi, every with-replacement sketch has spectrum bounded by `B_pi = max_i ||z_i||^2 / pi_i`. The 48 dataset/method/rule support checks require `B_pi <= L` and `h B_pi <= 0.9` for Landweber/Showalter/Nesterov, `0 < h eta <= .01` and `h^2 B_pi <= 2` for HBF, and `h^2 B_pi <= 8` for SOAR. Ridge uses an SPD solve. `support_gate.json` records these checks. The per-draw field `step_bound_observed` is the inherited Cholesky diagnostic at the older full-data scale; it is a separate check.

All 530 sketch tasks completed, with 12,720 metric records, no observed step-bound violations and all support gates passed. OPT has the lowest observed mean in 78/78 dataset/method/budget cells. The maximum-budget OPT empirical/first-order ratios span approximately 0.969 to 1.179. These are finite-repetition comparisons; stability and first-order oracle optimality do not prove a complete finite-budget conditional-MSE ranking. The historical and full-support stable protocols use different seeds and, for three methods, different numerical targets, so mean changes cannot be attributed solely to the step size.

From the repository root, recompute saved means and regenerate convenient V target-error curves without running trajectories:

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
```

The output includes `summary.csv`, `r5_01_gdsc_target.pdf`, `r5_02_year_target.pdf` and `validation.json`. It verifies source SHA-256 values and all saved mean, SE, prediction RMSE and calibration columns. `metrics.csv` includes every scalar outcome, not every state array. `independent_validation.json` records the original scalar-record completeness/summary checks and full-target integrity/comparisons; it does not certify independent per-sketch state-error recalculation. `targets/<dataset>/<method>/summary.json` preserves matched full-target prediction references and algorithm parameters.

The scientific implementation and rerun prerequisites are documented in [the versioned source directory](../../Experiments/experiment5_support_stable_20261031/README.md). Full reruns require official inputs and historical full-data arrays, which the public review-data asset does not contain. The protocol, support checks and validation records are provided in this directory; `PROVENANCE.json` identifies their sources and file checksums.

The saved-metric plotting tool exports convenience layouts, rather than asserting identity with the journal artwork. Final manuscript figure assets are matched separately in the paper result map.
