# Validation records

[Repository guide](../README.md) · [Paper result map](../docs/PAPER_RESULTS.md)

- [Current release checks](current_release.json): `v2026.11.02.1` packaging, execution-adapter regression tests and saved-record verification.
- [Manuscript alignment](manuscript_alignment_20261102.json): manuscript source hashes, figure-file comparisons and numerical result cross-checks.
- [Reported results](reported_results_checks_20261101.json): original saved-scalar checks for the three reported studies and six latest figure assets.
- [Historical core release](history/release_v2026.10.30.2.json) and [historical empirical report](history/empirical_20261030.json): unchanged checks for the earlier release.

Stable V contains 12,720 saved scalar records, 530 sketch tasks, 48 support-gate records and matched full-target summaries. Its original `independent_validation.json` records result completeness and summaries; the public postprocessor checks scalar aggregation, full-target changes and hashes. These receipts do not establish per-sketch state-error recomputation.

The simulated Ridge comparison contains 104,000 records and an original independent state/quadratic-form validation receipt. `tools/analyze_latest_saved.py` checks hashes and recomputes saved scalar summaries, intervals and the prespecified primary comparison. It does not repeat that original state-array validation.

The GDSC addendum contains 180 new states and records plus 720 preserved baseline records. Its analyzer checks 30 scalar summary cells and six paired intervals without raw inputs. Supplying `--input-root` additionally verifies saved states against preprocessed data. Intervals are pointwise Monte Carlo intervals conditional on one data set.

The root manifest protects the current package; 54 historical scientific sources remain separately frozen. The review-data descriptor protects the unchanged 545-file archive for I–IV and historical V. Integrity checks, saved-result reanalysis, small execution tests and full scientific reruns are distinct validation scopes.

中文：当前发布验证与历史回执分开存放。稳定 V 的公开回执支持完整性、标量汇总与完整目标核对，不应称作逐草图状态误差重算；Ridge 的保存指标复算亦不重复原状态核验。GDSC 只有提供预处理输入时才额外核验全部新增状态。具体执行范围见当前回执。
