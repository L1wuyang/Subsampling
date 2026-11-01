"""Make review figures from completed saved results; never rerun estimators."""
from pathlib import Path
import argparse
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter
import numpy as np
import pandas as pd
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
CHANGES = ROOT.parents[1] / "changes"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--evidence-root", type=Path, help="Companion evidence directory containing experiment5_stable and ridge_liniu")
parser.add_argument("--output", type=Path, default=ROOT / "Overleaf" / "figures")
parser.add_argument("--qa-output", type=Path, default=ROOT / "review" / "figures")
parser.add_argument("--receipt", type=Path, default=ROOT / "review" / "figure_receipt.json")
args = parser.parse_args()
SOURCES = args.evidence_root.resolve() if args.evidence_root else CHANGES
V = SOURCES / "experiment5_stable" if args.evidence_root else CHANGES / "experiment_v_stable_rerun_20261031" / "formal_01"
LN = SOURCES / "ridge_liniu" if args.evidence_root else CHANGES / "ridge_liniu_ablation_20261101" / "formal_01"
OUT = args.output
QA = args.qa_output
OUT.mkdir(parents=True, exist_ok=True)
QA.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({
    "font.family": "serif", "font.size": 8,
    "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.spines.top": False,
    "axes.spines.right": False, "pdf.fonttype": 42,
    "ps.fonttype": 42, "lines.linewidth": 1.1,
    "axes.linewidth": .55, "savefig.dpi": 180,
})
METHODS = ["Ridge", "Landweber", "Showalter", "HBF", "Nesterov", "SOAR"]
COLORS = {"UNI": "#5B6676", "NORM": "#277DA8", "LEV": "#D68B24",
          "OPT": "#B83D47", "LN_floor": "#277DA8", "FULL_OPT": "#B83D47"}
MARKERS = {"UNI": "o", "NORM": "s", "LEV": "^", "OPT": "D",
           "LN_floor": "s", "FULL_OPT": "D"}
STYLES = {"UNI": "-", "NORM": "--", "LEV": "-.", "OPT": "-",
          "LN_floor": "--", "FULL_OPT": "-"}
GDSC_LN = SOURCES / "gdsc_ridge_liniu" if args.evidence_root else CHANGES / "experiment_v_gdsc_liniu_20261101" / "formal_01"
gdsc_ln = pd.read_csv(GDSC_LN / "summary.csv")
gdsc_pairs = pd.read_csv(GDSC_LN / "paired_comparisons.csv")
assert len(gdsc_ln) == 30 and len(gdsc_pairs) == 6
v = pd.read_csv(V / "summary.csv")
ln = pd.read_csv(LN / "summary.csv")
dm = pd.read_csv(LN / "dataset_means.csv")
assert len(v) == 312 and len(ln) == 65 and len(dm) == 2600
generated = []


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=.035,
                metadata={"Title": name.removesuffix(".pdf")})
    fig.savefig(QA / name.replace(".pdf", ".png"), bbox_inches="tight", pad_inches=.035)
    generated.append(name)
    plt.close(fig)


def grid(ax):
    ax.grid(True, which="major", color="#DDE1E6", linewidth=.45, alpha=.8)
    ax.set_axisbelow(True)


for dataset, name in [("gdsc", "r5_01_gdsc_target.pdf"), ("year", "r5_02_year_target.pdf")]:
    fig, axes = plt.subplots(2, 3, figsize=(6.35, 3.35))
    for ax, method in zip(axes.flat, METHODS):
        for rule in ["UNI", "NORM", "LEV", "OPT"]:
            d = v[(v.dataset == dataset) & (v.method == method) & (v.rule == rule)].sort_values("budget")
            # GDSC NORM=UNI is displayed as the same line, without artificial offsets.
            ax.plot(d.budget, d["mean"], color=COLORS[rule], marker=MARKERS[rule],
                    markersize=2.5, linestyle=STYLES[rule], label=rule)
        if dataset == "gdsc" and method == "Ridge":
            d = gdsc_ln[gdsc_ln.rule == "LN_floor"].sort_values("budget")
            ax.plot(d.budget, d["mean"], color="#7555A1", marker="x", markersize=3,
                    linestyle="--", label="LN_floor")
        ax.set(xscale="log", yscale="log", title=method)
        ax.xaxis.set_minor_formatter(NullFormatter())
        grid(ax)
    for ax in axes[1]:
        ax.set_xlabel("Draw budget $N$")
    for ax in axes[:, 0]:
        ax.set_ylabel("Relative squared error")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False,
               bbox_to_anchor=(.53, 1.015))
    fig.subplots_adjust(left=.08, right=.995, bottom=.13, top=.88, wspace=.30, hspace=.50)
    save(fig, name)

fig, axes = plt.subplots(2, 6, figsize=(7.0, 3.15))
for row, dataset in enumerate(["gdsc", "year"]):
    for col, method in enumerate(METHODS):
        ax = axes[row, col]
        for rule in ["UNI", "NORM", "LEV", "OPT"]:
            d = v[(v.dataset == dataset) & (v.method == method) & (v.rule == rule)].sort_values("budget")
            ax.plot(d.budget, d.test_rmse, color=COLORS[rule], linestyle=STYLES[rule], label=rule)
        if dataset == "gdsc" and method == "Ridge":
            d = gdsc_ln[gdsc_ln.rule == "LN_floor"].sort_values("budget")
            ax.plot(d.budget, d.test_rmse, color="#7555A1", linestyle="--", label="LN_floor")
        full = json.loads((V / "targets" / dataset / method / "summary.json").read_text())
        ax.axhline(full["full"]["response_test_rmse"], color="black", ls=":", lw=.8, label="Full model")
        ax.set_xscale("log")
        ax.set_title(method)
        ax.tick_params(labelsize=6)
        if col == 0:
            ax.set_ylabel(("GDSC" if row == 0 else "Year") + " test RMSE")
        if row == 1:
            ax.set_xlabel("Draw budget $N$", fontsize=7)
        ax.xaxis.set_major_locator(LogLocator(base=10, numticks=3))
        ax.xaxis.set_minor_formatter(NullFormatter())
        grid(ax)
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, bbox_to_anchor=(.53, 1.02))
fig.subplots_adjust(left=.07, right=.995, bottom=.13, top=.87, wspace=.65, hspace=.65)
save(fig, "r5_04_prediction.pdf")

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.5), gridspec_kw={"width_ratios": [1.15, 1]})
for rule in ["UNI", "NORM", "LEV", "LN_floor", "FULL_OPT"]:
    d = ln[ln.rule == rule].sort_values("budget")
    ax = axes[0]
    ax.plot(d.budget, d["mean"], color=COLORS[rule], marker=MARKERS[rule],
            markersize=2.4, ls=STYLES[rule], label=rule)
    ax.fill_between(d.budget.to_numpy(), d.ci_low.to_numpy(), d.ci_high.to_numpy(), color=COLORS[rule], alpha=.12, linewidth=0)
axes[0].set(xscale="log", yscale="log", xlabel="Draw budget $N$", ylabel="Relative squared error", title="Coefficient-target approximation")
axes[0].legend(frameon=False, ncol=2, fontsize=6.7, loc="lower left")
grid(axes[0])
paired = dm.pivot(index=["data_id", "budget"], columns="rule", values="relative_gap")
diff = (paired.FULL_OPT - paired.LN_floor).groupby("budget").agg(["mean", "std", "count"])
half = t.ppf(.975, 39) * diff["std"] / np.sqrt(diff["count"])
axes[1].axhline(0, color="#5B6676", lw=.7)
axes[1].errorbar(diff.index, diff["mean"], yerr=half, color="#5B6676", marker="o", ms=2.5, lw=.8, capsize=2)
axes[1].errorbar([150], [diff.loc[150, "mean"]], yerr=[half.loc[150]], color=COLORS["FULL_OPT"], marker="D", ms=4.0, lw=1.4, capsize=3)
axes[1].set(xscale="log", xlabel="Draw budget $N$", ylabel="Paired mean error difference", title="FULL_OPT minus LN_floor")
axes[1].text(.96, .94, "$N=150$: primary", ha="right", va="top", transform=axes[1].transAxes, fontsize=7, color=COLORS["FULL_OPT"])
axes[1].ticklabel_format(axis="y", style="sci", scilimits=(-3, -3), useMathText=True)
for ax in axes:
    ax.xaxis.set_minor_formatter(NullFormatter())
    grid(ax)
fig.subplots_adjust(left=.09, right=.99, bottom=.20, top=.87, wspace=.42)
save(fig, "r1_04_ridge_liniu.pdf")

fig, ax = plt.subplots(figsize=(5.8, 2.5))
for rule in ["LN_floor", "FULL_OPT"]:
    d = ln[ln.rule == rule].sort_values("budget")
    ax.plot(d.budget, d.calibration, color=COLORS[rule], marker=MARKERS[rule],
            markersize=3.0, ls=STYLES[rule], label=rule)
ax.axhline(1, color="#5B6676", ls=":", lw=.8)
ax.set(xscale="log", xlabel="Draw budget $N$", ylabel="Empirical error / first-order prediction")
ax.set_ylim(.98, 1.65)
ax.legend(frameon=False, loc="upper right")
ax.xaxis.set_minor_formatter(NullFormatter())
grid(ax)
fig.subplots_adjust(left=.12, right=.99, bottom=.20, top=.98)
save(fig, "r1_05_ridge_liniu_calibration.pdf")

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.5), gridspec_kw={"width_ratios": [1.05, 1]})
for rule in ["UNI", "NORM", "LEV", "OPT", "LN_floor"]:
    d = gdsc_ln[gdsc_ln.rule == rule].sort_values("budget")
    color = "#7555A1" if rule == "LN_floor" else COLORS[rule]
    axes[0].plot(d.budget, d["mean"], color=color, marker=MARKERS[rule], ms=2.5, ls=STYLES[rule], label=rule)
axes[0].set(xscale="log", yscale="log", xlabel="Draw budget $N$", ylabel="Relative squared error", title="GDSC Ridge: five sampling rules")
axes[0].legend(frameon=False, fontsize=6.8, ncol=2, loc="lower left")
axes[1].axhline(0, color="#5B6676", lw=.7)
d = gdsc_pairs.sort_values("budget")
axes[1].errorbar(d.budget, d.OPT_minus_LN,
                 yerr=[d.OPT_minus_LN - d.ci_low, d.ci_high - d.OPT_minus_LN],
                 color="#7555A1", marker="o", ms=3, lw=.8, capsize=2)
axes[1].set(xscale="log", xlabel="Draw budget $N$", ylabel="Paired mean error difference", title="OPT minus LN_floor")
for ax in axes:
    ax.xaxis.set_minor_formatter(NullFormatter())
    grid(ax)
fig.subplots_adjust(left=.09, right=.99, bottom=.20, top=.87, wspace=.43)
save(fig, "r5_05_gdsc_liniu.pdf")

receipt = {
    "operation": "redraw_saved_results_only", "generated": {},
    "sources": {p.relative_to(SOURCES).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [V / "summary.csv", LN / "summary.csv", LN / "dataset_means.csv"]
                + [V / "targets" / d / m / "summary.json" for d in ["gdsc", "year"] for m in METHODS]
                + [GDSC_LN / "summary.csv", GDSC_LN / "paired_comparisons.csv"]},
    "V_finite_repetition_means_without_confidence_bands": True,
    "LN_interval_units": "40 independent data-set means; paired differences use the same inputs",
    "LN_primary_budget": 150,
    "GDSC_LN_interval_units": "30 paired common-uniform draws, single fixed dataset; pointwise t29 Monte Carlo intervals",
    "GDSC_LN_all_budgets_descriptive": True,
}
for name in generated:
    receipt["generated"]["figures/" + name] = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
args.receipt.parent.mkdir(parents=True, exist_ok=True)
args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
