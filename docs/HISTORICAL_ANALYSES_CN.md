# 历史分析与协议记录

[当前实验 V 流程](../evidence/experiment5/README_CN.md) · [English](HISTORICAL_ANALYSES.md)

本页区分早期分析记录与当前报告流程。本次仅整理文档入口；脚本、原始指标归档、参考表和科学协议保留在原路径，其原始字节不变。

## 当前报告

保存的实验 V 记录使用 `evidence/experiment5/empirical.py`，新生成的完整运行使用根目录 `run.py analyze --experiment 5`。两者都报告有限重复的经验汇总和描述性图形，不生成均值检验或均值置信带。这些汇总不建立完整条件 MSE 的排序；预测比较也只作描述性解释，因为测试集曾被探索使用。

[尾部诊断](../evidence/experiment5/tail_diagnostics/README.md)仍属于当前证据，用于解释经验汇总的限制。下面的历史 p 值不能替代这些诊断。

## 历史证据位置

| 材料 | 仓库位置 | 用途 |
| --- | --- | --- |
| 原始逐次记录与单侧比较表 | `evidence/experiment5/saved_records.tar.gz` | 保留 530 份逐次 CSV、12,720 条标量记录、12 份完整目标摘要、协议及执行元数据。单侧表位于归档成员 `Experiments/experiment5_native_realdata_20261025/outputs/formal_01/primary_comparisons.csv`。 |
| 后续双侧/Holm 比较表 | `evidence/experiment5/reference/paired_comparisons_two_sided.csv` | 历史统计修订的冻结输出。 |
| 详细统计修订及输入哈希 | `evidence/experiment5/reference/inference_revision.json` | 记录历史比较家族、计算结果和来源输入。 |
| 保留的重分析实现 | `evidence/experiment5/reference/reanalyze_saved_v.py` | 原分析脚本，通过下面的归档适配入口调用。 |
| 公开历史校验／重放入口 | `evidence/experiment5/reanalyze.py` | 先校验并提供原归档路径，再执行保留脚本。 |
| 来源与校验清单 | `evidence/experiment5/PROVENANCE.json` 和 `evidence/experiment5/MANIFEST.json` | 标识来源归档，校验证据文件及归档成员。 |

## 校验或重放历史均值分析

`evidence/experiment5/reference/` 保留此前的双侧比较表、详细统计修订报告及原始保存记录分析脚本。它们与更早的单侧比较表均为历史记录，不是当前实验 V 的推断依据。来源记录见 `evidence/experiment5/PROVENANCE.json`，包内文件及归档成员的校验值见 `evidence/experiment5/MANIFEST.json`。

需要明确核验或重放历史分析时执行：

```bash
python -B evidence/experiment5/reanalyze.py --verify
python -B evidence/experiment5/reanalyze.py --output runs/experiment5_historical
```

仅校验的命令使用 Python 标准库；历史重分析使用 NumPy、pandas 和 SciPy。它在 GDSC 预算 749、Year 预算 5,000 处重新计算 36 项双侧配对 Student t 检验，统一进行一次 Holm 校正，并核对保存的参考表；比较家族保留 GDSC NORM/UNI 重复项。输出包括 `paired_comparisons_two_sided.csv`、`inference_revision.json`、`mean_coefficient_errors.csv` 和 `verification.json`。

历史 p 值、标准误和逐点 95% 区间不涵盖尾部诊断揭示的稀有事件贡献，也未调整历史参数及测试集探索，因此不用于推断完整条件 MSE 的排序。适配脚本仅将通过校验的普通文件释放到临时目录，再调用保留的历史脚本，不拟合模型或产生新抽样。

## 冻结科学协议与内嵌入口

`Experiments/` 保留科学算法、协议和来源历史。其中 `Experiments/experiment5_native_realdata_20261025/formal_protocol.json` 及其归档分析器仍描述早期统计流程。其单侧／双侧检验或置信带说明记录的是当时的计算，不是当前经验报告的执行说明。当前报告由 `repro1026/empirical_v.py` 以及文档指定的根目录／保存记录入口实现。

实验 III/IV 的部分内嵌命令引用原完整工程中的验证或交付模块。新校验、运行和分析统一使用根目录 `run.py`。根目录适配层仍导入 `Experiments/` 中的科学模块，`provenance/frozen_scientific_sources.json` 列出的文件及 III/IV pilot 哈希门禁也仍是依赖；不能因为目录名包含历史日期就删除。

早期包验收记录集中列于 [validation/README.md](../validation/README.md)。其中日期、环境、校验值、旧路径和结论描述的是当时受检版本，不代表本次目录整理重新执行了那些检查。当前入口与保留策略见[仓库维护说明](MAINTENANCE.md)。
