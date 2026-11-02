# 实验 V：全支持稳定版本

2026-11-01 报告结果。此目录提供论文中的全支撑稳定实验 V 证据；v2026.10.30.2 数据包保留历史基线，本次结果随投稿源码版本 v2026.11.02.1 提供。

协议 `experiment-V-support-stable-20261031-v1` 保留真实数据预处理、历史 c、预算、重复次数和四规则定义，新的抽样种子为 202610310501。Landweber、Showalter、Nesterov 使用每套数据共同的全支持谱界，并重算数值完整目标、算法导数和 OPT。Ridge/HBF/SOAR 沿用经哈希核验的完整目标与概率；六种方法均重新抽样。

对任意有放回草图，`B_pi=max_i ||z_i||^2/pi_i` 是其谱上界。48 个数据集×方法×规则检查全部通过：Landweber/Showalter/Nesterov 要求 `B_pi<=L`、`h B_pi<=0.9`；HBF 要求 `0<h eta<=0.01`、`h^2 B_pi<=2`；SOAR 要求 `h^2 B_pi<=8`；Ridge 直接 SPD 求解。详见 `support_gate.json`。指标中的 `step_bound_observed` 是旧冻结抽样器按旧完整数据尺度做的独立 Cholesky 诊断，不能替代新门禁。

完成 530 组抽样、12,720 条指标，观测步长违规为零。OPT 在 78/78 个数据集×方法×预算组合中观测均值最低；最大预算经验/一阶比约 0.969—1.179。有限重复排序不等于完整条件 MSE 的有限预算严格排序。新旧种子不同，三种方法的数值目标重算，均值变化不能全部归因于步长。

在仓库根目录只用已保存指标复算并绘图：

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
```

输出汇总、两张正文目标误差图和核验回执；检查来源哈希及全部均值、标准误、预测 RMSE 和校准值。不会执行轨迹。`metrics.csv` 是完整标量记录，不包含全部状态数组；原 `independent_validation.json` 记录源目录的标量完整性、汇总及完整目标的完整性与新旧比较，不代表逐草图状态误差的独立重算。完整目标参数与预测参考位于 `targets/<dataset>/<method>/summary.json`。

完整重跑说明见[版本化科研实现](../../Experiments/experiment5_support_stable_20261031/README_CN.md)，需要官方输入及历史完整数据数组，轻量公开数据包不足以单独重跑。原协议、门禁和验证保留原始字节；来源目录及逐文件哈希见 `PROVENANCE.json`。


保存指标工具导出便捷图，不声明与期刊图片版式相同；精确论文图片和重绘脚本见图表对照。
