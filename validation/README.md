# Validation records for the reported experiments

[Repository guide](../README.md) · [仓库说明](../README_CN.md)

The validation records distinguish integrity checks, reanalysis of saved scalar metrics, and checks using stored estimator states. The [reported-results receipt](reported_results_checks_20261101.json) identifies the evidence hashes and six manuscript figure assets.

## Reported studies

| Study | Evidence and verification |
| --- | --- |
| Full-support stable Experiment V | [Evidence](../evidence/experiment5_stable/README.md), 12,720 scalar records, 530 paired sketch tasks, 48 full-support certificates and the original state-validation receipt. |
| Simulated Ridge score comparison | [Evidence](../evidence/ridge_liniu/README.md), 104,000 scalar records on 40 data sets, a single prespecified primary comparison, and original state-based quadratic-form checks. |
| GDSC Ridge score comparison | [Evidence](../evidence/gdsc_ridge_liniu/README.md), 180 LN_floor records and states, 720 retained baseline records, 30 summary cells and six paired intervals. |

`tools/analyze_latest_saved.py` verifies evidence hashes and reaggregates stable-V and simulated Ridge scalar summaries. The original independent-validation receipts in the evidence directories record the state-array checks. `Experiments/experiment5_gdsc_liniu_20261101/analyze.py` verifies the GDSC scalar records and, with the original inputs, all 180 newly saved states. These analyses use saved results without additional estimator solves or numerical trajectories.

The GDSC paired intervals are pointwise Monte Carlo intervals conditional on one fixed data set. The stable-V 78/78 ranking concerns UNI, NORM, LEV and OPT; the additional LN_floor rule is evaluated separately.

## Source and archive integrity

```text
python tools/update_manifest.py --check
python run.py review-data verify
```

The root manifest covers code and compact evidence. `provenance/frozen_scientific_sources.json` anchors the 54 historical scientific sources and III/IV pilot checks. The separate review-data descriptor checks the 545-file v2026.10.30.2 archive and its installed contents. The archive contains Experiments I–IV and historical V evidence; current stable-V and Ridge-comparison evidence is included directly in this repository.

`current_release.json` and `current_empirical_release_20261030.json` retain the checks for that earlier archive. The current evidence directories and [paper result map](../docs/PAPER_RESULTS.md) identify the records used in the manuscript.

## 中文说明

本目录区分文件完整性、保存标量指标汇总和保存状态数组核验。稳定实验五、模拟 Ridge 分数对照及 GDSC Ridge 对照分别提供协议、指标、来源哈希与原始核验回执。保存指标分析入口重新计算汇总和统计区间；GDSC 入口还可结合原始输入核验全部 180 个新增状态。

根清单核对代码与紧凑证据，冻结来源清单保护 54 份历史科学来源及 III/IV pilot。v2026.10.30.2 独立数据包保留 I—IV 与历史 V 的 545 个文件；当前稿件所用稳定 V 和 Ridge 对照证据随仓库提供。具体实验和图表对应关系见[论文结果索引](../docs/PAPER_RESULTS_CN.md)。
