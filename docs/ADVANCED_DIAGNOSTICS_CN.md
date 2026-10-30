# 进一步数值诊断

[English](ADVANCED_DIAGNOSTICS.md) · [仓库说明](../README_CN.md)

常规复现流程见根目录 README。下列工具用于进一步检查数值行为。每次使用新的输出目录，并将诊断中的输入哈希与结果一同保留。

## 实验 IV：数值分辨率与重放

运行 `python run.py review-data download` 后，已有汇总和诊断表位于 `simulations/experiment4/tables/` 与 `simulations/experiment4/diagnostics/`，字段含义见[仿真数据说明](SIMULATION_DATA_CN.md#解释结果时的条件)。

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

## 实验 V：已报告协议的诊断

[可移植尾部诊断](../evidence/experiment5/tail_diagnostics/README.md) 核验现有协议的单原子尾部反例及标量稳定性前提。轻量检查使用 `review-data` 安装的紧凑输入；另行运行的 Year/Landweber 重建使用哈希匹配的原始数据和冻结的原生代码。这些诊断解释当前有限重复经验汇总的适用范围，不改变已报告的实验协议。

独立的前瞻性 `stable-v` 协议不属于本投稿核心包。其原实现保留在[此前完整快照](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4)中，不是复现当前论文所需的流程。
