# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**Companion code and experimental materials** · [中文说明](README_CN.md)

**Version [v2026.10.30.2](VERSION)** · [Release and downloads](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.10.30.2) · [Current validation](validation/README.md)

This repository accompanies the manuscript by Junchen Li, Ying-Ao Wang and Ye Zhang. The core package contains the implementations of Experiments I–V, protocols, verification/reporting tools and documentation. Saved simulation inputs, metric records, tables and Experiment V diagnostic inputs are supplied as a separate review-data archive. The implementations use the numerical recurrences and fixed-grid fourth-order Runge–Kutta (RK4) maps described in the manuscript, with matching full-data targets, derivatives, probability designs and random seeds.

For a particular manuscript result, start with the **[paper figure and table map](docs/PAPER_RESULTS.md)**. For the scope of the recorded checks, see the **[validation guide](validation/README.md)**. Experiment V's current report describes finite-repetition empirical means; it does not establish complete conditional-MSE rankings.

## Code and review data

The [Release](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.10.30.2) separates two downloads:

- `Subsampling-core-v2026.10.30.2.zip`: core code, frozen protocols, source checksums and guides; 107 files, approximately 1.2 MB after extraction. It is sufficient to verify the code and generate new simulations.
- [`Subsampling-review-data-v2026.10.30.2.zip`](https://github.com/L1wuyang/Subsampling/releases/download/v2026.10.30.2/Subsampling-review-data-v2026.10.30.2.zip): all 545 previously released simulation and saved-evidence files, with their original bytes; the archive is 240,281,192 bytes (approximately 240 MB). Install it to check the reported results without rerunning trajectories.

Git history retains the earlier large data files, so an ordinary full `git clone` still downloads that history. For the small core download, use the Release core ZIP or a shallow checkout of this tag:

```text
git clone --depth 1 --branch v2026.10.30.2 https://github.com/L1wuyang/Subsampling.git
```

The data archive does not include the official raw GDSC/Year data or every trajectory-level state array. Full reruns obtain or generate those separately. Installing review data restores its original relative paths and leaves it outside the tracked core inventory. [Release notes](docs/RELEASE_NOTES.md) describe the split.

## Experiments and files

| Experiment | Purpose | Review-data locations after installation |
| --- | --- | --- |
| I | Column-sampling probability comparison | `simulations/experiment1/`: 40 input datasets, metrics, tables and protocol metadata |
| II | Row-sampling probability comparison | `simulations/experiment2/`: 40 input datasets, metrics, tables and protocol metadata |
| III | First-order conditional MSE calibration | `simulations/experiment3/`: 20 column and 20 row inputs, metrics and tables |
| IV | Least-squares comparison using the same sampling draws | `simulations/experiment4/`: five inputs per direction, metrics, tables and numerical diagnostics |
| V | GDSC and YearPredictionMSD applications | `evidence/experiment5/`: saved metrics, empirical figures and tail diagnostics; [official input data](docs/DATA_SOURCES.md) |

I–IV contain **130 NPZ inputs and 1,432,512 per-repetition metric records**. [The simulation guide](docs/SIMULATION_DATA.md) documents fields, grouping and interpretation. Experiment V's [evidence guide](evidence/experiment5/README.md) documents the current empirical summaries, figures and reproducible tail diagnostics.

## Install and verify

Use Python 3.11 or 3.12; the recorded validation environment is Python 3.12.7 on Windows. From the repository root:

```text
python -m pip install -r requirements-lock.txt
python run.py verify
```

`requirements-lock.txt` and `environment.json` record the dependencies and validation environment. Use the **root `run.py`** for the workflows below. The scripts nested under `Experiments/` are retained source records; see [entry points and source provenance](docs/MAINTENANCE.md#entry-points-and-frozen-sources).

## Install the review data

Download the versioned archive, verify its SHA-256 and every member, and restore the declared paths:

```text
python run.py review-data download
python run.py review-data verify
```

For offline use, download the data ZIP from the Release elsewhere and install the local file:

```text
python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip
```

Replace the example path with your local ZIP path. The descriptor `provenance/review_data.json` fixes the archive and file hashes. Installation refuses conflicting existing contents. `python run.py verify` checks only the core; `review-data verify` checks the installed data. Neither launches experiments.

## Check the reported results from saved records

After installing the review data, verify and recompute I–IV dataset means, equally weighted summaries and selected plots:

```text
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

This command produces convenient saved-record summaries and plots, not all of the typeset manuscript figures. The [figure and table map](docs/PAPER_RESULTS.md) identifies the data selection and additional work needed for each result.

Reproduce V's current empirical summaries and the two manuscript target-error figures, without mean-confidence bands:

```text
python -B evidence/experiment5/empirical.py --output runs/reported_v
python -B evidence/experiment5/tail_diagnostics/verify_witnesses.py
python -B evidence/experiment5/tail_diagnostics/verify_stability.py
```

These commands analyze the installed review-data records. Select `--experiment 1` through `4` for one simulation experiment. Choose a new output directory for each analysis. V uses 12,720 saved metric records and a 276-point target-figure reference. Its [tail diagnostics](evidence/experiment5/tail_diagnostics/README.md) include lightweight witness and stability checks and a separate reconstruction workflow.

## Rerun the experiments

`smoke` checks the execution and reporting workflow with smaller dimensions, budgets and replication counts. `formal` runs the full frozen experimental protocol.

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis

python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

Saved review data is not required to generate new simulation runs. `simulations` selects I–IV; `--experiment 1` through `5` selects one experiment. Formal execution regenerates inputs from the frozen seeds. IV alone entails approximately 40.5 billion updates; check the workflow with `smoke` before allocating resources for a full run.

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
- [Current validation records](validation/README.md)
- [Simulation data, metric definitions and statistical interpretation](docs/SIMULATION_DATA.md)
- [Experiment V: empirical results and tail diagnostics](evidence/experiment5/README.md)
- [Official real-data acquisition](docs/DATA_SOURCES.md)
- [Additional numerical diagnostics](docs/ADVANCED_DIAGNOSTICS.md)
- [How to cite the manuscript and identify the code version](docs/CITATION.md)
- [Repository maintenance and frozen-source records](docs/MAINTENANCE.md)

`MANIFEST.json` records core files and checksums. `provenance/review_data.json` identifies the separate data asset; the installed `simulations/manifest.json` describes I–IV records. `provenance/` also records fixed inputs and source origins. Historical dates in internal directory and module names identify the preserved computation records. Use an exact Git commit when identifying the materials used for a result.

## Earlier materials

The [complete previous version](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4) preserves the preceding combined code/data layout and the optional `stable-v` extension omitted from this core package. Earlier validation/history remains reachable through its commit history. V's earlier tests are not the inferential basis of the current empirical report. Required archive-verification code stays in the core, and its historical reference files are installed with the review data. Frozen source modules and pilot hash gates remain because the reproduction workflows use or verify them; retained original source paths are not a claim that every legacy subcommand is a supported paper workflow.
