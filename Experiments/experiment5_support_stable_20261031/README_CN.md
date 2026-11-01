# 实验 V 全抽样支持稳定版（2026-10-31）

独立的新科学协议，见 `protocol.json`。不修改原 2026-10-25 冻结源码/协议或旧结果。

Landweber、Showalter–RK4、Nesterov 采用每套数据共同的候选支持谱界，重算完整目标、原生离散导数和 OPT，全部通过支持门禁后才释放新的随机抽样。UNI/NORM/LEV/OPT 定义、数据划分、历史 c、预算和重复数均保留。所有规定迭代和 RK4 阶段实际执行；独立输出坐标块并行复用冻结原生内核，未使用谱公式、矩阵幂或提前停止。

Ridge/HBF/SOAR 的参数不变，复用经 SHA-256 验证的历史完整目标、常数和概率。正式抽样仍对全部六方法重新执行，种子为 202610310501。总计 530 个预算—重复任务、12,720 条方法—规则指标。

本地运行：

```text
D:\anaconda1\python.exe -B -X utf8 run_stable.py --historical-root D:/desk/learning/Subsampling/Manuscript/Experiments/experiment5_native_realdata_20261025 --output D:/desk/learning/Subsampling/Manuscript/Workspace/changes/experiment_v_stable_rerun_20261031/formal_01 --workers 8
```

输出上一级需要先有 `pilot.json` 原生分块伴随与独立密集递推/切线验证。当前本机已完成六种数据—方法组合的检查。输入必须具有原始历史数据和目标清单，轻量复核数据包本身不包含这些完整数组。恢复时只复用已有坐标块和完整抽样任务；科学源码哈希不同将拒绝恢复。日志和输出全部在仓库外工作台。

进度看输出目录 `status.json`；新支持稳定性证据看 `support_gate.json`，正式结果看最终 `results.json`、`summary.csv`、`metrics.csv`。新门禁覆盖全部可能抽样谱；逐次指标中的 `step_bound_observed` 仍是冻结历史抽样器对完整数据尺度的 Cholesky 诊断，不能替代新门禁。通过稳定性检查不等于证明有限预算完整 MSE 排序。
