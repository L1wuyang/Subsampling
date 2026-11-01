# Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework

**论文配套代码与实验材料** · [English](README.md)

**2026-11-01 结果更新。** 收录全支撑稳定实验五、模拟 Ridge 分数对照及 GDSC Ridge Li–Niu 对照，附独立版本实现与保存证据。VERSION 和 v2026.10.30.2 标识此前保持不变的代码与复核数据归档；三个更新实验随当前仓库提供。[更新说明](docs/RESULTS_UPDATE_20261101.md) · [论文图表对照](docs/PAPER_RESULTS_CN.md)

本仓库配套 Junchen Li、Ying-Ao Wang 和 Ye Zhang 的论文。I—IV 冻结科学来源与原公开输入结果保持原样；实验 V 采用全支持稳定协议，并补入 Ridge 列抽样分数对照。迭代方法继续执行实际递推与固定网格 RK4，采用匹配的完整数据数值目标和算法导数。

## 报告结果

| 实验 | 保存证据 | 解释 |
| --- | --- | --- |
| 全支持稳定 V | [evidence/experiment5_stable](evidence/experiment5_stable/README_CN.md)：12,720 条完整标量指标，530 组抽样，48 项全支持门禁、目标摘要及原校验回执 | 在原四规则 UNI/NORM/LEV/OPT 中，OPT 在 78/78 个组合观测均值最低；有限重复不证明完整条件 MSE 排序。 |
| Ridge Li–Niu 分数对照 | [evidence/ridge_liniu](evidence/ridge_liniu/README_CN.md)：104,000 条完整指标，40 份既有输入，13 预算，5 规则及原校验 | N=150 的 FULL−LN=-0.0003228063，95% CI=[-0.0009423789,0.0002967663]，双侧 p=.298436；未检出显著差异，不代表等价。 |
| 实验五 GDSC–Ridge LN 补充 | [evidence/gdsc_ridge_liniu](evidence/gdsc_ridge_liniu/README_CN.md)：新增180条LN_floor，保留720条四规则指标；6预算×30次配对 | 最大预算OPT低约0.768%；N=374/749反转，六个逐点配对区间均跨零，没有清楚的有限预算经验优势。 |

误差指相对完整正则化目标的平方系数偏差，不是真实系数恢复或预测风险。LN_floor 与 FULL_OPT 采用共同精确下界约束；未运行 NOPL 或原文外层迭代。[详细解释](docs/LATEST_RESULTS_CN.md)

## 安装与校验

使用 Python 3.11 或 3.12（已记录环境 Windows、Python 3.12.7）：

```text
python -m pip install -r requirements-lock.txt
python run.py verify
```

根清单检查代码与紧凑证据；`provenance/frozen_scientific_sources.json` 保留 54 份冻结科学来源哈希和 III/IV pilot 门禁。原验证回执描述原检查，读取回执不等于重复状态数组校验。

## 不重跑轨迹复算最新结果

两项分析无需真实原始数据或旧 240 MB 包，每次指定新的输出目录：

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

检查来源 SHA-256，重新计算全部标量均值、相应区间与校准、唯一 Ridge 主比较并输出便捷 PDF/PNG 图。数值轨迹执行次数为零，不冒充重新完成原独立状态校验。完整未裁剪指标、协议、门禁与原回执已保存，前两项的轨迹数组及官方原始数据不包含在紧凑包中；本次GDSC–LN新增的180个状态、随机数和计数随证据保存，可按独立入口核验。

最终论文六幅图的精确副本位于 `evidence/paper_figures_20261101/`。按期刊版式重绘：

```text
python -B tools/make_review_paper_figures.py --evidence-root evidence --output runs/paper_figures --qa-output runs/paper_figure_qa --receipt runs/paper_figure_receipt.json
```

## I—IV 与历史 V

此前公开 v2026.10.30.2 的 review-data 包为 240,281,192 字节、545 个文件，恢复 I—IV 输入结果及历史 V，不覆盖三个最新证据目录。I—IV 共 130 份 NPZ 输入、1,432,512 条逐次指标。

```text
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

离线安装：`python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip`。描述文件固定哈希且拒绝冲突覆盖。旧 V 均值、罕见事件见证与旧 Holm 分析保留在 [evidence/experiment5](evidence/experiment5/README_CN.md)，用于追溯，不作为新稳定版本曲线。[仿真数据说明](docs/SIMULATION_DATA_CN.md) · [图表对照](docs/PAPER_RESULTS_CN.md)

## 完整重跑

I—IV 继续使用根 CLI 的 `preflight`、`smoke`、`formal` 与 `analyze`（见英文入口）。稳定V与模拟分数对照使用独立协议，新增GDSC Ridge对照见文末入口：

- [稳定 V 实现及完整重跑说明](Experiments/experiment5_support_stable_20261031/README_CN.md)：需要官方数据和历史完整目标/数组，轻量包不足以单独重跑；先通过分块伴随 pilot，再通过全支持门禁释放抽样。
- [Ridge 对照实现](Experiments/ridge_liniu_ablation_20261101/README_CN.md)：先安装旧 review-data 恢复 40 份原输入，再按准备、pilot 与前序门禁执行。输入复用属于消融，不称为新数据独立确认。

根入口 `formal --experiment 5` 仍执行旧冻结 V 协议，本次报告的 V 使用独立稳定版目录。[真实数据来源](docs/DATA_SOURCES_CN.md)说明官方输入与校验。

## 文档与来源

[图表](docs/PAPER_RESULTS_CN.md) · [结果解释](docs/LATEST_RESULTS_CN.md) · [验证范围](validation/README.md) · [进一步诊断](docs/ADVANCED_DIAGNOSTICS_CN.md) · [引用](docs/CITATION.md) · [维护](docs/MAINTENANCE.md)

根清单覆盖代码与报告所用紧凑指标；review-data 描述与 VERSION 保留旧基线，新科学改动以独立协议版本标识，不改旧冻结哈希。原记录保留历史路径，PROVENANCE.json 固定复制文件哈希；三个实验以各自协议版本及证据目录中的来源哈希定位。

## GDSC Ridge Li-Niu addendum / 实验五新增对照

[Results / 结果](evidence/gdsc_ridge_liniu/README.md) · [运行与状态核验](Experiments/experiment5_gdsc_liniu_20261101/README_CN.md)

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_check.json
```
