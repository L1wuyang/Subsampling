"""Frozen Ridge probability ablation; direct solves and explicit full recovery."""
import os
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import solve
from scipy.optimize import brentq

RULES = ("UNI", "NORM", "LEV", "LN_floor", "FULL_OPT")
SOURCE_FILES = ("core.py", "protocol.json", "pilot.py", "run_experiment.py",
                "analyze.py", "queue_after_v.py", "README_CN.md")
V_VERSION = "experiment-V-support-stable-20261031-v1"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def save_npz(path, **arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    os.replace(temporary, path)


def write_rows(path, rows):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def constrained(scores, epsilon):
    """Solve the floor-constrained score objective, including zero scores."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError("Scores must be a finite nonnegative vector")
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must lie strictly between zero and one")
    p = len(scores)
    if scores.max() == 0:
        return np.full(p, 1.0 / p)
    scaled = scores / scores.max()
    floor = epsilon / p
    tau = brentq(lambda t: np.maximum(floor, t * scaled).sum() - 1,
                 0.0, 2.0 / scaled.sum(), xtol=1e-15, rtol=1e-14)
    probability = np.maximum(floor, tau * scaled)
    if abs(probability.sum() - 1) > 2e-12:
        raise ValueError("Probability normalization failed")
    return probability


def load_input(path, config):
    """Same deterministic main-arm reconstruction as frozen Experiment I."""
    with np.load(path, allow_pickle=False) as data:
        G, z = data["G"], data["scale_z"]
        beta, noise = data["beta0"], data["standard_noise"]
    if G.shape != (config["n"], config["p"]):
        raise ValueError("Input dimensions differ from protocol")
    scales = np.exp(config["heterogeneity"] * z)
    scales = np.minimum(scales, np.quantile(scales, .98, method="linear"))
    scales /= np.sqrt(np.mean(scales ** 2))
    X = G * scales / np.sqrt(len(noise))
    y = X @ beta + config["sigma"] * noise
    return X, y


def setup(X, y, alpha, epsilon):
    """Analytic unit-atom influences, without eigensolvers or explicit inverses."""
    H = X @ X.T
    u = solve(H + alpha * np.eye(len(y)), y, assume_a="pos")
    beta = X.T @ u
    W = solve(H + alpha * np.eye(len(y)), X, assume_a="pos")
    norms = np.sum(X * X, axis=0)
    leverage = np.maximum(np.sum(X * solve(H, X, assume_a="pos"), axis=0), 0)
    transformed_sq = np.maximum(np.sum(W * (H @ W), axis=0), 0)
    ln_scores = np.abs(beta) * np.sqrt(norms)
    full_scores = np.abs(beta) * np.sqrt(transformed_sq)
    J = -W * beta[None, :]
    sumJ = J.sum(axis=1)
    center = float(sumJ @ H @ sumJ)
    probabilities = {
        "UNI": np.full(X.shape[1], 1 / X.shape[1]),
        "NORM": (1 - epsilon) * norms / norms.sum() + epsilon / len(norms),
        "LEV": (1 - epsilon) * leverage / leverage.sum() + epsilon / len(norms),
        "LN_floor": constrained(ln_scores, epsilon),
        "FULL_OPT": constrained(full_scores, epsilon)}
    diagnostics = []
    for rule, pi in probabilities.items():
        if (pi < epsilon / len(pi) - 1e-15).any() or abs(pi.sum() - 1) > 2e-12:
            raise ValueError("Invalid probability vector")
        uncentered = float(np.sum(full_scores ** 2 / pi))
        criterion = uncentered - center
        if criterion < -1e-10 * max(1.0, uncentered):
            raise ValueError("Coefficient covariance trace is negative")
        diagnostics.append(dict(
            rule=rule, alpha=float(alpha), target_norm_sq=float(beta @ beta),
            coefficient_Q=max(0.0, criterion), inner_surrogate=float(np.sum(ln_scores ** 2 / pi)),
            min_probability=float(pi.min()), max_probability=float(pi.max()),
            floor_atoms=int(np.sum(pi <= epsilon / len(pi) * (1 + 1e-9)))))
    reference = diagnostics[-1]["coefficient_Q"]
    if any(reference > r["coefficient_Q"] + 1e-10 * max(1, r["coefficient_Q"]) for r in diagnostics):
        raise ValueError("FULL_OPT does not minimize its fixed coefficient criterion")
    state = dict(X=X, y=y, H=H, alpha=np.array(alpha), full_u=u, beta=beta,
                 ln_scores=ln_scores, full_scores=full_scores, center=np.array(center),
                 **{"pi_" + name: pi for name, pi in probabilities.items()},
                 **{"Q_" + r["rule"]: np.array(r["coefficient_Q"]) for r in diagnostics})
    return state, diagnostics


def verify_prepared(prepared, check_live=False):
    prepared = Path(prepared)
    seal = read(prepared / "seal.json")
    for relative, expected in seal["files"].items():
        if digest(prepared / relative) != expected:
            raise ValueError("Prepared artifact changed: " + relative)
    if check_live:
        for name, expected in seal["sources"].items():
            if digest(Path(seal["source_directory"]) / name) != expected:
                raise ValueError("Live source changed after preparation: " + name)
    return seal


def predecessor_ready(output):
    """Require computation and independent old/new report, irrespective of ranking."""
    output = Path(output)
    try:
        if read(output / "protocol.json").get("version") != V_VERSION:
            return False, "实验五协议不匹配"
        if not read(output / "status.json").get("completed"):
            return False, "等待实验五全部正式抽样完成"
        results = read(output / "results.json")
        if not results.get("completed") or results.get("records") != 12720:
            return False, "等待实验五完整结果"
        if not read(output / "support_gate.json").get("passed"):
            return False, "等待实验五全支持稳定性门禁"
        validation = read(output / "independent_validation.json")
        if not validation.get("passed") or validation.get("records") != 12720 or validation.get("tasks") != 530:
            return False, "等待实验五独立核验"
        for name in ("RESULTS.md", "old_new_comparison.csv", "target_changes.csv",
                     "old_new_comparison.png"):
            if not (output / name).is_file():
                return False, "等待实验五新旧对照报告完成"
        return True, "实验五正式计算与独立结果核验均已完成"
    except (OSError, ValueError, KeyError):
        return False, "等待实验五完成标志及独立核验文件"


def task_key(data_id, budget):
    return f"d{data_id:02d}_N{budget}"


def execute_task(prepared, output, data_id, budget, config, identity):
    """One data-set/budget checkpoint; all rules use the same uniforms."""
    prepared, output = Path(prepared), Path(output)
    key = task_key(data_id, budget)
    folder = output / "tasks"
    marker = folder / (key + ".json")
    if marker.exists():
        old = read(marker)
        if old["identity"] != identity:
            raise ValueError("Task identity mismatch")
        for name, expected in old["files"].items():
            if digest(folder / name) != expected:
                raise ValueError("Completed task corrupted: " + name)
        return old
    with np.load(prepared / "states" / f"data_{data_id:02d}.npz", allow_pickle=False) as values:
        state = {k: values[k] for k in values.files}
    X, H, y, alpha = state["X"], state["H"], state["y"], float(state["alpha"])
    reps = config["repetitions"]
    uniforms = np.random.default_rng(np.random.SeedSequence(
        [config["sampling_seed"], data_id, budget, 1])).random((reps, budget))
    rows, arrays = [], dict(uniforms=uniforms)
    target_norm = float(state["beta"] @ state["beta"])
    started = time.perf_counter()
    failures = 0
    for rule in config["rules"]:
        pi = state["pi_" + rule]
        cdf = np.cumsum(pi)
        cdf[-1] = 1.0
        indices = np.searchsorted(cdf, uniforms, side="right")
        U = np.full((reps, len(y)), np.nan)
        for rep, selected in enumerate(indices):
            counts = np.bincount(selected, minlength=X.shape[1])
            active = np.flatnonzero(counts)
            Z = X[:, active] * np.sqrt(counts[active] / (budget * pi[active]))
            B = Z @ Z.T
            status = "complete"
            message = ""
            absolute = relative = None
            try:
                U[rep] = solve(B + alpha * np.eye(len(y)), y, assume_a="pos")
                coefficient_error = (U[rep] - state["full_u"]) @ X
                absolute = float(coefficient_error @ coefficient_error)
                if not np.isfinite(U[rep]).all() or not np.isfinite(absolute):
                    raise FloatingPointError("nonfinite solve/metric")
                if target_norm > 1e-24:
                    relative = absolute / target_norm
                else:
                    status = "zero_target"
            except (ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
                status, message = "numerical_failure", type(error).__name__ + ": " + str(error)
                absolute = relative = None
                failures += 1
            rows.append(dict(data_id=data_id, budget=budget, rule=rule, rep=rep,
                             status=status, error=message, absolute_gap=absolute,
                             relative_gap=relative, unique_atoms=len(active),
                             target_norm_sq=target_norm,
                             first_order_relative=float(state["Q_" + rule]) / budget / target_norm
                             if target_norm > 1e-24 else None))
        arrays["U_" + rule] = U
    folder.mkdir(parents=True, exist_ok=True)
    csv_path, raw_path = folder / (key + ".csv"), folder / (key + ".npz")
    write_rows(csv_path, rows)
    save_npz(raw_path, **arrays)
    result = dict(identity=identity, data_id=data_id, budget=budget, rows=len(rows),
                  failures=failures, seconds=time.perf_counter() - started,
                  files={p.name: digest(p) for p in (csv_path, raw_path)})
    save(marker, result)
    return result
