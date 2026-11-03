# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

Junchen Li、Dianpeng Wang、Ying-Ao Wang 与 Ye Zhang 的论文配套代码和实验材料。[English](README.md)

投稿版本 **v2026.11.02.1** 包含实验 I—IV、全支撑稳定实验 V，以及模拟与 GDSC Ridge 分数对照。[论文图表索引](docs/PAPER_RESULTS_CN.md) · [数值与解释](docs/LATEST_RESULTS_CN.md) · [引用](docs/CITATION.md)

## 安装与校验

使用 Python 3.11 或 3.12；原实验记录环境为 Windows、Python 3.12.7。以下命令均在仓库根目录执行，每次分析使用新输出目录。

```text
python -m pip install -r requirements-lock.txt
python run.py verify
```

## 复核保存结果

三个当前实验的紧凑证据随仓库提供。以下命令核验标量记录并重算汇总，无需运行估计量或获取真实原始数据：

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_check.json
```

| 实验 | 随附证据 | 完整重跑 |
| --- | --- | --- |
| 稳定 V：GDSC 与 YearPredictionMSD | [12,720 条标量记录与支撑稳定性证书](evidence/experiment5_stable/README_CN.md) | [指南](Experiments/experiment5_support_stable_20261031/README_CN.md) |
| 模拟 Ridge 分数对照 | [40 份既有输入上的 104,000 条标量记录](evidence/ridge_liniu/README_CN.md) | [指南](Experiments/ridge_liniu_ablation_20261101/README_CN.md) |
| GDSC Ridge 分数对照 | [180 个 LN_floor 状态与 900 条对照记录](evidence/gdsc_ridge_liniu/README_CN.md) | [指南](Experiments/experiment5_gdsc_liniu_20261101/README_CN.md) |

稳定 V 的核验覆盖记录完整性、标量汇总及完整目标的完整性与协议间比较，不包含逐草图状态误差的独立重算。GDSC 状态核验另需原预处理输入。稳定 V 和模拟 Ridge 的轨迹数组未随紧凑包分发。[核验范围](validation/README.md)

I—IV 输入和保存结果来自 **v2026.10.30.2 数据归档**（240 MB、545 个文件，含历史 V），单独安装：

```text
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

离线安装见[仿真数据说明](docs/SIMULATION_DATA_CN.md)；图表的精确数据选择及六幅随附论文图的重绘命令见[论文图表索引](docs/PAPER_RESULTS_CN.md)。

## 从输入完整运行

I—IV 使用根入口：

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

Smoke 使用缩小规模，仅检查运行流程。正式运行可能昂贵，历史 IV 约含 405 亿次更新。当前 V 和 Ridge 对照请使用上表独立指南。根入口 `formal --experiment 5` 生成稳定 V 所需的历史 V 输入与完整目标，不能直接替代报告中的稳定协议。[真实数据获取](docs/DATA_SOURCES_CN.md)

## 解释与来源

各实验分别评价系数目标近似、真实系数恢复和预测。有限重复的观测排序不证明完整条件 MSE 排序。两项 Li–Niu 对照采用共同概率下界下的精确分数，未评价 NOPL 或原文外层迭代，也未确立 FULL/OPT 相对 LN_floor 的显著有限预算优势。详细数值与边界集中在[结果说明](docs/LATEST_RESULTS_CN.md)。

`MANIFEST.json` 列出代码源文件及校验值；`provenance/frozen_scientific_sources.json` 标识已记录实验采用的科研实现。`provenance/review_data.json` 标识数据版本及压缩包、成员文件的校验值。引用时注明实际分析采用的代码 tag/commit 及数据版本。[维护](docs/MAINTENANCE.md) · [进一步诊断](docs/ADVANCED_DIAGNOSTICS_CN.md) · [发行说明](docs/RELEASE_NOTES.md)
