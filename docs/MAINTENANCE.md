# Repository maintenance

[Repository guide](../README.md) · [中文说明](../README_CN.md)

This page is for maintainers. Reproduction commands are in the root README, and the [paper result map](PAPER_RESULTS.md) identifies each figure and numerical table. The [validation guide](../validation/README.md) describes the checks for the numbered release in [VERSION](../VERSION).

## Entry points and frozen sources

Use the root `run.py` for verification, data acquisition, experiment execution and analysis. The current V saved-record entry point is `evidence/experiment5/empirical.py`. Retain `evidence/experiment5/reanalyze.py` and `evidence/experiment5/reference/`: the current workflow imports their archive-verification code and checks reference hashes. Portable tail checks and reconstruction are documented in `evidence/experiment5/tail_diagnostics/README.md`.

The scripts under `Experiments/` preserve the scientific implementation and its source history. Some nested III/IV commands refer to verification or delivery modules from the original full workspace. The archived V analyzer preserves the original one-sided analysis and mean-confidence bands. These are historical entry points; the root workflow now uses `repro1026/empirical_v.py` for current empirical-only V reporting, while I–IV retain their analysis paths.

`provenance/frozen_scientific_sources.json` identifies the protected source and protocol files. III/IV pilot records also provide source-hash gates used by the execution workflow. Reference modules can be imported by other experiments even when their contents are identical. Retain these files and hashes when editing documentation or adding statistical evidence.

The [complete previous version](https://github.com/L1wuyang/Subsampling/tree/5e1c6b81166b2b574aef6e439aadfb143996793d) preserves earlier acceptance records and detailed historical analyses. Historical paths and dates identify the computations they describe. Record current release checks in `validation/current_release.json`, retaining the original empirical-report verification record unchanged.

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

The manifest tool updates the root release inventory and checks protected sources; it preserves the simulation-data manifest and frozen-source records. Also rerun the affected workflow when changes alter its code, data or report behavior. For V, use `python evidence/experiment5/empirical.py --output runs/release_v_check`; choose a fresh output directory. Documentation-only organization does not require rerunning the full experiments.

For a numbered release, keep `VERSION` and `validation/current_release.json` consistent with the reviewed changes before sealing the manifests. Review the exact files, commit them and push the reviewed commit. Upload extracted repository files rather than a ZIP containing another copy of the repository. For a manuscript revision, record the actual commit in the code availability statement and verify that its referenced paths exist at that commit. A version tag should identify that same immutable version.

## 中文维护说明

复现读者统一使用根目录 `run.py`，V 当前经验汇总使用 `evidence/experiment5/empirical.py`。当前流程仍依赖 `evidence/experiment5/reanalyze.py` 和 `evidence/experiment5/reference/` 中的归档校验代码及参考文件，须保留这些依赖。`Experiments/` 中的内嵌入口作为来源记录保留，部分旧命令依赖原完整工程，不作为本仓库的公开运行入口。

修改文档或增加统计材料时，保留冻结源码、协议、reference 模块以及 III/IV pilot 门禁文件的原始字节。历史路径对应原运行，早期验收记录及详细历史说明可从[完整旧版](https://github.com/L1wuyang/Subsampling/tree/5e1c6b81166b2b574aef6e439aadfb143996793d)追溯。当前编号版本及检查分别记录在 `VERSION` 和 `validation/current_release.json`，原经验报告核验记录保持不变。若改动了 V 证据清单覆盖的文件，先更新 `evidence/experiment5/MANIFEST.json` 中对应文件的字节数及 SHA-256，不改其他条目或压缩包成员记录。然后按上面的命令暂存已审阅的增删移动、更新根发布清单并校验，再提交和推送。代码、数据或报告行为改变时另行复测受影响流程；仅整理文档不需要重跑完整实验。

论文代码可用性说明中的固定提交号，需要与实际包含引用文件的提交一致。使用准确的提交或固定标签识别版本，避免只用本地日期式目录名代替版本定位。
