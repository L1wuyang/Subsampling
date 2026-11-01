# 论文图表对照：2026-11-01

[English](PAPER_RESULTS.md) · [仓库说明](../README_CN.md)

论文报告全支撑稳定 V，并包含 Ridge 分数对照。旧 v2026.10.30.2 提供 I—IV 复核数据及历史 V；更新实验的紧凑证据随当前仓库提供。序号可能随新增小节变化，以标签/资产识别。

## 保存指标与最终论文图片

```text
python run.py verify
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/paper_saved_metrics
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

C0 表示核心/已安装复核数据/仿真校验，C1 是 I—IV 保存记录汇总，C3 表示直接查看指定 CSV/JSON，R 是完整重跑并分析。C0/C1/C3 不执行轨迹；I—IV 需旧 review-data，两个新分析只需自带紧凑证据。新分析复算全部标量均值、相应区间/校准与唯一主比较，不重复原独立状态数组校验。便捷图不声明与期刊图相同排版。

最终六幅图的精确副本在 `evidence/paper_figures_20261101/`，对应收据固定来源及 PDF 哈希。期刊版式只读表格重绘：

```text
python -B tools/make_review_paper_figures.py --evidence-root evidence --output runs/paper_figures --qa-output runs/paper_figure_qa --receipt runs/paper_figure_receipt.json
```

重绘 PDF 元数据可能随时间/环境变化，复制的最终资产与本次论文所用文件一致。下文路径相对仓库根，`Tn` 表示 `simulations/experimentn/tables/`。

## 新图片与补充表

| 标签或资产 | 精确来源与筛选 | 解释 |
| --- | --- | --- |
| `fig:real_column_fixed` / `r5_01_gdsc_target.pdf` | `evidence/experiment5_stable/summary.csv`，gdsc，`mean`，每点30次重复；Ridge的LN_floor另读 `evidence/gdsc_ridge_liniu/summary.csv` | NORM=UNI，无均值置信带。 |
| `fig:real_row_fixed` / `r5_02_year_target.pdf` | 同上，year，每点50次重复 | 有限重复经验均值，不是完整 MSE 排序。 |
| `fig:real_native_prediction` / `r5_04_prediction.pdf` | 稳定版 summary `test_rmse`，加上GDSC Ridge LN_floor的新summary；`targets/<dataset>/<method>/summary.json` 的 `full.response_test_rmse` | 逐次 RMSE 均值不是平均 MSE 的平方根；描述性测试集比较。 |
| `r1_04_ridge_liniu.pdf` | `evidence/ridge_liniu/summary.csv` 及 `dataset_means.csv` 的 FULL_OPT−LN_floor 配对差 | 五规则曲线及逐点t39区间，保留全部预算与反转。 |
| `r1_05_ridge_liniu_calibration.pdf` | Ridge summary `calibration`，LN_floor/FULL_OPT，全部13预算 | 小预算约1.58，最大约1.12，不是精确有限样本公式。 |
| `tab:rd_min_parameters` | 稳定版 `candidate_bounds.json`、`support_gate.json`、12份完整目标 summary、`metrics.csv` 的 `prescribed_steps` 与协议 | 替换旧步长表，48项全支持门禁及新抽样种子202610310501。 |
| `tab:real_calibration` | 稳定版 summary：C=`budget*theoretical`，OPT/UNI和OPT/LEV；最小/最大预算的 `empirical_to_first_order` | GDSC 75/2996、Year 500/50000，勿使用旧重算方法常数。 |
| `tab:real_prediction_compact` | 稳定版 summary `test_rmse`，GDSC N=2996、Year N=50000；完整目标预测参考 | 保留全部四规则与GDSC重复项。 |
| Ridge唯一主比较 | `primary_comparison.json`，N=150，40个数据集均值 | FULL−LN=-0.0003228063，95% CI=[-0.0009423789,0.0002967663]，p=.298436，26/40 FULL较低。 |
| Ridge分数诊断 | `score_diagnostics.csv` | 概率TV均值.002990，一阶准则平均降幅.006058%；LN_floor含共同精确下界。 |

## I—IV 正文图的原来源

| 图片 | 来源与筛选 | 命令与输出 | 范围 |
| --- | --- | --- | --- |
| 图 1，`fig:v7_probability_column`；`01_target_approximation.pdf` | T1 `summary_curves.csv`，`metric=relative_gap`；40 个数据集均值、13 个预算、6 种方法、4 种规则；字段 `mean,ci_low,ci_high`。 | C0/C1；便捷图 `exp1/figures/relative_gap.png`。I 的 R 分析另生成 `01_target_approximation.*`。 | 已发布表含 312 个均值及逐点区间；最终论文版式属于论文资产。 |
| 图 2，`fig:v7_probability_row`；`r2_01_target_approximation.pdf` | T2 `summary_curves.csv`，`metric=relative_gap`；汇总方式同图 1。 | C0/C1；便捷图 `exp2/figures/relative_gap.png`。II 的 R 分析在其独立分析目录生成 `01_target_approximation.*`。 | 312 个均值与区间；C1 不导出最终版式。 |
| 图 3，`fig:v7_absolute_mse`；`r3_01_mse_absolute_compact.pdf` | T3 `mse_summary.csv`，`arm=main,data_id=1`；`mean,low95,high95,theory=C/budget`，两种方向，每点 500 次抽样。 | C0/C1；C3 查看原表。III 的 R 分析输出 `exp3/figures/01_mse_absolute_compact.*` 和 `mse_summary.csv`。 | 156 个经验均值及一阶曲线和区间；不能用 C1 的跨数据集平均图替代。 |
| 图 4，`fig:v7_ls_gap`；`r4_01_scaled_gap.pdf` | T4 `gap_summary.csv`，`arm=main,data_id=1`；`mean,lower,upper`。均值字段**已经**乘 N，每点 100 次抽样。 | C0/C1/C3；IV 的 R 分析输出 `exp4/figures/01_scaled_gap.*` 和 `gap_summary.csv`。 | 156 个均值；对数轴只绘制下端点为正的区间。保留 H.2 对高预算 Nesterov 数值分辨率的限定。 |
| 图 G.1，`fig:v7_mse_ratio`；`r3_02_mse_ratio.pdf` | T3 `mse_summary.csv`，`arm=main,data_id=1`；`ratio,ratio_low95,ratio_high95` 与单位线。 | C0/C3；III 的 R 分析输出 `exp3/figures/02_mse_ratio.*`。 | 156 个比值及条件区间；C1 不导出该比值图。 |

## I—IV 补充图的原来源

| 图片 | 来源 | 命令 | 范围 |
| --- | --- | --- | --- |
| 图 E.1，`fig:native_coef`；`03_true_coefficient_risk.pdf` | T1 `summary_curves.csv`，`metric=true_coef_rel_sq`；`mean,ci_low,ci_high`，另加零预测器单位参考线。 | C0/C1；便捷图 `exp1/figures/true_coef_rel_sq.png`。I 的 R 分析生成 `03_true_coefficient_risk.*`。 | 312 个均值及基于 40 个数据集均值的区间。论文风险纵轴为线性轴，便捷图样式不同。 |
| 图 F.1，`fig:row_native_coef`；`r2_03_true_coefficient_risk.pdf` | T2 `summary_curves.csv`，指标与字段同 E.1。 | C0/C1；便捷图 `exp2/figures/true_coef_rel_sq.png`。II 的 R 分析生成 `03_true_coefficient_risk.*`。 | 范围同 E.1；该设计下总体相对信号风险等于系数风险。 |
| 图 G.1，`fig:v7_mse_ratio`；`r3_02_mse_ratio.pdf` | T3 `mse_summary.csv`，`arm=main,data_id=1`；`ratio,ratio_low95,ratio_high95` 与单位线。 | C0/C3；III 的 R 分析输出 `exp3/figures/02_mse_ratio.*`。 | 156 个比值及条件区间；C1 不导出该比值图。 |

## I—IV 补充表的原来源

| 表格 | 来源与筛选 | 解释 |
| --- | --- | --- |
| D.1 `tab:native_shared_defaults` | I–III `metadata/protocol.json`、`Experiments/experiment5_native_realdata_20261025/formal_protocol.json`，以及冻结源码中的数值更新定义。 | C0 后查看协议。这是固定终止时间构造/参数定义表，不是 Monte Carlo 表。HBF 方程选正根；解析定义和证明不是实验生成结果。 |
| E.1 `tab:native_primary` | T1 `summary_curves.csv` 选 `metric=relative_gap,budget=150,rule=OPT` 得 OPT 均值；T1 `primary_comparisons.csv` 中 UNI/NORM/LEV 各基线的 `ratio` 给出预指定预算的比值。 | C0/C3；I 的 R 分析重算分析表。对 40 个数据集均值平均，不改变汇总总体。 |
| E.2 `tab:native_risks` | T1 `risk_r600.csv` 选 `rule=OPT`，取 `relative_gap,true_coef_rel_sq,design_signal_rel_sq,population_signal_rel_sq`；对应完整目标的 `true_coef_rel_sq` 来自 T1 `full_reference.csv`，在数据集间平均。 | C0/C3；保留目标误差、系数、设计信号、总体信号的不同分母。 |
| F.1 `tab:row_native_primary` | T2 `summary_curves.csv` 和 `primary_comparisons.csv`，N=150；筛选与字段同 E.1。 | C0/C3；II 的 R 分析重算分析表。 |
| F.2 `tab:row_native_risks` | T2 `risk_r600.csv` 选 `rule=OPT`，另用 T2 `full_reference.csv`。 | C0/C3；目标误差/系数/设计字段同 E.2，但论文最后一列是 `population_response_mse`（未来响应 MSE），不是总体信号风险。 |
| G.1 `tab:v7_robustness` | T3 `robustness_summary.csv` 选 `budget=19200`；按方向/方法查看 `median,minimum,maximum`。 | C0/C3；每组为 20 个数据集的比值。最小—最大是观察范围，不是置信区间。 |
| G.2 `tab:v7_decomposition` | T3 `endpoint_decomposition.csv`，`budget=38400,arm=main,data_id=1`；`ratio,linear_ratio,remainder_ratio,cross_ratio`。 | C0/C3；检查总量=线性+余项+带符号交叉项，每项基于 500 次抽样。 |
| H.1 `tab:exp4_endpoints` | T4 `endpoint_comparison.csv` 的 `at_1200,at_38400,endpoint_ratio`。 | C0/C3；用 T4 `gap_summary.csv` 的 `arm=main,data_id=1` 交叉核对。保留 Nesterov 的分辨率限定。 |
| H.2 `tab:exp4_replay` | `simulations/experiment4/metadata/verification.json` 的 `dense_native_replays`，选 `budget=38400`；`relative_coefficient_difference,replay_change_over_gap`。 | C0 后查看 JSON：10 行保存结果，5 种方法×2 个方向，第 0 次重复。`diagnostics/resolution_report.json` 另记录两项 Nesterov 警告。当前根目录 IV 诊断仅回放选定 Nesterov 配置，其核验范围限于所选配置，完整十行表需使用对应的保存记录。 |
| H.3 `tab:exp4_tails` | T4 `gap_summary.csv`，`arm=tails,budget=60`；`mean,median,maximum,top_one_percent_share`。 | C0/C3；6 组、每组 1,000 次抽样。最后一列是 0–1 的份额，不是次数，也不是已乘 100 的百分数。 |

旧V见证及Holm分析保留在 `evidence/experiment5/`，其数值与旧步长不用于新图表。复算标量不恢复全部轨迹数组，不建立新数据独立确认或端到端加速结论。

## GDSC Ridge Li-Niu addendum / 实验五新增对照

`fig:real_column_fixed` (`r5_01_gdsc_target.pdf`) and `fig:real_native_prediction` (`r5_04_prediction.pdf`) additionally use `evidence/gdsc_ridge_liniu/summary.csv`, rule=LN_floor, for the GDSC Ridge panel only. Other methods and Year are unchanged.

New supplement `fig:gdsc_liniu` / `r5_05_gdsc_liniu.pdf` reads all 30 five-rule cells and `paired_comparisons.csv`; `tab:gdsc_liniu_budgets` contains all six paired results. Intervals are pointwise t29 Monte Carlo intervals across 30 common-uniform sketches of one fixed dataset, rather than t39 intervals across simulated datasets. All new budgets are descriptive. At N=2996 LN_floor/OPT errors are .02879534/.02857425; at N=374/749 OPT is higher. The 78/78 claim applies only to the original four rules.

Saved scalar reanalysis (no additional estimator solves):

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_check.json
```
