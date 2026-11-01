"""Recompute the November 1 draft results from bundled metrics; no trajectories."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]


def check_sources(folder):
    provenance = json.loads((folder / "PROVENANCE.json").read_text(encoding="utf-8"))
    for name, expected in provenance["files"].items():
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        if actual != expected["sha256"]:
            raise ValueError("Bundled source hash mismatch: " + name)


def interval(values):
    values = np.asarray(values)
    se = float(values.std(ddof=1) / np.sqrt(len(values)))
    mean = float(values.mean())
    width = float(t.ppf(.975, len(values) - 1)) * se
    return dict(n=len(values), mean=mean, se=se, ci_low=mean-width, ci_high=mean+width)


def stable(folder, output):
    data = pd.read_csv(folder / "metrics.csv")
    keys = ["dataset", "method", "rule", "budget"]
    if len(data) != 12720 or data.duplicated(keys+["rep"]).any():
        raise ValueError("Stable V record coverage differs from the frozen run")
    if not data.status.eq("complete").all() or not np.isfinite(data.relative_coefficient_error).all():
        raise ValueError("Stable V contains incomplete or invalid outcomes")
    for dataset, repetitions in (("gdsc", 30), ("year", 50)):
        if not data[data.dataset.eq(dataset)].groupby(keys).size().eq(repetitions).all():
            raise ValueError("Stable V repetitions differ")
    summary = data.groupby(keys, as_index=False).agg(
        n=("relative_coefficient_error", "size"), mean=("relative_coefficient_error", "mean"),
        sd=("relative_coefficient_error", "std"), theoretical=("theoretical_relative_mse", "first"),
        test_rmse=("test_response_rmse", "mean"))
    summary["se"] = summary.sd / np.sqrt(summary.n)
    summary["empirical_to_first_order"] = summary["mean"] / summary.theoretical
    reference = pd.read_csv(folder / "summary.csv")
    joined = summary.merge(reference, on=keys, suffixes=("_new", "_saved"), validate="one_to_one")
    for column in ("mean", "se", "theoretical", "test_rmse", "empirical_to_first_order"):
        if not np.allclose(joined[column+"_new"], joined[column+"_saved"], rtol=2e-10, atol=1e-13):
            raise ValueError("Stable V summary mismatch: " + column)
    gate = json.loads((folder / "support_gate.json").read_text(encoding="utf-8"))
    if not gate["passed"] or len(gate["checks"]) != 48 or not all(x["passed"] for x in gate["checks"]):
        raise ValueError("Incomplete full-support stability gate")
    wins = 0
    for _, group in summary.groupby(["dataset", "method", "budget"]):
        wins += int(group[group.rule.eq("OPT")]["mean"].iloc[0] < group[~group.rule.eq("OPT")]["mean"].min())
    summary.drop(columns="sd").to_csv(output / "summary.csv", index=False)
    import matplotlib.pyplot as plt
    methods = ("Ridge", "Landweber", "Showalter", "HBF", "Nesterov", "SOAR")
    colors = {"UNI":"#4878a8", "NORM":"#d58c38", "LEV":"#46906a", "OPT":"#c44448"}
    references=[]
    for dataset in ("gdsc","year"):
        for method in methods:
            reference=json.loads((folder/"targets"/dataset/method/"summary.json").read_text(encoding="utf-8"))
            references.append(dict(dataset=dataset,method=method,matched_full_test_rmse=reference["full"]["response_test_rmse"]))
    pd.DataFrame(references).to_csv(output/"full_prediction_reference.csv",index=False)
    for dataset in ("gdsc", "year"):
        fig, axes = plt.subplots(2, 3, figsize=(11.5, 6), layout="constrained")
        for ax, method in zip(axes.flat, methods):
            for rule, color in colors.items():
                if dataset == "gdsc" and rule == "NORM":
                    continue
                part = summary[(summary.dataset == dataset) & (summary.method == method) & (summary.rule == rule)].sort_values("budget")
                ax.loglog(part.budget, part["mean"], "o-", ms=3, color=color, label=rule)
            ax.set_title(method)
            ax.set_xlabel("Draw budget N")
            ax.set_ylabel("Mean relative squared coefficient error")
            ax.grid(alpha=.2)
        axes.flat[0].legend(fontsize=8)
        for suffix in ("pdf", "png"):
            fig.savefig(output / ("r5_01_gdsc_target."+suffix if dataset == "gdsc" else "r5_02_year_target."+suffix), dpi=180)
        plt.close(fig)
    fig,axes=plt.subplots(2,6,figsize=(14,5),layout="constrained")
    for row,dataset in enumerate(("gdsc","year")):
        for col,method in enumerate(methods):
            ax=axes[row,col]
            for rule,color in colors.items():
                if dataset=="gdsc" and rule=="NORM":
                    continue
                part=summary[(summary.dataset==dataset)&(summary.method==method)&(summary.rule==rule)].sort_values("budget")
                ax.semilogx(part.budget,part.test_rmse,"o-",ms=2,color=color,label=rule)
            full=next(r["matched_full_test_rmse"] for r in references if r["dataset"]==dataset and r["method"]==method)
            ax.axhline(full,color="#555555",ls="--",lw=.8,label="Full")
            ax.set_title(dataset+" / "+method,fontsize=9)
            ax.set_xlabel("Draw budget N");ax.set_ylabel("Mean test RMSE");ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=7)
    for suffix in ("pdf","png"):
        fig.savefig(output/("r5_04_prediction."+suffix),dpi=180)
    plt.close(fig)
    return dict(passed=True, records=len(data), sketch_tasks=len(data.groupby(["dataset","budget","rep"])),
                cells=78, opt_lowest_observed_cells=wins, support_checks=48,
                saved_summary_matches=True, full_conditional_mse_ordering_inferred=False,
                original_state_array_validation_repeated=False)


def ridge(folder, output):
    data = pd.read_csv(folder / "metrics.csv")
    keys = ["data_id", "budget", "rule"]
    if len(data) != 104000 or data.duplicated(keys+["rep"]).any():
        raise ValueError("Ridge record coverage differs from the protocol")
    if not data.status.eq("complete").all() or not np.isfinite(data.relative_gap).all():
        raise ValueError("Ridge contains incomplete or invalid outcomes")
    if not data.groupby(keys).size().eq(40).all():
        raise ValueError("Ridge repetitions differ")
    means = data.groupby(keys, as_index=False).agg(relative_gap=("relative_gap","mean"), first_order_relative=("first_order_relative","first"))
    curves = []
    for (budget, rule), group in means.groupby(["budget", "rule"]):
        curves.append(dict(budget=int(budget), rule=rule, **interval(group.relative_gap),
                           first_order_relative=float(group.first_order_relative.mean()),
                           calibration=float(group.relative_gap.mean()/group.first_order_relative.mean())))
    summary = pd.DataFrame(curves)
    reference = pd.read_csv(folder / "summary.csv")
    joined = summary.merge(reference, on=["budget","rule"], suffixes=("_new","_saved"), validate="one_to_one")
    for column in ("mean","se","ci_low","ci_high","first_order_relative","calibration"):
        if not np.allclose(joined[column+"_new"], joined[column+"_saved"], rtol=2e-10, atol=1e-13):
            raise ValueError("Ridge summary mismatch: " + column)
    primary = means[means.budget.eq(150)].pivot(index="data_id",columns="rule",values="relative_gap")
    difference = primary.FULL_OPT - primary.LN_floor
    inference = interval(difference)
    inference.update(budget=150, contrast="FULL_OPT minus LN_floor", two_sided_p=float(2*t.sf(abs(inference["mean"]/inference["se"]),39)),
                     full_lower_datasets=int((difference<0).sum()), full_over_ln_ratio_of_means=float(primary.FULL_OPT.mean()/primary.LN_floor.mean()))
    saved = json.loads((folder/"primary_comparison.json").read_text(encoding="utf-8"))
    for column in ("mean","ci_low","ci_high","two_sided_p","full_over_ln_ratio_of_means"):
        if not np.isclose(inference[column],saved[column],rtol=2e-10,atol=1e-13):
            raise ValueError("Primary comparison mismatch: " + column)
    summary.to_csv(output/"summary.csv",index=False)
    means.to_csv(output/"dataset_means.csv",index=False)
    (output/"primary_comparison.json").write_text(json.dumps(inference,indent=2)+"\n",encoding="utf-8")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.3),layout="constrained")
    for rule,color in zip(("UNI","NORM","LEV","LN_floor","FULL_OPT"),("#4878a8","#d58c38","#46906a","#8c62aa","#c44448")):
        group=summary[summary.rule.eq(rule)].sort_values("budget")
        axes[0].plot(group.budget,group["mean"],"o-",ms=3,label=rule,color=color)
        axes[0].fill_between(group.budget,group.ci_low.where(group.ci_low>0,np.nan),group.ci_high,color=color,alpha=.1)
        if rule in ("LN_floor","FULL_OPT"):
            axes[1].plot(group.budget,group.calibration,"o-",label=rule,color=color)
    axes[0].set(xscale="log",yscale="log",xlabel="Draw budget N",ylabel="Mean relative squared coefficient gap")
    axes[1].axhline(1,color="#555555",ls="--",lw=1)
    axes[1].set(xscale="log",xlabel="Draw budget N",ylabel="Empirical mean / first-order prediction")
    for ax in axes:
        ax.grid(alpha=.2);ax.legend(fontsize=8)
    for suffix in ("pdf","png"):
        fig.savefig(output/("ridge_liniu_comparison."+suffix),dpi=180)
    plt.close(fig)
    return dict(passed=True,records=len(data),datasets=40,tasks=520,saved_summary_matches=True,
                primary_matches=True,independent_state_quadratic_form_validation_repeated=False,
                original_independent_validation="independent_validation.json",**inference)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment",choices=("stable-v","ridge-liniu"),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    folder=ROOT/"evidence"/("experiment5_stable" if args.experiment=="stable-v" else "ridge_liniu")
    check_sources(folder)
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    import matplotlib
    matplotlib.use("Agg")
    result=(stable if args.experiment=="stable-v" else ridge)(folder,output)
    result["numerical_trajectories_executed"]=0
    result["bundled_sources_sha256_checked"]=True
    (output/"validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
