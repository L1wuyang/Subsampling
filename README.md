# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

Companion code and experimental materials for the manuscript by Junchen Li, Dianpeng Wang, Ying-Ao Wang and Ye Zhang. [中文说明](README_CN.md)

Submission version **v2026.11.02.1** includes Experiments I–IV, full-support stable Experiment V, and the simulated and GDSC Ridge score comparisons. [Paper figure/table map](docs/PAPER_RESULTS.md) · [Results and interpretation](docs/LATEST_RESULTS.md) · [Citation](docs/CITATION.md)

## Install and check

Use Python 3.11 or 3.12; the recorded experimental environment is Windows with Python 3.12.7. Run commands from the repository root and use a new output directory for each analysis.

```text
python -m pip install -r requirements-lock.txt
python run.py verify
```

## Recompute saved results

The three current studies are bundled. These commands check saved scalar records and recompute their summaries without running estimators or acquiring raw real data:

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_check.json
```

| Study | Included evidence | Full rerun |
| --- | --- | --- |
| Stable V: GDSC and YearPredictionMSD | [12,720 scalar records and support certificates](evidence/experiment5_stable/README.md) | [Guide](Experiments/experiment5_support_stable_20261031/README.md) |
| Simulated Ridge score comparison | [104,000 scalar records on 40 fixed inputs](evidence/ridge_liniu/README.md) | [Guide](Experiments/ridge_liniu_ablation_20261101/README.md) |
| GDSC Ridge score comparison | [180 LN_floor states and 900 comparison records](evidence/gdsc_ridge_liniu/README.md) | [Guide](Experiments/experiment5_gdsc_liniu_20261101/README.md) |

Stable-V verification covers record completeness, scalar summaries and full-target integrity/comparisons; it does not independently recompute every sketch error from states. The GDSC state check additionally requires the original preprocessed inputs. Stable-V and simulated Ridge trajectory arrays are not bundled. See [validation scope](validation/README.md).

I–IV inputs and saved results are supplied by the **v2026.10.30.2 data archive** (240 MB, 545 files including historical V). Install it separately:

```text
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

For offline installation and exact figure/table selections, see the [simulation guide](docs/SIMULATION_DATA.md) and [paper result map](docs/PAPER_RESULTS.md). The latter also documents regeneration of the six bundled manuscript figure assets.

## Run experiments from inputs

For I–IV:

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

Smoke runs use reduced dimensions and are workflow checks. Formal runs can be expensive; historical IV alone entails about 40.5 billion updates. Follow the study guides above for the current V and Ridge comparisons. Root `formal --experiment 5` generates the historical V inputs/targets used by the stable-V workflow; it does not directly run the reported stable protocol. [Official real-data acquisition](docs/DATA_SOURCES.md)

## Interpretation and provenance

The studies distinguish coefficient-target approximation, true-coefficient recovery and prediction. Observed finite-repetition rankings do not establish full conditional-MSE ordering. The two Li–Niu comparisons evaluate exact scores under a common probability floor; they do not evaluate NOPL or its outer iteration, and do not establish a significant finite-budget advantage of FULL/OPT over LN_floor. Detailed numbers and scope are centralized in [reported results](docs/LATEST_RESULTS.md).

`MANIFEST.json` lists the source files and checksums for this checkout; `provenance/frozen_scientific_sources.json` identifies the scientific implementations used in the recorded experiments. `provenance/review_data.json` identifies the data version and archive/member checksums. Cite the code tag/commit and the data version used in your analysis. [Maintenance](docs/MAINTENANCE.md) · [Additional diagnostics](docs/ADVANCED_DIAGNOSTICS.md) · [Release notes](docs/RELEASE_NOTES.md)
