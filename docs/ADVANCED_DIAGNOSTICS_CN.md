# 可选数值诊断与扩展

[English](ADVANCED_DIAGNOSTICS.md) · [仓库说明](../README_CN.md)

常规复现流程见根目录 README。下列工具用于进一步检查数值行为。每次使用新的输出目录，并将诊断中的输入哈希与结果一同保留。

## 实验 IV：数值分辨率与重放

已有汇总和诊断表位于 `simulations/experiment4/tables/` 与 `simulations/experiment4/diagnostics/`，字段含义见[仿真数据说明](SIMULATION_DATA_CN.md#解释结果时的条件)。

对重新生成的完整 IV 运行进行诊断：

```text
python run.py iv-diagnostics --input runs/formal_simulations/exp4 --output runs/iv_diagnostics
```

输入目录需要包含新运行生成的 IV 数据、参数和抽样计数。工具比较系数差距与局部相减尺度、检查选定递推的重放偏差，并记录尾部集中程度。结合对应差距估计解释 `resolution_limited`、重放偏差和尾部集中指标。

对于选定的 Nesterov 抽样，可执行更高精度的重放：

```text
python -m repro1026.iv_precision --help
python -m repro1026.iv_precision --input runs/formal_simulations/exp4 --direction column --budget 1200 --reps 1 --tiers dd-td --output runs/iv_precision
```

命令按保存的更新次数执行双双精度和三双精度计算。精度层间的一致性用于衡量选定抽样的数值稳定程度；输出记录精度层和容差，不构成统一浮点误差界。即使只重放一次抽样，计算量也可能较大。

## 实验 V：全支持界扩展

`stable-v` 定义独立的实验协议：保留 UNI、NORM 和 LEV，使用更大的公共步长控制界，并重新计算数值目标、导数和 OPT 概率。其输出与论文实验 V 的结果分开保存。

获取 V 的官方数据后，先检查成本计划：

```text
python run.py stable-v --action plan --output runs/v_support_plan --workers 2
```

`--action validate` 用缩小规模检查实现；`--action formal` 执行扩展的完整协议。协议和输出字段见 `python run.py stable-v --help` 及 `repro1026/v_stability.py`。成本计划先记录新的步长控制界和更新次数，供安排完整扩展运行时参考。
