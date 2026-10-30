# Validation records

[Repository guide](../README.md) · [仓库说明](../README_CN.md)

Each record describes the version, environment and checks named inside it. A historical `passed: true` is not a new test result for the current checkout. Records are retained as evidence rather than rewritten to describe later work.

## Current reporting and organization

| Record | Scope |
| --- | --- |
| [current_empirical_release_20261030.json](current_empirical_release_20261030.json) | Verification of the empirical Experiment V release: preserved sources and metrics, the two target figures, public report entry points and portable tail/stability checks. Its original contents are retained. |
| [submission_organization_20261030.json](submission_organization_20261030.json) | Checks specific to the subsequent submission-package organization, including evidence preservation, relocated records, links and release inventory. This is separate from the earlier scientific/reporting checks. |

For the current workflows, use the [root reproduction guide](../README.md), [Experiment V empirical guide](../evidence/experiment5/README.md) and [tail-diagnostic guide](../evidence/experiment5/tail_diagnostics/README.md).

## Historical acceptance records

The following four JSON records moved together from this directory into `history/`, preserving every byte. The relative `lite_base_acceptance.json` reference inside `acceptance_summary.json` still points to a record in the same directory.

| Record | Historical scope |
| --- | --- |
| [history/lite_base_acceptance.json](history/lite_base_acceptance.json) | Earlier source-only package and smoke-workflow acceptance; includes the former V statistical workflow and notes what was not executed. |
| [history/acceptance_summary.json](history/acceptance_summary.json) | Addition and verification of the I–IV simulation inputs, scalar metrics and tables. |
| [history/metric_reconciliation.json](history/metric_reconciliation.json) | Reconciliation of I–IV saved metrics with the corresponding tables. |
| [history/submission_materials_20261028.json](history/submission_materials_20261028.json) | Checks for the earlier manuscript-companion release, including historical V reanalysis. |

Dates, old local-project references, source hashes and older analysis statements are preserved to identify their original context. Consult [historical analyses](../docs/HISTORICAL_ANALYSES.md) to distinguish the earlier V tests from the current empirical report.

## 中文说明

每份记录只对应其内部标明的版本、环境和检查范围。历史 `passed: true` 不代表当前版本刚刚通过同一检查，旧记录也不会改写为新结果。

- `current_empirical_release_20261030.json` 保留原位置与原始字节，记录经验版实验 V 的源码、指标、目标图、报告入口及尾部／稳定性核验。
- `submission_organization_20261030.json` 单独记录本次投稿包整理的证据保留、历史记录移动、链接和发布清单等检查，不替代前一份科学／报告核验。
- 四份早期验收 JSON 整体移动到 `history/`，字节不变；`acceptance_summary.json` 对 `lite_base_acceptance.json` 的同目录引用保持有效。旧日期、本地工程引用、校验值及早期统计表述用于识别原始上下文。

当前复现入口见[仓库说明](../README_CN.md)和[实验 V 经验报告](../evidence/experiment5/README_CN.md)，旧统计流程见[历史分析说明](../docs/HISTORICAL_ANALYSES_CN.md)。
