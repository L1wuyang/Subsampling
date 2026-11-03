# Ridge column score ablation

Reported results, November 1, 2026; bundled in the current repository, separately from the earlier v2026.10.30.2 review-data archive. This oracle-score ablation reuses all 40 stored Experiment I main-arm inputs (`n=60,p=1200`), fixes `alpha=trace(XX^T)/60`, and uses 13 budgets and 40 paired sketches per dataset/budget. Five rules share fresh uniforms with seed 202611010301. The protocol is `ridge-LN-floor-ablation-20261101-v1`.

With `H=XX^T`, `K=(H+alpha I)^(-1)` and full Ridge beta, the Li–Niu score is `abs(beta_j) ||a_j||`; the complete coefficient score is `abs(beta_j) ||X^T K a_j||`. LN_floor and FULL_OPT use the exact common lower-bound allocation `pi_j=max(.01/p,tau*score_j)`. NORM and LEV use a .01 uniform mixture. The label LN_floor identifies the floor adaptation; the experiment does not implement NOPL or the original outer iteration.

All 104,000 records are retained with no numerical failures. At the sole prespecified primary budget N=150, mean relative squared coefficient gaps are UNI 0.46852476, NORM 0.11064956, LEV 0.11647983, LN_floor 0.07697390 and FULL_OPT 0.07665110. FULL−LN equals −0.0003228063 with t39 95% CI [−0.0009423789, 0.0002967663] and two-sided p=0.298436. FULL is lower on 26/40 datasets; its ratio of means is 0.9958063. No significant difference was detected; equivalence was not established. Dataset means, rather than 1,600 individual sketches, are the inferential units.

Mean probability total-variation distance is 0.002990. FULL's deterministic first-order coefficient criterion improves by only 0.006058% on average. The resulting probability vectors and criteria are already close at this calibration, consistently with the overlapping empirical curves. Full first-order oracle optimality does not require lower error on every finite sketch. Other budgets, baselines and pointwise intervals are descriptive; reversals and tail records remain. Reused inputs do not provide independent-data confirmation, and no end-to-end speedup is reported.

Recompute the 40 dataset means, primary inference, calibration and figure from bundled metrics:

```text
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

The command verifies original source hashes, checks all saved means/SEs/intervals/calibrations and the primary result, and exports `ridge_liniu_comparison.pdf`. It runs no trajectories. The original independent quadratic-form check is recorded in `independent_validation.json`; repeating it requires prepared arrays and saved states not bundled here. The compact evidence includes the full untrimmed `metrics.csv`, score diagnostics, original protocol, gates, validation and preparation seal. [Versioned source and full rerun commands](../../Experiments/ridge_liniu_ablation_20261101/README.md) describe input preparation and execution; file sources and checksums are listed in `PROVENANCE.json`. For fresh preparation, install the earlier public review-data archive to recover all 40 original NPZ inputs.
