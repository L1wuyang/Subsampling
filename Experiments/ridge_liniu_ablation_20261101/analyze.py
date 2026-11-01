"""Recheck stored tasks and raw states before untrimmed, data-set-level inference."""
from core import *
import argparse


def mean_interval(values):
    from scipy.stats import t
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    se = float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.
    width = float(t.ppf(.975, len(values) - 1)) * se if len(values) > 1 else 0.
    return dict(n=len(values), mean=mean, se=se, ci_low=mean - width, ci_high=mean + width)


def analyze(prepared, output):
    import pandas as pd
    from scipy.stats import t
    prepared, output = Path(prepared), Path(output)
    verify_prepared(prepared)
    config = read(prepared / "protocol.json")
    identity = digest(prepared / "seal.json")
    expected = {(did, budget) for did in config["data_ids"] for budget in config["budgets"]}
    actual = set()
    pieces = []
    max_relative_check = 0.
    for marker in sorted((output / "tasks").glob("*.json")):
        entry = read(marker)
        key = (entry["data_id"], entry["budget"])
        if key in actual or key not in expected or entry["identity"] != identity:
            raise ValueError("Unexpected or duplicate task")
        actual.add(key)
        for name, expected_sha in entry["files"].items():
            if digest(marker.parent / name) != expected_sha:
                raise ValueError("Task file digest mismatch")
        data_id, budget = key
        data = pd.read_csv(marker.with_suffix(".csv"))
        expected_keys = {(rule, rep) for rule in config["rules"]
                         for rep in range(config["repetitions"])}
        if set(zip(data.rule, data.rep)) != expected_keys or len(data) != len(expected_keys):
            raise ValueError("Task record coverage mismatch")
        if not data.data_id.eq(data_id).all() or not data.budget.eq(budget).all():
            raise ValueError("Task record identity mismatch")
        with np.load(prepared / "states" / f"data_{data_id:02d}.npz") as state, \
             np.load(marker.with_suffix(".npz")) as raw:
            uniforms = np.random.default_rng(np.random.SeedSequence(
                [config["sampling_seed"], data_id, budget, 1])).random(
                    (config["repetitions"], budget))
            if not np.array_equal(uniforms, raw["uniforms"]):
                raise ValueError("Sampling stream differs from frozen fresh seed")
            for rule in config["rules"]:
                rows = data[data.rule == rule].sort_values("rep")
                if not rows.status.isin(["complete", "zero_target", "numerical_failure"]).all():
                    raise ValueError("Unknown outcome status")
                valid = rows.status.ne("numerical_failure").to_numpy()
                difference = raw["U_" + rule] - state["full_u"]
                # Independent quadratic form, rather than runner's explicit p-coordinate norm.
                checked = np.sum(difference * (difference @ state["H"]), axis=1)
                reported = rows.absolute_gap.to_numpy()
                norm = float(state["beta"] @ state["beta"])
                if valid.any():
                    error = np.max(np.abs(checked[valid] - reported[valid]) /
                                   np.maximum(1e-16, np.abs(reported[valid])))
                    max_relative_check = max(max_relative_check, float(error))
                    if not np.allclose(checked[valid], reported[valid], rtol=2e-9, atol=1e-13):
                        raise ValueError("Independent coefficient norm check failed")
                    if norm > 1e-24:
                        if not np.allclose(reported[valid] / norm,
                                           rows.relative_gap.to_numpy()[valid], rtol=2e-10, atol=1e-13):
                            raise ValueError("Relative-gap normalization failed")
                cdf = np.cumsum(state["pi_" + rule])
                cdf[-1] = 1
                selected = np.searchsorted(cdf, uniforms, side="right")
                unique = [len(np.unique(row)) for row in selected]
                if not np.array_equal(unique, rows.unique_atoms):
                    raise ValueError("Unique-atom diagnostic mismatch")
                if norm > 1e-24:
                    if not np.allclose(rows.first_order_relative,
                                       float(state["Q_" + rule]) / budget / norm, rtol=2e-10):
                        raise ValueError("First-order diagnostic differs from frozen state")
                elif not rows.first_order_relative.isna().all():
                    raise ValueError("Zero-target relative prediction must remain undefined")
        pieces.append(data)
    if actual != expected:
        raise ValueError("Incomplete data-set/budget grid")
    data = pd.concat(pieces, ignore_index=True)
    failures = int(data.status.eq("numerical_failure").sum())
    zero_targets = int(data.status.eq("zero_target").sum())
    validation = dict(passed=False, rows=len(data), tasks=len(expected), failures=failures,
                      zero_targets=zero_targets, max_independent_metric_relative_error=max_relative_check,
                      all_outcomes_retained=True, formal=config["scope"] == "formal_reused_inputs_ablation")
    data.to_csv(output / "metrics.csv", index=False)
    if failures or zero_targets:
        validation["reason"] = "Failures/undefined relative targets retained; no success-only inference"
        save(output / "independent_validation.json", validation)
        return validation
    if not np.isfinite(data[["absolute_gap", "relative_gap"]].to_numpy()).all() or (data.absolute_gap < 0).any():
        raise ValueError("Invalid outcome metric")
    means = data.groupby(["data_id", "budget", "rule"], as_index=False).agg(
        relative_gap=("relative_gap", "mean"), absolute_gap=("absolute_gap", "mean"),
        first_order_relative=("first_order_relative", "first"),
        mean_unique_atoms=("unique_atoms", "mean"))
    means["calibration"] = means.relative_gap / means.first_order_relative
    means.to_csv(output / "dataset_means.csv", index=False)
    curves, tails = [], []
    for (budget, rule), group in means.groupby(["budget", "rule"]):
        curves.append(dict(budget=int(budget), rule=rule, **mean_interval(group.relative_gap),
                           first_order_relative=float(group.first_order_relative.mean()),
                           calibration=float(group.relative_gap.mean() / group.first_order_relative.mean())))
        values = data[(data.budget == budget) & (data.rule == rule)].relative_gap.to_numpy()
        k = max(1, int(np.ceil(.01 * len(values))))
        tails.append(dict(budget=int(budget), rule=rule, count=len(values),
                          mean=float(values.mean()), median=float(np.median(values)),
                          p95=float(np.quantile(values, .95)), p99=float(np.quantile(values, .99)),
                          maximum=float(values.max()),
                          top_1percent_share=float(np.sort(values)[-k:].sum() / values.sum())))
    pd.DataFrame(curves).to_csv(output / "summary.csv", index=False)
    pd.DataFrame(tails).to_csv(output / "tails.csv", index=False)
    primary_budget = config["primary"]["budget"]
    primary = means[means.budget == primary_budget].pivot(index="data_id", columns="rule",
                                                        values="relative_gap")
    difference = (primary.FULL_OPT - primary.LN_floor).to_numpy()
    inference = mean_interval(difference)
    if inference["se"] > 0:
        statistic = inference["mean"] / inference["se"]
        pvalue = float(2 * t.sf(abs(statistic), len(difference) - 1))
    else:
        statistic = None
        pvalue = 1. if inference["mean"] == 0 else 0.
    inference.update(budget=primary_budget, contrast="FULL_OPT minus LN_floor",
                     metric="data-set mean relative squared target gap", two_sided_p=pvalue,
                     t_statistic=statistic, full_lower_datasets=int((difference < 0).sum()),
                     full_over_ln_ratio_of_means=float(primary.FULL_OPT.mean() / primary.LN_floor.mean()),
                     one_prespecified_primary_contrast=True, independent_data_confirmation=False)
    save(output / "primary_comparison.json", inference)
    pd.DataFrame(dict(data_id=primary.index, difference=difference)).to_csv(
        output / "primary_dataset_differences.csv", index=False)
    diagnostics = pd.read_csv(prepared / "score_diagnostics.csv")
    diagnostics.to_csv(output / "score_diagnostics.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), layout="constrained")
    curve_frame = pd.DataFrame(curves)
    omitted_intervals = int((curve_frame.ci_low <= 0).sum())
    for rule, color in zip(config["rules"], ["#4878a8", "#d58c38", "#46906a", "#8c62aa", "#c44448"]):
        group = curve_frame[curve_frame.rule == rule].sort_values("budget")
        axes[0].plot(group.budget, group["mean"], "o-", ms=3, label=rule, color=color)
        # Nonpositive t endpoints cannot be represented on a logarithmic axis.
        # Omit those intervals, retain their actual endpoints in summary.csv.
        lower = group.ci_low.where(group.ci_low > 0, np.nan)
        axes[0].fill_between(group.budget, lower,
                             group.ci_high, color=color, alpha=.10)
        if rule in ("LN_floor", "FULL_OPT"):
            axes[1].plot(group.budget, group.calibration, "o-", label=rule, color=color)
    axes[0].set(xscale="log", yscale="log", xlabel="Draw budget N",
                ylabel="Mean relative squared coefficient gap")
    if omitted_intervals:
        axes[0].text(.02, .02,
                     f"{omitted_intervals} intervals omitted: lower endpoint <= 0.\n"
                     "Unmodified 95% pointwise t intervals are in summary.csv.",
                     transform=axes[0].transAxes, fontsize=7, va="bottom")
    axes[1].axhline(1, color="#555555", ls="--", lw=1)
    axes[1].set(xscale="log", xlabel="Draw budget N", ylabel="Empirical mean / first-order prediction")
    for ax in axes:
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.savefig(output / "comparison.png", dpi=180)
    fig.savefig(output / "comparison.svg")
    plt.close(fig)
    report = [
        "# Ridge 列抽样：Li–Niu 分数与完整系数分数对照", "",
        f"协议：{config['version']}。复用既有输入，使用新的共同抽样随机数；不是新数据独立确认。",
        f"完整记录 {len(data):,} 条，数据—预算任务 {len(expected)} 个；不删除极端值。", "",
        f"唯一主比较：N={primary_budget}，FULL_OPT 减 LN_floor；统计单位是数据集均值。",
        f"差值均值 {inference['mean']:.8g}，95% CI "
        f"[{inference['ci_low']:.8g}, {inference['ci_high']:.8g}]，"
        f"双侧 p={pvalue:.6g}。",
        f"FULL/LN 均值比 {inference['full_over_ln_ratio_of_means']:.6g}；"
        f"FULL 较低的数据集数 {inference['full_lower_datasets']}/{len(difference)}。", "",
        "LN_floor 为共同下界约束版本；不冒充未改变的原文概率。",
        "FULL 对自身一阶准则的最小性是确定性核对，有限预算经验误差是另一个结果。",
        "其他预算/基线和曲线区间为描述性、逐点结果，没有同时覆盖率声明。",
        f"对数图省略下端点非正的区间 {omitted_intervals} 个；summary.csv 保留全部原始区间，不以正数替换。",
        "保留持平、反转和尾部记录；本实验不评价 NOPL 或原文外层迭代，不建立端到端加速结论。", "",
        "结果入口：primary_comparison.json、summary.csv、tails.csv、comparison.png、metrics.csv。"]
    (output / "RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    validation["passed"] = True
    save(output / "independent_validation.json", validation)
    return validation


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.prepared, args.output), indent=2), flush=True)
