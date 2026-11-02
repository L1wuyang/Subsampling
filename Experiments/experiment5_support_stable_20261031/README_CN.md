# 实验五：全支撑稳定的真实数据比较

[English](README.md) · [保存证据](../../evidence/experiment5_stable/README_CN.md) · [数值与解释](../../docs/LATEST_RESULTS_CN.md)

协议 `experiment-V-support-stable-20261031-v1` 比较 GDSC 和 YearPredictionMSD 上六种回归方法的 UNI、NORM、LEV、OPT 抽样规则。正式抽样前固定完整数值目标、原生离散导数与概率，使用种子 202610310501。GDSC 的六个预算各重复 30 次，Year 的七个预算各重复 50 次，共 530 组任务、12,720 条标量指标。

## 复核保存结果

在仓库根目录执行：

```text
python -B tools/analyze_latest_saved.py --experiment stable-v --output runs/stable_v_saved
```

该命令核验来源哈希并重算标量汇总。原 `independent_validation.json` 记录完整性、汇总及完整目标的完整性与新旧比较，不代表逐草图状态误差的独立重算。全支撑证书与观测 Cholesky 诊断分别记录。紧凑证据不含轨迹数组和官方原始输入。

## 从官方输入完整重跑

先安装根目录固定依赖。下载并核验官方输入，再生成稳定协议所需的历史输入和完整目标：

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py formal --experiment 5 --output runs/historical_v --workers 8
```

根命令生成 `runs/historical_v/exp5/inputs` 和 `runs/historical_v/exp5/formal`，执行较早的冻结 V 协议，计算可能昂贵；其指标属于历史协议，下一步才生成当前稳定协议结果。轻量 review-data ZIP 不包含这些完整数组。手动获取与导入见[真实数据说明](../../docs/DATA_SOURCES_CN.md)。

pilot 与正式运行使用新输出目录：

```text
python -B Experiments/experiment5_support_stable_20261031/pilot.py --output runs/stable_v/pilot.json
python -B Experiments/experiment5_support_stable_20261031/run_stable.py --historical-root runs/historical_v/exp5 --output runs/stable_v/formal_01 --workers 8
```

运行器兼容上述根入口输出，以及历史的 `inputs/` 加 `outputs/formal_01/` 布局。程序核验所消耗输入与源码哈希，重算发生变化的目标并冻结概率，通过全支撑门禁后才抽样。Ridge/HBF/SOAR 保留匹配哈希且参数不变的历史目标，Landweber/Showalter/Nesterov 重算稳定数值映射。所有规定迭代与 RK4 阶段均执行。

抽样后自动检查标量完整性与均值、核验完整目标并比较新旧目标，生成 `independent_validation.json`、`RESULTS.md` 和比较表图。该后处理不新增估计量求解，也不逐草图独立重算状态误差。已有完整输出可单独执行：

```text
python -B Experiments/experiment5_support_stable_20261031/compare_results.py --historical-root runs/historical_v/exp5 --output runs/stable_v/formal_01
```

全支撑稳定性不证明每一有限预算下完整条件 MSE 的排序；报告排序属于有限重复的观测结果，详细边界见结果说明。
