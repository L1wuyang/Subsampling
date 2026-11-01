"""Independently reaggregate saved GDSC-LN metrics, optionally check raw states.

No additional estimator solves are executed. Pointwise intervals describe
Monte Carlo uncertainty conditional on the single fixed training data set.
"""
import os
for key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[key] = "1"

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--stable-root", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, help="Optional raw-state validation using original inputs")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    protocol = read("protocol.json")
    release = read("sampling_release.json")
    new = pd.read_csv(root / "new_metrics.csv")
    data = pd.read_csv(root / "comparison_metrics.csv")
    summary = pd.read_csv(root / "summary.csv")
    pairs = pd.read_csv(root / "paired_comparisons.csv")
    old = pd.read_csv(args.stable_root / "metrics.csv")
    old = old[(old.dataset == "gdsc") & (old.method == "Ridge")]
    keys = ["budget", "rep", "rule"]
    assert len(new) == 180 and len(data) == 900 and len(summary) == 30 and len(old) == 720
    assert not data.duplicated(keys).any() and data.status.eq("complete").all()
    assert new.rule.eq("LN_floor").all()
    inherited = data[data.rule != "LN_floor"].sort_values(keys).reset_index(drop=True)
    original = old.sort_values(keys).reset_index(drop=True)
    for column in old.columns:
        if pd.api.types.is_numeric_dtype(old[column]):
            assert np.allclose(inherited[column], original[column], rtol=2e-14, atol=1e-15), column
        else:
            assert inherited[column].equals(original[column]), column
    for (budget, rule), group in data.groupby(["budget", "rule"]):
        expected = summary[(summary.budget == budget) & (summary.rule == rule)].iloc[0]
        error = group.relative_coefficient_error.to_numpy()
        se = np.std(error, ddof=1) / np.sqrt(30)
        half = t.ppf(.975, 29) * se
        actual = [error.mean(), se, error.mean() - half, error.mean() + half,
                  group.theoretical_relative_mse.mean(), group.test_response_rmse.mean()]
        assert np.allclose(actual, expected[["mean", "se", "ci_low", "ci_high", "theoretical", "test_rmse"]].to_numpy(dtype=float),
                           rtol=2e-12, atol=1e-14)
    for budget, group in data.groupby("budget"):
        pivot = group.pivot(index="rep", columns="rule", values="relative_coefficient_error")
        difference = (pivot.OPT - pivot.LN_floor).to_numpy()
        expected = pairs[pairs.budget == budget].iloc[0]
        half = t.ppf(.975, 29) * difference.std(ddof=1) / np.sqrt(30)
        assert np.allclose([difference.mean(), difference.mean() - half, difference.mean() + half],
                           expected[["OPT_minus_LN", "ci_low", "ci_high"]].to_numpy(dtype=float), rtol=2e-12, atol=1e-14)
    for name, expected in release["prepared"].items():
        assert sha(root / "prepared" / name) == expected
    checked_states = 0
    max_relative_error = 0.
    if args.input_root:
        X = np.load(args.input_root / "gdsc/X.npy", mmap_mode="r")
        E = np.load(args.input_root / "gdsc/E.npy", mmap_mode="r")
        ey = np.load(args.input_root / "gdsc/ey.npy")
        target = np.load(root / "prepared/target.npy")
        denominator = float(np.linalg.norm(X.T @ target) ** 2)
        pi = np.load(root / "prepared/LN_floor_probability.npy")
        cdf = np.cumsum(pi)
        cdf[-1] = 1
        Egram = E @ X.T
        for row in new.itertuples():
            path = root / "draws" / f"r{row.budget}_rep{row.rep:03d}.npz"
            with np.load(path) as saved:
                regenerated = np.random.default_rng(np.random.SeedSequence(
                    [protocol["sampling_seed"], 0, row.budget, row.rep])).random(row.budget)
                assert np.array_equal(regenerated, saved["uniforms"])
                ix, counts = np.unique(np.searchsorted(cdf, regenerated, side="right"), return_counts=True)
                assert np.array_equal(ix, saved["indices"]) and np.array_equal(counts, saved["counts"])
                state = saved["state"]
                error = np.linalg.norm(X.T @ (state - target)) ** 2 / denominator
                residual = abs(error - row.relative_coefficient_error) / error
                max_relative_error = max(max_relative_error, float(residual))
                assert residual < 1e-11
                mse = np.mean((Egram @ state - ey) ** 2)
                assert np.isclose(mse, row.test_response_mse, rtol=1e-12)
                assert saved["solve_residual"] < 1e-12
                checked_states += 1
    report = dict(passed=True, comparison_records=900, newly_computed_records=180,
        preserved_baseline_records=720, independently_reaggregated_summary_cells=30,
        independently_reaggregated_paired_intervals=6, raw_states_verified=checked_states,
        max_recomputed_relative_error=max_relative_error, extra_estimator_solves=0,
        interval_scope="Pointwise t29 Monte Carlo intervals conditional on one fixed dataset; all budgets descriptive",
        files={name:sha(root / name) for name in ["protocol.json", "new_metrics.csv", "comparison_metrics.csv",
                                                "summary.csv", "paired_comparisons.csv", "score_diagnostics.json"]})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
