# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**论文配套代码与实验材料** · [English](README.md)

**版本 [v2026.10.30.2](VERSION)** · [Release 与下载](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.10.30.2) · [当前验证记录](validation/README.md)

本仓库配套 Junchen Li、Ying-Ao Wang 和 Ye Zhang 的上述论文，核心包提供实验 I—V 的实现、协议、校验与报告工具及说明；仿真输入、逐次指标、结果表和 V 诊断输入另放在独立复核数据包中。实现采用论文中的实际递推与固定网格四阶 Runge–Kutta（RK4）计算，并使用匹配的完整数据目标、导数、抽样概率和随机种子。

核验某项论文结果，请先看**[论文图表对照表](docs/PAPER_RESULTS_CN.md)**；了解已有检查的范围，请看**[验证记录说明](validation/README.md)**。实验 V 当前报告有限重复抽样的经验均值，不据此确立完整条件 MSE 排序。

## 代码与复核数据

[Release](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.10.30.2) 分别提供两个下载：

- `Subsampling-core-v2026.10.30.2.zip`：核心代码、冻结协议、源码校验值与说明，解压后共 107 个文件、约 1.2 MB，可独立校验代码并重新生成仿真实验。
- [`Subsampling-review-data-v2026.10.30.2.zip`](https://github.com/L1wuyang/Subsampling/releases/download/v2026.10.30.2/Subsampling-review-data-v2026.10.30.2.zip)：此前发布的全部 545 份仿真与保存证据文件，保留原始字节；压缩包为 240,281,192 字节（约 240 MB）。安装后可不重跑轨迹而复核已报告结果。

Git 历史仍保留旧版的大数据文件，因此普通完整 `git clone` 仍会下载这些历史内容。只获取小体积核心包时，使用 Release 核心 ZIP，或按本版 tag 浅克隆：

```text
git clone --depth 1 --branch v2026.10.30.2 https://github.com/L1wuyang/Subsampling.git
```

复核数据包不包含 GDSC/Year 官方原始数据，也不包含全部轨迹级状态数组；完整重跑时另行获取或生成。安装会恢复原相对路径，数据不加入核心代码的跟踪清单。拆分说明见[版本说明](docs/RELEASE_NOTES.md)。

## 实验与文件对应

| 实验 | 研究内容 | 安装复核数据后的位置 |
| --- | --- | --- |
| I | 列抽样概率比较 | `simulations/experiment1/`：40 份输入、指标、结果表和协议元数据 |
| II | 行抽样概率比较 | `simulations/experiment2/`：40 份输入、指标、结果表和协议元数据 |
| III | 一阶条件 MSE 校准 | `simulations/experiment3/`：20 份列输入、20 份行输入、指标和结果表 |
| IV | 同次抽样最小二乘比较 | `simulations/experiment4/`：每个方向五份输入、指标、结果表和数值诊断 |
| V | GDSC 与 YearPredictionMSD 应用 | `evidence/experiment5/`：保存指标、经验图形和尾部诊断；[原始数据官方来源](docs/DATA_SOURCES_CN.md) |

I—IV 合计 **130 份 NPZ 输入、1,432,512 条逐次指标**。[仿真数据说明](docs/SIMULATION_DATA_CN.md) 解释字段、分组和统计含义；V 的[材料说明](evidence/experiment5/README_CN.md) 给出当前经验汇总、论文图形和尾部诊断的复核方法。

## 安装与完整性检查

使用 Python 3.11 或 3.12；已记录的验证环境为 Windows 上的 Python 3.12.7。在仓库根目录运行：

```text
python -m pip install -r requirements-lock.txt
python run.py verify
```

`requirements-lock.txt` 和 `environment.json` 记录依赖与验证环境。下列流程统一使用**根目录 `run.py`**；`Experiments/` 内嵌脚本作为源代码记录保留，详见[入口与冻结源码说明](docs/MAINTENANCE.md#entry-points-and-frozen-sources)。

## 安装复核数据

下载对应版本的数据包，检查压缩包及全部成员的 SHA-256，并恢复指定路径：

```text
python run.py review-data download
python run.py review-data verify
```

离线使用时，在其他机器从 Release 下载数据 ZIP，再安装本地文件：

```text
python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip
```

把示例路径替换为本机 ZIP 路径。`provenance/review_data.json` 固定压缩包与文件校验值；安装器拒绝覆盖内容不符的现有文件。`python run.py verify` 只校验核心包，`review-data verify` 校验安装后的数据，均不启动实验。

## 从保存指标核验论文结果

安装复核数据后，核验并重新计算 I—IV 的数据集内均值、数据集等权汇总和部分图：

```text
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

该命令生成保存记录的便捷汇总和图形，并不直接生成全部论文排版图。[图表对照表](docs/PAPER_RESULTS_CN.md)逐项说明数据选择及所需的额外步骤。

复现 V 当前的经验汇总及两张不含均值置信区间的论文目标误差图：

```text
python -B evidence/experiment5/empirical.py --output runs/reported_v
python -B evidence/experiment5/tail_diagnostics/verify_witnesses.py
python -B evidence/experiment5/tail_diagnostics/verify_stability.py
```

上述命令分析已安装复核数据中的实验记录。可用 `--experiment 1` 至 `4` 单独选择仿真实验；每次使用新的输出目录。V 使用 12,720 条保存指标和包含 276 个点的目标图参考。[尾部诊断说明](evidence/experiment5/tail_diagnostics/README.md)提供轻量见证与稳定性核验，以及独立的输入重建流程。

## 重新运行实验

`smoke` 缩小维度、预算和重复次数，用于检查计算及报告流程；`formal` 执行完整的冻结实验协议。

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis

python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

重新生成仿真实验不要求预先安装保存的复核数据。`simulations` 选择 I—IV；`--experiment 1` 至 `5` 单独选择一个实验。完整运行按冻结种子重新生成输入。IV 约需执行 405 亿次更新，建议先用 `smoke` 检查流程，再安排完整运行资源。

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
- [当前验证记录](validation/README.md)
- [仿真数据、指标定义和统计解释](docs/SIMULATION_DATA_CN.md)
- [实验 V 经验结果与尾部诊断](evidence/experiment5/README_CN.md)
- [真实数据官方获取渠道](docs/DATA_SOURCES_CN.md)
- [进一步数值诊断](docs/ADVANCED_DIAGNOSTICS_CN.md)
- [论文引用与代码版本标识](docs/CITATION.md)
- [仓库维护及冻结源码记录](docs/MAINTENANCE.md)

`MANIFEST.json` 记录核心文件及其校验和；`provenance/review_data.json` 标识独立数据附件，安装后的 `simulations/manifest.json` 描述 I—IV 数据；`provenance/` 同时记录固定输入及源码来源。内部目录和模块名中的历史日期用于识别保存的计算记录。引用某次结果所用材料时，请记录准确的 Git 提交。

## 早期材料

[完整旧版](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4)保留此前代码与数据合并的布局，以及本核心包移除的可选 `stable-v` 扩展；更早的验证记录与历史说明可沿提交历史查看。V 的旧均值检验不作为当前经验报告的推断依据。归档校验代码保留在核心包，所需历史参考文件随复核数据安装。冻结源码模块与 pilot 门禁因复现流程调用或校验而保留；保留原源码路径不代表所有旧子命令都是受支持的论文流程。
