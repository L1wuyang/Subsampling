# Simulation data for Experiments I-IV

[中文说明](SIMULATION_DATA_CN.md) · [Repository guide](../README.md)

The `simulations/` directory supplies original simulated inputs, the per-repetition metrics underlying the reported results, and the corresponding summary tables. NPZ inputs preserve the original bytes. Metric records preserve the original fields, including sensitivity, zero-response and tail arms.

## Contents

| Experiment | Input NPZ files | Main/robustness records | Sensitivity records | Separate tails | Zero-response records | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| I: column probabilities | 40 | 499,200 | 46,080 | 0 | 720 | 546,000 |
| II: row probabilities | 40 | 499,200 | 46,080 | 0 | 720 | 546,000 |
| III: first-order MSE | 40 | 306,000 | 9,600 | 0 | 360 | 315,960 |
| IV: same-draw LS | 10 | 18,480 | 0 | 6,000 | 72 | 24,552 |
| **Total** | **130** | **1,322,880** | **101,760** | **6,000** | **1,872** | **1,432,512** |

III/IV robustness datasets are included in the main column. Separate arms remain separate in analysis.

```text
simulations/
  manifest.json
  experiment1/ ... experiment4/
    inputs/       original simulation NPZ inputs
    records/      per-repeat CSV.gz shards
    tables/       reported summaries, comparisons and risks
    metadata/     protocols, execution metadata, parameters and provenance
  experiment4/diagnostics/
```

I-III keep separate main and sensitivity shard groups; zero-response records belong to the sensitivity group. IV combines its original chunk CSVs into `records/metrics.partXXXX.csv.gz`, retaining the fields that identify each observation.

I-III inputs contain base Gaussian variables, noise, coefficient directions and scale/spike variables used by the frozen constructors. IV inputs contain the constructed design, response, truth and population-risk quantities. III has 20 column and 20 row inputs; IV has five of each. Inspect a file using `np.load(path, allow_pickle=False)`. Formal execution continues to generate inputs from frozen seeds; no automatic load-input option is implied.

Tables correspond to the reported analyses, with rebuilt reporting tables where available and frozen formal values otherwise. IV summaries include the numerical diagnostics documented below. Protocols retain seeds, budgets and replication counts. Historical verification records describe the original run and retain its original paths; `simulations/manifest.json` maps the released files.

## Verify and summarize

```text
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

Select one experiment using `--experiment 1` through `4`. The output root contains `verification.json` and `summary_manifest.json`; each `expN/` contains `dataset_means.csv`, `equal_dataset_summary.csv`, `record_status_counts.csv` and `figures/`. Choose a new output directory.

The command averages repetitions within each dataset, budget, method and arm, then weights datasets equally. Undefined or nonfinite metrics retain NaN means with valid counts. Selected plots show main arms; all arms remain in the output tables. It summarizes saved metrics without executing numerical trajectories.

For custom analysis, pandas reads a shard directly:

```python
from pathlib import Path
import pandas as pd

shards = sorted(Path("simulations/experiment4/records").glob("*.csv.gz"))
records = pd.concat((pd.read_csv(path) for path in shards), ignore_index=True)
```

Within an experiment, I/II keys are `(data_id, arm, budget, method, rule, rep)`; III/IV keys are `(direction, data_id, arm, budget, method, rep)`. The released records contain no duplicate keys. Summary rows are derived statistics and must not be appended as additional observations.

## Interpretation

| Field or condition | Meaning |
| --- | --- |
| `budget` | Draws with replacement, denoted N in the paper. Repeated selections count as draws. |
| `data_id`, `rep`, `rule` | I/II inference uses 40 independent dataset means. Sketch repeats condition on one dataset; methods and probability rules have paired randomness. Pooling sketches as independent datasets changes the inference. |
| `arm`, `direction` | Parameter/noise/design sensitivities, zero-response/tail arms and row/column schemes define separate groups. |
| `relative_gap`, `absolute_gap` | I-III squared coefficient error relative to the frozen full numerical target, normalized and unnormalized respectively. Each method has its own target. |
| `true_coef_rel_sq`, `design_signal_rel_sq` | Relative squared error against simulated truth in coefficient space and on the fixed design. These differ from target approximation. |
| `population_signal_rel_sq`, `population_response_mse` | Future-design signal risk and future-response MSE. Response MSE includes irreducible noise. Row population-relative signal risk may algebraically equal coefficient risk. |
| `linear_relative`, `remainder_relative`, `cross_relative` | III's error decomposition. The cross term is signed and may be negative; retain it when comparing empirical and first-order MSE. |
| `scaled_squared_gap`, `absolute_squared_gap`, `relative_squared_gap` | IV compares numerical output with QR least squares from the same draw. The scaled quantity is N times the absolute squared gap. |
| `status`, missing relative values | All 1,872 zero-target/zero-response records have undefined relative metrics; keep empty/NaN values. `status` identifies the run outcome; original tail records are retained. |
| `rank`, `unique_objects`/`unique_rows`, `spike_draws` | Rank and coverage of sampled objects. Low coverage and repeated draws belong to the sampling distribution. |
| IV diagnostics | `resolution_limited` concerns the local final-subtraction scale. The recorded diagnostics additionally preserve two unresolved selected replay warnings and six tail-concentration groups; `accuracy_certified` is false. Read these with the corresponding small gaps and tail means. |
| OPT | A first-order probability-design oracle using complete data and responses. Better target approximation alone does not imply better prediction or lower total computation. |
| V statistics | Saved metrics and statistical references are supplied separately in [the V evidence directory](../evidence/experiment5/README.md). The analysis uses two-sided paired tests and one joint 36-comparison Holm family. Historical test exploration makes predictive comparisons descriptive. |

III/IV pointwise Monte Carlo intervals condition on the specified full dataset and parameter path. Formal tables retain their original uncertainty calculations; convenience summaries do not change the statistical unit or establish a new hypothesis family.

## Complete reruns

Use `formal` or `smoke`, then `analyze --results`, for newly generated complete directories. Saved-metric summaries use a separate command because full III analysis computes bias from saved vectors and IV replay requires states/counts. The released materials provide existing tables and diagnostics; complete reruns generate the additional numerical outputs for those workflows.

Full saved states, influence arrays and sampling counts are generated during a complete rerun. Official V input acquisition is documented in the [data source guide](DATA_SOURCES.md); the [V saved-metric workflow](../evidence/experiment5/README.md) checks its statistical results directly from the bundled records.
