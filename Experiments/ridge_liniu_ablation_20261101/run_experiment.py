"""Prepare exact scores now; release the formal ablation only after stable V."""
from core import *
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import shutil
import sys
import traceback

HERE = Path(__file__).resolve().parent


def prepare(repo, output):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Preparation directory already exists; never overwrite a frozen preparation")
    config = read(HERE / "protocol.json")
    descriptor = repo / "provenance/review_data.json"
    prior_protocol = repo / "simulations/experiment1/metadata/protocol.json"
    for path, expected in [(descriptor, config["review_descriptor_sha256"]),
                           (prior_protocol, config["original_protocol_sha256"])]:
        if digest(path) != expected.lower():
            raise ValueError("Reference descriptor/protocol changed: " + str(path))
    original = read(prior_protocol)
    main_arm = next(a for a in original["arms"] if a["tag"] == "main")
    if (original["n"], original["p"], main_arm["c"], main_arm["sigma"],
        main_arm["heterogeneity"], main_arm["floor"]) != (
            config["n"], config["p"], config["alpha_multiplier"], config["sigma"],
            config["heterogeneity"], config["epsilon"]):
        raise ValueError("Main-arm reconstruction parameters changed")
    if config["data_ids"] != main_arm["data_ids"] or config["budgets"] != main_arm["budgets"]:
        raise ValueError("Input/budget population differs from original main arm")
    if config["sampling_seed"] == original["sampling_seed"]:
        raise ValueError("A fresh sampling seed is required")
    sources = {name: digest(HERE / name) for name in SOURCE_FILES}
    output.mkdir(parents=True)
    (output / "states").mkdir()
    (output / "source_snapshot").mkdir()
    for name in SOURCE_FILES:
        shutil.copy2(HERE / name, output / "source_snapshot" / name)
    save(output / "protocol.json", config)
    provenance = read(descriptor)["files"]
    input_hashes, rows = {}, []
    for data_id in config["data_ids"]:
        relative = f"simulations/experiment1/inputs/data_{data_id:02d}.npz"
        expected = provenance[relative]["sha256"]
        if digest(repo / relative) != expected:
            raise ValueError("Stored input digest differs from review-data descriptor")
        input_hashes[relative] = expected
        X, y = load_input(repo / relative, config)
        alpha = config["alpha_multiplier"] * np.trace(X @ X.T) / len(y)
        state, diagnostics = setup(X, y, alpha, config["epsilon"])
        save_npz(output / "states" / f"data_{data_id:02d}.npz", **state)
        distance = float(np.sum(np.abs(state["pi_LN_floor"] - state["pi_FULL_OPT"])) / 2)
        for row in diagnostics:
            rows.append(dict(data_id=data_id, **row, probability_TV_LN_FULL=distance))
    write_rows(output / "score_diagnostics.csv", rows)
    save(output / "input_hashes.json", input_hashes)
    files = {p.relative_to(output).as_posix(): digest(p)
             for p in output.rglob("*") if p.is_file()}
    save(output / "seal.json", dict(
        version=config["version"], source_directory=str(HERE), sources=sources, files=files,
        original_input_hashes=input_hashes, formal_draws_executed=0,
        created_at=time.time(), comment="All 40 data sets retained without score-based selection"))
    verify_prepared(output, check_live=True)
    print(json.dumps(dict(prepared=True, datasets=len(config["data_ids"]),
                          diagnostic_rows=len(rows), formal_draws_executed=0), indent=2), flush=True)


def run(prepared, output, predecessor, pilot, workers):
    prepared, output = Path(prepared).resolve(), Path(output).resolve()
    ready, reason = predecessor_ready(predecessor)
    if not ready:
        raise ValueError("Predecessor release gate closed: " + reason)
    seal = verify_prepared(prepared)
    config = read(prepared / "protocol.json")
    if config["scope"] != "formal_reused_inputs_ablation":
        raise ValueError("Only the frozen formal protocol can be released")
    acceptance = read(pilot)
    if not acceptance.get("passed") or acceptance.get("sources") != seal["sources"]:
        raise ValueError("Pilot not passed for these exact frozen sources")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / "run.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    started = time.perf_counter()
    try:
        identity = digest(prepared / "seal.json")
        execution_path = output / "execution.json"
        if execution_path.exists():
            if read(execution_path).get("identity") != identity:
                raise ValueError("Output belongs to another preparation")
            if read(execution_path).get("completed"):
                print("Already completed; no trajectories executed", flush=True)
                return
        save(execution_path, dict(completed=False, identity=identity, pid=os.getpid()))
        save(output / "protocol.json", config)
        save(output / "pilot_acceptance.json", acceptance)
        save(output / "release_gate.json", dict(
            passed=True, predecessor=str(Path(predecessor).resolve()),
            files={name: digest(Path(predecessor) / name) for name in
                   ("protocol.json", "status.json", "results.json", "support_gate.json",
                    "independent_validation.json", "RESULTS.md")}))
        shutil.copy2(prepared / "seal.json", output / "preparation_seal.json")
        total = len(config["data_ids"]) * len(config["budgets"])
        save(output / "status.json", dict(phase="formal_draws", completed=False, pid=os.getpid(),
                                         tasks_done=0, tasks_total=total, started=time.time()))
        failures = 0
        with ProcessPoolExecutor(max_workers=workers) as pool:
            tasks = [pool.submit(execute_task, str(prepared), str(output), did, budget,
                                 config, identity)
                     for did in config["data_ids"] for budget in config["budgets"]]
            for count, future in enumerate(as_completed(tasks), 1):
                result = future.result()
                failures += result["failures"]
                save(output / "status.json", dict(
                    phase="formal_draws", completed=False, pid=os.getpid(),
                    tasks_done=count, tasks_total=total, failures=failures,
                    elapsed=time.perf_counter() - started))
                print("TASK", count, total, result["data_id"], result["budget"],
                      "failures", result["failures"], flush=True)
        verify_prepared(prepared)
        save(output / "status.json", dict(phase="independent_analysis", completed=False,
                                         tasks_done=total, tasks_total=total, pid=os.getpid()))
        from analyze import analyze
        validation = analyze(prepared, output)
        if not validation["passed"]:
            raise ValueError("Independent analysis found failures; all records retained")
        save(execution_path, dict(completed=True, identity=identity, pid=os.getpid(),
                                 rows=validation["rows"], tasks=total,
                                 seconds=time.perf_counter() - started))
        save(output / "status.json", dict(phase="completed", completed=True,
                                         tasks_done=total, tasks_total=total,
                                         rows=validation["rows"], elapsed=time.perf_counter() - started))
        print("COMPLETED", json.dumps(validation, ensure_ascii=False), flush=True)
    except BaseException as error:
        save(output / "status.json", dict(phase="failed", completed=False, pid=os.getpid(),
                                         error=type(error).__name__ + ": " + str(error)))
        raise
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--repo", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    launch = sub.add_parser("run")
    launch.add_argument("--prepared", type=Path, required=True)
    launch.add_argument("--output", type=Path, required=True)
    launch.add_argument("--predecessor", type=Path, required=True)
    launch.add_argument("--pilot", type=Path, required=True)
    launch.add_argument("--workers", type=int, default=2, choices=range(1, 5))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.repo, args.output)
    else:
        run(args.prepared, args.output, args.predecessor, args.pilot, args.workers)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
