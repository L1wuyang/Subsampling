# Current validation records

[Repository guide](../README.md) · [仓库说明](../README_CN.md)

The release identifier is [VERSION](../VERSION). This directory retains the current reporting evidence and the checks for this package:

| Record | Scope |
| --- | --- |
| [current_release.json](current_release.json) | Checks for v2026.10.30.1: source/data preservation, dependency-safe removal, local links and saved-evidence verification. |
| [current_empirical_release_20261030.json](current_empirical_release_20261030.json) | Original verification of the current empirical V reporting and portable tail/stability diagnostics. Retained unchanged; its entries are not claims that the underlying experiments were rerun for this package. |

Earlier engineering acceptance records and the previous organization record are omitted from this version. Their original files and detailed historical explanations remain available in the [complete previous snapshot](https://github.com/L1wuyang/Subsampling/tree/5e1c6b81166b2b574aef6e439aadfb143996793d). Normal subsequent commits preserve that snapshot.

For the current workflows, use the [reproduction guide](../README.md), [paper result map](../docs/PAPER_RESULTS.md) and [Experiment V evidence guide](../evidence/experiment5/README.md). The root and evidence manifests verify released files; the simulation manifest and source/pilot hash records remain necessary execution inputs.

## 中文说明

当前版本号见 [VERSION](../VERSION)。本目录仅保留本版检查 `current_release.json`，以及当前 V 经验报告和尾部／稳定性诊断的原验证记录 `current_empirical_release_20261030.json`；后一记录保持原始字节，不表示本次重新执行了完整实验。

4 份旧工程验收记录和上一轮整理记录已从本版移除，可在[旧版完整快照](https://github.com/L1wuyang/Subsampling/tree/5e1c6b81166b2b574aef6e439aadfb143996793d)追溯。源码、数据、证据及 pilot 门禁校验文件仍是复现依赖，继续保留。当前使用方法见[仓库说明](../README_CN.md)与[论文图表对照](../docs/PAPER_RESULTS_CN.md)。
