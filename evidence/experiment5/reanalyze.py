"""Verify and reanalyze the saved Experiment V metrics without fitting models."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import subprocess
import sys
import tarfile
import tempfile


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
INPUT_DIRECTORIES = ("Experiments", "Data", "provenance", "repro1026", "docs",
                     "validation", "simulations", "evidence", "tools")
FORMAL = Path("Experiments/experiment5_native_realdata_20261025/outputs/formal_01")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_archive():
    manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf8"))
    missing = [name for name in manifest['files'] if not (HERE / name).is_file()]
    if missing:
        raise FileNotFoundError('Review data are not installed. Run python run.py review-data download, '
                                'or python run.py review-data install --file PATH.zip before checking saved results.')
    for name, item in manifest["files"].items():
        path = HERE / name
        data = path.read_bytes()
        if len(data) != item["bytes"] or digest(data) != item["sha256"]:
            raise ValueError(f"Evidence file checksum mismatch: {name}")
    expected = manifest["archive_members"]
    payloads = {}
    with tarfile.open(HERE / "saved_records.tar.gz", "r:gz") as archive:
        for member in archive:
            name = member.name
            path = PurePosixPath(name)
            if (not member.isfile() or path.is_absolute() or ".." in path.parts
                    or "\\" in name or name in payloads or name not in expected):
                raise ValueError(f"Invalid archive member: {name}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"Unreadable archive member: {name}")
            data = source.read()
            item = expected[name]
            if (len(data) != item["bytes"] or member.size != item["bytes"]
                    or digest(data) != item["sha256"]):
                raise ValueError(f"Archive member checksum mismatch: {name}")
            payloads[name] = data
    if set(payloads) != set(expected):
        raise ValueError("The saved-record archive has missing members")
    historical = json.loads((HERE / "reference/inference_revision.json").read_text(encoding="utf8"))
    for name, expected_digest in historical["input_hashes"].items():
        if name not in payloads or digest(payloads[name]) != expected_digest:
            raise ValueError(f"Historical analysis input mismatch: {name}")
    return payloads, historical


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf8"))))


def compare_reference(output, historical):
    reference = csv_rows((HERE / "reference/paired_comparisons_two_sided.csv").read_bytes())
    observed = csv_rows((output / "paired_comparisons_two_sided.csv").read_bytes())
    keys = ("dataset", "budget", "method", "comparison")
    key = lambda row: tuple(row[column] for column in keys)
    ref_index = {key(row): row for row in reference}
    obs_index = {key(row): row for row in observed}
    if len(reference) != 36 or len(observed) != 36 or set(ref_index) != set(obs_index):
        raise ValueError("The paired-comparison family differs from the reference")
    maxima = {}
    for identity, ref in ref_index.items():
        row = obs_index[identity]
        if set(row) != set(ref):
            raise ValueError("The paired-comparison columns differ from the reference")
        for column in ref:
            if column in keys or column in ("n", "supports_OPT_lower"):
                if row[column] != ref[column]:
                    raise ValueError(f"Reference mismatch at {identity}: {column}")
            else:
                actual, expected = float(row[column]), float(ref[column])
                if not (math.isfinite(actual) and math.isfinite(expected)
                        and math.isclose(actual, expected, rel_tol=2e-11, abs_tol=0.0)):
                    raise ValueError(f"Numeric reference mismatch at {identity}: {column}")
                maxima[column] = max(maxima.get(column, 0.0), abs(actual - expected))
    revision = json.loads((output / "inference_revision.json").read_text(encoding="utf8"))
    for field in ("input_hashes", "draw_csv_files", "saved_records", "comparisons",
                  "supports_OPT_lower", "inference", "protocol_note", "intervals"):
        if revision[field] != historical[field]:
            raise ValueError(f"Historical report mismatch: {field}")
    return maxima


def summarize_metrics(payloads, output):
    files = sorted(name for name in payloads
                   if name.startswith(FORMAL.as_posix() + "/draws/") and name.endswith(".csv"))
    rows = [row for name in files for row in csv_rows(payloads[name])]
    if len(files) != 530 or len(rows) != 12720:
        raise ValueError("Expected 530 saved draw files and 12,720 metric records")
    keys = [(r["dataset"], r["budget"], r["rep"], r["method"], r["rule"]) for r in rows]
    if len(set(keys)) != len(rows) or any(r["status"] != "complete" for r in rows):
        raise ValueError("Saved records contain duplicate keys or incomplete draws")
    if any(r["step_bound_observed"].lower() != "true" for r in rows):
        raise ValueError("A saved draw failed its observed step-bound check")
    groups = {}
    for row in rows:
        group = (row["dataset"], int(row["budget"]), row["method"], row["rule"])
        groups.setdefault(group, []).append(float(row["relative_coefficient_error"]))
    summary = []
    for group, values in sorted(groups.items()):
        expected_reps = {"gdsc": 30, "year": 50}[group[0]]
        if len(values) != expected_reps or not all(math.isfinite(v) for v in values):
            raise ValueError(f"Unexpected saved repetitions: {group}")
        summary.append(dict(zip(("dataset", "budget", "method", "rule"), group),
                            n=len(values), mean_relative_coefficient_error=statistics.mean(values),
                            se_relative_coefficient_error=statistics.stdev(values) / math.sqrt(len(values))))
    cells = sorted({group[:3] for group in groups})
    opt_smallest = sum(statistics.mean(groups[cell + ("OPT",)])
                       < min(statistics.mean(groups[cell + (rule,)]) for rule in ("UNI", "NORM", "LEV"))
                       for cell in cells)
    if len(cells) != 78 or opt_smallest != 78:
        raise ValueError("The saved means do not match the reported 78-cell comparison")
    with (output / "mean_coefficient_errors.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    return dict(draw_csv_files=len(files), saved_records=len(rows),
                method_budget_cells=len(cells), opt_smallest_mean_cells=opt_smallest,
                observed_step_bound_checks_passed=len(rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Verify the evidence checksums only")
    parser.add_argument("--output", type=Path, help="New directory for a saved-metric reanalysis")
    args = parser.parse_args()
    if args.verify and args.output is not None:
        parser.error("Use --verify or --output, not both")
    if not args.verify and args.output is None:
        parser.error("Provide --verify or --output NEW_DIRECTORY")
    payloads, historical = verify_archive()
    if args.verify:
        print(json.dumps(dict(verified=True, archive_members=len(payloads),
                              historical_inputs=len(historical["input_hashes"])), indent=2))
        return
    output = args.output.expanduser().resolve()
    if (output.exists() or REPOSITORY.is_relative_to(output)
            or any(output.is_relative_to(REPOSITORY / name) for name in INPUT_DIRECTORIES)):
        raise ValueError("Use a new output directory outside the repository input directories")
    with tempfile.TemporaryDirectory(prefix="subsampling_v_saved_") as folder:
        root = Path(folder).resolve()
        for name, data in payloads.items():
            target = (root / name).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Archive path escapes the extraction directory: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        subprocess.run([sys.executable, "-B", str(HERE / "reference/reanalyze_saved_v.py"),
                        "--project-root", str(root), "--output", str(output)], check=True)
    maxima = compare_reference(output, historical)
    report = summarize_metrics(payloads, output)
    report.update(reference_comparisons_matched=36,
                  maximum_absolute_differences_by_column=maxima,
                  maximum_two_sided_holm_p=historical["max_two_sided_holm_p"],
                  no_estimator_execution=True, no_random_draws_generated=True,
                  reference_files_preserved=True)
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
