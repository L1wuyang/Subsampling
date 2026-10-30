"""Rebuild the frozen Year/Landweber input, target, influences and probabilities.

This regenerates the historical protocol; it does not select new parameters.
Use a new output directory. Raw Year TXT or ZIP is supplied explicitly.
"""
import argparse
import os
for key in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMBA_NUM_THREADS"]:
    os.environ[key] = "1"
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import time
import zipfile

HERE = Path(__file__).resolve().parent
RAW_SHA256 = "4b6f8e50235b359e01689ae7fb33ad0f89677e9a15f25f3d6259327a6bb927bb"
RECORDS_SHA256 = "e1355e6de8ba6103bc1e72460e915cb1d6fa98fe3b9154ceae1f006417a63d2a"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_raw(path, pd):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            with archive.open("YearPredictionMSD.txt") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != RAW_SHA256:
                raise ValueError("Raw Year text SHA256 mismatch")
            with archive.open("YearPredictionMSD.txt") as stream:
                return pd.read_csv(stream, header=None).to_numpy(dtype=float)
    if sha(path) != RAW_SHA256:
        raise ValueError("Raw Year text SHA256 mismatch")
    return pd.read_csv(path, header=None).to_numpy(dtype=float)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-year", type=Path, required=True, help="Hash-matched YearPredictionMSD.txt or its ZIP")
    parser.add_argument("--output", type=Path, required=True, help="New directory for regenerated large arrays")
    parser.add_argument("--repository-root", type=Path, default=HERE.parents[2])
    args = parser.parse_args()
    root, out = args.repository_root.resolve(), args.output.resolve()
    if out.exists():
        raise FileExistsError("Use a new --output directory; existing results are never overwritten")
    source_hashes = read(HERE / "source_hashes.json")
    actual = {name: sha(root / name) for name in source_hashes}
    if actual != source_hashes:
        raise ValueError("Frozen Experiment V source hash mismatch")
    archive_path = root / "evidence/experiment5/saved_records.tar.gz"
    if sha(archive_path) != RECORDS_SHA256:
        raise ValueError("Frozen saved-records archive SHA256 mismatch")
    with tarfile.open(archive_path) as archive:
        members = [m for m in archive if m.name.endswith("targets/year/Landweber/summary.json")]
        if len(members) != 1:
            raise ValueError("Expected one historical Landweber target summary")
        original = json.load(archive.extractfile(members[0]))
    if original != read(HERE / "reference/original_summary.json"):
        raise ValueError("Historical target summary differs from the diagnostic reference")
    # Set all thread controls before importing numerical libraries.
    sys.dont_write_bytecode = True
    os.environ["NUMBA_CACHE_DIR"] = str(out / "numba_cache")
    sys.path.insert(0, str(root / "Experiments/experiment5_native_realdata_20261025/src"))
    import numpy as np
    import pandas as pd
    from native_exp5 import common, data, setup, kernel
    common.guard()
    started = time.perf_counter()
    arr = load_raw(args.raw_year, pd)
    if arr.shape != (515345, 91):
        raise ValueError("Unexpected raw Year dimensions")
    X, E, y, ey, prep = data.normalize(arr[:463715,1:], arr[463715:,1:], arr[:463715,0], arr[463715:,0])
    inputs = out / "inputs/year"
    inputs.mkdir(parents=True)
    for name, value in [("X",X),("E",E),("y",y),("ey",ey)]:
        np.save(inputs / (name + ".npy"), value)
    np.savez_compressed(inputs / "preprocessing.npz", **prep, train=np.arange(463715), test=np.arange(463715,515345))
    del arr, X, E, y, ey
    d = data.load(out / "inputs", "year")
    M, rhs, C, Z, base, rank = setup.basis(d)
    config = read(root / "Experiments/experiment5_native_realdata_20261025/formal_protocol.json")
    L = float(config["step_infinity_factor"] * np.linalg.norm(M, np.inf))
    p = kernel.parameters("Landweber", setup.HISTORIC_C["year"]["Landweber"] * np.trace(M)/len(M), L)
    if p["steps"] != 741388:
        raise ValueError("Unexpected frozen Landweber iteration count")
    folder = out / "targets/year"
    dest = folder / "Landweber"
    dest.mkdir(parents=True)
    np.save(folder / "M.npy", M)
    np.save(folder / "rhs.npy", rhs)
    for rule, pi in base.items():
        np.save(folder / (rule + "_probability.npy"), pi)
    save(dest / "parameters.json", p)
    print("Replaying frozen Landweber target and checkpointed derivatives", flush=True)
    target, J = kernel.influences(M, rhs, p, Z, d["y"], C, dest / "influences.npy",
                                  qbatch=config["adjoint_batch"], block=config["checkpoint_block"], progress=True)
    squared = np.sum(J*J, axis=0)
    scores = np.sqrt(np.maximum(squared, 0))
    pi = setup.optimum(scores)
    sumJ = np.sum(J, axis=1)
    den = float(np.dot(C@target, C@target))
    constants = {rule:max(float(np.sum(squared/prob)-np.dot(sumJ,sumJ)),0)/den
                 for rule,prob in {**base,"OPT":pi}.items()}
    prediction = d["E"] @ target
    summary = dict(c=.001, full=dict(response_test_mse=float(np.mean((prediction-d["ey"])**2)),
        response_test_rmse=float(np.sqrt(np.mean((prediction-d["ey"])**2))), coefficient_norm_squared=den),
        constants=constants, minimum_opt_probability=float(pi.min()),
        maximum_atom_to_probability=float(np.max(np.sum(Z*Z,axis=0)/pi)))
    for name,value in [("target",target),("scores",scores),("OPT_probability",pi)]:
        np.save(dest / (name + ".npy"), value)
    save(dest / "summary.json", summary)
    comparisons = {}
    for group in ["full","constants"]:
        for key,value in summary[group].items():
            reference = original[group][key]
            comparisons[group+"."+key] = dict(restored=value, archived=reference,
                                              relative_difference=abs(value-reference)/abs(reference))
    for key in ["minimum_opt_probability","maximum_atom_to_probability"]:
        value, reference = summary[key], original[key]
        comparisons[key] = dict(restored=value, archived=reference, relative_difference=abs(value-reference)/abs(reference))
    passed = all(c["relative_difference"] < 1e-8 for c in comparisons.values())
    save(out / "original_summary.json", original)
    save(out / "restoration_validation.json", dict(raw_sha256=RAW_SHA256,
        raw_container_sha256=sha(args.raw_year), frozen_source_hashes=actual,
        saved_records_sha256=sha(archive_path), parameters=p, rank=rank, comparisons=comparisons,
        restoration_matches_historical_summaries=passed, restoration_tolerance=1e-8,
        original_arrays_available=False, seconds=time.perf_counter()-started,
        versions=dict(python=sys.version, numpy=np.__version__, pandas=pd.__version__),
        claim="Reconstruction matches frozen historical summaries within tolerance; historical array-byte identity is not established. Scalar interval checks do not certify preprocessing or native floating-point trajectories."))
    save(out / "array_manifest.json", {path.relative_to(out).as_posix():sha(path)
         for top in [out/"inputs",out/"targets"] for path in sorted(top.rglob("*")) if path.is_file()})
    print(json.dumps({"restoration_matches_historical_summaries":passed,
                      "seconds":time.perf_counter()-started}), flush=True)
    if not passed:
        raise ValueError("Restored summaries exceed historical comparison tolerance")


if __name__ == "__main__":
    main()
