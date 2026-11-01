# Reported results: November 1, 2026

[中文详细数值与解释](LATEST_RESULTS_CN.md) · [Figure/table map](PAPER_RESULTS.md)

Stable V completed 530 sketch tasks and 12,720 metric records; all 48 full-support stability gates passed. Among UNI/NORM/LEV/OPT, OPT has the lowest observed mean in 78/78 dataset/method/budget cells. At maximum budgets GDSC 2996 and Year 50000, OPT empirical/first-order ratios span approximately 0.969 to 1.179. Reductions against the best baseline range from 34.27% to 36.65% on GDSC and 51.06% to 58.89% on Year. These finite-repetition observations do not prove complete finite-budget conditional-MSE ordering.

The Ridge ablation reuses all 40 existing Experiment I inputs, with 13 budgets, 40 paired sketches and five rules (104,000 complete records). At the sole primary N=150, UNI/NORM/LEV/LN_floor/FULL_OPT mean errors are .46852476/.11064956/.11647983/.07697390/.07665110. FULL minus LN = -.0003228063263, t39 95% CI [-.0009423789104,.0002967662577], two-sided p=.2984364561. FULL is lower on 26/40 datasets, reducing the ratio of means by about .419%. No significant difference was detected; equivalence was not proved. The inferential units are 40 dataset means.

Probability total-variation distance has mean .002990 and range [.002291,.004290]. FULL's deterministic first-order complete-coefficient objective decreases by only .006058% on average, range [.003262%,.011598%]. Thus the resulting probability vectors and criteria are already close under the fixed regularization calibration, consistently with the empirical curves. FULL minimizes a first-order criterion, rather than every finite-sketch error.

Other budgets and baselines are descriptive, retaining reversals, pointwise intervals and tail outcomes. Calibration decreases from about 1.58 at N=30 to 1.12 at N=600; it is not an exact finite-sample formula. LN_floor uses the same exact probability-floor constraint as FULL_OPT; NOPL and the original outer iteration are not evaluated. Reused inputs do not provide new-data independent confirmation. End-to-end costs were not measured, and no speedup is claimed.

Errors here are relative squared coefficient deviations from fixed full-data regularized numerical targets, separate from true-coefficient recovery or prediction. New scientific protocols version changes separately from frozen historical sources. These results are bundled in the current repository; the earlier release remains the archive for I-IV review data and historical V.


## Experiment V addendum: GDSC Ridge Li-Niu score comparison

Six unchanged budgets, 30 common-uniform draws per budget, 180 new LN_floor records and 720 preserved UNI/NORM/LEV/OPT records. All 180 streams exactly match the saved stable-V uniforms and seed 202610310501. The existing data, preprocessing, split, alpha=17737, full coefficient target and four probability rules remain unchanged.

Both scores use the exact common constraint pi_j=max(0.01/p,tau*s_j). This is an oracle-score comparison, not NOPL or the original outer iteration. All budgets are descriptive; paired pointwise t29 Monte Carlo intervals are conditional on the single fixed training set. There is no new primary test, population inference or simultaneous interval claim.

At N=2996 LN_floor/OPT mean errors are 0.02879534/0.02857425, a 0.768% lower observed OPT mean. OPT-LN=-0.00022109, pointwise 95% interval [-0.00125154,0.00080936]. OPT has higher observed means at N=374 and N=749 (5.34% and 3.14%). All six paired intervals include zero; equivalence is not established.

The probability total-variation distance is 0.03119715; the deterministic complete-coefficient first-order criterion decreases by 0.646970% under OPT. This case does not demonstrate a clear empirical finite-budget improvement over LN_floor. The original 78/78 statement applies only to UNI/NORM/LEV/OPT, excluding this new rule.

All 180 new states pass explicit-coefficient, Gram and QR-coordinate checks; normalized solve residuals are at most 5.35e-17. A separate analysis recomputes 30 summary cells and six paired intervals, preserves all 720 baseline records, and verifies all 180 new states with original inputs. Prediction outcomes are secondary and the previously explored test split is descriptive. No additional tuning or cost experiment was performed. The complete saved records and verification receipts accompany this repository.

See paired_comparisons.csv for every budget, summary.csv for all five rules, comparison_metrics.csv for all 900 records, and independent_validation.json for the verification scope.
