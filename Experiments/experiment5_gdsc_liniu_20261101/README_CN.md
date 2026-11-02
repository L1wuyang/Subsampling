# 实验五 GDSC–Ridge Li–Niu 分数对照

[English](README.md) · [保存证据](../../evidence/gdsc_ridge_liniu/README_CN.md) · [数值与解释](../../docs/LATEST_RESULTS_CN.md)

协议 `experiment-V-GDSC-ridge-LN-floor-20261101-v1` 在既定稳定 V 的 GDSC Ridge 实验上新增 180 次 LN_floor 求解。原 720 条四规则指标、目标、概率、数据划分与预处理保持不变；六个预算各采用 30 次共同均匀随机数配对抽样。

## 复核保存标量与状态

安装根目录固定依赖后，在仓库根目录执行：

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_scalar_check.json
```

该命令无需原始数据或额外估计量求解，重算 30 个标量均值与六个配对区间。按下方流程准备原预处理输入后，可追加 `--input-root runs/historical_v/exp5/inputs`，逐一核验 180 个随附新增状态、均匀随机数及抽样计数。仅标量模式不执行依赖输入的状态核验。

## 完整重跑新增抽样

先完成[稳定 V 完整重跑](../experiment5_support_stable_20261031/README_CN.md)。该指南生成精确预处理输入，以及包含 `draws/gdsc/*.npz` 和完整 `targets/` 的稳定 V 输出。紧凑证据和旧 review-data ZIP 不包含这些全部数组。

沿用该指南路径并指定新输出目录：

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/run.py --input-root runs/historical_v/exp5/inputs --stable-root runs/stable_v/formal_01 --output runs/gdsc_ln_new --workers 4
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root runs/gdsc_ln_new --stable-root runs/stable_v/formal_01 --input-root runs/historical_v/exp5/inputs --report runs/gdsc_ln_new_check.json
```

运行前核对输入/目标哈希与解析 OPT 量，封存概率和源码后释放抽样，沿用稳定 V 共同均匀随机数。两种目标相关分数采用同一精确约束 `pi_j=max(0.01/p,tau*s_j)`，`alpha=17737`。六个预算均固定，保留反转与全部结果。

结果是单一固定训练集条件下的描述性比较，区间为 t29 逐点 Monte Carlo 区间。该 oracle 分数对照不评价 NOPL/原文外层迭代、总体预测优越性或端到端加速。原源码快照与来源回执保留原运行字节，本指南说明投稿版本的便携流程。
