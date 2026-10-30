# Repository maintenance

[Repository guide](../README.md) · [中文说明](../README_CN.md)

This page is for maintainers. Reproduction commands are in the root README, and the [paper result map](PAPER_RESULTS.md) identifies each figure and numerical table. The [validation guide](../validation/README.md) separates current checks from historical records.

## Entry points and frozen sources

Use the root `run.py` for verification, data acquisition, experiment execution and analysis. The current V saved-record entry point is `evidence/experiment5/empirical.py`; `evidence/experiment5/reanalyze.py` preserves historical mean-based analyses. Portable tail checks and reconstruction are documented in `evidence/experiment5/tail_diagnostics/README.md`.

The scripts under `Experiments/` preserve the scientific implementation and its source history. Some nested III/IV commands refer to verification or delivery modules from the original full workspace. The archived V analyzer preserves the original one-sided analysis and mean-confidence bands. These are historical entry points; the root workflow now uses `repro1026/empirical_v.py` for current empirical-only V reporting, while I–IV retain their analysis paths.

`provenance/frozen_scientific_sources.json` identifies the protected source and protocol files. III/IV pilot records also provide source-hash gates used by the execution workflow. Reference modules can be imported by other experiments even when their contents are identical. Retain these files and hashes when editing documentation or adding statistical evidence.

Historical paths, dates and acceptance records identify the computations they describe. New checks belong in a new validation record; earlier successful-check records retain their original content. Four earlier acceptance records are archived together in `validation/history/`; current reporting and organization records remain in `validation/`.

## Update the repository

Make changes in the local Git checkout, keeping the directory structure. Retain `.gitattributes` so Git preserves frozen source bytes, and `.gitignore` so downloaded real data, local runs and caches stay outside the release.

If any file covered by `evidence/experiment5/MANIFEST.json` changes, first update that file's `bytes` and SHA-256 entry in the evidence manifest. Preserve entries for unchanged files and all `archive_members` records. The root manifest tool does not regenerate this nested evidence manifest.

After reviewing changes, stage the intended file additions, moves and removals so that the inventory reflects the release. Then run:

```text
git add -A
python tools/update_manifest.py
python tools/update_manifest.py --check
python run.py verify
python run.py simulation-data verify --experiment all
git add MANIFEST.json
git diff --check
git diff --cached --check
git status --short
```

The manifest tool updates the root release inventory and checks protected sources; it preserves the simulation-data manifest and frozen-source records. Also rerun the affected workflow when changes alter its code, data or report behavior. For V, use `python evidence/experiment5/empirical.py --output runs/release_v_check`; choose a fresh output directory. Historical reanalysis is a separate workflow documented in [historical analyses](HISTORICAL_ANALYSES.md). Documentation-only organization does not require rerunning the full experiments.

Review the exact files, commit them and push the reviewed commit. Upload extracted repository files rather than a ZIP containing another copy of the repository. For a manuscript revision, record the actual commit in the code availability statement and verify that its referenced paths exist at that commit. A label or tag should identify that same immutable version.

## 中文维护说明

复现读者统一使用根目录 `run.py`；V当前经验汇总使用 `evidence/experiment5/empirical.py`，历史均值分析使用 `evidence/experiment5/reanalyze.py`。`Experiments/` 中的内嵌入口及旧V单侧分析作为来源记录保留，部分旧命令依赖原完整工程，不作为本仓库的公开运行入口。

修改文档或增加统计材料时，保留冻结源码、协议、reference 模块以及 III/IV pilot 门禁文件的原始字节。历史路径和验收记录对应原运行，新校验另存记录；四份早期验收记录放在 `validation/history/`。若改动了 V 证据清单覆盖的文件，先更新 `evidence/experiment5/MANIFEST.json` 中对应文件的字节数及 SHA-256，不改其他条目或压缩包成员记录。然后按上面的命令暂存已审阅的增删移动、更新根发布清单并校验，再提交和推送。代码、数据或报告行为改变时另行复测受影响流程；仅整理文档不需要重跑完整实验。

论文代码可用性说明中的固定提交号，需要与实际包含引用文件的提交一致。使用准确的提交或固定标签识别版本，避免只用本地日期式目录名代替版本定位。
