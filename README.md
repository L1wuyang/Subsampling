# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**Companion code and experimental materials** · [中文说明](README_CN.md)

This repository accompanies the manuscript by Junchen Li, Ying-Ao Wang and Ye Zhang. It provides the implementations of Experiments I–V, simulated inputs and per-repetition records for I–IV, and saved metrics, empirical reports and tail diagnostics for V. The implementations use the numerical recurrences and fixed-grid fourth-order Runge–Kutta (RK4) maps described in the manuscript, with matching full-data targets, derivatives, probability designs and random seeds.

For a particular manuscript result, start with the **[paper figure and table map](docs/PAPER_RESULTS.md)**. For the scope of the recorded checks, see the **[validation guide](validation/README.md)**. Experiment V's current report describes finite-repetition empirical means; it does not establish complete conditional-MSE rankings.

## Experiments and files

| Experiment | Purpose | Released materials |
| --- | --- | --- |
| I | Column-sampling probability comparison | `simulations/experiment1/`: 40 input datasets, metrics, tables and protocol metadata |
| II | Row-sampling probability comparison | `simulations/experiment2/`: 40 input datasets, metrics, tables and protocol metadata |
| III | First-order conditional MSE calibration | `simulations/experiment3/`: 20 column and 20 row inputs, metrics and tables |
| IV | Least-squares comparison using the same sampling draws | `simulations/experiment4/`: five inputs per direction, metrics, tables and numerical diagnostics |
| V | GDSC and YearPredictionMSD applications | `evidence/experiment5/`: saved metrics, empirical figures, tail diagnostics and historical analyses; [official input data](docs/DATA_SOURCES.md) |

I–IV contain **130 NPZ inputs and 1,432,512 per-repetition metric records**. [The simulation guide](docs/SIMULATION_DATA.md) documents fields, grouping and interpretation. Experiment V's [evidence guide](evidence/experiment5/README.md) documents the current empirical summaries and figures, reproducible tail diagnostics, and historical mean-based analyses.

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

This command produces convenient saved-record summaries and plots, not all of the typeset manuscript figures. The [figure and table map](docs/PAPER_RESULTS.md) identifies the data selection and additional work needed for each result.

Reproduce V's current empirical summaries and the two manuscript target-error figures, without mean-confidence bands:

```text
python -B evidence/experiment5/empirical.py --output runs/reported_v
python -B evidence/experiment5/tail_diagnostics/verify_witnesses.py
python -B evidence/experiment5/tail_diagnostics/verify_stability.py
```

These commands analyze the bundled experimental records. Select `--experiment 1` through `4` for one simulation experiment. Choose a new output directory for each analysis. V uses 12,720 saved metric records and a 276-point target-figure reference. Its [tail diagnostics](evidence/experiment5/tail_diagnostics/README.md) include lightweight witness and stability checks and a separate reconstruction workflow.

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

The [data source guide](docs/DATA_SOURCES.md) gives exact versions, checksums and manual import instructions. The GDSC training/test ID split is included; Year uses its official ordered split. For newly executed experiments, `analyze --results` reads the complete generated run directory, including the saved states needed for III's bias analysis and IV's diagnostics. For V, this default analysis now produces empirical summaries and figures, without automatically running historical mean-based tests.

## Documentation and provenance

- [Paper figures and tables: inputs, commands and outputs](docs/PAPER_RESULTS.md)
- [Current and historical validation records](validation/README.md)
- [Simulation data, metric definitions and statistical interpretation](docs/SIMULATION_DATA.md)
- [Experiment V: empirical results, tail diagnostics and historical analyses](evidence/experiment5/README.md)
- [Official real-data acquisition](docs/DATA_SOURCES.md)
- [Optional numerical diagnostics and extensions](docs/ADVANCED_DIAGNOSTICS.md)
- [How to cite the manuscript and identify the code version](docs/CITATION.md)
- [Repository maintenance and frozen-source records](docs/MAINTENANCE.md)

`MANIFEST.json` records the released files and checksums; `simulations/manifest.json` describes I–IV data; `provenance/` records fixed inputs and source origins. Historical dates in internal directory and module names identify the preserved computation records. Use an exact Git commit when identifying the materials used for a result.

## Historical analyses

The original one-sided and later two-sided/Holm analyses for V are retained separately as historical evidence. Their definitions, commands and limitations are in the [historical analysis guide](docs/HISTORICAL_ANALYSES.md). They are not the inferential basis of the current V report. Historical acceptance records retain their original bytes in `validation/history/`.
