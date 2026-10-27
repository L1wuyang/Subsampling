# 1026 实验源码与仿真数据

[English](README.md)

本仓库提供实验 I—V 的运行代码，以及论文 I—IV 的 **130 份 NPZ 仿真输入、1,432,512 条逐次指标、汇总表和协议参数**。保留实际递推、有限网格 RK4、匹配导数、概率设计和冻结种子。可以直接查看随包仿真结果，也可以按协议重新运行。

新增数据位于 `simulations/experiment1/` 至 `experiment4/`。实验 V 的原始真实数据从官方渠道另行获取；完整状态、影响量数组、论文文件和重复压缩包不随仓库分发。

## 直接检查并汇总发布结果

建议使用 Python 3.11 或 3.12；实际验证环境为 Python 3.12.7。在仓库根运行：

```text
python -m pip install -r requirements-lock.txt
python run.py verify
python run.py simulation-data verify --experiment all
python run.py simulation-data summarize --experiment all --output runs/published_analysis
```

仿真数据命令核验随包输入和指标分片，并从发布指标重新计算数据集均值、等权汇总和少量图。不需要下载真实数据或重新执行迭代。可用 `--experiment 1` 至 `4` 单独选择实验，每次使用新的输出目录。

记录数量、字段、配对关系、风险定义和 IV 诊断见[仿真数据说明](docs/SIMULATION_DATA_CN.md)。

## 重新运行算法

原运行入口继续保留。`smoke` 缩小维度、预算和重复次数，检查实际算法与输出链路；`formal` 执行冻结的正式协议。

```text
python run.py preflight --experiment simulations
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis

python run.py formal --experiment simulations --output runs/formal_simulations --workers 8
python run.py analyze --experiment simulations --results runs/formal_simulations --output runs/formal_simulations_analysis
```

`simulations` 选择 I—IV；`--experiment 1` 至 `5` 可单独运行。正式计算量较大，仅 IV 就约 405 亿次更新。

**`simulation-data summarize` 读取随包发布指标；`analyze --results` 读取你重新运行生成的完整目录。** 正式入口仍按冻结种子生成输入，不会自动改为加载随包 NPZ。

## 真实数据实验 V

[官方数据获取说明](docs/DATA_SOURCES_CN.md)包含版本、校验和与手动导入方式，固定 GDSC ID 划分已保留。

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py smoke --experiment 5 --output runs/v_smoke --workers 2
python run.py analyze --experiment 5 --results runs/v_smoke --output runs/v_smoke_analysis
```

数据齐备后，用 `formal --experiment all` 和 `analyze --experiment all` 运行与分析 I—V。V 保留双侧配对检验和一次联合 36 项 Holm；OPT 的 oracle 含义及历史测试探索的解释见[数据说明](docs/SIMULATION_DATA_CN.md#解释结果时的条件)。

IV 精度重放与独立的 V 全支持界扩展仍可通过 `iv-diagnostics`、`python -m repro1026.iv_precision --help` 和 `stable-v` 调用。重放读取新运行的完整 IV 目录；随包指标用于查看已发布的诊断。

## 更新已有 GitHub 仓库

解压本包，将里面的文件放到已有仓库根目录，与 `run.py` 同层，保留目录结构。在 GitHub Desktop 中检查更改、提交，再 Push/同步。上传解压后的文件，不上传 ZIP 本身。保留 `.gitattributes`，避免自动转换换行改变冻结源码哈希；`.gitignore` 会排除下载的真实数据和新运行产物。

`MANIFEST.json` 记录发布文件，`simulations/manifest.json` 描述仿真数据，`provenance/` 保存源码与数据来源。代码实际在 Windows 上验证；不同 BLAS/平台比较数值容差。运行实验不需要 TeX。
