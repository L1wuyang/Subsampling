# Historical analyses and protocol records

[Current Experiment V workflow](../evidence/experiment5/README.md) · [中文说明](HISTORICAL_ANALYSES_CN.md)

This guide separates earlier analysis records from the current reporting workflow. It reorganizes their documentation; the scripts, raw metric archive, reference tables and scientific protocols remain at their existing paths with their original bytes.

## Current reporting

Use `evidence/experiment5/empirical.py` for the saved Experiment V records, or the root `run.py analyze --experiment 5` for a newly generated full run. Both report finite-repetition empirical summaries and descriptive figures without mean tests or mean-confidence bands. These summaries do not establish the ordering of the full conditional MSE; prediction comparisons are descriptive because the test sets had been explored previously.

The [tail diagnostics](../evidence/experiment5/tail_diagnostics/README.md) remain part of the current evidence. They explain limitations of the empirical summaries and are not superseded by the historical p-values below.

## Where the historical evidence is stored

| Material | Repository location | Role |
| --- | --- | --- |
| Original draw records and one-sided comparison table | `evidence/experiment5/saved_records.tar.gz` | Preserves 530 draw CSVs, 12,720 scalar records, 12 full-target summaries, protocols and execution metadata. The one-sided table is the archive member `Experiments/experiment5_native_realdata_20261025/outputs/formal_01/primary_comparisons.csv`. |
| Later two-sided/Holm comparison table | `evidence/experiment5/reference/paired_comparisons_two_sided.csv` | Frozen output of the historical statistical revision. |
| Detailed statistical revision and input hashes | `evidence/experiment5/reference/inference_revision.json` | Records the historical comparison family, calculations and source inputs. |
| Preserved reanalysis implementation | `evidence/experiment5/reference/reanalyze_saved_v.py` | Original analysis script, invoked through the archive wrapper below. |
| Public historical verification/replay wrapper | `evidence/experiment5/reanalyze.py` | Verifies and supplies the original archive paths before executing the preserved script. |
| Source provenance and checksums | `evidence/experiment5/PROVENANCE.json` and `evidence/experiment5/MANIFEST.json` | Identifies the source archive and verifies the evidence files and archive members. |

## Verify or replay the historical mean-based analyses

`evidence/experiment5/reference/` preserves the previous two-sided comparison table, detailed inference-revision report and original saved-record analysis script. These files and the earlier one-sided table are historical records, not the current inferential basis for Experiment V. `evidence/experiment5/PROVENANCE.json` identifies the archived sources; `evidence/experiment5/MANIFEST.json` records package and archive-member checksums.

To verify or replay that historical analysis explicitly:

```bash
python -B evidence/experiment5/reanalyze.py --verify
python -B evidence/experiment5/reanalyze.py --output runs/experiment5_historical
```

The checksum-only command uses Python's standard library. Historical reanalysis uses NumPy, pandas and SciPy. It recomputes 36 two-sided paired Student t tests at budgets 749 (GDSC) and 5,000 (Year), with one joint Holm correction, and checks the saved reference table. The family retains the GDSC NORM/UNI duplicate. Its outputs include `paired_comparisons_two_sided.csv`, `inference_revision.json`, `mean_coefficient_errors.csv` and `verification.json`.

The historical p-values, standard errors and pointwise 95% intervals do not account for the rare-event contributions identified by the tail diagnostics or for historical parameter/test-set exploration. They are not used to infer full conditional-MSE rankings. The wrapper unpacks verified regular files into a temporary directory and runs the preserved historical script; it does not fit models or draw new samples.

## Frozen scientific protocols and nested entry points

`Experiments/` retains the scientific algorithms, protocols and source history. In particular, `Experiments/experiment5_native_realdata_20261025/formal_protocol.json` and its archived analyzer still describe the earlier statistical workflow. Their one-sided/two-sided testing or confidence-band statements record that earlier computation; they are not instructions for the current empirical report. The current report is implemented by `repro1026/empirical_v.py` and the documented root/saved-record entry points.

Some nested Experiment III/IV commands reference verification or delivery modules from the original full workspace. Use the root `run.py` for new verification, execution and analysis. The root adapters still import scientific modules from `Experiments/`, and the files in `provenance/frozen_scientific_sources.json` and the III/IV pilot hash gates remain required. Historical directory dates do not make these dependencies removable.

Earlier package acceptance records are indexed in [validation/README.md](../validation/README.md). Their dates, environments, checksums, old paths and conclusions describe the versions tested at the time; they are not claims that those checks were rerun for the current organization change. See [repository maintenance](MAINTENANCE.md) for the current entry-point and preservation policy.
