# 1026 精简实验源码包

2026-10-27。本包用于从源码重新生成论文实验 I—V。保留实际递推、有限网格 RK4、匹配导数、概率设计、冻结正式协议、随机种子、固定真实数据划分、统计和绘图代码。

原始真实数据、预处理数组、历史保存状态/结果、论文 PDF/TeX、历史图表、重复源码 ZIP 和数值运行缓存均不随包分发。模拟数据由固定种子重新生成；真实数据从官方渠道另行获取。论文已报告的数值不在源码包内重复存放。这里的 `analyze` 必须读取你重新运行得到的结果，不能跳过运行直接复画原论文全部结果。

## 环境与文件核验

建议 Python 3.11 或 3.12；实际验证环境为 Python 3.12.7。锁定依赖中包含特定 NumPy/Numba 版本，不建议未经检查直接换用更高 Python 主次版本。

```text
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python run.py verify
python run.py preflight --experiment all --no-data
```

`verify` 只核验随包源码、配置和小清单，不要求先下载真实数据。`preflight` 检查依赖以及 III/IV 正式运行门控；`--no-data` 用于下载前检查。本包不要求原提供者的 D 盘目录、旧工程或保存缓存；数值运行不依赖 TeX。

## 先运行不需要外部数据的 I—IV

```text
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis
```

smoke 使用缩小维度、预算和重复次数，只检查实际算法及输出链路；其摘要和图明确标记为 smoke，不作为论文数值或正式显著性结论。

完整重新执行正式实验 I—IV：

```text
python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

正式运行包含大规模实际迭代；仅原 IV 就约 405 亿次更新。源码包变小不会减少这些运算。可以用 `--experiment 1` 至 `4` 分别运行；每次选一个新的输出目录。

## 获取真实数据，再运行 V 或全部实验

精确官方地址、版本、三个必要文件的字节数/SHA-256、手动导入方式及目标目录见 [数据获取说明](docs/DATA_SOURCES_CN.md)。固定 GDSC 划分已经保留；不需要重新选药或重新划分数据。

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py smoke --experiment 5 --output runs/v_smoke --workers 2
python run.py analyze --experiment 5 --results runs/v_smoke --output runs/v_smoke_analysis
```

下载层只使用 Python 标准库，并校验版本与完整性；也可按 `gdsc`、`year` 分别获取，或手动从官方渠道下载后导入。三个最终原始文件合计约 600.63 MiB；不会随源码 ZIP 一起上传。获取层不会关闭证书验证，也不会将中断文件当作完整数据。

数据齐备后，从零运行并分析全部正式实验：

```text
python run.py formal --experiment all --output runs/formal --workers 8
python run.py analyze --experiment all --results runs/formal --output runs/analysis
```

所有实验 I—V 的模拟输入、完整目标、导数、概率、抽样状态和统计结果都写入新运行目录。I/II 的结果子目录为 `expN/outputs/formal_01/`；III/IV 为 `expN/`；V 为 `exp5/formal/`，统一 `analyze` 入口自动识别。

## 精度与稳定性扩展

对你新生成的 IV 结果进行诊断或高精度重放：

```text
python run.py iv-diagnostics --input runs/formal/exp4 --output runs/iv_diagnostics
python -m repro1026.iv_precision --input runs/formal/exp4 --direction column --budget 38400 --reps 1 --tiers dd-td --output runs/iv_precision
```

诊断报告局部相减尺度、选定重放变化和尾部集中。新的结果可以产生不同警告，不会要求复现历史警告数；这些诊断不是统一浮点误差认证。高精度入口显式读取用户结果，不依赖随包保存状态。

V 全支持界是独立新协议，重新计算目标、导数及 OPT，不能只改步长后沿用原目标或历史均值：

```text
python run.py stable-v --action plan --output runs/support_plan
python run.py stable-v --action validate --output runs/support_validation --workers 2
python run.py stable-v --action formal --output runs/support_formal --workers 8
```

`plan` 默认从原始文件重建输入和基线参数；也可用 `--inputs runs/formal/exp5/inputs` 复用新准备的输入，避免重复预处理。`validate` 仅代表性检查。Year 的完整支持界协议可能增加约 44 倍的一阶方法步数。本轮未执行该新协议全量正式实验，也未执行所有高预算样本的双档高精度轨迹。

## 来源与范围

- `Experiments/`：未改字节的必要科学核、内部导入模块、冻结正式协议及 III/IV 门控记录。
- `repro1026/`、`run.py`：精简包运行、数据获取和当前统计适配层。
- `provenance/exp5_inputs/gdsc_split.json`：固定细胞 ID 和顺序，不含表达/药敏数值。
- `provenance/frozen_scientific_sources.json`：科学源码与协议保护哈希。
- `MANIFEST.json`：本次实际交付文件的完整 SHA-256 清单。

III/IV 各保留两个小型历史门控 JSON，因为原正式运行核要求它们核验源码与先导接受状态；不含完整轨迹、抽样状态或论文结果表。这些历史接受记录不等于本轮重新执行了先导或正式实验。请使用包根 `run.py`，嵌套源码中的旧 paper/render/package 路径只代表历史实现，不作为当前交付入口。

当前统计保持预算 N、V 的双侧配对检验和一次联合 36 项 Holm。OPT 使用完整数据及响应，是概率设计 oracle；固定目标逼近改善不等于普遍预测优势或端到端提速。历史测试探索不能撤销，预测仍是描述性证据。原论文与原完整档案没有因精简包而被改写。

本轮以异目录并禁止读取原工程的方式检查精简包；运行/核验摘要见 `validation/acceptance_summary.json`。完整科学正式规模没有重新全部执行。Windows/Python 3.12.7 为实际测试环境；路径中的历史 Windows 分隔符已在适配层归一化，但没有另在 Linux/macOS 执行。不同 BLAS/平台应比较容差，不承诺轨迹逐位一致。

GitHub 上传时将此 ZIP 解压后的源码文件放到仓库根即可；`.gitignore` 已排除下载数据和新运行产物。请一并保留 `.gitattributes`，它禁止 Git 自动转换换行，避免改变冻结科学源的 SHA-256。论文/Overleaf 工程单独管理，无需放入实验源码仓库。
