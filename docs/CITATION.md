# Manuscript and code citation

[Repository guide](../README.md) · [Machine-readable citation](../CITATION.cff)

Junchen Li, Dianpeng Wang, Ying-Ao Wang and Ye Zhang. *Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework*. Manuscript, 2026.

```bibtex
@unpublished{li2026optimal,
  author = {Li, Junchen and Wang, Dianpeng and Wang, Ying-Ao and Zhang, Ye},
  title = {Optimal Subsampling for Regularized Linear Regression:
           A Generator-Function Framework},
  year = {2026},
  note = {Manuscript}
}
```

Use the fixed [v2026.11.02.1 manuscript companion](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.11.02.1) for the current code, reported stable Experiment V and two Ridge score comparisons. The [manuscript alignment receipt](../validation/manuscript_alignment_20261102.json) identifies the checked manuscript sources and figure hashes; [the figure/table map](PAPER_RESULTS.md) identifies numerical selections.

```text
Code release: v2026.11.02.1
Repository: https://github.com/L1wuyang/Subsampling
Fixed code URL: https://github.com/L1wuyang/Subsampling/tree/v2026.11.02.1
Historical I-IV / V data archive: v2026.10.30.2
Data SHA-256: d69a39aaec588f9024ea84c184986c21c301231798b774077427a08b6d777c82
Exact source commit: recorded in the Release notes; git rev-parse HEAD
```

Suggested data/code availability wording:

> Code and computational materials are available in the Subsampling repository, release v2026.11.02.1 (https://github.com/L1wuyang/Subsampling/releases/tag/v2026.11.02.1). This release includes the reported full-support Experiment V and Ridge score comparisons and uses the v2026.10.30.2 review-data archive for Experiments I–IV and historical V. Official raw real data are obtained separately as documented in the repository.

The I–IV inputs and historical V evidence are supplied by the [v2026.10.30.2 data release](https://github.com/L1wuyang/Subsampling/releases/tag/v2026.10.30.2). Record its version and SHA-256 alongside the code version. To identify a reproducible source version, cite a fixed tag or commit rather than the moving `main` branch. Software authorship is listed separately in `CITATION.cff`.

中文：论文引用采用上列论文作者名单；软件署名另见 `CITATION.cff`。代码请注明固定 tag/commit；使用 I–IV 及历史 V 数据时，同时注明数据版本 `v2026.10.30.2` 及上述校验值。
