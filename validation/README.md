# Current validation records

[Repository guide](../README.md) · [仓库说明](../README_CN.md)

The release identifier is [VERSION](../VERSION). This directory retains the current reporting evidence and the checks for this package:

| Record | Scope |
| --- | --- |
| [current_release.json](current_release.json) | Checks for v2026.10.30.2: source/data separation, archive integrity and installation, core verification, local links and saved-evidence reporting. Read the record for the exact completed checks. |
| [current_empirical_release_20261030.json](current_empirical_release_20261030.json) | Original verification of the current empirical V reporting and portable tail/stability diagnostics. Retained unchanged; its entries are not claims that the underlying experiments were rerun for this package. |

Earlier engineering acceptance records and the previous organization record are omitted from this version. Their original files and detailed historical explanations remain available through the commit history of the [complete previous snapshot](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4). Normal subsequent commits preserve that snapshot.

For the current workflows, use the [reproduction guide](../README.md), [paper result map](../docs/PAPER_RESULTS.md) and [Experiment V evidence guide](../evidence/experiment5/README.md). The root manifest verifies core files without installed data. The review-data descriptor verifies the separate archive and restored files; the installed simulation manifest and the core evidence manifest provide their detailed checks. Source/pilot hash records stay in the core because execution depends on them.

## 中文说明

当前版本号见 [VERSION](../VERSION)。本目录仅保留本版检查 `current_release.json`，以及当前 V 经验报告和尾部／稳定性诊断的原验证记录 `current_empirical_release_20261030.json`；后一记录保持原始字节，不表示本次重新执行了完整实验。

此前移除的旧工程验收记录及组织说明可沿[旧版完整快照](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4)的提交历史追溯。本版核心清单不要求安装保存数据；独立数据由复核数据描述文件及安装后的原清单校验。源码与 pilot 门禁留在核心包，数据与参考证据通过独立附件安装。当前使用方法见[仓库说明](../README_CN.md)与[论文图表对照](../docs/PAPER_RESULTS_CN.md)。
