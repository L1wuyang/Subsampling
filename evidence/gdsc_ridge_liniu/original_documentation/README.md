# Experiment V addendum: GDSC Ridge Li-Niu score comparison

Six unchanged budgets, 30 common-uniform draws per budget, 180 new LN_floor records and 720 preserved UNI/NORM/LEV/OPT records. All 180 streams exactly match the saved stable-V uniforms and seed 202610310501. The existing data, preprocessing, split, alpha=17737, full coefficient target and four probability rules remain unchanged.

Both scores use the exact common constraint pi_j=max(0.01/p,tau*s_j). This is an oracle-score comparison, not NOPL or the original outer iteration. All budgets are descriptive; paired pointwise t29 Monte Carlo intervals are conditional on the single fixed training set. There is no new primary test, population inference or simultaneous interval claim.

At N=2996 LN_floor/OPT mean errors are 0.02879534/0.02857425, a 0.768% lower observed OPT mean. OPT-LN=-0.00022109, pointwise 95% interval [-0.00125154,0.00080936]. OPT has higher observed means at N=374 and N=749 (5.34% and 3.14%). All six paired intervals include zero; equivalence is not established.

The probability total-variation distance is 0.03119715; the deterministic complete-coefficient first-order criterion decreases by 0.646970% under OPT. This case does not demonstrate a clear empirical finite-budget improvement over LN_floor. The original 78/78 statement applies only to UNI/NORM/LEV/OPT, excluding this new rule.

All 180 new states pass explicit-coefficient, Gram and QR-coordinate checks; normalized solve residuals are at most 5.35e-17. A separate analysis recomputes 30 summary cells and six paired intervals, preserves all 720 baseline records, and verifies all 180 new states with original inputs. Prediction outcomes are secondary and the previously explored test split is descriptive. No additional tuning or cost experiment was performed.

See paired_comparisons.csv for every budget, summary.csv for all five rules, comparison_metrics.csv for all 900 records, and independent_validation.json for the verification scope.

[中文说明](README_CN.md) · [Reproduction](../../../Experiments/experiment5_gdsc_liniu_20261101/README_CN.md)
