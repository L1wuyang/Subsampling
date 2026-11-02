# v2026.11.02.1 — Manuscript companion

This release fixes a source version for *Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework*, including the reported stable Experiment V, simulated Ridge score ablation and GDSC Ridge Li–Niu addendum. The manuscript alignment receipt records the manuscript source and figure hashes checked for this release. Manuscript prose is not redistributed in the code archive.

## Downloads

| Asset | Contents |
| --- | --- |
| `Subsampling-core-v2026.11.02.1.zip` | Current code, English/Chinese guides, compact saved metrics, manuscript figure assets, protocols and validation records. |
| `Subsampling-review-data-v2026.10.30.2.zip` | Unchanged 545-file historical review-data archive: I–IV inputs/results and historical V evidence. Original filename, bytes and SHA-256 retained. |
| `SHA256SUMS.txt` | Checksums of both archives. |

The data archive is a byte-identical convenience copy of the original asset; the installer retains its original fixed URL. It supplies 130 simulation inputs and 1,432,512 I–IV metric records. Official GDSC/Year inputs and full stable-V trajectory outputs are not included; see the acquisition and full-rerun guides.

## Changes

- Accept the public root V runner's `inputs/` plus `formal/` layout as well as the original `outputs/formal_01/` layout; bridge the historical calibration column name and verify each source-manifest format.
- Complete stable V postprocessing automatically so subsequent GDSC runs receive the required validation receipt. The receipt states its scalar/full-target verification scope; it does not claim per-sketch state-error recomputation.
- Allow simulated Ridge to run independently with its own pilot, input and source checks. The original stable-V predecessor scheduling check remains available explicitly through `--predecessor`.
- Add English full-rerun guides, concise result navigation, a machine-readable citation and separately identified code/data versions. Move previous release checks into `validation/history/`.
- Pin the plotting-layout dependency `kiwisolver` to 1.4.7, which supplies a Python 3.12 Windows wheel. The earlier 1.4.4 pin required a local C++ build toolchain; the historical environment record remains unchanged.
- Preserve the original scientific protocols, all 54 frozen sources, saved numerical evidence and source snapshots. Current execution adapters are versioned by this release; original run-source hashes retain their historical meaning.

## Verification

```text
python -m pip install -r requirements-lock.txt
python run.py verify
python run.py review-data download
python run.py review-data verify
python run.py simulation-data verify --experiment all
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_saved
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_saved
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_saved.json
```

For offline installation use `python run.py review-data install --file /path/to/Subsampling-review-data-v2026.10.30.2.zip`. Follow [the repository guide](../README.md) for complete experimental reruns and [the paper result map](PAPER_RESULTS.md) for precise figure/table selections. Use new output directories.

Completed checks and limits are recorded in `validation/current_release.json`. The release process verifies archive/member hashes and performs a clean-package public-download check. This packaging release does not claim a full rerun of the scientific experiments. Finite-repetition means do not establish full conditional-MSE ordering or Li–Niu equivalence. No license is added in this release.

## 中文

本版固定当前文稿对应代码、稳定实验五及两组 Ridge 对照，修复历史 V 到稳定 V 的目录/字段衔接，自动完成稳定 V 后处理，并解除模拟 Ridge 对真实数据实验的非科学性调度依赖。新旧代码版本、原始运行快照及数据版本分别记录。

核心包为 `v2026.11.02.1`；数据包继续使用原名、原字节的 `v2026.10.30.2`，旧发布保持不变。已有数值记录和冻结科学来源保持原样。实际验证范围见 `validation/current_release.json`，文稿对应关系见 `validation/manuscript_alignment_20261102.json`；未重跑全部科学实验，亦未新增许可。
