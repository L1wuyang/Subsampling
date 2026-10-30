# 论文图表与数值证据对照

[English](PAPER_RESULTS.md) · [仓库说明](../README_CN.md) · [模拟数据](SIMULATION_DATA_CN.md) · [实验 V 证据](../evidence/experiment5/README_CN.md)

本页把当前正文的六幅图，以及补充材料的四幅图和十三张表，对应到已发布的输入、命令和结果。图表编号附带 LaTeX 标签或图片文件名，便于版面变化后追踪。除 `figures/*.pdf` 表示论文源文件包内的图片资产外，下列路径均相对于仓库根目录。仓库不包含论文源文及其最终排版资产。

## 各工作流能复现什么

- **保存数值证据：**I–IV 的逐次指标分片、报告 CSV 表、协议与核验记录已公开，可在不重跑数值轨迹的情况下核对数值和统计单位。
- **便捷汇总：**`simulation-data summarize` 生成每个数据集的均值、数据集等权汇总及简易 PNG 图，不导出论文最终版式、置信带或 LaTeX 表格。特别地，论文 III/IV 主图选取 `data_id=1`，便捷图则对数据集汇总。
- **当前 V 的两张目标误差图：**`evidence/experiment5/empirical.py` 读取保存记录，对照 `paper_plot_reference.json` 恢复 276 个绘图均值、面板范围，导出无均值置信带的 PDF/SVG/PNG。这是针对两张图的复现入口，不重新拟合模型；不保证不同渲染环境产生逐字节相同的 PDF。
- **其余最终图片版式：**下表给出数值来源，但仓库尚未包含 I–IV 及 V 预测图的最终投稿版式导出器。完整运行的分析器会输出对应科学图，版式或标签不同；重命名文件不等于恢复投稿原图。

## 命令、输入与输出

安装 `requirements-lock.txt` 后，在仓库根目录执行。每个写出结果的命令应使用新的输出目录。

**C0 — 核验发布文件与保存证据，不执行数值轨迹。**

```bash
python run.py verify
python run.py simulation-data verify --experiment all
python evidence/experiment5/reanalyze.py --verify
```

这些命令分别检查包清单、I–IV 文件哈希和记录结构/数量，以及 V 证据归档。核验已保存证据与从头独立生成证据是不同操作。

**C1 — 从 I–IV 保存指标重算便捷汇总。**

```bash
python run.py simulation-data summarize --experiment all --output runs/paper_saved_metrics
```

输入：`simulations/experimentN/records/*.csv.gz` 和 `simulations/manifest.json`。输出包括 `runs/paper_saved_metrics/verification.json`、`summary_manifest.json`，以及 `expN/{dataset_means.csv,equal_dataset_summary.csv,record_status_counts.csv,figures/}`。图片采用指标名，例如 `relative_gap.png`、`true_coef_rel_sq.png`、`scaled_squared_gap.png`。先在各数据集内平均重复抽样，再对数据集等权平均。C1 不重算归档中的假设检验，也不执行 III 依赖完整状态的全部分析。

**C2 — 从保存记录复现当前 V 经验汇总与两张目标误差图。**

```bash
python -B evidence/experiment5/empirical.py --output runs/paper_v
```

输入：`evidence/experiment5/saved_records.tar.gz`、其清单和 `paper_plot_reference.json`。输出包括 `summary.csv`、`full_prediction_reference.csv`、`rankings.json`、`figure_validation.json`、`auxiliary_figure_validation.json`、`saved_evidence_verification.json`、两份 `r5_*_target_plotted_points.csv` 和 `figures/`。`summary.csv` 保留四种规则，仅隐藏图中与 UNI 重复的 GDSC NORM 曲线。辅助 `figures/04_prediction.{pdf,svg,png}` 重算预测均值与匹配全模型参考值，其版式不同于论文图片。

**C3 — 查看已发布表格，不重新执行分析。**

以下示例打印补充表 G.1 对应的数值；其他表可按下表更换 CSV 与筛选条件：

```bash
python -c "import pandas as pd; t=pd.read_csv('simulations/experiment3/tables/robustness_summary.csv'); print(t.loc[t.budget.eq(19200)].to_string(index=False))"
```

输出为标准输出中的已保存表格切片。C0 核验文件来源和完整性，C1 则可另外检查底层标量均值；这些命令都不是论文表格的自动排版导出器。

**R — 重新生成数值轨迹，再分析新的完整运行目录。**

以实验 III 为例：

```bash
python run.py formal --experiment 3 --output runs/new_iii --workers 2
python run.py analyze --experiment 3 --results runs/new_iii --output runs/new_iii_analysis
```

其他实验替换 `3` 及输出目录。V 还需要 [DATA_SOURCES_CN.md](DATA_SOURCES_CN.md) 中的官方原始数据。完整运行可能较耗时；`smoke` 使用缩减设置检查执行流程，不属于论文证据。分析入口需要新生成的完整目录，不能只传入发布的指标分片。I/II 分析位于 `expN/outputs/formal_01/`，III–V 分析位于 `expN/`。III 的均值误差平方还需保存状态，IV 回放需要状态与抽样计数；本发布包未包含全部此类轨迹数组。原实验目录中的旧 `paper`、`render`、`package`、`verify` 子命令不是受支持的快捷入口，其中部分引用未随包提供的交付/核验模块。

## 正文六幅图

下表 `Tn` 表示 `simulations/experimentn/tables/`。所有 I–IV 表格输入均可用 C0 核验，并用 C1 汇总其底层标量记录。

| 论文图 / 论文图片资产 | 数值输入与筛选 | 命令和输出 | 复现范围 |
| --- | --- | --- | --- |
| 图 1，`fig:v7_probability_column`；`01_target_approximation.pdf` | T1 `summary_curves.csv`，`metric=relative_gap`；40 个数据集均值、13 个预算、6 种方法、4 种规则；字段 `mean,ci_low,ci_high`。 | C0/C1；便捷图 `exp1/figures/relative_gap.png`。I 的 R 分析另生成 `01_target_approximation.*`。 | 已发布表含 312 个均值及逐点区间；最终论文版式属于论文资产。 |
| 图 2，`fig:v7_probability_row`；`r2_01_target_approximation.pdf` | T2 `summary_curves.csv`，`metric=relative_gap`；汇总方式同图 1。 | C0/C1；便捷图 `exp2/figures/relative_gap.png`。II 的 R 分析在其独立分析目录生成 `01_target_approximation.*`。 | 312 个均值与区间；C1 不导出最终版式。 |
| 图 3，`fig:v7_absolute_mse`；`r3_01_mse_absolute_compact.pdf` | T3 `mse_summary.csv`，`arm=main,data_id=1`；`mean,low95,high95,theory=C/budget`，两种方向，每点 500 次抽样。 | C0/C1；C3 查看原表。III 的 R 分析输出 `exp3/figures/01_mse_absolute_compact.*` 和 `mse_summary.csv`。 | 156 个经验均值及一阶曲线和区间；不能用 C1 的跨数据集平均图替代。 |
| 图 4，`fig:v7_ls_gap`；`r4_01_scaled_gap.pdf` | T4 `gap_summary.csv`，`arm=main,data_id=1`；`mean,lower,upper`。均值字段**已经**乘 N，每点 100 次抽样。 | C0/C1/C3；IV 的 R 分析输出 `exp4/figures/01_scaled_gap.*` 和 `gap_summary.csv`。 | 156 个均值；对数轴只绘制下端点为正的区间。保留 H.2 对高预算 Nesterov 数值分辨率的限定。 |
| 图 5，`fig:real_column_fixed`；`r5_01_gdsc_target.pdf` | V 保存抽样记录，`dataset=gdsc`；`relative_coefficient_error`，30 次重复。 | C2 → `figures/r5_01_gdsc_target.{pdf,svg,png}`、`r5_01_gdsc_target_plotted_points.csv`。 | 当前图专用导出：108 个可见均值；GDSC NORM=UNI，无均值置信带。 |
| 图 6，`fig:real_row_fixed`；`r5_02_year_target.pdf` | V 保存抽样记录，`dataset=year`；`relative_coefficient_error`，50 次重复。 | C2 → `figures/r5_02_year_target.{pdf,svg,png}`、`r5_02_year_target_plotted_points.csv`。 | 当前图专用导出：168 个可见均值，无均值置信带。 |

## 补充材料四幅图

| 论文图 / 论文图片资产 | 数值输入与筛选 | 命令和输出 | 复现范围 |
| --- | --- | --- | --- |
| 图 E.1，`fig:native_coef`；`03_true_coefficient_risk.pdf` | T1 `summary_curves.csv`，`metric=true_coef_rel_sq`；`mean,ci_low,ci_high`，另加零预测器单位参考线。 | C0/C1；便捷图 `exp1/figures/true_coef_rel_sq.png`。I 的 R 分析生成 `03_true_coefficient_risk.*`。 | 312 个均值及基于 40 个数据集均值的区间。论文风险纵轴为线性轴，便捷图样式不同。 |
| 图 F.1，`fig:row_native_coef`；`r2_03_true_coefficient_risk.pdf` | T2 `summary_curves.csv`，指标与字段同 E.1。 | C0/C1；便捷图 `exp2/figures/true_coef_rel_sq.png`。II 的 R 分析生成 `03_true_coefficient_risk.*`。 | 范围同 E.1；该设计下总体相对信号风险等于系数风险。 |
| 图 G.1，`fig:v7_mse_ratio`；`r3_02_mse_ratio.pdf` | T3 `mse_summary.csv`，`arm=main,data_id=1`；`ratio,ratio_low95,ratio_high95` 与单位线。 | C0/C3；III 的 R 分析输出 `exp3/figures/02_mse_ratio.*`。 | 156 个比值及条件区间；C1 不导出该比值图。 |
| 图 I.1，`fig:real_native_prediction`；`r5_04_prediction.pdf` | V 抽样 `test_response_rmse` 及 12 个目标汇总的 `full.response_test_rmse`。 | C2 → `summary.csv`、`full_prediction_reference.csv`、`figures/04_prediction.*`。 | 相同预测均值和全模型参考值，不导出论文紧凑版式。逐次 RMSE 的均值不等于 MSE 均值的平方根。 |

## 补充数值表与协议表

对于已保存的 CSV/JSON，C0 核验文件，C3 示例展示查看方式；仅在论文排版时舍入数值。这里的命令不宣称自动生成 LaTeX 表格。

| 表 / LaTeX 标签 | 已发布来源与准确筛选 | 命令、输出和解释 |
| --- | --- | --- |
| D.1 `tab:native_shared_defaults` | I–III `metadata/protocol.json`、`Experiments/experiment5_native_realdata_20261025/formal_protocol.json`，以及冻结源码中的数值更新定义。 | C0 后查看协议。这是固定终止时间构造/参数定义表，不是 Monte Carlo 表。HBF 方程选正根；解析定义和证明不是实验生成结果。 |
| E.1 `tab:native_primary` | T1 `summary_curves.csv` 选 `metric=relative_gap,budget=150,rule=OPT` 得 OPT 均值；T1 `primary_comparisons.csv` 中 UNI/NORM/LEV 各基线的 `ratio` 给出预指定预算的比值。 | C0/C3；I 的 R 分析重算分析表。对 40 个数据集均值平均，不改变汇总总体。 |
| E.2 `tab:native_risks` | T1 `risk_r600.csv` 选 `rule=OPT`，取 `relative_gap,true_coef_rel_sq,design_signal_rel_sq,population_signal_rel_sq`；对应完整目标的 `true_coef_rel_sq` 来自 T1 `full_reference.csv`，在数据集间平均。 | C0/C3；保留目标误差、系数、设计信号、总体信号的不同分母。 |
| F.1 `tab:row_native_primary` | T2 `summary_curves.csv` 和 `primary_comparisons.csv`，N=150；筛选与字段同 E.1。 | C0/C3；II 的 R 分析重算分析表。 |
| F.2 `tab:row_native_risks` | T2 `risk_r600.csv` 选 `rule=OPT`，另用 T2 `full_reference.csv`。 | C0/C3；目标误差/系数/设计字段同 E.2，但论文最后一列是 `population_response_mse`（未来响应 MSE），不是总体信号风险。 |
| G.1 `tab:v7_robustness` | T3 `robustness_summary.csv` 选 `budget=19200`；按方向/方法查看 `median,minimum,maximum`。 | C0/C3；每组为 20 个数据集的比值。最小—最大是观察范围，不是置信区间。 |
| G.2 `tab:v7_decomposition` | T3 `endpoint_decomposition.csv`，`budget=38400,arm=main,data_id=1`；`ratio,linear_ratio,remainder_ratio,cross_ratio`。 | C0/C3；检查总量=线性+余项+带符号交叉项，每项基于 500 次抽样。 |
| H.1 `tab:exp4_endpoints` | T4 `endpoint_comparison.csv` 的 `at_1200,at_38400,endpoint_ratio`。 | C0/C3；用 T4 `gap_summary.csv` 的 `arm=main,data_id=1` 交叉核对。保留 Nesterov 的分辨率限定。 |
| H.2 `tab:exp4_replay` | `simulations/experiment4/metadata/verification.json` 的 `dense_native_replays`，选 `budget=38400`；`relative_coefficient_difference,replay_change_over_gap`。 | C0 后查看 JSON：10 行保存结果，5 种方法×2 个方向，第 0 次重复。`diagnostics/resolution_report.json` 另记录两项 Nesterov 警告。当前根目录 IV 诊断仅回放选定 Nesterov 配置，不能冒充完整十行表重建。 |
| H.3 `tab:exp4_tails` | T4 `gap_summary.csv`，`arm=tails,budget=60`；`mean,median,maximum,top_one_percent_share`。 | C0/C3；6 组、每组 1,000 次抽样。最后一列是 0–1 的份额，不是次数，也不是已乘 100 的百分数。 |
| I.1 `tab:rd_min_parameters` | V 归档 `formal_01/protocol.json`、抽样字段 `prescribed_steps`、目标汇总 `c`，以及冻结目标构造代码。Year 附加值见 `evidence/experiment5/tail_diagnostics/reference/diagnosis.json`、`witness_inputs.json`。 | C0；用 Python `tarfile` 读取归档（前缀见下）。协议和记录的步数无需拟合即可核对。标量归档**没有**包含全部原始逐方法目标参数数组；重建全部精确步长/终点需官方数据工作流，不能把论文舍入值当完整精度输入。 |
| I.2 `tab:real_calibration` | C2 `summary.csv` 中的 `first_order_relative_value,empirical_to_first_order`；原目标汇总另含 `constants`。 | C2。固定预算下以 C=`budget * first_order_relative_value` 算 OPT/UNI、OPT/LEV，再取 OPT 在最小/最大预算的 K（GDSC 75/2996；Year 500/50000）。这里比较经验均值与一阶值。 |
| I.3 `tab:real_prediction_compact` | C2 `summary.csv` 选 GDSC N=2996、Year N=50000，字段 `test_response_rmse_mean`；另取 `full_prediction_reference.csv` 的 `matched_full_test_rmse`。 | C2；表内保留全部四种规则，包括 GDSC NORM/UNI 重复项。它们是对曾探索过测试集的描述性比较。 |

`saved_records.tar.gz` 内 V 运行前缀为 `Experiments/experiment5_native_realdata_20261025/outputs/formal_01/`，其下包含 `draws/<dataset>/r<budget>_rep<index>.csv`、`targets/<dataset>/<method>/summary.json` 和 `protocol.json`。读取归档成员不需要解压或下载原始数据；归档清单列出了各成员与校验和。

## 核对论文时需要保留的边界

I–IV 的主要数值表和逐次指标已公开，但尚无一条命令以相同字体和排版导出全部投稿图表。请采用上述明确筛选，勿将数据集等权均值替代首个数据集图，勿删除失败或尾部观察，勿重新解释零响应下未定义的相对误差，也勿把缩减的 smoke 检查称为正式重复。尾部见证及输入重建的适用范围见[便携诊断说明](../evidence/experiment5/tail_diagnostics/README.md)。保存指标核验不会恢复缺失的历史轨迹数组，也不会增加新的科学结论。
