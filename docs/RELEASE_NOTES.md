# v2026.10.30.2 — Core code and separate review data

This version separates the submission code from saved numerical evidence. A source download contains the experiment implementations, frozen protocols, verification/reporting tools and guides. The large saved-data tree is installed only when checking the reported results.

## Assets

| Asset | Contents |
| --- | --- |
| `Subsampling-core-v2026.10.30.2.zip` | Core code and documentation, with its file inventory. |
| `Subsampling-review-data-v2026.10.30.2.zip` | All 545 previously released data/evidence files: the complete 524-file simulation tree and 21 Experiment V saved-evidence/reference inputs. Original file bytes are preserved. |
| `SHA256SUMS.txt` | Checksums for the packaged downloads. |

The review-data archive includes 130 simulation inputs, 1,432,512 I–IV per-repetition metric records, Experiment V's 12,720 saved metric records, tables and diagnostic inputs. It does not contain the official raw GDSC/Year files or every original trajectory-level state array. Those remain subject to the documented acquisition/recomputation workflows.

## Changes

- Add `review-data download`, `review-data install --file` and `review-data verify` to acquire, validate and restore the exact saved data at its original paths. The archive and member hashes are fixed in `provenance/review_data.json`.
- Make core verification independent of whether saved data is installed. Restored data remains outside the tracked core inventory.
- Remove the prospective `stable-v` extension from the submission workflow. Retain the current paper's algorithms, protocols, source hash gates, reporting, and numerical/tail diagnostics.
- Keep the figure/table map's selections and reproduction limits. This release does not add an exporter for every final typeset manuscript figure.

The preserved data comes from commit `26989d357a1fdbd7ad928482fdac9fba76c8eae4`. The [previous complete snapshot](https://github.com/L1wuyang/Subsampling/tree/26989d357a1fdbd7ad928482fdac9fba76c8eae4) and its ancestors remain available for earlier layouts, optional extensions and historical records.

## Use and validation

After extracting the core and installing its pinned requirements, run:

```text
python run.py verify
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python -B evidence/experiment5/empirical.py --output runs/reported_v
```

For an offline copy, replace the download command with `python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip`.

The release process checks package/member integrity before publication. Consult `validation/current_release.json` for the exact completed implementation and reporting checks. Saved-evidence verification or smoke execution is not a claim that the full scientific experiments were rerun. The current V report remains descriptive and does not establish full conditional-MSE rankings.

## 中文说明

本版把核心代码与完整已发布复核数据分开：核心包保留实现、冻结协议、校验与报告工具和说明；独立数据包保留全部 545 份原始文件字节，包括 I—IV 的完整仿真目录及 V 保存证据。数据安装后恢复原路径，但不再进入核心 Git 文件清单。

新增 `review-data` 下载、离线安装及校验入口，移除非当前论文流程的 `stable-v` 扩展。论文算法、记录、尾部与数值诊断继续保留。官方真实数据和未归档的完整轨迹数组仍需另行获取或重算；本版也没有新增全部论文图片的最终版式导出器。

附件校验值见 `SHA256SUMS.txt`；实际完成的检查见 `validation/current_release.json`。核验保存记录不等于重跑完整科学实验，V 的有限重复经验报告也不确立完整条件 MSE 排序。旧版及更早记录可通过固定提交和 Git 历史追溯。
