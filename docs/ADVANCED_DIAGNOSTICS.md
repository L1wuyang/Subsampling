# Additional numerical diagnostics

[中文说明](ADVANCED_DIAGNOSTICS_CN.md) · [Repository guide](../README.md)

The standard reproduction workflow is described in the root README. The tools below support additional numerical inspection. Use fresh output directories and retain each diagnostic's input hashes with its results.

## Experiment IV: numerical resolution and replay

After `python run.py review-data download`, the saved summaries and diagnostic tables are under `simulations/experiment4/tables/` and `simulations/experiment4/diagnostics/`. Their field definitions are in the [simulation guide](SIMULATION_DATA.md#interpretation).

To inspect a newly generated complete IV run:

```text
python run.py iv-diagnostics --input runs/formal_simulations/exp4 --output runs/iv_diagnostics
```

The input must contain the IV data, parameters and saved sampling counts produced by a new run. The tool compares coefficient gaps with the local subtraction scale, examines selected recurrence replays, and reports tail concentration. Interpret `resolution_limited`, replay discrepancies and tail concentration together with the corresponding gap estimates.

For selected Nesterov draws, higher-precision replay is available:

```text
python -m repro1026.iv_precision --help
python -m repro1026.iv_precision --input runs/formal_simulations/exp4 --direction column --budget 1200 --reps 1 --tiers dd-td --output runs/iv_precision
```

This executes the saved number of updates using double-double and triple-double arithmetic. Precision-tier agreement measures numerical consistency for the selected draws. The output records the chosen tiers and tolerances; it is not a uniform floating-point error bound. Replay can be expensive even for one draw.

## Experiment V: diagnostics for the reported protocol

The [portable tail diagnostics](../evidence/experiment5/tail_diagnostics/README.md) check the existing protocol's single-atom tail witnesses and scalar stability premises. Lightweight checks use compact inputs installed by `review-data`; a separate Year/Landweber restoration uses hash-verified raw data and the frozen native code. These diagnostics explain the scope of the current finite-repetition empirical summaries without changing the reported protocol.

The separate prospective `stable-v` protocol is not part of this submission core. Its earlier implementation remains in the [previous full snapshot](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4); it is not required to reproduce the current paper.
