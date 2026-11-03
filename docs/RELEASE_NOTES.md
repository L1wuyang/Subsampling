# v2026.11.02.1 — Manuscript companion

This release provides the computational materials for *Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework*, including the reported stable Experiment V, simulated Ridge score ablation and GDSC Ridge Li–Niu comparison. The manuscript alignment receipt records the manuscript source and figure hashes checked for this release. Manuscript prose is not redistributed in the code archive.

## Downloads

| Asset | Contents |
| --- | --- |
| `Subsampling-core-v2026.11.02.1.zip` | Current code, English/Chinese guides, compact saved metrics, manuscript figure assets, protocols and validation records. |
| `Subsampling-review-data-v2026.10.30.2.zip` | 545-file data archive, version v2026.10.30.2: I–IV inputs/results and historical V evidence. |
| `SHA256SUMS.txt` | Checksums of both archives. |

The data archive supplies 130 simulation inputs and 1,432,512 I–IV metric records. The installer obtains it from the fixed v2026.10.30.2 data release. Official GDSC/Year inputs and full stable-V trajectory outputs are not included; see the acquisition and full-rerun guides.

## Changes

- Support both documented V output layouts (`inputs/` plus `formal/`, and `outputs/formal_01/`) and their calibration fields and source manifests.
- Complete stable V postprocessing automatically so subsequent GDSC runs receive the required validation receipt. The receipt states its scalar/full-target verification scope; it does not claim per-sketch state-error recomputation.
- Allow simulated Ridge to run independently with its own pilot, input and source checks. The optional `--predecessor` parameter checks completion and validation of a specified stable-V run.
- Provide English full-rerun guides, result navigation, a machine-readable software citation and separate code/data version identifiers.
- Pin the plotting-layout dependency `kiwisolver` to 1.4.7, which supplies a Python 3.12 Windows wheel. This avoids the C++ build toolchain required by version 1.4.4 on that platform.
- Include scientific protocols, 54 identified scientific source files, saved numerical evidence and source snapshots. Their correspondence to the reported results is documented in the provenance and validation guides.

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

Completed checks and limits are recorded in `validation/current_release.json`. Validation covers archive/member checksums, execution-adapter regression tests, saved-result summaries and a public-download check from a clean extracted package. Full scientific experiment reruns are outside this release-validation scope. Finite-repetition means do not establish full conditional-MSE ordering or Li–Niu equivalence.

## License status

This repository does not specify a software license.

## 中文

本版提供论文对应代码、全支撑稳定实验 V，以及模拟和 GDSC Ridge 分数对照。代码支持两种已记录的 V 输出布局，自动完成稳定 V 后处理，并支持独立运行模拟 Ridge 对照。环境依赖、运行入口、保存结果复核与完整实验复现方式见仓库指南。

核心代码包版本为 `v2026.11.02.1`；独立数据包 `v2026.10.30.2` 提供 I—IV 输入与结果及历史 V 证据，下载文件的校验值见 `SHA256SUMS.txt`。发布核验覆盖文件完整性、适配器回归测试及保存结果复核，完整科学实验重新执行不属于此次发布核验范围。具体范围见 `validation/current_release.json`，论文来源与图文件对应关系见 `validation/manuscript_alignment_20261102.json`。有限重复均值不证明完整条件 MSE 排序或 Li–Niu 等价性。仓库目前未指定软件许可。
