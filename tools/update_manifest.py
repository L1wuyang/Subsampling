"""Maintain the release file manifest; this is not a numerical experiment runner.

Run from a Git checkout after editing the repository's documentation or evidence.
Only Python's standard library and Git are required.  The released simulation
manifest, scientific source hashes, and pilot gates are checked, never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "MANIFEST.json"
FROZEN = "provenance/frozen_scientific_sources.json"
SIMULATIONS = "simulations/manifest.json"
PILOTS = (
    ("Experiments/experiment3_native_comprehensive_20261024", "outputs/pilot_01"),
    ("Experiments/experiment4_native_comprehensive_20261025", "outputs/pilot_02"),
)


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Git command failed: {detail}")
    return result.stdout


def local_file(relative: str) -> Path:
    """Accept only regular files below ROOT, with no symbolic-link components."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"Invalid repository path: {relative!r}")
    parts = relative.split("/")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in ("", ".", "..") or ":" in part for part in parts):
        raise ValueError(f"Unsafe repository path: {relative!r}")
    candidate = ROOT
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            raise ValueError(f"Symbolic links and junctions are not release files: {relative!r}")
    if not candidate.resolve().is_relative_to(ROOT):
        raise ValueError(f"Repository path escapes the checkout: {relative!r}")
    if not candidate.is_file():
        raise ValueError(f"Missing or non-regular repository file: {relative!r}")
    return candidate


def record(relative: str) -> dict:
    path = local_file(relative)
    before = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in fields):
        raise ValueError(f"File changed while its checksum was being read: {relative!r}")
    return {"sha256": digest, "bytes": after.st_size}


def unchanged_from_head(relative: str) -> bytes:
    current = local_file(relative).read_bytes()
    if current != git("show", f"HEAD:{relative}"):
        raise ValueError(f"Protected manifest differs from HEAD: {relative!r}")
    return current


def require_digest(files: dict, relative: str, digest: str, size: int | None = None) -> None:
    actual = files.get(relative)
    if actual is None:
        raise ValueError(f"Protected file is not included by Git: {relative!r}")
    if actual["sha256"] != digest or (size is not None and actual["bytes"] != size):
        raise ValueError(f"Protected file checksum or length changed: {relative!r}")


def verify_protected(files: dict) -> dict:
    frozen = json.loads(unchanged_from_head(FROZEN))
    if not isinstance(frozen, dict) or not frozen:
        raise ValueError("The frozen scientific source manifest must be a nonempty object")
    for relative, digest in frozen.items():
        require_digest(files, relative, digest)

    gates = {}
    for folder, pilot in PILOTS:
        protocol_name = f"{folder}/formal_protocol.json"
        verification_name = f"{folder}/{pilot}/verification.json"
        sources_name = f"{folder}/{pilot}/frozen_sources.json"
        # These are also frozen above; anchor the gate documents independently
        # so that editing a list cannot silently approve replacement sources.
        protocol = json.loads(unchanged_from_head(protocol_name))
        verification = json.loads(unchanged_from_head(verification_name))
        pilot_sources = json.loads(unchanged_from_head(sources_name))
        if not verification.get("passed"):
            raise ValueError(f"Pilot verification did not pass: {verification_name}")
        require_digest(files, verification_name, protocol["pilot"]["verification_sha256"])
        for relative, digest in pilot_sources.items():
            require_digest(files, f"{folder}/{relative.replace(chr(92), '/')}", digest)
        gates[folder] = len(pilot_sources)

    simulation_manifest = json.loads(unchanged_from_head(SIMULATIONS))
    if simulation_manifest.get("schema") != 1:
        raise ValueError("Unsupported simulation manifest schema")
    protected_simulations = 0
    for experiment in simulation_manifest["experiments"].values():
        members = list(experiment["files"])
        for records in experiment["record_sets"]:
            members.extend(records["parts"])
        for member in members:
            require_digest(files, member["path"], member["sha256"], member["bytes"])
            protected_simulations += 1
    return {
        "frozen_scientific_sources": len(frozen),
        "pilot_sources": gates,
        "simulation_files": protected_simulations,
    }


def rebuild(check: bool) -> dict:
    checkout = Path(os.fsdecode(git("rev-parse", "--show-toplevel")).strip()).resolve()
    if checkout != ROOT:
        raise ValueError("This script must reside in tools/ under the Git repository root")
    manifest_path = local_file(MANIFEST)
    original_bytes = manifest_path.read_bytes()
    original = json.loads(original_bytes)
    if not isinstance(original, dict) or not isinstance(original.get("files"), dict):
        raise ValueError("The existing root manifest must have a files object")

    entries = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    names = sorted({os.fsdecode(item) for item in entries.split(b"\0") if item})
    files = {relative: record(relative) for relative in names if relative != MANIFEST}
    protection = verify_protected(files)
    updated = dict(original)
    updated["files"] = files
    updated["file_count"] = len(files)
    updated["bytes"] = sum(member["bytes"] for member in files.values())
    if check and updated != original:
        prior = original["files"]
        added = sorted(set(files) - set(prior))
        removed = sorted(set(prior) - set(files))
        changed = sorted(name for name in set(files) & set(prior) if files[name] != prior[name])
        raise ValueError(
            "Release manifest is stale: "
            + json.dumps({"added": added, "removed": removed, "changed": changed,
                          "file_count_expected": updated["file_count"],
                          "bytes_expected": updated["bytes"]}, ensure_ascii=False)
        )
    if not check:
        text = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
        if b"\r\n" in original_bytes:
            text = text.replace("\n", "\r\n")
        payload = text.encode("utf-8")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", prefix=".MANIFEST.", suffix=".tmp",
                                             dir=ROOT, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if manifest_path.read_bytes() != original_bytes:
                raise ValueError("Root manifest changed concurrently; no replacement was made")
            os.replace(temporary, manifest_path)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return {"passed": True, "action": "check" if check else "update",
            "files": len(files), "bytes": updated["bytes"], **protection,
            "numerical_trajectories_executed": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Check the existing manifest without changing any files")
    args = parser.parse_args()
    try:
        result = rebuild(args.check)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Manifest maintenance failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
