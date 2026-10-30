# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**论文配套代码与实验材料** · [English](README.md)

本仓库配套 Junchen Li、Ying-Ao Wang 和 Ye Zhang 的上述论文，提供实验 I—V 的实现、I—IV 的仿真输入和逐次指标，以及 V 的保存指标、经验报告和尾部诊断。实现采用论文中的实际递推与固定网格四阶 Runge–Kutta（RK4）计算，并使用匹配的完整数据目标、导数、抽样概率和随机种子。

核验某项论文结果，请先看**[论文图表对照表](docs/PAPER_RESULTS_CN.md)**；了解已有检查的范围，请看**[验证记录说明](validation/README.md)**。实验 V 当前报告有限重复抽样的经验均值，不据此确立完整条件 MSE 排序。

## 实验与文件对应

| 实验 | 研究内容 | 随仓库提供的材料 |
| --- | --- | --- |
| I | 列抽样概率比较 | `simulations/experiment1/`：40 份输入、指标、结果表和协议元数据 |
| II | 行抽样概率比较 | `simulations/experiment2/`：40 份输入、指标、结果表和协议元数据 |
| III | 一阶条件 MSE 校准 | `simulations/experiment3/`：20 份列输入、20 份行输入、指标和结果表 |
| IV | 同次抽样最小二乘比较 | `simulations/experiment4/`：每个方向五份输入、指标、结果表和数值诊断 |
| V | GDSC 与 YearPredictionMSD 应用 | `evidence/experiment5/`：保存指标、经验图形、尾部诊断及历史分析；[原始数据官方来源](docs/DATA_SOURCES_CN.md) |

I—IV 合计 **130 份 NPZ 输入、1,432,512 条逐次指标**。[仿真数据说明](docs/SIMULATION_DATA_CN.md) 解释字段、分组和统计含义；V 的[材料说明](evidence/experiment5/README_CN.md) 给出当前经验汇总、论文图形、尾部诊断及历史均值分析的复核方法。

## 安装与完整性检查

使用 Python 3.11 或 3.12；已记录的验证环境为 Windows 上的 Python 3.12.7。在仓库根目录运行：

```text
python -m pip install -r requirements-lock.txt
python run.py verify
python run.py simulation-data verify --experiment all
```

`requirements-lock.txt` 和 `environment.json` 记录依赖与验证环境。下列流程统一使用**根目录 `run.py`**；`Experiments/` 内嵌脚本作为源代码记录保留，详见[入口与冻结源码说明](docs/MAINTENANCE.md#entry-points-and-frozen-sources)。

## 从保存指标核验论文结果

重新计算 I—IV 的数据集内均值、数据集等权汇总和部分图：

```text
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

该命令生成保存记录的便捷汇总和图形，并不直接生成全部论文排版图。[图表对照表](docs/PAPER_RESULTS_CN.md)逐项说明数据选择及所需的额外步骤。

复现 V 当前的经验汇总及两张不含均值置信区间的论文目标误差图：

```text
python -B evidence/experiment5/empirical.py --output runs/reported_v
python -B evidence/experiment5/tail_diagnostics/verify_witnesses.py
python -B evidence/experiment5/tail_diagnostics/verify_stability.py
```

上述命令分析随仓库提供的实验记录。可用 `--experiment 1` 至 `4` 单独选择仿真实验；每次使用新的输出目录。V 使用 12,720 条保存指标和包含 276 个点的目标图参考。[尾部诊断说明](evidence/experiment5/tail_diagnostics/README.md)提供轻量见证与稳定性核验，以及独立的输入重建流程。

## 重新运行实验

`smoke` 缩小维度、预算和重复次数，用于检查计算及报告流程；`formal` 执行完整的冻结实验协议。

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis

python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

`simulations` 选择 I—IV；`--experiment 1` 至 `5` 单独选择一个实验。完整运行按冻结种子重新生成输入。IV 约需执行 405 亿次更新，建议先用 `smoke` 检查流程，再安排完整运行资源。

V 先获取固定版本的官方数据并核验校验和：

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py formal --experiment 5 --output runs/formal_v --workers 8
python run.py analyze --experiment 5 --results runs/formal_v --output runs/formal_v_analysis
```

[数据来源说明](docs/DATA_SOURCES_CN.md) 包含精确版本、校验和及手动导入方法。仓库保留 GDSC 训练/测试 ID 划分；Year 使用官方顺序划分。重新执行实验后，`analyze --results` 读取生成的完整运行目录，其中包含 III 偏差分析和 IV 诊断所需的保存状态。V的默认分析现为经验汇总和图形，不再自动执行历史均值检验。

## 文档与来源记录

- [论文图表：输入、命令与输出对照](docs/PAPER_RESULTS_CN.md)
- [当前及历史验证记录](validation/README.md)
- [仿真数据、指标定义和统计解释](docs/SIMULATION_DATA_CN.md)
- [实验 V 经验结果、尾部诊断与历史分析](evidence/experiment5/README_CN.md)
- [真实数据官方获取渠道](docs/DATA_SOURCES_CN.md)
- [可选数值诊断与扩展](docs/ADVANCED_DIAGNOSTICS_CN.md)
- [论文引用与代码版本标识](docs/CITATION.md)
- [仓库维护及冻结源码记录](docs/MAINTENANCE.md)

`MANIFEST.json` 记录发布文件及其校验和；`simulations/manifest.json` 描述 I—IV 数据；`provenance/` 记录固定输入及源码来源。内部目录和模块名中的历史日期用于识别保存的计算记录。引用某次结果所用材料时，请记录准确的 Git 提交。

## 历史分析

V 的原单侧检验及后续双侧/Holm 分析单独保留为历史证据；其定义、命令和限制见[历史分析说明](docs/HISTORICAL_ANALYSES_CN.md)。这些分析不作为当前 V 报告的推断依据。早期验收记录以原始字节保存在 `validation/history/`。
