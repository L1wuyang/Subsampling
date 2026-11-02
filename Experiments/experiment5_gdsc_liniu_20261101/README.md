# GDSC Ridge Li–Niu score comparison

[中文说明](README_CN.md) · [Saved evidence](../../evidence/gdsc_ridge_liniu/README.md) · [Results and interpretation](../../docs/LATEST_RESULTS.md)

Protocol `experiment-V-GDSC-ridge-LN-floor-20261101-v1` adds 180 LN_floor solves to the fixed stable-V GDSC Ridge study. The 720 original four-rule records, targets, probabilities, data split and preprocessing remain unchanged. Six budgets use 30 common-uniform paired draws each.

## Check saved scalars and states

After installing the root pinned requirements, run from the repository root:

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_scalar_check.json
```

This recomputes 30 scalar means and six paired intervals without raw data or additional estimator solves. To verify all 180 bundled new states, uniforms and counts against the original preprocessed input, add `--input-root runs/historical_v/exp5/inputs` after preparing those inputs as described below. A scalar-only run does not perform the input-dependent state checks.

## Rerun the new sampling

First complete the [stable-V full rerun](../experiment5_support_stable_20261031/README.md). Its commands provide the exact preprocessed inputs and complete stable-V output, including `draws/gdsc/*.npz` and full `targets/`. The compact evidence and old review-data ZIP do not contain all those arrays.

Using the paths from that guide and a new output directory:

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/run.py --input-root runs/historical_v/exp5/inputs --stable-root runs/stable_v/formal_01 --output runs/gdsc_ln_new --workers 4
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root runs/gdsc_ln_new --stable-root runs/stable_v/formal_01 --input-root runs/historical_v/exp5/inputs --report runs/gdsc_ln_new_check.json
```

The runner checks input/target hashes and the analytic OPT quantities, seals probabilities/sources, and reuses the stable-V common uniforms. Both target-dependent scores use the exact constraint `pi_j=max(0.01/p,tau*s_j)`, with `alpha=17737`. All six budgets are fixed; reversals and all outcomes are retained.

The comparison is descriptive conditional on one fixed training set. Intervals are pointwise t29 Monte Carlo intervals. It is an oracle-score comparison and does not evaluate NOPL/outer iteration, population predictive superiority or end-to-end speedup. Original source snapshots and provenance receipts retain the earlier run's bytes; these current guides describe the portable submission workflow.
