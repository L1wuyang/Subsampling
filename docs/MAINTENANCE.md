# Repository maintenance

[Repository guide](../README.md) · [中文说明](../README_CN.md)

This page is for maintainers. The reproduction commands are in the root README.

## Entry points and frozen sources

Use the root `run.py` for verification, data acquisition, experiment execution and analysis. The current V saved-record entry point is `evidence/experiment5/empirical.py`; `evidence/experiment5/reanalyze.py` preserves historical mean-based analyses. Portable tail checks and reconstruction are documented in `evidence/experiment5/tail_diagnostics/README.md`.

The scripts under `Experiments/` preserve the scientific implementation and its source history. Some nested III/IV commands refer to verification or delivery modules from the original full workspace. The archived V analyzer preserves the original one-sided analysis and mean-confidence bands. These are historical entry points; the root workflow now uses `repro1026/empirical_v.py` for current empirical-only V reporting, while I–IV retain their analysis paths.

`provenance/frozen_scientific_sources.json` identifies the protected source and protocol files. III/IV pilot records also provide source-hash gates used by the execution workflow. Reference modules can be imported by other experiments even when their contents are identical. Retain these files and hashes when editing documentation or adding statistical evidence.

Historical paths, dates and acceptance records identify the computations they describe. New checks belong in a new validation record; earlier successful-check records retain their original content.

## Update the repository

Make changes in the local Git checkout, keeping the directory structure. Retain `.gitattributes` so Git preserves frozen source bytes, and `.gitignore` so downloaded real data, local runs and caches stay outside the release.

After reviewing changes:

```text
python tools/update_manifest.py
python tools/update_manifest.py --check
python run.py verify
python run.py simulation-data verify --experiment all
python evidence/experiment5/empirical.py --output runs/release_v_check
python evidence/experiment5/reanalyze.py --output runs/release_v_historical_check
git diff --check
git status --short
```

Choose a fresh V check output path. The manifest tool updates the root release inventory and checks protected sources; it preserves the simulation-data manifest and frozen-source records.

Review the exact files, commit them and push the reviewed commit. Upload extracted repository files rather than a ZIP containing another copy of the repository. For a manuscript revision, record the actual commit in the code availability statement and verify that its referenced paths exist at that commit. A label or tag should identify that same immutable version.

## 中文维护说明

复现读者统一使用根目录 `run.py`；V当前经验汇总使用 `evidence/experiment5/empirical.py`，历史均值分析使用 `evidence/experiment5/reanalyze.py`。`Experiments/` 中的内嵌入口及旧V单侧分析作为来源记录保留，部分旧命令依赖原完整工程，不作为本仓库的公开运行入口。

修改文档或增加统计材料时，保留冻结源码、协议、reference 模块以及 III/IV pilot 门禁文件的原始字节。历史路径和验收记录对应原运行，新校验另存记录。完成更改后按上面的命令更新发布清单、执行校验，检查 Git 差异，再提交和推送。

论文代码可用性说明中的固定提交号，需要与实际包含引用文件的提交一致。使用准确的提交或固定标签识别版本，避免只用本地日期式目录名代替版本定位。
