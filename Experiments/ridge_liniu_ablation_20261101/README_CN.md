# Ridge 列抽样：Li–Niu 与完整系数影响分数对照

[English](README.md) · [保存证据](../../evidence/ridge_liniu/README_CN.md) · [数值与解释](../../docs/LATEST_RESULTS_CN.md)

协议 `ridge-LN-floor-ablation-20261101-v1` 复用实验 I 的全部 40 份输入（`n=60, p=1200`），在 13 个预算下比较 UNI/NORM/LEV/LN_floor/FULL_OPT，每份数据每个预算 40 次配对抽样，共 104,000 条指标。唯一预设主比较为 N=150 的 FULL_OPT 减 LN_floor，以 40 个数据集均值进行推断。

令 `H=X X^T`、`alpha=trace(H)/60`、`K=(H+alpha I)^(-1)`、`beta=X^T K y`，第 j 列为 `a_j`：

```text
s_LN[j]   = abs(beta[j]) * norm(a_j)
s_FULL[j] = abs(beta[j]) * norm(X^T K a_j)
pi[j]     = max(0.01/p, tau * s[j])
```

tau 使概率和为一；全零分数使用均匀规则。两个目标相关分数采用同一精确概率下界。本实验是复用输入的 oracle 分数消融，不是新数据独立确认，未评价 NOPL 或原文外层迭代。

## 复核保存结果

```text
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

该命令核验来源哈希，重算标量汇总、逐点区间、校准和主比较。原二次型状态检查另有回执；轨迹数组未随紧凑包分发。

## 完整重跑

安装根目录固定依赖后，在仓库根目录执行，输出使用新目录：

```text
python run.py review-data download
python run.py simulation-data verify --experiment 1
python -B Experiments/ridge_liniu_ablation_20261101/pilot.py --repo . --output runs/ridge_ln/pilot
python -B Experiments/ridge_liniu_ablation_20261101/run_experiment.py prepare --repo . --output runs/ridge_ln/prepared
python -B Experiments/ridge_liniu_ablation_20261101/run_experiment.py run --prepared runs/ridge_ln/prepared --output runs/ridge_ln/formal --pilot runs/ridge_ln/pilot/pilot.json --workers 2
```

数据包恢复 40 份冻结输入，离线安装见[仿真数据说明](../../docs/SIMULATION_DATA_CN.md)。prepare 固定目标、概率及源码哈希；pilot 核对导数、概率约束、重复抽样权重和系数恢复。正式运行保存五规则状态与共同随机数，随后进行独立状态分析。已完成任务仅在身份和哈希一致时复用。

本实验默认独立运行。可选参数 `--predecessor /path/to/completed-stable-v` 核对指定稳定 V 的协议、完成状态、核验回执及比较报告；`queue_after_v.py` 提供相应等待功能。两种模式均执行上述输入、pilot 和源码检查。

所有预算与原始区间端点均保留；对数图省略非正下端点并说明。未检出显著差异不等于证明等价。
