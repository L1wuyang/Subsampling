# Paper figure and table map: November 1, 2026

[中文说明](PAPER_RESULTS_CN.md) - [Repository guide](../README.md)

The manuscript reports full-support stable Experiment V and the Ridge score comparisons. Earlier release v2026.10.30.2 supplies I-IV review data and historical V only. References below use LaTeX labels/assets because figure and table numbers may change after inserting the new ablation.

## Commands and scope

```text
python run.py verify
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/paper_saved_metrics
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

C0 below denotes core/review-data/simulation verification. C1 is the saved I-IV summarization command. C3 means inspecting the named original CSV/JSON (for example with pandas); R means executing the frozen experiment and its formal analysis. None of C0/C1/C3 runs trajectories. Install old review data for I-IV; the two new saved-metric analyses need only the bundled compact evidence.

Convenience I-IV summaries weight datasets equally and do not replace III/IV's first-dataset figures. New analyses verify copied source hashes and recompute every reported scalar mean, corresponding interval/calibration and the sole Ridge primary inference. They do not repeat the original independent state-array checks. The six matching manuscript assets and their figure-generation script are included in this repository. Convenience plotting outputs here need not share its final layout.

## Latest manuscript figures

| Label / manuscript asset | Exact numerical source and selection | Reproduction and interpretation |
| --- | --- | --- |
| `fig:real_column_fixed` / `r5_01_gdsc_target.pdf` | `evidence/experiment5_stable/summary.csv`, dataset=gdsc; `mean`, 30 repetitions at each method/rule/budget; the Ridge LN_floor series additionally comes from `evidence/gdsc_ridge_liniu/summary.csv` | Stable saved analysis produces matching means and a convenience layout; NORM=UNI, no mean-confidence bands. |
| `fig:real_row_fixed` / `r5_02_year_target.pdf` | Same source, dataset=year; `mean`, 50 repetitions | Stable analysis; finite-repetition means, not a proved complete-MSE ordering. |
| `fig:real_native_prediction` / `r5_04_prediction.pdf` | Stable summary `test_rmse`, plus GDSC Ridge LN_floor from the addendum summary; `targets/<dataset>/<method>/summary.json` - `full.response_test_rmse` | Stable analysis exports convenience prediction curves and `full_prediction_reference.csv`. Mean individual RMSE is not sqrt(mean MSE). |
| Ridge score-ablation figure / `r1_04_ridge_liniu.pdf` | `evidence/ridge_liniu/summary.csv`; paired dataset differences from `dataset_means.csv`, FULL_OPT-LN_floor | Full five-rule curves, pointwise t39 intervals and paired differences retain all budgets and reversals. Convenience output `ridge_liniu_comparison.pdf` has a different panel layout. |
| Ridge calibration / `r1_05_ridge_liniu_calibration.pdf` | Ridge summary `calibration`, LN_floor/FULL_OPT, all 13 budgets | Empirical mean divided by first-order prediction; approximately 1.58 at N=30 and 1.12 at N=600. Not an exact finite-sample formula. |

## Latest supplementary tables and protocol evidence

| Label / result | Exact source and selection | Scope |
| --- | --- | --- |
| `tab:rd_min_parameters` | Stable `candidate_bounds.json`, `support_gate.json`, `targets/<dataset>/<method>/summary.json` and new protocol; steps also in `metrics.csv` `prescribed_steps` | Replace the older L=32 infinity-norm numerical parameters. Preserve 48 full-support gate checks and fresh seed 202610310501. |
| `tab:real_calibration` | Stable summary: C=`budget * theoretical`; OPT/UNI and OPT/LEV C ratios; `empirical_to_first_order` at smallest/largest budgets | GDSC 75/2996, Year 500/50000. Do not substitute historical V constants for recomputed methods. |
| `tab:real_prediction_compact` | Stable summary `test_rmse`, GDSC N=2996 / Year N=50000; matched full references in target summaries | Includes four rules, including GDSC UNI/NORM duplication; previously explored test splits are descriptive. |
| Ridge unique primary comparison | Ridge `primary_comparison.json`, N=150; `summary.csv` mean by rule | FULL-LN=-0.0003228063, t39 95% CI [-0.0009423789,0.0002967663], two-sided p=.298436, 26/40 datasets lower. |
| Ridge score diagnostics | Ridge `score_diagnostics.csv`, one record per dataset/rule | Probability TV mean .002990; deterministic coefficient-objective reduction .006058% on average. LN_floor includes the common exact floor. |

## Unchanged I-IV main figures

| Paper figure / manuscript asset | Numerical input and selection | Command and output | Scope |
| --- | --- | --- | --- |
| Fig. 1, `fig:v7_probability_column`; `01_target_approximation.pdf` | T1 `summary_curves.csv`, `metric=relative_gap`; 40 dataset means, 13 budgets, six methods, four rules. Fields `mean,ci_low,ci_high`. | C0/C1; convenience `exp1/figures/relative_gap.png`. R for I also generates `01_target_approximation.*`. | The 312 means and pointwise intervals are in the released table. Final paper layout is a manuscript asset. |
| Fig. 2, `fig:v7_probability_row`; `r2_01_target_approximation.pdf` | T2 `summary_curves.csv`, `metric=relative_gap`; same aggregation as Fig. 1. | C0/C1; convenience `exp2/figures/relative_gap.png`. R for II generates `01_target_approximation.*` within its own analysis directory. | 312 means and intervals; final layout not exported by C1. |
| Fig. 3, `fig:v7_absolute_mse`; `r3_01_mse_absolute_compact.pdf` | T3 `mse_summary.csv`, `arm=main,data_id=1`; `mean,low95,high95,theory=C/budget`, both directions. Each point uses 500 sketches. | C0/C1; inspect saved table with C3. R for III exports `exp3/figures/01_mse_absolute_compact.*` and `mse_summary.csv`. | 156 empirical means plus first-order curves and intervals. Do not substitute the C1 plot averaged over datasets. |
| Fig. 4, `fig:v7_ls_gap`; `r4_01_scaled_gap.pdf` | T4 `gap_summary.csv`, `arm=main,data_id=1`; `mean,lower,upper`. Mean is **already** N times squared gap; 100 sketches per point. | C0/C1/C3; R for IV exports `exp4/figures/01_scaled_gap.*` and `gap_summary.csv`. | 156 means; only intervals with positive lower endpoints are drawn on logarithmic axes. Retain high-budget Nesterov resolution annotations from H.2. |

## Unchanged I-IV supplementary figures

| Figure | Source | Command | Scope |
| --- | --- | --- | --- |
| Fig. E.1, `fig:native_coef`; `03_true_coefficient_risk.pdf` | T1 `summary_curves.csv`, `metric=true_coef_rel_sq`; `mean,ci_low,ci_high`, plus unit zero-predictor reference. | C0/C1; convenience `exp1/figures/true_coef_rel_sq.png`. R for I generates `03_true_coefficient_risk.*`. | 312 means and intervals across 40 dataset means. Paper uses a linear risk axis; convenience styling differs. |
| Fig. F.1, `fig:row_native_coef`; `r2_03_true_coefficient_risk.pdf` | T2 `summary_curves.csv`, same metric/fields as E.1. | C0/C1; convenience `exp2/figures/true_coef_rel_sq.png`. R for II generates `03_true_coefficient_risk.*`. | Same scope as E.1. Population-relative signal risk equals coefficient risk in this design. |
| Fig. G.1, `fig:v7_mse_ratio`; `r3_02_mse_ratio.pdf` | T3 `mse_summary.csv`, `arm=main,data_id=1`; `ratio,ratio_low95,ratio_high95` and unit line. | C0/C3; R for III exports `exp3/figures/02_mse_ratio.*`. | 156 ratios and conditional intervals. C1 does not export this ratio figure. |

## Unchanged I-IV supplementary tables

| Table | Source and selection | Interpretation |
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

`Tn` denotes `simulations/experimentn/tables/`. Original V witnesses and Holm analyses remain at `evidence/experiment5/` as historical evidence; their parameters and means are not the current stable-run results. New scalar reanalysis does not reconstruct every historical trajectory array, establish independent-data confirmation or add a speedup claim.

## Exact manuscript figure assets

The six matching manuscript PDF assets are in [`evidence/paper_figures_20261101/`](../evidence/paper_figures_20261101/). `figure_receipt.json` fixes source-table and PDF hashes. Regenerate their journal layouts from bundled tables:

```text
python -B tools/make_review_paper_figures.py --evidence-root evidence --output runs/paper_figures --qa-output runs/paper_figure_qa --receipt runs/paper_figure_receipt.json
```

This script reads summary tables and matched full-target JSON only; it performs no estimator updates. Regenerated PDF metadata may differ by rendering time/environment; copied final assets are the exact reviewed files. The separate saved-metric tool above checks the summaries against the full scalar records before plotting convenience figures.

## GDSC Ridge Li-Niu addendum / 实验五新增对照

`fig:real_column_fixed` (`r5_01_gdsc_target.pdf`) and `fig:real_native_prediction` (`r5_04_prediction.pdf`) additionally use `evidence/gdsc_ridge_liniu/summary.csv`, rule=LN_floor, for the GDSC Ridge panel only. Other methods and Year are unchanged.

New supplement `fig:gdsc_liniu` / `r5_05_gdsc_liniu.pdf` reads all 30 five-rule cells and `paired_comparisons.csv`; `tab:gdsc_liniu_budgets` contains all six paired results. Intervals are pointwise t29 Monte Carlo intervals across 30 common-uniform sketches of one fixed dataset, rather than t39 intervals across simulated datasets. All new budgets are descriptive. At N=2996 LN_floor/OPT errors are .02879534/.02857425; at N=374/749 OPT is higher. The 78/78 claim applies only to the original four rules.

Saved scalar reanalysis (no additional estimator solves):

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_check.json
```
