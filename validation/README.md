# Validation records for the reported experiments

[November 1 reported-results checks](reported_results_checks_20261101.json) record the saved-metric reanalysis, evidence hashes, six figure assets and exact scope of the current checks.

## GDSC Ridge comparison

The GDSC comparison executes 180 new direct Ridge solves. It preserves all 720 previous GDSC Ridge records. `Experiments/experiment5_gdsc_liniu_20261101/analyze.py` separately verifies 900 records, 30 summaries, six paired intervals, and (with original inputs) all 180 newly saved states without further solves. The evidence is `evidence/gdsc_ridge_liniu/`; the 78/78 ranking excludes this fifth rule. All new intervals are pointwise Monte Carlo intervals conditional on one fixed dataset.

## November 1 saved-record checks

The original checks for stable V and Ridge are copied with unchanged bytes into their respective `evidence/` directories. Those checks used saved states at the original run directories. `tools/analyze_latest_saved.py` separately verifies bundled hashes, complete record grids, all saved scalar means/intervals/calibrations and the Ridge primary comparison; it executes zero trajectories and does not repeat state-array validation. `tools/make_review_paper_figures.py` redraws the final journal figure layouts from checked tables. Exact assets are copied with a receipt.

Use `python tools/update_manifest.py --check` to verify the root inventory.
The 54 historical scientific source hashes, III/IV pilot gates and the
545-member review-data descriptor remain anchored to their original records.
See [results update](../docs/RESULTS_UPDATE_20261101.md) and the saved verification
receipts in this directory for their precise scope. Collection-time labels such
as "local" or "published: false" in preserved receipts describe the time the
checks were made; they do not replace the current repository status.

## Earlier published baseline records

### Earlier archive validation

[Repository guide](../README.md) · [仓库说明](../README_CN.md)

The release identifier is [VERSION](../VERSION). This directory retains the current reporting evidence and the checks for this package:

| Record | Scope |
| --- | --- |
| [current_release.json](current_release.json) | Checks for v2026.10.30.2: source/data separation, archive integrity and installation, core verification, local links and saved-evidence reporting. Read the record for the exact completed checks. |
| [current_empirical_release_20261030.json](current_empirical_release_20261030.json) | Original verification of the historical empirical V reporting and portable tail/stability diagnostics. Retained unchanged; its entries are not claims that the underlying experiments were rerun for this package. |

Earlier engineering acceptance records and the previous organization record are omitted from this version. Their original files and detailed historical explanations remain available through the commit history of the [complete previous snapshot](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4). Normal subsequent commits preserve that snapshot.

For the earlier baseline workflows, use the [reproduction guide](../README.md), [paper result map](../docs/PAPER_RESULTS.md) and [Experiment V evidence guide](../evidence/experiment5/README.md). The root manifest verifies core files without installed data. The review-data descriptor verifies the separate archive and restored files; the installed simulation manifest and the core evidence manifest provide their detailed checks. Source/pilot hash records stay in the core because execution depends on them.

## 中文说明

当前版本号见 [VERSION](../VERSION)。本目录仅保留本版检查 `current_release.json`，以及历史 V 经验报告和尾部／稳定性诊断的原验证记录 `current_empirical_release_20261030.json`；后一记录保持原始字节，不表示本次重新执行了完整实验。

此前移除的旧工程验收记录及组织说明可沿[旧版完整快照](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4)的提交历史追溯。本版核心清单不要求安装保存数据；独立数据由复核数据描述文件及安装后的原清单校验。源码与 pilot 门禁留在核心包，数据与参考证据通过独立附件安装。当前使用方法见[仓库说明](../README_CN.md)与[论文图表对照](../docs/PAPER_RESULTS_CN.md)。

The reported V workflow is [full-support stable V](../evidence/experiment5_stable/README.md); the new Ridge ablation is [here](../evidence/ridge_liniu/README.md).
