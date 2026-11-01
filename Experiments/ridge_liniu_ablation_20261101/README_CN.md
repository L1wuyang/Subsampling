# Ridge 列抽样：Li–Niu 与完整系数影响分数对照

本实验比较 Li–Niu (2024) 公式 (2.10) 的列抽样分数与完整系数影响分数，考察系数恢复变换对抽样概率、一阶误差准则和有限预算误差的影响。协议为 `ridge-LN-floor-ablation-20261101-v1`，完整结果见[保存证据](../../evidence/ridge_liniu/README_CN.md)。

## 实验设计

复用实验 I 的全部 40 份主输入，`n=60`、`p=1200`，固定 `alpha=trace(H)/60`，其中 `H=XX^T`。采用 13 个预算，每份数据、每个预算抽样 40 次。五条规则 UNI、NORM、LEV、LN_floor、FULL_OPT 共享均匀随机数，抽样种子为 202611010301；不同数据集和预算使用独立随机流。共完成 520 个数据集—预算任务、104,000 条指标。

令 `K=(H+alpha I)^(-1)`、`beta=X^T K y`，`a_j` 为第 j 列。两种目标相关分数为：

```text
s_LN[j]   = abs(beta[j]) * norm(a_j)
s_FULL[j] = abs(beta[j]) * norm(X^T K a_j)
```

LN_floor 和 FULL_OPT 使用相同的概率约束 `pi[j]>=0.01/p`，精确分配为 `pi[j]=max(0.01/p,tau*s[j])`，其中 tau 使概率和为一；全零分数使用均匀分布。NORM、LEV 采用 0.01 的均匀混合。各规则均进行有放回加权列抽样，求解同一个草图 Ridge 方程，并以完整 `X^T` 恢复系数。评价指标为相对共同完整 Ridge 目标的平方系数误差。

唯一预设主比较为 `N=150` 的 FULL_OPT 减 LN_floor。先在每份数据内平均 40 次配对抽样，再以 40 个数据集均值进行双侧配对 t 检验及 t39 的 95% 区间估计。其他预算和规则的结果为描述性比较，曲线区间为逐点区间。

## 结果与解释

主比较差值为 -0.0003228063，95% CI 为 [-0.0009423789, 0.0002967663]，双侧 p=0.298436，未检出显著差异。LN_floor 与 FULL_OPT 的概率总变差距离均值为 0.002990，完整一阶系数准则的平均改善为 0.006058%。全部预算、反转及尾部结果见 `evidence/ridge_liniu/`。

本实验使用完整数据目标构造精确分数，评价的是共同概率下界下的 oracle 分数；Li–Niu 的 NOPL 近似和外层迭代不在此比较范围内。复用输入的设计用于分数消融。指定一阶准则的最小化与有限预算经验误差分别报告。

## 复核保存结果

在仓库根目录执行：

```text
python -B tools/analyze_latest_saved.py --experiment ridge-liniu --output runs/ridge_liniu_saved
```

该命令检查证据哈希，重新汇总全部指标、逐点区间和主比较，并生成图表。原始运行的状态数组核验见 `evidence/ridge_liniu/independent_validation.json`。

## 完整复现

先按[数据说明](../../docs/SIMULATION_DATA_CN.md)安装 review-data 数据包，恢复实验 I 的 40 份原始输入。以下命令均在仓库根目录执行，输出使用新目录：

```text
python -B Experiments/ridge_liniu_ablation_20261101/pilot.py --repo . --output runs/ridge_ln/pilot
python -B Experiments/ridge_liniu_ablation_20261101/run_experiment.py prepare --repo . --output runs/ridge_ln/prepared
python -B Experiments/ridge_liniu_ablation_20261101/run_experiment.py run --prepared runs/ridge_ln/prepared --output runs/ridge_ln/formal --predecessor /path/to/stable-v/formal_01 --pilot runs/ridge_ln/pilot/pilot.json --workers 2
```

该版本运行入口要求提供已完成稳定实验五的协议、完成状态和核验回执。这项运行顺序检查不参与分数构造、参数选择或统计检验，也不检查 OPT 排名。`queue_after_v.py` 提供相同入口的等待启动方式。

`prepare` 核对原输入与协议，保存全部目标、概率及源码快照；pilot 核对解析导数、概率约束、重复抽样权重和完整系数恢复。正式任务保存共同随机数、全部五条规则的状态及指标，完成任务仅在身份和哈希一致时复用。独立分析器 `analyze.py` 从保存状态重新计算误差并核验完整任务网格。

`summary.csv` 保留全部原始区间端点。对数图省略下端点非正的区间，并在图中标明；所有原始误差和尾部记录均保留。
