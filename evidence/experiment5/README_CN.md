# 实验 V：经验结果与保存证据

本目录对应论文 *Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework* 的 GDSC 与 YearPredictionMSD 真实数据实验。当前报告流程从保存记录复现经验均值、两幅系数目标误差图及描述性诊断。这些有限重复汇总不建立完整条件 MSE 的排序；预测比较也只作描述性解释，因为测试集曾被探索使用。

`saved_records.tar.gz` 保留 530 份原始逐次指标 CSV，共 12,720 条记录，以及 12 份全样本目标汇总、正式协议、执行记录和原单侧比较表。归档保留原始文件字节及相对路径。这些文件是实验输出的标量指标；原始协变量、响应值和拟合系数向量由完整复现流程获取或计算。

## 复现当前经验汇总与图形

在仓库根目录使用仓库固定的数值依赖执行：

```bash
python -B evidence/experiment5/empirical.py --output runs/experiment5_empirical
```

每次选用新的输出目录。命令校验保存归档及全部 530 份逐次文件、12,720 条记录，并根据 `paper_plot_reference.json` 核对论文两幅目标误差图的 276 个可见数据点。程序同时核验 OPT 在全部 78 个“方法—预算”单元中的经验平均系数目标误差最小。GDSC 的 NORM 记录完整保留在汇总中，目标误差图中以 UNI 表示两者重合的曲线。

输出包括：

- `summary.csv`、`summary.json`、`rankings.json`：经验均值、重复次数、经验值与一阶值的比值、已实现样本的稳定性检查及经验排序；
- `figures/r5_01_gdsc_target.*`、`figures/r5_02_year_target.*`：PDF、SVG、PNG 目标误差图，展示经验均值曲线，不带均值置信带；
- `r5_01_gdsc_target_plotted_points.csv`、`r5_02_year_target_plotted_points.csv`、`figure_validation.json`：目标误差绘图数值及与论文参考值的核对结果；
- 经验值与一阶值比值、相对匹配完整模型的测试 RMSE、未修剪误差分布、抽样对象覆盖情况等描述性诊断；
- `saved_evidence_verification.json`：归档校验值、输入数量及核验范围；
- `index.html`：汇总结果及图形的本地页面。

该命令使用保存的标量记录，不拟合模型，也不产生新的随机抽样；不生成均值检验或置信区间。已观察的稳定性检查仅针对实际抽到的矩阵，经验值与一阶值的比值只比较已观察均值和一阶准则，均不证明整个抽样支持集的稳定性或有限预算下条件 MSE 近似准确。

## 核验尾部诊断

[可移植尾部诊断说明](tail_diagnostics/README.md) 提供 Year Landweber UNI/OPT、Showalter UNI、Nesterov UNI 反例的轻量高精度核验、独立的 HBF/SOAR 稳定性前提核验，以及从哈希匹配的官方原始数据完整重建 Year/Landweber 的流程。

```bash
python -B evidence/experiment5/tail_diagnostics/verify_witnesses.py
python -B evidence/experiment5/tail_diagnostics/verify_stability.py
```

轻量核验使用随包提供的紧凑输入，需要 `mpmath==1.3.0`，不需要下载原始数据。诊断说明列明各项检查的前提与适用范围。尾部反例解释有限重复均值为何可能不能代表完整条件 MSE，并未建立所有抽样规则的完整 MSE 排序。

## 早期分析

原单侧及后续双侧/Holm 分析详见[完整旧版](https://github.com/L1wuyang/Subsampling/tree/5e1c6b81166b2b574aef6e439aadfb143996793d)，不作为当前实验 V 的推断依据。当前保存记录流程仍使用 `reanalyze.py` 和 `reference/` 中的归档校验代码及参考校验值，因此保留这些依赖；当前结果使用上面的经验汇总流程。

## 与完整复现的关系

下载官方数据、运行新实验和分析新实验时，使用仓库根目录 `run.py`。当前 `run.py analyze --experiment 5 --results runs/formal_v --output runs/formal_v_analysis` 生成经验汇总和图形，不自动执行历史均值检验。

完整运行指定 `--output runs/formal_v` 时，实验 V 指标保存于 `runs/formal_v/exp5/formal/`；分析指定 `--output runs/formal_v_analysis` 时，报告保存于 `runs/formal_v_analysis/exp5/`。上述保存记录命令直接写入其指定的输出目录。保留的历史脚本所需原完整工程路径由归档适配脚本提供，当前经验汇总流程不依赖这些历史路径。

[English guide](README.md) · [仓库复现说明](../../README_CN.md)