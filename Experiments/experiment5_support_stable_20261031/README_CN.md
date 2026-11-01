# 实验五：全支撑稳定的真实数据比较

协议 `experiment-V-support-stable-20261031-v1` 比较 GDSC 和 YearPredictionMSD 上六种回归方法的 UNI、NORM、LEV、OPT 抽样规则。完整结果见[保存证据](../../evidence/experiment5_stable/README_CN.md)。

## 数值流程

Landweber、Showalter–RK4、Nesterov 对每套数据采用共同的候选谱界，重新计算完整数据数值目标、原生离散导数和 OPT 概率。正式抽样前扫描最终概率向量覆盖的全部原子，检查全支撑谱界及对应步长条件。检查失败时程序停止；扩大尺度后的计算使用新的尝试目录。

Ridge、HBF、SOAR 使用经 SHA-256 核验的完整目标和概率，并分别采用直接正定求解或各自的全支撑稳定条件。六种方法均使用种子 202610310501 的共同随机数重新抽样。GDSC 的 6 个预算各重复 30 次，Year 的 7 个预算各重复 50 次，共 530 个配对抽样任务、12,720 条指标。48 项全支撑检查均通过。

所有迭代和 RK4 阶段按照规定网格执行。独立输出坐标块调用相同的原生伴随内核，数值目标、算法导数和抽样概率均在正式抽样前固定。方法、概率、参数和检查公式见 `protocol.json` 及[证据说明](../../evidence/experiment5_stable/README_CN.md)。

## 复核保存结果

在仓库根目录执行：

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
```

该命令核验来源哈希并重新汇总标量结果。`support_gate.json` 保存全支撑证书；`independent_validation.json` 保存原运行的状态核验。逐次指标中的 `step_bound_observed` 是完整矩阵尺度下的 Cholesky 诊断，与全支撑证书分别记录。

## 完整复现

需要官方真实数据、按既定流程生成的预处理 `inputs/`，以及 `experiment5_native_realdata_20261025` 的完整目标与数组。公开的紧凑 review-data 包提供保存指标复核所需材料，不包含这些完整数组。数据来源见[真实数据说明](../../docs/DATA_SOURCES_CN.md)。

在仓库根目录执行，并为本次计算指定新目录：

```text
python -B Experiments/experiment5_support_stable_20261031/pilot.py --output runs/stable_v/pilot.json
python -B Experiments/experiment5_support_stable_20261031/run_stable.py --historical-root /path/to/experiment5_native_realdata_20261025 --output runs/stable_v/formal_01 --workers 8
```

pilot 核对两套数据方向、三种方法的坐标分块伴随、密集递推及切线。完整运行验证输入和来源哈希，计算并冻结全部目标及概率，通过全支撑检查后进行正式抽样；进度和最终汇总分别写入 `status.json`、`results.json`、`summary.csv` 和 `metrics.csv`。

在原四规则中，OPT 在 78/78 个数据集—方法—预算组合的观测均值最低。该排序描述有限次重复的结果；全支撑稳定性本身不证明每个有限预算下完整条件 MSE 的排序。
