# 真实数据获取和逐字节校验

Lite 包只保留运行所需源码、冻结配置和小型 ID 分割清单；不包含原始数据、预处理数组或保存结果。实验 I—IV 的模拟数据由代码生成；实验 V 需要下列三个文件。获取完成后，仍由训练部分独立拟合均值、标准差和响应截距，历史测试探索的限制继续保留。

## 官方来源和固定版本

| 键 | 必需最终文件 | 版本/字节数 |
|---|---|---:|
| expression | `sanger1018_brainarray_ensemblgene_rma.txt.gz` | GDSC release-6.0；141,390,873 |
| response | `GDSC2_fitted_dose_response_24Jul22.csv` | GDSC release-8.4；39,834,719 |
| year | `YearPredictionMSD.txt` | UCI dataset 203；448,576,698 |

GDSC 表达矩阵精确下载地址：

```text
https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/release-6.0/sanger1018_brainarray_ensemblgene_rma.txt.gz
```

GDSC2 响应精确下载地址：

```text
https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/release-8.4/GDSC2_fitted_dose_response_24Jul22.csv
```

YearPredictionMSD 官方介绍及下载地址：

```text
https://archive.ics.uci.edu/dataset/203/yearpredictionmsd
https://archive.ics.uci.edu/static/public/203/yearpredictionmsd.zip
```

Year 的下载对象是 **211,011,981 字节 ZIP**，其中精确成员名为 `YearPredictionMSD.txt`；程序只读取这个成员，并写入实验要求的目录层级。ZIP 与解压后 TXT 分别校验，不能将二者的 SHA 混用。所有字节数、SHA-256、完整 URL 和目标相对路径都记录在 `provenance/data_sources.json`。这批 SHA 是本项目冻结输入的哈希，**不是提供者签发或发布的官方校验和**。原 GDSC 下载在 2026-10-16、UCI ZIP 在 2026-10-17 经独立官方全量读取比对；2026-10-27 仅对三下载地址进行了证书验证的 HEAD 检查，均返回 200，未重新下载大文件或宣称重新验证远端全量哈希。

```text
expression SHA256
90fe07de1a72fa9f4fdcbdfc0c0bb23c70b1435bac2adad7e99c2f2bb154ca93

response SHA256
9d6dc82b9a072bb00b6139dcd6c4c11de1e047f210382fb726e92ab8dd0eae2a

year TXT SHA256
4b6f8e50235b359e01689ae7fb33ad0f89677e9a15f25f3d6259327a6bb927bb

year ZIP SHA256
06f801af323bb7798e800583acce4ea1ed2697ac12c23f4424aea0a7a3d09e11
```

## 下载和检查

从 Lite 包根运行；获取层仅使用 Python 标准库，不需要先安装数值计算依赖。

```bash
# 可按数据集分别获取；默认 --dataset all
python -m repro1026.data_sources download --dataset gdsc
python -m repro1026.data_sources download --dataset year

# 离线检查三个最终文件及 GDSC 固定 ID 清单
python -m repro1026.data_sources check --dataset all
```

也可用 `--root PATH` 指定另一份包/数据根；数据写入 `PATH/Data/...`，GDSC ID 清单应位于其 `provenance/exp5_inputs/gdsc_split.json`。不提供 `--root` 时以模块所在的 Lite 包根为准，不依赖当前终端目录或旧完整工程。

下载完成后的三个最终位置是：

```text
Data/real_data_20261016/raw/gdsc/expression_release_6.0/sanger1018_brainarray_ensemblgene_rma.txt.gz
Data/real_data_20261016/raw/gdsc/response_release_8.4/GDSC2_fitted_dose_response_24Jul22.csv
Data/real_data_20261016/raw/yearpredictionmsd/yearpredictionmsd/YearPredictionMSD.txt
```

这三个最终文件合计约 600.63 MiB。自动获取 Year 还会保留约 201.24 MiB 的官方 ZIP，供再次校验/解压使用。I—V 的实验计算会另行产生新输出，Lite 包下载前不携带这些大文件。

## 手动下载或复用已有文件

可以用浏览器从上述官方地址下载，再按目标路径原样放置，运行 `check`。不要重新保存 CSV、转换换行、重新压缩或重写 TXT。

已有文件位于其他目录时，`check --file` 只读校验这些路径；`download --file` 在校验后复制到标准位置。支持的键为 `expression`、`response`、`year`、`year_archive`，可重复传入：

```bash
python -m repro1026.data_sources check --dataset gdsc --file "expression=D:/data/sanger1018_brainarray_ensemblgene_rma.txt.gz" --file "response=D:/data/GDSC2_fitted_dose_response_24Jul22.csv"

# 本地官方 ZIP：无需再次下载；校验 ZIP 后仅提取目标 TXT
python -m repro1026.data_sources download --dataset year --file "year_archive=D:/data/yearpredictionmsd.zip"

# 也可直接导入已经校验的官方 TXT
python -m repro1026.data_sources download --dataset year --file "year=D:/data/YearPredictionMSD.txt"
```

`check` 的通过条件是所选数据集的最终原始文件全部有效；只给 `year_archive` 不会把尚缺的 TXT 当作已经准备完成。程序以 JSON 报告状态，全部通过退出码为 0，否则为 1。

## 失败、已有文件和固定分割

已有正确的正式文件只校验并跳过，不重复下载；已有文件大小或 SHA 不符时立即报错，保留原文件，绝不覆盖。传输/导入/解压先使用独占创建的 `.part`，通过字节数和 SHA 后才发布。中断、证书错误、错误版本或哈希不符均保留 `.part`，不会当成可用文件。再次执行会拒绝残留 `.part`；请先检查并将其移走或手动删除，再重试。本版不承诺 HTTP 断点续传。下载启用系统默认 TLS 证书验证，并拒绝 HTTPS 跳转到 HTTP；不要通过关闭证书检查绕过失败。

发布使用同目录硬链接实现“不覆盖已有目标”的原子操作。NTFS 和常见本地文件系统支持此操作；若特殊文件系统不支持，程序留下已经验证的 `.part` 并报错，可手动移到目标文件名后再运行 `check`。校验和不符也可能是官方后来更新了同名文件；应先检查版本，不能自动改清单迁就新字节。

小型 `gdsc_split.json` 只保存药物 ID 1862、937 个匹配细胞 ID 与固定 749/188 的训练/测试 ID 顺序，不含表达或响应数值。获取层还检查它的字节数、SHA 和互斥完整分区；独立运行不会重新挑选细胞或重新划分训练集。Year 使用官方前 463,715 行训练、其后 51,630 行测试的固定顺序。

获取接口可供主入口直接调用：`load_manifest()`、`required_files(dataset)`、`check_data(root, dataset)`、`download_data(root, dataset)`。源码和配置始终与结果分开；下载数据不意味着已有任何实验结论或新的独立泛化验证。
