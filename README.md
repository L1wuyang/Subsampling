# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**Companion code and experimental materials** - [中文说明](README_CN.md)

**Results update: November 1, 2026.** Includes full-support stable Experiment V, the simulated Ridge score comparison and the GDSC Ridge Li-Niu comparison, with versioned implementations and saved evidence. [VERSION](VERSION) and release `v2026.10.30.2` identify the unchanged earlier code/review-data archive; the three updated studies are bundled in the current repository. [Update notes](docs/RESULTS_UPDATE_20261101.md) - [Paper result map](docs/PAPER_RESULTS.md)

This repository accompanies the manuscript by Junchen Li, Ying-Ao Wang and Ye Zhang. Experiments I-IV retain their frozen scientific sources and existing published inputs/results. Experiment V uses a full-support stable protocol, with additional Ridge column-score comparisons on simulated and real data. Iterative methods continue to use the actual recurrences and fixed-grid RK4 maps with their matching full-data numerical targets and algorithmic influences.

## Reported results

| Study | Bundled records and source | Interpretation |
| --- | --- | --- |
| Stable Experiment V | [evidence/experiment5_stable](evidence/experiment5_stable/README.md): 12,720 complete scalar records, 530 sketch tasks, protocol, 48 full-support gates, matched full-target summaries and original validation | Among UNI/NORM/LEV/OPT, OPT has the lowest observed mean in 78/78 cells; finite repetitions do not prove full conditional-MSE ordering. |
| Ridge Li-Niu score ablation | [evidence/ridge_liniu](evidence/ridge_liniu/README.md): 104,000 complete scalar records, results covering all 40 reused inputs, 13 budgets, five rules and original validation | At prespecified N=150, FULL-LN=-0.0003228063, 95% CI [-0.0009423789, 0.0002967663], two-sided p=.298436. No significant difference detected; equivalence not established. |
| GDSC Ridge LN addendum | [evidence/gdsc_ridge_liniu](evidence/gdsc_ridge_liniu/README.md): 180 new LN_floor records and 720 preserved four-rule records; six budgets, 30 paired draws | At N=2996 OPT is 0.768% lower; reversals at N=374/749 and all six pointwise paired intervals spanning zero are retained. |

All errors in this table are relative squared coefficient deviations from the fixed full-data regularized target. They are separate from true-coefficient recovery or predictive risk. LN_floor is the exact lower-bound adaptation of the Li-Niu score, with the same floor constraint as FULL_OPT; this experiment does not run NOPL or the original outer iteration. [Detailed result boundaries](docs/LATEST_RESULTS.md)

## Install and verify

Use Python 3.11 or 3.12 (recorded environment: Windows, Python 3.12.7):

```text
python -m pip install -r requirements-lock.txt
python run.py verify
```

The root manifest checks the source and compact evidence. The unchanged `provenance/frozen_scientific_sources.json` anchors 54 historical scientific sources, including III/IV pilot gates.

## Recompute the latest results without trajectories

No raw real data or old 240 MB review archive is needed for these two commands. Choose a new output directory:

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

These commands verify bundled-source SHA-256 values, recompute all saved scalar means and relevant intervals, check the unique Ridge primary comparison and export PDF/PNG curves. They operate on saved scalar metrics; state-based checks are recorded in the original independent validation receipts. The full untrimmed metrics, original gates and original validation receipts are bundled with their provenance. The earlier two studies' trajectory arrays and official raw real data are not bundled. The new GDSC-LN addendum includes its 180 new states, uniforms and counts; see its separate verification command below.

## Earlier Experiments I-IV and historical V

The earlier [public release](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.10.30.2) separates a core source archive and `Subsampling-review-data-v2026.10.30.2.zip` (240,281,192 bytes). Its 545 files restore I-IV inputs/results plus **historical** V evidence. They do not overwrite the three versioned latest-result evidence directories.

```text
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

For offline installation, use `python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip`. The descriptor fixes all hashes and refuses conflicting files. I-IV comprise 130 NPZ inputs and 1,432,512 per-repetition metric records; see the [simulation guide](docs/SIMULATION_DATA.md). The [paper result map](docs/PAPER_RESULTS.md) identifies precise selections and figure inputs. Earlier V means, scalar rare-event witnesses and historical Holm analyses remain at [evidence/experiment5](evidence/experiment5/README.md); they are retained for provenance and do not supply the new stable-run curves.

## Full experimental reruns

I-IV continue to use the root CLI. A smoke run checks the workflow at reduced dimensions; formal execution regenerates the frozen input streams:

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

The versioned latest studies use their own fixed protocols and prerequisites:

- [Stable V implementation and full rerun prerequisites](Experiments/experiment5_support_stable_20261031/README_CN.md). Official GDSC/Year inputs and the historical complete targets/arrays are required; the lightweight public review-data package alone is insufficient. The split-adjoint pilot must pass before the new support gate releases sampling.
- [Ridge score-ablation implementation](Experiments/ridge_liniu_ablation_20261101/README_CN.md). Install the old review-data archive to recover the 40 frozen Experiment I inputs, then follow the preparation, pilot and predecessor-gate steps. Reusing these inputs is an ablation, not new-data independent confirmation.

The root `formal --experiment 5` command still implements the earlier frozen V protocol; use the separate stable-V directory for the reported full-support protocol. [Official raw input acquisition](docs/DATA_SOURCES.md) remains available through `python run.py data download` and `data check`.

## Documentation and provenance

[Paper figures and tables](docs/PAPER_RESULTS.md) - [Latest result interpretation](docs/LATEST_RESULTS.md) - [Validation scope](validation/README.md) - [Data sources](docs/DATA_SOURCES.md) - [Additional diagnostics](docs/ADVANCED_DIAGNOSTICS.md) - [Citation](docs/CITATION.md) - [Maintenance](docs/MAINTENANCE.md)

`MANIFEST.json` covers the source and compact reported metrics. `provenance/review_data.json` and VERSION retain their unchanged earlier baseline. New experiment protocols version the scientific changes separately; no old frozen hash is changed. Original run records may retain historical local paths, while bundled `PROVENANCE.json` records the copied hashes. The three studies are identified by their protocol versions and the source hashes stored with each evidence directory.

The saved-metric plotting tool exports convenience layouts, rather than asserting identity with the journal artwork. Final manuscript figure assets are matched separately in the paper result map.

## Verify the GDSC Ridge comparison

[Results](evidence/gdsc_ridge_liniu/README.md) · [Reproduction and saved-state verification](Experiments/experiment5_gdsc_liniu_20261101/README_CN.md)

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_check.json
```
