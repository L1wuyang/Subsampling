# Ridge 列抽样：Li–Niu 与完整系数影响分数对照

独立协议 ridge-LN-floor-ablation-20261101-v1。用户授权先准备代码，稳定实验五完成后立即运行。此目录为科研实现及运行说明，不是实验知识笔记；不改变历史冻结来源、原实验 I 或正在运行的实验五。

## 固定比较与边界

复用实验 I 全部 40 份主输入（n=60,p=1200），alpha=trace(H)/60；沿用 13 个预算、每预算 40 次抽样。另用新种子 202611010301，五规则共享同一组均匀随机数。共 520 个数据—预算任务、104,000 条指标。统计单位为每份数据的重复均值，唯一主比较是 N=150 时 FULL_OPT 减 LN_floor 的相对平方系数误差；双侧配对 t 检验和 95% t39 区间。其余曲线、基线及预算为描述性、逐点结果。该设计复用既有数据，不称独立数据确认。

Li–Niu 分数为 abs(beta_j)*norm(a_j)。完整分数为 abs(beta_j)*norm(X.T K a_j)，K=(H+alpha I)^-1。两者采用共同下界 epsilon/p、epsilon=.01，按 max(epsilon/p,tau*score) 精确分配，所以称 LN_floor；它是受约束版本，不冒充未改动的原文算法。NORM/LEV 沿用 .99*normalized_score+.01/p。全部分数为零时退回均匀分布。

所有规则解同一列草图岭方程，并使用完整 X.T 恢复系数。没有迭代步长、外层加速、NOPL 或预抽样近似。FULL 在自身一阶准则的最小性只作确定性核对；正式评价看全部有限预算误差、校准与尾部。保留持平、反转、极端值和失败，不以 FULL 胜出或显著性作为接受条件，不声明端到端加速。

## 实现和轻量准备

- core.py：解析影响、分数、概率、完整系数恢复、加权重复抽样和检查点。
- pilot.py：所有列的有限差分导数、原冻结 Ridge 实现对照、KKT/零分数、各向同性等价、重复权重、门禁、损坏检测和 270 条合成数据端到端流程。
- run_experiment.py prepare：校验受发布描述符锚定的原输入和协议；对全部 40 份数据构造目标和概率，保存诊断，冻结全部源码及状态；不执行正式抽样。
- run_experiment.py run：前置实验门禁与 pilot 必须通过；按冻结源码运行，分任务落盘并校验后续复用。
- analyze.py：从原始输出状态独立重算二次型误差，核验随机流/完整格点/哈希，保留全部记录；生成曲线、尾部、数据集均值和唯一主比较。
- queue_after_v.py：只等待完成文件，30 秒轮询；前置门禁开后立即释放一次正式计算，默认 2 个进程，每个 BLAS 单线程；生成人类可读的实时页面。

典型调用（路径由命令行显式给出，输出目录放仓库之外）：

    python -B -X utf8 pilot.py --repo CODE_ROOT --output WORK/pilot_01
    python -B -X utf8 run_experiment.py prepare --repo CODE_ROOT --output WORK/prepared
    python -B -X utf8 queue_after_v.py --prepared WORK/prepared --root WORK --predecessor STABLE_V/formal_01 --pilot WORK/pilot_01/pilot.json

准备和 pilot 都完成后，只有精确相同源码的 pilot 才能放行。等待中若修改源码，队列会在释放前拒绝运行；应另建准备/pilot 版本，不能悄改冻结回执。已有准备目录拒绝覆盖。队列与运行各有独占锁，重复启动会拒绝；异常退出留下锁时，应先确认原进程已退出后再处理，禁止启动重复计算。

## 实验五完成门禁

必须是 experiment-V-support-stable-20261031-v1：status/results 标明完成且 12,720 条记录；support_gate 通过；independent_validation 通过且为 530 个任务；RESULTS.md、新旧对照 CSV、目标变化 CSV 和新旧图已生成。目标分块结束不足以开门，普通进程退出也不足以开门。门禁完全不检查 OPT 排名。缺文件、失败或未核验时始终等待，不改实验五进程或结果。

## 输出

准备目录：seal.json、source_snapshot、states、score_diagnostics.csv、input_hashes.json。

正式目录：tasks 下每个数据—预算的 CSV、状态 NPZ、哈希完成标志；metrics.csv、dataset_means.csv、summary.csv、tails.csv、primary_comparison.json、primary_dataset_differences.csv、score_diagnostics.csv、comparison.png/svg、RESULTS.md、independent_validation.json、execution.json。

曲线使用对数坐标；95% 逐点 t 区间下端点非正时省略该区间并在图上注明，summary.csv 始终保留未经修改的端点。不得用接近零的正数替代负端点并拉伸坐标。

任务保存共同均匀随机数和全部五规则输出，可重建抽样索引；续跑只复用身份和文件哈希匹配的完整任务。出现失败时保存失败记录和状态，不生成仅成功样本的结论。中途非完整任务可在人工恢复同一冻结运行后重算。正式输出只在独立核验完成后标为 completed。
