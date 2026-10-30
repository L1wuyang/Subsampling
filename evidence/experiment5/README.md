# Experiment V: empirical results and saved evidence

This directory supports the real-data results in *Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework*. The current workflow reproduces empirical means, the two coefficient-target figures, and descriptive diagnostics from the saved GDSC and YearPredictionMSD records. These finite-repetition summaries do not establish the ordering of the full conditional MSE. Prediction comparisons are descriptive because the test sets had been explored previously.

`saved_records.tar.gz` contains 530 original draw CSVs with 12,720 metric records, 12 full-target summaries, the formal protocols, the execution record, and the original one-sided comparison table. Original file bytes and relative paths are preserved. These are scalar experiment outputs; raw covariates, responses and fitted coefficient vectors are obtained or computed through the full reproduction workflow.

## Reproduce the current empirical summaries and figures

From the repository root, using its pinned numerical requirements, first install the separate review-data archive. This restores `saved_records.tar.gz`, the plot/reference files and diagnostic inputs at their original paths; the scripts remain in the core:

```bash
python run.py review-data download
python run.py review-data verify
python -B evidence/experiment5/empirical.py --output runs/experiment5_empirical
```

For offline installation, use `python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip` instead of the download command. Choose a new output directory. This command verifies the saved archive, checks all 530 draw files and 12,720 records, and reproduces the 276 visible points in the manuscript's two target-error figures against `paper_plot_reference.json`. It checks that OPT has the smallest empirical mean coefficient-target error in all 78 method-budget cells. GDSC NORM records remain in the summaries; the duplicate NORM curve is represented by UNI in the target figure.

Outputs include:

- `summary.csv`, `summary.json` and `rankings.json`: empirical means, repetition counts, empirical-to-first-order ratios, observed stability checks and empirical rankings;
- `figures/r5_01_gdsc_target.*` and `figures/r5_02_year_target.*`: PDF, SVG and PNG target-error figures with empirical mean curves and no mean-confidence bands;
- `r5_01_gdsc_target_plotted_points.csv`, `r5_02_year_target_plotted_points.csv` and `figure_validation.json`: plotted target values and checks against the paper reference;
- descriptive diagnostics for empirical-to-first-order ratios, test RMSE against matched full-model references, untrimmed error distributions and sampled-object coverage;
- `saved_evidence_verification.json`: archive checksums, input counts and verification scope;
- `index.html`: a local report with the generated figures.

The command uses saved scalar records and performs no model fitting or new random sampling. It does not generate mean-based tests or confidence intervals. Observed stability checks concern the realized matrices, and empirical-to-first-order ratios compare the observed means with the first-order criterion; neither certifies full-support stability or finite-budget conditional MSE accuracy.

## Check the tail diagnostics

The [portable tail-diagnostic guide](tail_diagnostics/README.md) documents lightweight high-precision checks of the Year Landweber UNI/OPT, Showalter UNI and Nesterov UNI witnesses, separate HBF/SOAR stability-premise checks, and a full Year/Landweber reconstruction from hash-verified official raw data.

```bash
python -B evidence/experiment5/tail_diagnostics/verify_witnesses.py
python -B evidence/experiment5/tail_diagnostics/verify_stability.py
```

After review-data installation, the lightweight checks use the compact supplied inputs and require `mpmath==1.3.0`; no raw-data download is needed. The guide states the assumptions and limits of each check. The tail examples explain why finite-repetition means need not represent the full conditional MSE; they do not establish a complete MSE ordering among sampling rules.

## Earlier analyses

Earlier one-sided and two-sided/Holm analyses are documented in the [complete previous version](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4); they are not the inferential basis of the current V report. `reanalyze.py` remains in the core; `reference/` is restored from the data archive because the current saved-record workflow uses its reference checksums and the archive-verification code. Use the empirical workflow above for the current results.

## Relation to full reproduction

Use the root `run.py` for obtaining official data and running or analyzing new experiments. `run.py analyze --experiment 5 --results runs/formal_v --output runs/formal_v_analysis` now generates empirical summaries and figures; it does not automatically run the historical mean-based tests.

For a full run with `--output runs/formal_v`, Experiment V metrics are written under `runs/formal_v/exp5/formal/`. Analysis with `--output runs/formal_v_analysis` writes reports under `runs/formal_v_analysis/exp5/`. The saved-record commands above write directly to their specified output directories. The preserved historical script's original full-project paths are supplied by its archive wrapper and are not required for the current empirical workflow.

[Chinese guide](README_CN.md) · [Repository reproduction guide](../../README.md)