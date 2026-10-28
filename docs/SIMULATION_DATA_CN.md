# 实验 I—IV 仿真数据说明

[English](SIMULATION_DATA.md) · [仓库使用说明](../README_CN.md)

`simulations/` 提供原始仿真输入、论文结果对应的逐次指标和汇总表。输入 NPZ 保持原始字节；指标保留原字段，敏感性、零响应和尾部记录全部收录。

## 内容与数量

| 实验 | 输入 NPZ | 主实验及稳健性记录 | 敏感性记录 | 独立尾部记录 | 零响应记录 | 合计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| I：列概率 | 40 | 499,200 | 46,080 | 0 | 720 | 546,000 |
| II：行概率 | 40 | 499,200 | 46,080 | 0 | 720 | 546,000 |
| III：一阶 MSE | 40 | 306,000 | 9,600 | 0 | 360 | 315,960 |
| IV：同次抽样 LS | 10 | 18,480 | 0 | 6,000 | 72 | 24,552 |
| **总计** | **130** | **1,322,880** | **101,760** | **6,000** | **1,872** | **1,432,512** |

III、IV 的稳健性数据计入主实验列；分析时仍按数据集与实验臂分组。

```text
simulations/
  manifest.json
  experiment1/ ... experiment4/
    inputs/       原始仿真 NPZ 输入
    records/      每次重复的 CSV.gz 分片
    tables/       当前汇总、比较及风险表
    metadata/     协议、执行记录、参数和来源
  experiment4/diagnostics/
```

I—III 的主实验与敏感性指标分别分片，零响应记录包含在敏感性组中。IV 将原分块 CSV 合并为 `records/metrics.partXXXX.csv.gz`，保留标识每条观测的字段。

I—III 输入保存冻结构造器使用的基础高斯变量、噪声、系数方向、尺度或尖峰变量；IV 输入保存已经构造的设计、响应、真系数和总体风险相关量。III 包含 20 份列输入与 20 份行输入，IV 各 5 份。可用 `np.load(path, allow_pickle=False)` 直接读取。正式入口仍按冻结种子生成输入，没有自动改为加载这些文件。

汇总表优先采用当前重建后的报告版本，其余保留冻结正式表；IV 使用已修正数值诊断语义的版本。协议记录种子、预算与重复次数。历史验证记录描述原运行，其内部路径仍为原档案路径；本次发布对应关系见 `simulations/manifest.json`。

## 核验并汇总

```text
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/reported_simulations
```

可用 `--experiment 1` 至 `4` 单独选择实验。输出根包含 `verification.json` 和 `summary_manifest.json`；各 `expN/` 下生成 `dataset_means.csv`、`equal_dataset_summary.csv`、`record_status_counts.csv` 和 `figures/`。每次选用新的输出目录。

先在每个数据集内按预算、方法和实验臂计算重复均值，再按 `data_id` 等权汇总。遇到未定义或非有限指标时，均值保留 NaN，并记录有效数。图展示主实验，各实验臂仍全部保留在输出表中。此命令从发布指标计算便捷摘要，不执行数值轨迹。

自行分析时，pandas 可直接读取 gzip 分片：

```python
from pathlib import Path
import pandas as pd

shards = sorted(Path("simulations/experiment4/records").glob("*.csv.gz"))
records = pd.concat((pd.read_csv(path) for path in shards), ignore_index=True)
```

实验内唯一键：I/II 为 `(data_id, arm, budget, method, rule, rep)`；III/IV 为 `(direction, data_id, arm, budget, method, rep)`。已发布记录没有重复键。汇总表是派生统计，不能追加为新的重复观测。

## 解释结果时的条件

| 字段或条件 | 含义 |
| --- | --- |
| `budget` | 有放回抽样次数，论文中记为 N；重复抽到同一对象仍计入预算。 |
| `data_id`、`rep`、`rule` | I/II 推断单位为 40 个独立数据集的均值。sketch 重复条件于该数据；方法和概率规则之间共享配对随机性。不能将全部 sketch 当作独立数据集。 |
| `arm`、`direction` | 参数、噪声、设计敏感性、零响应、尾部以及行列方案分别定义不同组。 |
| `relative_gap`、`absolute_gap` | I—III 相对各方法冻结完整数值目标的系数平方误差，分别为归一化值和绝对值；各方法的目标不同。 |
| `true_coef_rel_sq`、`design_signal_rel_sq` | 相对仿真真系数的系数风险、固定设计上的信号风险；与目标逼近误差不同。 |
| `population_signal_rel_sq`、`population_response_mse` | 未来设计信号风险和未来响应 MSE；后者包含不可约噪声。行方案的总体相对信号风险可能在代数上等于系数风险。 |
| `linear_relative`、`remainder_relative`、`cross_relative` | III 的误差分解；交叉项有符号，可以为负，比较实际与一阶 MSE 时须完整保留。 |
| `scaled_squared_gap`、`absolute_squared_gap`、`relative_squared_gap` | IV 与同一次抽样的 QR 最小二乘比较；缩放量为 N 乘绝对平方差。 |
| `status`、相对指标缺失 | 1,872 条零目标/零响应记录的相对指标未定义，保留空值/NaN；`status` 标识运行状态，尾部原记录完整保留。 |
| `rank`、`unique_objects`/`unique_rows`、`spike_draws` | 抽样对象的秩与覆盖；低覆盖和重复抽样属于原抽样分布。 |
| IV 数值诊断 | `resolution_limited` 只描述最终相减的局部尺度。发布诊断另保留两项尚未解决的选定重放警告和六组尾部集中警告，`accuracy_certified` 为 false；解释对应微小差距和尾部均值时须同时查看。 |
| OPT | 利用完整数据和响应的一阶概率设计 oracle；目标逼近改善本身不代表预测更优或总计算成本更低。 |
| V 的统计 | 保存指标和统计参考文件另见 [V 统计材料目录](../evidence/experiment5/README_CN.md)。分析使用双侧配对检验和一次联合 36 项 Holm；历史测试探索使预测比较仍属于描述性证据。 |

III/IV 的逐点 Monte Carlo 区间条件于指定完整数据和参数路径。正式表保留原不确定性计算；便捷汇总不改变统计单位，也不建立新的检验家族。

## 完整重跑

新生成的完整运行目录继续使用 `formal` 或 `smoke`，再用 `analyze --results`。发布指标使用独立入口，是因为 III 的完整分析从状态向量计算偏差，IV 重放还需要状态和抽样计数。本补充提供已有表和诊断；完整重跑会生成这些流程所需的额外数值输出。

完整状态、影响量和抽样计数由完整重跑生成。V 的原始数据获取方式见[数据来源说明](DATA_SOURCES_CN.md)；[V 保存指标核验流程](../evidence/experiment5/README_CN.md) 可直接使用随仓库提供的记录检查统计结果。
