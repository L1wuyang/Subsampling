# 实验五 GDSC–Ridge Li–Niu 对照

独立协议 `experiment-V-GDSC-ridge-LN-floor-20261101-v1`，在既定稳定V上仅新增180次LN_floor正定求解。完整结果见 [紧凑证据](../../evidence/gdsc_ridge_liniu/README_CN.md)。历史冻结源码、旧目标、旧概率及720条基线指标保持原样。

## 从保存指标独立复算

在配套仓库根目录执行，无需原始数据，也不运行估计量：

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/analyze.py --evidence-root evidence/gdsc_ridge_liniu --stable-root evidence/experiment5_stable --report runs/gdsc_ln_scalar_check.json
```

若有原始预处理输入，在命令末尾追加 `--input-root /path/to/historical-experiment5/inputs`，会逐个检查保存的新状态、随机数、抽样计数、显式系数误差及预测误差。随附核验回执记录了标量汇总与全部 180 个保存状态的检查结果。

## 完整复现新增抽样

需要历史实验五的精确预处理 `inputs/` 及完整稳定V输出（含 `draws/gdsc/*.npz` 和 `targets/`）。它们不是旧轻量review-data包的全部内容；需自行按稳定V协议准备和运行，或使用已有完成输出。给输出指定新目录：

```text
python -B Experiments/experiment5_gdsc_liniu_20261101/run.py --input-root /path/to/historical-experiment5/inputs --stable-root /path/to/stable-v/formal_01 --output runs/gdsc_ln_new --workers 4
```

运行前核对输入/目标哈希、完整目标、解析OPT概率及一阶常数，保存概率与源文件封印后释放抽样。沿用旧共同随机数，概率下界0.01/p，alpha=17737。所有六预算预先固定；不因结果调整参数或删去反转。新证据包含180个新状态/抽样计数及小型概率文件，官方真实输入不重复分发。

全部结果为固定数据条件下的描述性比较。逐点区间只反映30次抽样的Monte Carlo变化；本实验不复现NOPL/外层迭代，不检验总体预测优势，不报告加速比。
