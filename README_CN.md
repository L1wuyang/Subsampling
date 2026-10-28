# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**论文配套代码与实验材料** · [English](README.md)

本仓库配套 Junchen Li、Ying-Ao Wang 和 Ye Zhang 的上述论文，提供实验 I—V 的实现、I—IV 的仿真输入和逐次指标，以及 V 的保存指标与统计分析材料。实现采用论文中的实际递推与固定网格四阶 Runge–Kutta（RK4）计算，并使用匹配的完整数据目标、导数、抽样概率和随机种子。

## 实验与文件对应

| 实验 | 研究内容 | 随仓库提供的材料 |
| --- | --- | --- |
| I | 列抽样概率比较 | `simulations/experiment1/`：40 份输入、指标、结果表和协议元数据 |
| II | 行抽样概率比较 | `simulations/experiment2/`：40 份输入、指标、结果表和协议元数据 |
| III | 一阶条件 MSE 校准 | `simulations/experiment3/`：20 份列输入、20 份行输入、指标和结果表 |
| IV | 同次抽样最小二乘比较 | `simulations/experiment4/`：每个方向五份输入、指标、结果表和数值诊断 |
| V | GDSC 与 YearPredictionMSD 应用 | `evidence/experiment5/`：保存指标、配对比较和统计重分析；[原始数据官方来源](docs/DATA_SOURCES_CN.md) |

I—IV 合计 **130 份 NPZ 输入、1,432,512 条逐次指标**。[仿真数据说明](docs/SIMULATION_DATA_CN.md) 解释字段、分组和统计含义；V 的[统计材料说明](evidence/experiment5/README_CN.md) 给出保存指标及联合 36 项 Holm 分析的复核方法。

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

重新计算 V 的双侧配对检验和联合 Holm 校正：

```text
python evidence/experiment5/reanalyze.py --output runs/reported_v
```

上述命令分析随仓库提供的实验记录。可用 `--experiment 1` 至 `4` 单独选择仿真实验；每次使用新的输出目录。已有详细结果表位于各仿真实验的 `tables/` 及 V 的 `reference/` 目录。

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

[数据来源说明](docs/DATA_SOURCES_CN.md) 包含精确版本、校验和及手动导入方法。仓库保留 GDSC 训练/测试 ID 划分；Year 使用官方顺序划分。重新执行实验后，`analyze --results` 读取生成的完整运行目录，其中包含 III 偏差分析和 IV 诊断所需的保存状态。

## 文档与来源记录

- [仿真数据、指标定义和统计解释](docs/SIMULATION_DATA_CN.md)
- [实验 V 保存指标与统计核验](evidence/experiment5/README_CN.md)
- [真实数据官方获取渠道](docs/DATA_SOURCES_CN.md)
- [可选数值诊断与扩展](docs/ADVANCED_DIAGNOSTICS_CN.md)
- [论文引用与代码版本标识](docs/CITATION.md)
- [仓库维护及冻结源码记录](docs/MAINTENANCE.md)

`MANIFEST.json` 记录发布文件及其校验和；`simulations/manifest.json` 描述 I—IV 数据；`provenance/` 记录固定输入及源码来源。内部目录和模块名中的历史日期用于识别保存的计算记录。引用某次结果所用材料时，请记录准确的 Git 提交。
