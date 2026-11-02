# Ridge column sampling: Li–Niu and full-coefficient scores

[中文说明](README_CN.md) · [Saved evidence](../../evidence/ridge_liniu/README.md) · [Results and interpretation](../../docs/LATEST_RESULTS.md)

Protocol `ridge-LN-floor-ablation-20261101-v1` reuses all 40 Experiment I inputs (`n=60, p=1200`). It compares UNI/NORM/LEV/LN_floor/FULL_OPT at 13 budgets with 40 paired draws, giving 104,000 scalar records. The sole primary comparison is FULL_OPT minus LN_floor at N=150, with inference across 40 data-set means.

Let `H=X X^T`, `alpha=trace(H)/60`, `K=(H+alpha I)^(-1)` and `beta=X^T K y`. The compared scores for column `a_j` are:

```text
s_LN[j]   = abs(beta[j]) * norm(a_j)
s_FULL[j] = abs(beta[j]) * norm(X^T K a_j)
pi[j]     = max(0.01/p, tau * s[j])
```

Choose tau so probabilities sum to one; all-zero scores use the uniform rule. Both target-dependent scores use the same exact floor. This is an oracle-score ablation on reused inputs, not new-data independent confirmation or an evaluation of NOPL/outer iteration.

## Check saved results

```text
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

This verifies evidence hashes and recomputes scalar summaries, pointwise intervals, calibration and the primary comparison. The original quadratic-form state checks are recorded separately; trajectory arrays are not bundled.

## Full rerun

Install the root pinned requirements. Run from the repository root and use new output directories:

```text
python run.py review-data download
python run.py simulation-data verify --experiment 1
python -B Experiments/ridge_liniu_ablation_20261101/pilot.py --repo . --output runs/ridge_ln/pilot
python -B Experiments/ridge_liniu_ablation_20261101/run_experiment.py prepare --repo . --output runs/ridge_ln/prepared
python -B Experiments/ridge_liniu_ablation_20261101/run_experiment.py run --prepared runs/ridge_ln/prepared --output runs/ridge_ln/formal --pilot runs/ridge_ln/pilot/pilot.json --workers 2
```

The archive restores the 40 frozen inputs; see the [simulation guide](../../docs/SIMULATION_DATA.md) for offline installation. Preparation fixes targets/probabilities and source hashes. The pilot checks derivatives, probability constraints, sampling weights and coefficient recovery. Formal execution saves all five states and the common uniforms, then runs independent state-based analysis. Completed tasks can be reused only when their identity and hashes match.

Stable V is not required for this calculation. The original `release_gate` in the scientific protocol records the author's historical scheduling; the current portable runner defaults to a standalone release gate. To intentionally retain that schedule, add `--predecessor /path/to/completed-stable-v`. That option enforces the old protocol/status/validation/report checks. `queue_after_v.py` is an optional waiting wrapper, not part of the standalone reproduction path.

All budgets and raw interval endpoints remain in the summaries. Log plots omit nonpositive lower endpoints and state that convention; nonsignificance does not establish equivalence.
