# Full-support stable Experiment V

[中文说明](README_CN.md) · [Saved evidence](../../evidence/experiment5_stable/README.md) · [Results and interpretation](../../docs/LATEST_RESULTS.md)

Protocol `experiment-V-support-stable-20261031-v1` compares six regression methods and UNI/NORM/LEV/OPT on GDSC and YearPredictionMSD. It fixes the full-data numerical targets, native discrete derivatives and probabilities before sampling, using seed 202610310501. GDSC uses six budgets and 30 repetitions; Year uses seven budgets and 50 repetitions (530 tasks, 12,720 scalar records).

## Check saved results

Run from the repository root:

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
```

This checks provenance hashes and recomputes scalar summaries. The original `independent_validation.json` records completeness/summary checks and full-target integrity/comparisons; it is not a receipt for independently recomputing every sketch error from saved states. Full-support certificates and observed Cholesky diagnostics have separate scopes. The compact evidence excludes trajectory arrays and official raw inputs.

## Full rerun from official inputs

Install the root pinned requirements first. Acquire and verify the official inputs, then generate the historical inputs and full targets required by the stable protocol:

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py formal --experiment 5 --output runs/historical_v --workers 8
```

The root command creates `runs/historical_v/exp5/inputs` and `runs/historical_v/exp5/formal`. It executes the earlier frozen V protocol and can be expensive. Its saved metrics are historical; the following step produces the current stable protocol. The lightweight review-data ZIP alone does not supply these complete arrays. Manual data acquisition/import is documented in the [data guide](../../docs/DATA_SOURCES.md).

Use fresh output directories for the pilot and new run:

```text
python -B Experiments/experiment5_support_stable_20261031/pilot.py --output runs/stable_v/pilot.json
python -B Experiments/experiment5_support_stable_20261031/run_stable.py --historical-root runs/historical_v/exp5 --output runs/stable_v/formal_01 --workers 8
```

The runner accepts the portable root output layout above as well as the historical `inputs/` plus `outputs/formal_01/` layout. It checks the consumed input/source hashes, rebuilds the changed targets, freezes the probabilities, and requires the full-support gate before drawing. Ridge/HBF/SOAR reuse hash-matched historical targets under the unchanged parameters; Landweber/Showalter/Nesterov use the recomputed stable maps. Every prescribed iterative update and RK4 stage is retained.

After sampling, the runner automatically checks scalar completeness and means, verifies full-target integrity, compares the historical and full-support stable targets, and writes `independent_validation.json`, `RESULTS.md` and protocol-comparison tables/figures. This postprocessing performs no estimator solves and no independent per-sketch state-error recalculation. It can also be run separately on a completed output:

```text
python -B Experiments/experiment5_support_stable_20261031/compare_results.py --historical-root runs/historical_v/exp5 --output runs/stable_v/formal_01
```

Full-support stability does not prove complete conditional-MSE ordering at each finite budget. The reported rankings are finite-repetition observations; see the linked result guide for exact scope.
