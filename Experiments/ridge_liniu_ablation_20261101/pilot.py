"""Meaningful small checks and a complete miniature analysis; no formal draws."""
from core import *
import argparse
import importlib.util
import shutil
import traceback
from concurrent.futures import ProcessPoolExecutor

HERE = Path(__file__).resolve().parent


def pilot(output, repo):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    checks = {}
    rng = np.random.default_rng(202611010302)
    X, y = rng.normal(size=(5, 12)), rng.normal(size=5)
    alpha, epsilon = 1.7, .01
    state, diagnostics = setup(X, y, alpha, epsilon)
    primal = solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ y, assume_a="pos")
    assert np.allclose(primal, state["beta"], rtol=1e-12, atol=1e-12)
    checks["dual_equals_primal_ridge"] = True
    errors = []
    for j in range(X.shape[1]):
        atom = np.outer(X[:, j], X[:, j])
        step = 1e-5
        plus = X.T @ solve(state["H"] + step * atom + alpha * np.eye(len(y)), y, assume_a="pos")
        minus = X.T @ solve(state["H"] - step * atom + alpha * np.eye(len(y)), y, assume_a="pos")
        numerical = (plus - minus) / (2 * step)
        analytic = -state["beta"][j] * X.T @ solve(
            state["H"] + alpha * np.eye(len(y)), X[:, j], assume_a="pos")
        errors.append(float(np.linalg.norm(numerical - analytic) /
                            max(1e-12, np.linalg.norm(analytic))))
        assert np.allclose(numerical, analytic, rtol=2e-6, atol=2e-10)
        assert np.isclose(np.linalg.norm(analytic), state["full_scores"][j], rtol=1e-12, atol=1e-13)
    checks["all_atom_derivatives_max_relative_error"] = max(errors)
    for scores in [np.array([0., 0., 1e-200, 1., 7.]), np.arange(1., 10.)]:
        pi = constrained(scores, epsilon)
        assert np.isclose(pi.sum(), 1, rtol=0, atol=2e-12)
        assert (pi >= epsilon / len(scores)).all()
        free = pi > epsilon / len(scores) * (1 + 1e-8)
        assert np.allclose(scores[free] / pi[free], (scores[free] / pi[free])[0], rtol=1e-10)
    assert np.array_equal(constrained(np.zeros(4), epsilon), np.full(4, .25))
    checks["water_filling_KKT_extreme_zero_scores"] = True
    isoX = np.concatenate([np.eye(4), np.eye(4)], axis=1)
    iso, _ = setup(isoX, np.array([.1, -.4, .2, .8]), alpha, epsilon)
    assert np.allclose(iso["pi_LN_floor"], iso["pi_FULL_OPT"], atol=2e-13)
    checks["isotropic_LN_and_FULL_coincide"] = True
    zeros, _ = setup(X, np.zeros(5), alpha, epsilon)
    assert np.allclose(zeros["pi_LN_floor"], np.full(12, 1 / 12))
    assert np.allclose(zeros["pi_FULL_OPT"], np.full(12, 1 / 12))
    checks["zero_response_uniform_oracle_fallback"] = True
    selected = np.array([0, 0, 3, 5, 5])
    pi = state["pi_FULL_OPT"]
    explicit = sum(np.outer(X[:, j], X[:, j]) / (len(selected) * pi[j]) for j in selected)
    counts = np.bincount(selected, minlength=X.shape[1])
    nz = np.flatnonzero(counts)
    weighted = X[:, nz] * np.sqrt(counts[nz] / (len(selected) * pi[nz]))
    assert np.allclose(explicit, weighted @ weighted.T)
    checks["repeated_atoms_and_inverse_probability_weights"] = True
    native_path = Path(repo) / "Experiments/experiment1_native_comprehensive_20261024/native.py"
    spec = importlib.util.spec_from_file_location("historical_native_ln_check", native_path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    ref, tangent = native.full(X, state["H"], y, {"method": "Ridge", "alpha": alpha})
    assert np.allclose(ref, state["full_u"], rtol=1e-13, atol=1e-13)
    old_scores = np.sqrt(np.sum(tangent * (state["H"] @ tangent), axis=0))
    assert np.allclose(old_scores, state["full_scores"], rtol=1e-12, atol=1e-13)
    checks["agreement_with_frozen_Ridge_target_and_influences"] = True
    # A fake predecessor tests only the gate predicate; never handed to the production queue.
    gate = output / "fake_predecessor"
    gate.mkdir()
    assert not predecessor_ready(gate)[0]
    save(gate / "protocol.json", dict(version=V_VERSION))
    save(gate / "status.json", dict(completed=True))
    assert not predecessor_ready(gate)[0]
    save(gate / "results.json", dict(completed=True, records=12720))
    save(gate / "support_gate.json", dict(passed=True))
    save(gate / "independent_validation.json",
         dict(passed=True, records=12720, tasks=530, opt_lowest_cells=0))
    for name in ("RESULTS.md", "old_new_comparison.csv", "target_changes.csv", "old_new_comparison.png"):
        (gate / name).write_text("gate fixture only", encoding="utf-8")
    assert predecessor_ready(gate)[0], "Gate must not require an OPT victory"
    save(gate / "support_gate.json", dict(passed=False))
    assert not predecessor_ready(gate)[0]
    checks["predecessor_gate_requires_all_files_and_no_ranking_filter"] = True
    # Two synthetic data sets, three budgets, nine paired draws, five rules: 270 checks.
    prepared, run = output / "mini_prepared", output / "mini_run"
    (prepared / "states").mkdir(parents=True)
    (run / "tasks").mkdir(parents=True)
    config = dict(version="pilot-only-synthetic-LN-v1", scope="pilot_only",
                  data_ids=[1, 2], budgets=[2, 5, 13], repetitions=9,
                  sampling_seed=202611010303, rules=list(RULES),
                  primary=dict(budget=5))
    rows = []
    for did in config["data_ids"]:
        xx, yy = rng.normal(size=(5, 12)), rng.normal(size=5)
        ss, dd = setup(xx, yy, alpha, epsilon)
        save_npz(prepared / "states" / f"data_{did:02d}.npz", **ss)
        rows.extend(dict(data_id=did, **r) for r in dd)
    write_rows(prepared / "score_diagnostics.csv", rows)
    save(prepared / "protocol.json", config)
    mini_files = {p.relative_to(prepared).as_posix(): digest(p)
                  for p in prepared.rglob("*") if p.is_file()}
    save(prepared / "seal.json", dict(files=mini_files))
    identity = digest(prepared / "seal.json")
    with ProcessPoolExecutor(max_workers=2) as pool:
        work = [pool.submit(execute_task, str(prepared), str(run), did, budget, config, identity)
                for did in config["data_ids"] for budget in config["budgets"]]
        for item in work:
            assert item.result()["failures"] == 0
    checks["Windows_spawn_two_worker_execution"] = True
    before = digest(run / "tasks" / (task_key(1, 2) + ".csv"))
    execute_task(prepared, run, 1, 2, config, identity)
    assert digest(run / "tasks" / (task_key(1, 2) + ".csv")) == before
    checks["completed_task_resume_is_byte_preserving"] = True
    from analyze import analyze
    verified = analyze(prepared, run)
    assert verified["passed"] and verified["rows"] == 270 and verified["tasks"] == 6
    checks["miniature_end_to_end_270_rows_verified"] = True
    target = prepared / "protocol.json"
    payload = target.read_bytes()
    target.write_bytes(payload + b" ")
    try:
        verify_prepared(prepared)
    except ValueError:
        checks["tampered_preparation_rejected"] = True
    else:
        raise AssertionError("Tampered preparation accepted")
    finally:
        target.write_bytes(payload)
    original_task = (run / "tasks" / (task_key(1, 2) + ".csv")).read_bytes()
    task_path = run / "tasks" / (task_key(1, 2) + ".csv")
    task_path.write_bytes(original_task + b"\n")
    try:
        execute_task(prepared, run, 1, 2, config, identity)
    except ValueError:
        checks["tampered_completed_task_rejected"] = True
    else:
        raise AssertionError("Tampered task accepted")
    finally:
        task_path.write_bytes(original_task)
    result = dict(passed=True, checks=checks,
                  sources={name: digest(HERE / name) for name in SOURCE_FILES},
                  frozen_native_sha256=digest(native_path),
                  synthetic_rows=270, formal_draws_executed=0)
    save(output / "pilot.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        pilot(args.output, args.repo)
    except Exception:
        traceback.print_exc()
        raise
