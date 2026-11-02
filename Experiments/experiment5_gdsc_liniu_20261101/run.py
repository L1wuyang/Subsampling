"""Add GDSC Ridge LN_floor using the exact saved stable-V pairing.

Only 180 new Ridge solves are executed. Historical scientific sources, data,
targets, probability vectors and 720 baseline records are read without edits.
"""
import os
for key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd
from scipy import linalg as la
from scipy.optimize import brentq
from scipy.stats import t

SOURCE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def constrained(scores, epsilon):
    floor = epsilon / len(scores)
    if scores.max() == 0:
        return np.full(len(scores), 1 / len(scores))
    scaled = scores / scores.max()
    tau = brentq(lambda z: np.maximum(floor, z * scaled).sum() - 1,
                 0, 2 / scaled.sum(), xtol=1e-15, rtol=1e-14)
    return np.maximum(floor, tau * scaled)


def check_predecessor(stable, protocol):
    """Require completed stable results and their scalar/target validation."""
    stable = Path(stable)
    assert read(stable / "protocol.json")["version"] == protocol["predecessor"]
    assert read(stable / "results.json")["completed"]
    assert read(stable / "support_gate.json")["passed"]
    receipt = stable / "independent_validation.json"
    if not receipt.is_file():
        raise FileNotFoundError(
            f'Missing stable-V result-validation receipt: {receipt}. Complete '
            'Experiments/experiment5_support_stable_20261031/compare_results.py '
            '--output STABLE_FORMAL_OUTPUT --historical-root HISTORICAL_V_ROOT first.')
    assert read(receipt)["passed"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True, help="Historical experiment5 inputs directory")
    parser.add_argument("--stable-root", type=Path, required=True, help="Completed support-stable formal_01 output")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    out, stable, inputs = args.output.resolve(), args.stable_root.resolve(), args.input_root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    protocol = read(SOURCE / "protocol.json")
    if (out / "protocol.json").exists():
        assert read(out / "protocol.json") == protocol
    else:
        save(out / "protocol.json", protocol)
    check_predecessor(stable, protocol)
    source_hashes = {p.name: sha(p) for p in (SOURCE / "run.py", SOURCE / "protocol.json")}
    if (out / "source_hashes.json").exists():
        assert read(out / "source_hashes.json") == source_hashes
    else:
        save(out / "source_hashes.json", source_hashes)
    for name in source_hashes:
        (out / "source_snapshot").mkdir(exist_ok=True)
        shutil.copy2(SOURCE / name, out / "source_snapshot" / name)

    input_manifest = read(inputs / "data_manifest.json")
    target_manifest = read(stable / "target_manifest.json")
    consumed = {}
    for name in ("X", "E", "y", "ey"):
        path = inputs / "gdsc" / (name + ".npy")
        assert sha(path) == input_manifest["gdsc/" + path.name]
        consumed[str(path)] = sha(path)
    folder = stable / "targets/gdsc"
    names = ["M.npy", "C.npy", "UNI_probability.npy", "NORM_probability.npy", "LEV_probability.npy",
             "Ridge/target.npy", "Ridge/parameters.json", "Ridge/summary.json", "Ridge/OPT_probability.npy"]
    for name in names:
        path = folder / name
        assert sha(path) == target_manifest["targets/gdsc/" + name]
        consumed[str(path)] = sha(path)
    for path in (stable / "metrics.csv", inputs / "data_manifest.json", stable / "target_manifest.json"):
        consumed[str(path)] = sha(path)
    X, E, y, ey = [np.load(inputs / "gdsc" / (name + ".npy"), mmap_mode="r") for name in ("X", "E", "y", "ey")]
    H, C = [np.load(folder / (name + ".npy")) for name in ("M", "C")]
    target = np.load(folder / "Ridge/target.npy")
    full = read(folder / "Ridge/summary.json")
    parameters = read(folder / "Ridge/parameters.json")
    alpha = parameters["alpha"]
    assert X.shape == (protocol["training_n"], protocol["p"])
    assert E.shape == (protocol["test_n"], protocol["p"])
    assert alpha == protocol["alpha"]
    assert la.norm(H - X @ X.T) / la.norm(H) < 1e-12
    assert la.norm(C.T @ C - H) / la.norm(H) < 1e-12
    assert np.allclose(la.solve(H + alpha * np.eye(len(y)), y, assume_a="pos"), target, rtol=1e-12, atol=1e-14)
    beta = X.T @ target
    denominator = float(beta @ beta)
    assert np.isclose(denominator, full["full"]["coefficient_norm_squared"], rtol=1e-12)
    W = la.solve(H + alpha * np.eye(len(y)), X, assume_a="pos")
    norms = np.einsum("ij,ij->j", X, X)
    ln_scores = np.abs(beta) * np.sqrt(norms)
    full_scores = np.abs(beta) * la.norm(C @ W, axis=0)
    center_vector = C @ (W @ beta)
    center = float(center_vector @ center_vector)
    probabilities = {rule: np.load(folder / ("Ridge/OPT_probability.npy" if rule == "OPT" else rule + "_probability.npy"))
                     for rule in protocol["existing_rules_reused"]}
    probabilities["LN_floor"] = constrained(ln_scores, protocol["probability_floor_mass"])
    analytic_opt = constrained(full_scores, protocol["probability_floor_mass"])
    opt_gap = float(np.max(np.abs(analytic_opt - probabilities["OPT"])))
    assert opt_gap < 1e-11
    constants = {}
    probability_diagnostics = []
    for rule, pi in probabilities.items():
        assert abs(pi.sum() - 1) < 2e-12 and pi.min() >= .01 / len(pi) * (1 - 1e-12)
        constant = max(0., float(np.sum(full_scores ** 2 / pi) - center)) / denominator
        if rule != "LN_floor":
            assert np.isclose(constant, full["constants"][rule], rtol=2e-10, atol=1e-13), (rule, constant)
        constants[rule] = constant
        probability_diagnostics.append(dict(rule=rule, normalized_coefficient_constant=constant,
            min_probability=float(pi.min()), max_probability=float(pi.max()),
            maximum_atom_to_probability=float(np.max(norms / pi)),
            floor_atoms=int(np.count_nonzero(pi <= .01 / len(pi) * (1 + 1e-9)))))
    assert constants["OPT"] <= constants["LN_floor"] * (1 + 1e-10)
    diagnostics = dict(alpha=alpha, coefficient_target_norm_squared=denominator,
        probability_TV_LN_OPT=float(np.sum(np.abs(probabilities["LN_floor"] - probabilities["OPT"])) / 2),
        first_order_reduction_percent=100 * (1 - constants["OPT"] / constants["LN_floor"]),
        max_analytic_OPT_probability_discrepancy=opt_gap, rules=probability_diagnostics,
        stability="Every sampled Gram is positive semidefinite; alpha=17737 makes its Ridge system SPD.")
    save(out / "score_diagnostics.json", diagnostics)
    prepared = out / "prepared"
    prepared.mkdir(exist_ok=True)
    for rule, pi in probabilities.items():
        np.save(prepared / (rule + "_probability.npy"), pi)
    np.save(prepared / "target.npy", target)
    np.save(prepared / "ln_scores.npy", ln_scores)
    np.save(prepared / "full_scores.npy", full_scores)
    prepared_hashes = {p.name: sha(p) for p in prepared.iterdir() if p.is_file()}
    draw_paths = {}
    for budget in protocol["budgets"]:
        for rep in range(protocol["repetitions"]):
            path = stable / "draws/gdsc" / f"r{budget}_rep{rep:03d}.npz"
            draw_paths[str(path)] = sha(path)
    save(out / "sampling_release.json", dict(protocol_sha256=sha(out / "protocol.json"),
        sources=source_hashes, consumed=consumed, predecessor_draw_sha256=draw_paths,
        prepared=prepared_hashes, targets_and_probabilities_fixed_before_sampling=True,
        new_records=180, existing_records_reused=720))
    # No formal draw may run before the immutable pre-sampling receipt above.
    del W
    baseline = pd.read_csv(stable / "metrics.csv")
    baseline = baseline[(baseline.dataset == "gdsc") & (baseline.method == "Ridge")].copy()
    assert len(baseline) == 720 and baseline.status.eq("complete").all()
    Egram = E @ X.T
    design_den = float((H @ target) @ (H @ target))
    full_prediction = Egram @ target
    draws = out / "draws"
    draws.mkdir(exist_ok=True)
    pi = probabilities["LN_floor"]
    cdf = np.cumsum(pi)
    cdf[-1] = 1

    def execute(budget, rep):
        path = stable / "draws/gdsc" / f"r{budget}_rep{rep:03d}.npz"
        with np.load(path, allow_pickle=False) as saved:
            uniforms = saved["uniforms"].copy()
            opt_state = saved["Ridge_OPT_state"].copy()
        generated = np.random.default_rng(np.random.SeedSequence([protocol["sampling_seed"], 0, budget, rep])).random(budget)
        assert np.array_equal(uniforms, generated)
        selected = np.searchsorted(cdf, uniforms, side="right")
        ix, counts = np.unique(selected, return_counts=True)
        Z = X[:, ix] * np.sqrt(counts / (budget * pi[ix]))
        gram = Z @ Z.T
        system = gram + alpha * np.eye(len(y))
        state = la.solve(system, y, assume_a="pos")
        assert np.isfinite(state).all()
        residual = float(la.norm(system @ state - y) / (la.norm(system) * la.norm(state) + la.norm(y)))
        delta = state - target
        coef_delta = X.T @ delta
        squared = float(coef_delta @ coef_delta)
        gram_squared = float(delta @ H @ delta)
        qr_squared = float((C @ delta) @ (C @ delta))
        discrepancy = max(abs(squared - gram_squared), abs(squared - qr_squared)) / max(squared, 1e-30)
        assert discrepancy < 2e-10 and residual < 1e-12
        opt_delta = X.T @ (opt_state - target)
        opt_error = float(opt_delta @ opt_delta) / denominator
        previous = baseline[(baseline.budget == budget) & (baseline.rep == rep) & (baseline.rule == "OPT")].iloc[0]
        opt_discrepancy = abs(opt_error - previous.relative_coefficient_error) / max(opt_error, 1e-30)
        assert opt_discrepancy < 2e-10
        prediction = Egram @ state
        mse = float(np.mean((prediction - ey) ** 2))
        predgap = float(np.mean((prediction - full_prediction) ** 2))
        design_delta = H @ delta
        row = dict(dataset="gdsc", budget=budget, rep=rep, method="Ridge", rule="LN_floor", status="complete",
            relative_coefficient_error=squared / denominator, absolute_coefficient_squared_error=squared,
            relative_design_target_error=float(design_delta @ design_delta) / design_den,
            test_target_prediction_mse=predgap, test_response_mse=mse, test_response_rmse=float(np.sqrt(mse)),
            theoretical_relative_mse=constants["LN_floor"] / budget, unique_objects=len(ix), prescribed_steps=0,
            step_bound_observed=True)
        np.savez_compressed(draws / f"r{budget}_rep{rep:03d}.npz", uniforms=uniforms, indices=ix,
            counts=counts, state=state, relative_error_explicit=squared / denominator,
            relative_error_gram=gram_squared / denominator, relative_error_QR=qr_squared / denominator,
            solve_residual=residual, saved_OPT_error=opt_error)
        return row, dict(budget=budget, rep=rep, solve_residual=residual,
            coordinate_relative_discrepancy=discrepancy, saved_OPT_relative_discrepancy=opt_discrepancy)

    before = time.perf_counter()
    rows, verification = [], []
    tasks = [(budget, rep) for budget in protocol["budgets"] for rep in range(protocol["repetitions"])]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(execute, *task) for task in tasks]
        for index, job in enumerate(as_completed(jobs), 1):
            row, check = job.result()
            rows.append(row)
            verification.append(check)
            if index % 10 == 0 or index == 1:
                print("LN_DRAW", index, len(tasks), "seconds", round(time.perf_counter() - before, 1), flush=True)
                save(out / "status.json", dict(completed=False, completed_draws=index, total_draws=len(tasks)))
    new = pd.DataFrame(rows).sort_values(["budget", "rep"])
    assert len(new) == protocol["expected_new_records"] and new.status.eq("complete").all()
    new.to_csv(out / "new_metrics.csv", index=False)
    combined = pd.concat([baseline, new], ignore_index=True).sort_values(["budget", "rep", "rule"])
    assert len(combined) == protocol["expected_comparison_records"]
    combined.to_csv(out / "comparison_metrics.csv", index=False)
    summaries, comparisons = [], []
    for (budget, rule), group in combined.groupby(["budget", "rule"]):
        errors = group.relative_coefficient_error
        se = float(errors.std(ddof=1) / np.sqrt(len(errors)))
        critical = float(t.ppf(.975, len(errors) - 1))
        mean = float(errors.mean())
        first_order = float(group.theoretical_relative_mse.mean())
        summaries.append(dict(dataset="gdsc", method="Ridge", budget=int(budget), rule=rule, n=len(group),
            mean=mean, se=se, ci_low=mean - critical * se, ci_high=mean + critical * se,
            theoretical=first_order, empirical_to_first_order=mean / first_order,
            test_rmse=float(group.test_response_rmse.mean())))
    for budget, group in combined.groupby("budget"):
        paired = group.pivot(index="rep", columns="rule", values="relative_coefficient_error")
        difference = paired.OPT - paired.LN_floor
        mean, se = float(difference.mean()), float(difference.std(ddof=1) / np.sqrt(len(difference)))
        critical = float(t.ppf(.975, len(difference) - 1))
        comparisons.append(dict(budget=int(budget), repetitions=len(difference),
            LN_mean=float(paired.LN_floor.mean()), OPT_mean=float(paired.OPT.mean()),
            OPT_minus_LN=mean, ci_low=mean - critical * se, ci_high=mean + critical * se,
            reduction_percent=100 * (1 - paired.OPT.mean() / paired.LN_floor.mean()),
            OPT_lower_draws=int((difference < 0).sum())))
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(comparisons).to_csv(out / "paired_comparisons.csv", index=False)
    pd.DataFrame(verification).sort_values(["budget", "rep"]).to_csv(out / "numerical_checks.csv", index=False)
    for path, expected in {**consumed, **draw_paths}.items():
        assert sha(path) == expected, "Consumed input changed: " + path
    for name, expected in source_hashes.items():
        assert sha(SOURCE / name) == expected
    for name, expected in prepared_hashes.items():
        assert sha(prepared / name) == expected
    result = dict(completed=True, protocol=protocol["version"], new_records=180, comparison_records=900,
        failures=0, budgets=protocol["budgets"], paired_uniforms_verified=180,
        max_solve_residual=max(v["solve_residual"] for v in verification),
        max_coordinate_relative_discrepancy=max(v["coordinate_relative_discrepancy"] for v in verification),
        max_saved_OPT_relative_discrepancy=max(v["saved_OPT_relative_discrepancy"] for v in verification),
        all_consumed_sources_unchanged=True, score_diagnostics=diagnostics,
        comparisons=comparisons, formal_draw_seconds=time.perf_counter() - before,
        inferential_scope=protocol["analysis"])
    save(out / "results.json", result)
    save(out / "status.json", dict(completed=True, completed_draws=180, total_draws=180))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
