# Experimental protocols and source records / 实验协议与来源记录

[Repository guide](../README.md) · [Simulation data](SIMULATION_DATA.md) · [Figure/table map](PAPER_RESULTS.md) · [Validation scope](../validation/README.md)

The protocols specify the data construction, regularization, numerical targets, sampling rules, budgets, repetitions and checks for each experiment. The guides below give executable commands; the figure/table map gives the exact data selections used in the paper.

| Study / 实验 | Scientific design and protocol / 科学设计与协议 | Execution guide / 运行指南 |
| --- | --- | --- |
| I: column sampling / 列抽样 | Fixed numerical targets, 40 data sets, paired probability-rule comparisons and separate sensitivity arms. [Protocol](../Experiments/experiment1_native_comprehensive_20261024/formal_protocol.json). | [I–IV inputs, records and analysis](SIMULATION_DATA.md) |
| II: row sampling / 行抽样 | Fixed numerical targets, 40 spiked-row data sets, paired probability-rule comparisons and separate sensitivity arms. [Protocol](../Experiments/experiment2_native_comprehensive_20261024/formal_protocol.json). | [I–IV inputs, records and analysis](SIMULATION_DATA.md) |
| III: first-order MSE / 一阶均方误差 | Row/column schemes, empirical and first-order error decomposition, and robustness arms. [Protocol](../Experiments/experiment3_native_comprehensive_20261024/formal_protocol.json). | [I–IV inputs, records and analysis](SIMULATION_DATA.md) |
| IV: same-draw least squares / 同次抽样最小二乘 | Numerical output compared with QR least squares on the same draw; replay, resolution and tail diagnostics. [Protocol](../Experiments/experiment4_native_comprehensive_20261025/formal_protocol.json). | [Simulation data](SIMULATION_DATA.md), [numerical diagnostics](ADVANCED_DIAGNOSTICS.md) |
| V: full-support stable / 全支撑稳定协议 | GDSC and YearPredictionMSD, six generators, four rules and 48 support checks. [Protocol](../evidence/experiment5_stable/protocol.json). | [English](../Experiments/experiment5_support_stable_20261031/README.md), [中文](../Experiments/experiment5_support_stable_20261031/README_CN.md) |
| Simulated Ridge / 模拟 Ridge | 40 Experiment I inputs, 13 budgets, 40 paired sketches per input/budget and five rules; primary FULL_OPT–LN_floor comparison at N=150. [Protocol](../Experiments/ridge_liniu_ablation_20261101/protocol.json). | [English](../Experiments/ridge_liniu_ablation_20261101/README.md), [中文](../Experiments/ridge_liniu_ablation_20261101/README_CN.md) |
| GDSC Ridge | One fixed GDSC training set, six budgets and 30 common-uniform draws per budget; descriptive five-rule comparison. [Protocol](../Experiments/experiment5_gdsc_liniu_20261101/protocol.json). | [English](../Experiments/experiment5_gdsc_liniu_20261101/README.md), [中文](../Experiments/experiment5_gdsc_liniu_20261101/README_CN.md) |
| Historical V / 历史 V | The 2026-10-25 protocol corresponding to data version v2026.10.30.2, with historical empirical and tail diagnostics. [Protocol](../Experiments/experiment5_native_realdata_20261025/formal_protocol.json). | [English](../evidence/experiment5/README.md), [中文](../evidence/experiment5/README_CN.md) |

Original protocol files and execution receipts document the recorded runs. Some include drafting, task-scope or predecessor notes. These fields describe that execution context; the scientific design is given by the numerical and statistical fields, and current reproduction commands are given in the guides above. In particular, the historical V `preservation` note is not an instruction to omit I–IV reproduction. The Experiment II checker-tolerance record remains relevant to interpreting its numerical validation.

Source snapshots and hashes identify the implementations used in the recorded runs. `original_output_directory` in the stable-V, simulated-Ridge and GDSC-Ridge provenance records identifies an original execution location. The corresponding public evidence is under `evidence/experiment5_stable/`, `evidence/ridge_liniu/` and `evidence/gdsc_ridge_liniu/`, respectively; commands use repository-relative paths. Full-input and saved-state requirements are stated in each guide.

中文：协议记录数据构造、正则化、数值目标、抽样规则、预算、重复次数及核验条件；上表指南提供可执行命令，图表索引提供论文采用的精确数据筛选。原协议和回执中的写作、任务范围或前置任务备注属于当时的执行背景，不是当前复现要求；历史 V 的 `preservation` 备注不要求复现者跳过 I—IV。实验 II 的检查器容差记录仍用于解释原数值核验。来源记录中的原工作目录用于追溯，在其他计算机上应使用指南中的仓库相对路径。完整输入和状态数组的要求以各指南为准。
