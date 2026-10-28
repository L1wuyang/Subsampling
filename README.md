# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**Companion code and experimental materials** · [中文说明](README_CN.md)

This repository accompanies the manuscript by Junchen Li, Ying-Ao Wang and Ye Zhang. It provides the implementations of Experiments I–V, simulated inputs and per-repetition records for I–IV, and saved metrics and statistical analyses for V. The implementations use the numerical recurrences and fixed-grid fourth-order Runge–Kutta (RK4) maps described in the manuscript, with matching full-data targets, derivatives, probability designs and random seeds.

## Experiments and files

| Experiment | Purpose | Released materials |
| --- | --- | --- |
| I | Column-sampling probability comparison | `simulations/experiment1/`: 40 input datasets, metrics, tables and protocol metadata |
| II | Row-sampling probability comparison | `simulations/experiment2/`: 40 input datasets, metrics, tables and protocol metadata |
| III | First-order conditional MSE calibration | `simulations/experiment3/`: 20 column and 20 row inputs, metrics and tables |
| IV | Least-squares comparison using the same sampling draws | `simulations/experiment4/`: five inputs per direction, metrics, tables and numerical diagnostics |
| V | GDSC and YearPredictionMSD applications | `evidence/experiment5/`: saved metrics, paired comparisons and statistical reanalysis; [official input data](docs/DATA_SOURCES.md) |

I–IV contain **130 NPZ inputs and 1,432,512 per-repetition metric records**. [The simulation guide](docs/SIMULATION_DATA.md) documents fields, grouping and interpretation. Experiment V's [statistical evidence guide](evidence/experiment5/README.md) documents the saved records and the joint 36-comparison Holm analysis.

## Install and verify

Use Python 3.11 or 3.12; the recorded validation environment is Python 3.12.7 on Windows. From the repository root:

```text
python -m pip install -r requirements-lock.txt
python run.py verify
python run.py simulation-data verify --experiment all
```

`requirements-lock.txt` and `environment.json` record the dependencies and validation environment. Use the **root `run.py`** for the workflows below. The scripts nested under `Experiments/` are retained source records; see [entry points and source provenance](docs/MAINTENANCE.md#entry-points-and-frozen-sources).

## Check the reported results from saved records

Recompute I–IV dataset means, equally weighted summaries and selected plots:

```text
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

Recompute V's two-sided paired tests and joint Holm correction:

```text
python evidence/experiment5/reanalyze.py --output runs/reported_v
```

These commands analyze the bundled experimental records. Select `--experiment 1` through `4` for one simulation experiment. Choose a new output directory for each analysis. The existing detailed tables are available in each experiment's `tables/` directory and in V's `reference/` directory.

## Rerun the experiments

`smoke` checks the execution and reporting workflow with smaller dimensions, budgets and replication counts. `formal` runs the full frozen experimental protocol.

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis

python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

`simulations` selects I–IV; `--experiment 1` through `5` selects one experiment. Formal execution regenerates inputs from the frozen seeds. IV alone entails approximately 40.5 billion updates; check the workflow with `smoke` before allocating resources for a full run.

For V, obtain the fixed official data files and verify their checksums first:

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py formal --experiment 5 --output runs/formal_v --workers 8
python run.py analyze --experiment 5 --results runs/formal_v --output runs/formal_v_analysis
```

The [data source guide](docs/DATA_SOURCES.md) gives exact versions, checksums and manual import instructions. The GDSC training/test ID split is included; Year uses its official ordered split. For newly executed experiments, `analyze --results` reads the complete generated run directory, including the saved states needed for III's bias analysis and IV's diagnostics.

## Documentation and provenance

- [Simulation data, metric definitions and statistical interpretation](docs/SIMULATION_DATA.md)
- [Experiment V: saved statistical evidence](evidence/experiment5/README.md)
- [Official real-data acquisition](docs/DATA_SOURCES.md)
- [Optional numerical diagnostics and extensions](docs/ADVANCED_DIAGNOSTICS.md)
- [How to cite the manuscript and identify the code version](docs/CITATION.md)
- [Repository maintenance and frozen-source records](docs/MAINTENANCE.md)

`MANIFEST.json` records the released files and checksums; `simulations/manifest.json` describes I–IV data; `provenance/` records fixed inputs and source origins. Historical dates in internal directory and module names identify the preserved computation records. Use an exact Git commit when identifying the materials used for a result.
