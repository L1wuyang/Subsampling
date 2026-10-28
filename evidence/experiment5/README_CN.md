# 实验 V：保存指标与统计核验材料

本目录对应论文 *Optimal Subsampling for Regularized Linear Regression: A Generator-Function Framework* 的 GDSC 与 YearPredictionMSD 真实数据实验，提供保存的标量指标和统计报告修订记录。

`saved_records.tar.gz` 保留 530 份原始逐次指标 CSV，共 12,720 条记录，以及 12 份全样本目标汇总、正式协议、执行记录和原单侧比较表。归档内保留原始文件字节及相对路径。这些文件是实验输出的标量指标；原始协变量、表达测量、响应值和拟合系数向量由仓库主复现流程获取或计算。

`reference/` 保存论文使用的双侧比较表、详细统计修订报告及原始保存记录分析脚本。来源记录见 `PROVENANCE.json`，包内文件及归档成员的 SHA-256 校验值见 `MANIFEST.json`。

## 核验保存的结果

在仓库根目录执行：

```bash
python -B evidence/experiment5/reanalyze.py --verify
python -B evidence/experiment5/reanalyze.py --output runs/experiment5_saved_check
```

完整性校验仅使用 Python 标准库；重分析使用仓库固定依赖中的 NumPy、pandas 和 SciPy。输出目录必须是新目录，输入及参考文件保持原样。

重分析在 GDSC 预算 749、Year 预算 5,000 处重新计算 36 项双侧配对 Student t 检验，统一进行一次 Holm 校正，并与保存的参考表比较。最大校正 p 值约为 `2.9821e-8`。程序同时核验 OPT 在全部 78 个“方法—预算”单元中具有最小的平均系数目标误差。新输出目录包含：

- `paired_comparisons_two_sided.csv`、`inference_revision.json`：由原始分析脚本生成；
- `mean_coefficient_errors.csv`：由全部保存的逐次记录计算均值和标准误；
- `verification.json`：记录输入数量及参考结果比较情况。

统计分析以固定的数据、划分和参数为条件。36 项比较按论文保留 GDSC NORM/UNI 重复项；置信区间为逐点 95% 区间。原单侧统计作为后续双侧报告修订的来源记录保留。

适配脚本仅将通过校验的普通文件释放到临时目录，再调用保留的原始统计脚本，使用保存的标量记录完成计算。跨科学计算库版本的浮点末位差异通过数值容差检查。

## 与完整复现的关系

下载官方数据、运行新实验和分析新实验时，统一使用仓库根目录 `run.py`。其中 `run.py analyze --experiment 5` 生成当前双侧报告格式：CSV 不含历史 `original_one_sided_p` 列，JSON 为当前简版说明。本目录保留详细历史报告及其对应的保存输入。

完整运行指定 `--output runs/formal_v` 时，实验 V 指标保存于 `runs/formal_v/exp5/formal/`；分析指定 `--output runs/formal_v_analysis` 时，报告保存于 `runs/formal_v_analysis/exp5/`。本目录的保存指标适配脚本直接写入其指定的输出目录。

原脚本开头保留“需要完整工程归档”的历史说明。此处适配脚本会从紧凑归档建立所需的历史输入目录，因此可以独立于原始真实数据下载核验这些保存的统计结果。

[English guide](README.md) · [仓库复现说明](../../README_CN.md)
