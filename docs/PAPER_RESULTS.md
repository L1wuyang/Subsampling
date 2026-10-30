# Paper figures and numerical tables

[中文对照](PAPER_RESULTS_CN.md) · [Repository guide](../README.md) · [Simulation data](SIMULATION_DATA.md) · [Experiment V evidence](../evidence/experiment5/README.md)

This guide maps the current manuscript's six figures and the supplement's four figures and thirteen tables to the released evidence. Figure/table numbers are accompanied by LaTeX labels or asset names so that the mapping remains usable if pagination changes. Paths below are relative to the repository root, except `figures/*.pdf`, which identifies an asset in the manuscript source package. The manuscript sources and their final layout assets are not bundled here.

## What each workflow reproduces

- **Saved numerical evidence:** I–IV metric shards, reported CSV tables, protocols and verification reports are released. They allow the reported numbers and statistical units to be checked without rerunning trajectories.
- **Convenience summaries:** `simulation-data summarize` creates dataset means, equally weighted summaries across datasets and simple PNG plots. It does not export the manuscript's final figures, their confidence bands or LaTeX tables. In particular, the paper's primary III/IV figures use `data_id=1`; the convenience plots aggregate datasets.
- **Current V target figures:** `evidence/experiment5/empirical.py` reads the saved records and reproduces the two current target-error figures against `paper_plot_reference.json`, including 276 plotted means and panel limits. It generates PDF/SVG/PNG, with no mean-confidence bands. This is a figure-specific reproduction path; it does not rerun model fitting. PDF byte identity is not asserted across rendering environments.
- **Other final figure layouts:** the numerical sources are identified below, but the final manuscript layout exporter for I–IV and the V prediction figure is not included. The formal-run analyzers generate corresponding scientific plots with different layout/labels; renaming those files does not establish identity with the submitted artwork.

## Commands, inputs and outputs

Run from the repository root after installing `requirements-lock.txt`. Use a fresh output directory for each command that writes results.

**C0 — verify released files and saved evidence; no trajectories.**

```bash
python run.py verify
python run.py simulation-data verify --experiment all
python evidence/experiment5/reanalyze.py --verify
```

These commands check the package manifest, I–IV file hashes/record schemas/counts, and the V evidence archive. Verification preserves the distinction between checking stored evidence and independently regenerating it.

**C1 — recompute I–IV convenience summaries from saved metric shards.**

```bash
python run.py simulation-data summarize --experiment all --output runs/paper_saved_metrics
```

Inputs: `simulations/experimentN/records/*.csv.gz` and `simulations/manifest.json`. Outputs: `runs/paper_saved_metrics/verification.json`, `summary_manifest.json`, and `expN/{dataset_means.csv,equal_dataset_summary.csv,record_status_counts.csv,figures/}`. The figure names are metric names, such as `relative_gap.png`, `true_coef_rel_sq.png` and `scaled_squared_gap.png`. Means first average repetitions within a dataset; the second table weights datasets equally. C1 does not recompute the archived hypothesis tests or the complete III state-dependent analysis.

**C2 — reproduce current V empirical results and target figures from saved records.**

```bash
python -B evidence/experiment5/empirical.py --output runs/paper_v
```

Inputs: `evidence/experiment5/saved_records.tar.gz`, its manifest and `paper_plot_reference.json`. Outputs include `summary.csv`, `full_prediction_reference.csv`, `rankings.json`, `figure_validation.json`, `auxiliary_figure_validation.json`, `saved_evidence_verification.json`, two `r5_*_target_plotted_points.csv` files and `figures/`. `summary.csv` retains all four rules; only the redundant GDSC NORM curve is hidden. The auxiliary `figures/04_prediction.{pdf,svg,png}` reproduces prediction means and matching full-model references, with a different layout from the manuscript asset.

**C3 — inspect a released table, without rerunning an analysis.**

For example, this prints the values behind Supplementary Table G.1; substitute the CSV and selection given in the mapping below for other tables:

```bash
python -c "import pandas as pd; t=pd.read_csv('simulations/experiment3/tables/robustness_summary.csv'); print(t.loc[t.budget.eq(19200)].to_string(index=False))"
```

The output is the selected stored table on standard output. C0 verifies its provenance and integrity. C1 provides a separate check of underlying scalar means; neither command is an automatic paper-table exporter.

**R — regenerate numerical trajectories, then analyze a complete new run.**

For example, for Experiment III:

```bash
python run.py formal --experiment 3 --output runs/new_iii --workers 2
python run.py analyze --experiment 3 --results runs/new_iii --output runs/new_iii_analysis
```

Replace `3` and the output directories for other experiments. V additionally requires the official raw data described in [DATA_SOURCES.md](DATA_SOURCES.md). Formal runs can be expensive. `smoke` checks execution with reduced settings and is not paper evidence. Analysis reads complete newly generated directories, not just the released metric shards. I/II analysis is under `expN/outputs/formal_01/`; III–V analysis is under `expN/`. III analysis additionally needs saved states for its squared mean-error component; IV replay needs states and sampling counts. The release does not bundle all these trajectory-level arrays. Native legacy `paper`, `render`, `package` or `verify` subcommands are not a supported shortcut: some reference unbundled delivery/verification modules.

## Main-text figures

`Tn` below means `simulations/experimentn/tables/`. All I–IV table inputs can be verified by C0, and their underlying scalar records summarized by C1.

| Paper figure / manuscript asset | Numerical input and selection | Command and output | Reproduction scope |
| --- | --- | --- | --- |
| Fig. 1, `fig:v7_probability_column`; `01_target_approximation.pdf` | T1 `summary_curves.csv`, `metric=relative_gap`; 40 dataset means, 13 budgets, six methods, four rules. Fields `mean,ci_low,ci_high`. | C0/C1; convenience `exp1/figures/relative_gap.png`. R for I also generates `01_target_approximation.*`. | The 312 means and pointwise intervals are in the released table. Final paper layout is a manuscript asset. |
| Fig. 2, `fig:v7_probability_row`; `r2_01_target_approximation.pdf` | T2 `summary_curves.csv`, `metric=relative_gap`; same aggregation as Fig. 1. | C0/C1; convenience `exp2/figures/relative_gap.png`. R for II generates `01_target_approximation.*` within its own analysis directory. | 312 means and intervals; final layout not exported by C1. |
| Fig. 3, `fig:v7_absolute_mse`; `r3_01_mse_absolute_compact.pdf` | T3 `mse_summary.csv`, `arm=main,data_id=1`; `mean,low95,high95,theory=C/budget`, both directions. Each point uses 500 sketches. | C0/C1; inspect saved table with C3. R for III exports `exp3/figures/01_mse_absolute_compact.*` and `mse_summary.csv`. | 156 empirical means plus first-order curves and intervals. Do not substitute the C1 plot averaged over datasets. |
| Fig. 4, `fig:v7_ls_gap`; `r4_01_scaled_gap.pdf` | T4 `gap_summary.csv`, `arm=main,data_id=1`; `mean,lower,upper`. Mean is **already** N times squared gap; 100 sketches per point. | C0/C1/C3; R for IV exports `exp4/figures/01_scaled_gap.*` and `gap_summary.csv`. | 156 means; only intervals with positive lower endpoints are drawn on logarithmic axes. Retain high-budget Nesterov resolution annotations from H.2. |
| Fig. 5, `fig:real_column_fixed`; `r5_01_gdsc_target.pdf` | V saved draw records, `dataset=gdsc`; `relative_coefficient_error`, 30 repeats. | C2 → `figures/r5_01_gdsc_target.{pdf,svg,png}` and `r5_01_gdsc_target_plotted_points.csv`. | Current figure-specific export: 108 visible means; GDSC NORM=UNI; no mean-confidence band. |
| Fig. 6, `fig:real_row_fixed`; `r5_02_year_target.pdf` | V saved draw records, `dataset=year`; `relative_coefficient_error`, 50 repeats. | C2 → `figures/r5_02_year_target.{pdf,svg,png}` and `r5_02_year_target_plotted_points.csv`. | Current figure-specific export: 168 visible means; no mean-confidence band. |

## Supplementary figures

| Paper figure / manuscript asset | Numerical input and selection | Command and output | Reproduction scope |
| --- | --- | --- | --- |
| Fig. E.1, `fig:native_coef`; `03_true_coefficient_risk.pdf` | T1 `summary_curves.csv`, `metric=true_coef_rel_sq`; `mean,ci_low,ci_high`, plus unit zero-predictor reference. | C0/C1; convenience `exp1/figures/true_coef_rel_sq.png`. R for I generates `03_true_coefficient_risk.*`. | 312 means and intervals across 40 dataset means. Paper uses a linear risk axis; convenience styling differs. |
| Fig. F.1, `fig:row_native_coef`; `r2_03_true_coefficient_risk.pdf` | T2 `summary_curves.csv`, same metric/fields as E.1. | C0/C1; convenience `exp2/figures/true_coef_rel_sq.png`. R for II generates `03_true_coefficient_risk.*`. | Same scope as E.1. Population-relative signal risk equals coefficient risk in this design. |
| Fig. G.1, `fig:v7_mse_ratio`; `r3_02_mse_ratio.pdf` | T3 `mse_summary.csv`, `arm=main,data_id=1`; `ratio,ratio_low95,ratio_high95` and unit line. | C0/C3; R for III exports `exp3/figures/02_mse_ratio.*`. | 156 ratios and conditional intervals. C1 does not export this ratio figure. |
| Fig. I.1, `fig:real_native_prediction`; `r5_04_prediction.pdf` | V draw `test_response_rmse` and 12 target summaries' `full.response_test_rmse`. | C2 → `summary.csv`, `full_prediction_reference.csv`, `figures/04_prediction.*`. | Same prediction means/full references; paper's compact layout is not exported. Mean individual RMSE is not square root of mean MSE. |

## Supplementary numerical and protocol tables

For stored CSV/JSON tables, C0 verifies the released file and C3 illustrates inspection; values are rounded only for typesetting. No command here claims to regenerate the LaTeX table automatically.

| Table / LaTeX label | Released source and exact selection | Command/output and interpretation |
| --- | --- | --- |
| D.1 `tab:native_shared_defaults` | I–III `metadata/protocol.json` and `Experiments/experiment5_native_realdata_20261025/formal_protocol.json`; numerical update definitions in the frozen sources. | C0, then inspect protocols. This is the fixed-horizon construction/parameter-definition table, not a Monte Carlo table. Choose the positive HBF root. Analytical definitions/proofs are not generated by experiments. |
| E.1 `tab:native_primary` | T1 `summary_curves.csv`, `metric=relative_gap,budget=150,rule=OPT`, supplies the OPT mean. T1 `primary_comparisons.csv` supplies `ratio` for baselines UNI/NORM/LEV at that prespecified budget. | C0/C3; R for I regenerates analysis tables. Average the 40 dataset means, not a different pooled population. |
| E.2 `tab:native_risks` | T1 `risk_r600.csv`, `rule=OPT`: `relative_gap,true_coef_rel_sq,design_signal_rel_sq,population_signal_rel_sq`; matching full-target `true_coef_rel_sq` from T1 `full_reference.csv`, averaged over datasets. | C0/C3; keep the target-gap, coefficient, design and population denominators distinct. |
| F.1 `tab:row_native_primary` | T2 `summary_curves.csv` and `primary_comparisons.csv`, N=150; same selections and fields as E.1. | C0/C3; R for II regenerates analysis tables. |
| F.2 `tab:row_native_risks` | T2 `risk_r600.csv`, `rule=OPT`, plus T2 `full_reference.csv`. | C0/C3; same target-gap/coefficient/design fields as E.2, but the final paper column is `population_response_mse` (future response MSE), not population signal risk. |
| G.1 `tab:v7_robustness` | T3 `robustness_summary.csv`, `budget=19200`; `median,minimum,maximum`, grouped by direction/method. | C0/C3; each group contains 20 dataset ratios. Min–max is observed variation, not a confidence interval. |
| G.2 `tab:v7_decomposition` | T3 `endpoint_decomposition.csv`, `budget=38400,arm=main,data_id=1`; `ratio,linear_ratio,remainder_ratio,cross_ratio`. | C0/C3. Check total = linear + remainder + signed cross; 500 draws per entry. |
| H.1 `tab:exp4_endpoints` | T4 `endpoint_comparison.csv`; `at_1200,at_38400,endpoint_ratio`. | C0/C3. Cross-check T4 `gap_summary.csv`, `arm=main,data_id=1`. Preserve the resolution qualification for Nesterov. |
| H.2 `tab:exp4_replay` | `simulations/experiment4/metadata/verification.json`, `dense_native_replays`, select `budget=38400`; `relative_coefficient_difference,replay_change_over_gap`. | C0 and JSON inspection: ten saved rows, five methods × two directions, replicate 0. `diagnostics/resolution_report.json` separately records the two Nesterov warnings. The current root IV diagnostic command replays selected Nesterov cases; it is not a full ten-row table regenerator. |
| H.3 `tab:exp4_tails` | T4 `gap_summary.csv`, `arm=tails,budget=60`; `mean,median,maximum,top_one_percent_share`. | C0/C3; six groups, 1,000 sketches each. The final field is a share (0–1), not a count or already-multiplied percentage. |
| I.1 `tab:rd_min_parameters` | V archived `formal_01/protocol.json`, draw `prescribed_steps`, and target summaries' `c`; frozen target-construction code. Additional Year values: `evidence/experiment5/tail_diagnostics/reference/diagnosis.json` and `witness_inputs.json`. | C0; inspect the archive with Python `tarfile` (prefix below). Protocols and recorded step counts can be checked without fitting. The scalar archive does **not** include a complete original per-method target-parameter array set; reconstructing all exact step sizes/endpoints requires the official-data workflow. Do not treat rounded paper values as those full-precision inputs. |
| I.2 `tab:real_calibration` | C2 `summary.csv`: `first_order_relative_value`, `empirical_to_first_order`; original target summaries also contain `constants`. | C2. For any fixed budget, set C = `budget * first_order_relative_value`, compute OPT/UNI and OPT/LEV, and take OPT K at min/max budgets (GDSC 75/2996; Year 500/50000). This compares observed means with a first-order value. |
| I.3 `tab:real_prediction_compact` | C2 `summary.csv`, GDSC N=2996 and Year N=50000, `test_response_rmse_mean`; `full_prediction_reference.csv`, `matched_full_test_rmse`. | C2; retain all four rules in the table, including GDSC NORM/UNI duplicate. These are descriptive comparisons on previously explored test sets. |

Inside `saved_records.tar.gz`, the V run prefix is `Experiments/experiment5_native_realdata_20261025/outputs/formal_01/`; below it are `draws/<dataset>/r<budget>_rep<index>.csv`, `targets/<dataset>/<method>/summary.json` and `protocol.json`. Reading these archive members does not require extraction or raw-data download. The archive manifest lists every member and checksum.

## Limits that matter when checking the paper

The I–IV primary numerical tables and original draw metrics are available, but a single command exporting all submitted figures/tables with identical typography is not. Use the explicit selections above; do not substitute equal-dataset means for the first-dataset plots, discard failed/tail observations, reinterpret undefined zero-response relative errors, or call a reduced smoke run a formal replication. For tail witnesses and their input-reconstruction limits, use the [portable diagnostics guide](../evidence/experiment5/tail_diagnostics/README.md). None of the saved-metric checks reconstructs missing historical trajectory arrays or adds a new scientific conclusion.
