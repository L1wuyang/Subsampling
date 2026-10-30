# Repository maintenance

[Repository guide](../README.md) · [中文说明](../README_CN.md)

Reproduction commands are in the root README; the [paper result map](PAPER_RESULTS.md) identifies each figure and numerical table. [Current validation](../validation/README.md) records checks for the version in [VERSION](../VERSION).

## Entry points and frozen sources

Use the root `run.py` for core verification, data acquisition, experiment execution and analysis. The current V saved-record entry point is `evidence/experiment5/empirical.py`. Its imported `reanalyze.py` remains in the core; the required historical reference files arrive with the review data. The [tail guide](../evidence/experiment5/tail_diagnostics/README.md) describes portable diagnostics and restoration.

`Experiments/` preserves the scientific algorithms and source history. Some nested III/IV commands still refer to modules from the original full workspace, and the archived V analyzer describes the earlier inferential workflow. Use the documented root adapters for current reports. Retained original source modules and paths are execution/hash dependencies, not endorsements of every legacy command.

`provenance/frozen_scientific_sources.json` identifies protected source and protocol files. III/IV pilot records are execution hash gates. Some experiments import separate copies of reference modules even when their bytes are identical. Preserve these source bytes and gates when changing packaging or documentation. The prospective `stable-v` extension was removed from the submission core; it remains in the [previous full snapshot](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4).

## Core and data inventories

- `MANIFEST.json` inventories the tracked core. `python run.py verify` must succeed in a fresh source download with no review data installed.
- `provenance/review_data.json` identifies the versioned data ZIP, its SHA-256, source commit and every member's original bytes/hash. It is part of the core and fixes what the installer accepts.
- The data installer restores the original `simulations/` and evidence-data paths. Those files stay ignored by Git; do not add them back to the core manifest.
- The simulation manifest comes from the data archive. `evidence/experiment5/MANIFEST.json` stays in the core and checks its mixture of core helpers and installed evidence, including original archive members.

If a core file covered by the evidence manifest changes, update only that file's bytes/SHA-256 entry. Preserve unchanged data hashes and all `archive_members` entries. The root manifest tool does not regenerate the nested evidence manifest. A change to review-data contents requires a new versioned archive and descriptor; do not replace an existing published asset under the same name.

## Validate and release

Review the intended additions and removals, then stage them before regenerating the core inventory:

```text
git add -A
python tools/update_manifest.py
python tools/update_manifest.py --check
python run.py verify
python run.py preflight --experiment simulations
git add MANIFEST.json
git diff --check
git diff --cached --check
git status --short
```

In a separate clean checkout, install the prepared local review-data ZIP and check the restored evidence before publishing it:

```text
python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip
python run.py review-data verify
python run.py simulation-data verify --experiment all
python -B evidence/experiment5/empirical.py --output runs/release_v_check
```

Use a new report directory. Run relevant smoke/analysis or installer checks for changed execution paths; the checks above do not constitute full numerical replication. Record the checks actually completed in `validation/current_release.json`, without rewriting the original empirical-report verification as a new result.

Build the versioned core and data archives from the fixed prior source snapshot into a new output directory:

```text
python tools/build_release.py --output ../release-dist-v2026.10.30.2
```

For a local checkout of the immutable data-source commit, add `--source-dir /path/to/26989d3-checkout`. The builder checks the source/member hashes and writes `Subsampling-core-v2026.10.30.2.zip`, `Subsampling-review-data-v2026.10.30.2.zip`, `SHA256SUMS.txt`, `release_notes.md` and `build_validation.json`. Keep these build outputs outside the tracked core inventory.

Keep `VERSION`, the review-data descriptor and release notes consistent. The release workflow packages and checks the core and the immutable-source review data before creating the corresponding tag/Release and uploading assets. Inspect its result and compare the uploaded assets' checksums before citing the release. Publish changed contents under a new version; do not move an existing release tag or overwrite published assets. The manuscript's fixed links should identify that tag/commit and its separate review-data download.

## 中文维护说明

根目录 `run.py` 是当前复现入口。V 的 `empirical.py` 使用核心包中的 `reanalyze.py` 校验逻辑，以及复核数据安装的历史参考文件。原算法、reference 副本、协议和 III/IV pilot 门禁继续按原字节保留；旧目录中的所有子命令并非都属于当前支持流程。独立 `stable-v` 扩展已移出核心包，可在上述固定旧提交查看。

根 `MANIFEST.json` 只覆盖核心文件；`provenance/review_data.json` 固定数据 ZIP 与成员校验值。安装后恢复原数据路径，但这些数据应继续被 Git 忽略。V 的嵌套清单仍在核心中；修改其覆盖的核心说明或脚本时，只更新对应条目，不改原数据及压缩包成员哈希。

发布前分别检查“无保存数据的核心包”和“安装数据后的复核流程”，按实际执行结果更新当前验证记录。版本号、数据描述文件和 Release notes 保持一致。检查发布工作流、tag 指向和附件校验和后再在论文中引用；后续改动另用新版本，不移动旧 tag，不覆盖已发布附件。旧版资料保留在 Git 提交历史中。
