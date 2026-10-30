# Experiment V: official data sources and byte-level verification

[中文说明](DATA_SOURCES_CN.md) · [Repository guide](../README.md)

The experimental materials include the simulated inputs, per-repetition metrics and summary tables for Experiments I–IV; see the [simulation data guide](SIMULATION_DATA.md). The [Experiment V evidence guide](../evidence/experiment5/README.md) documents its current empirical summaries, figures and tail diagnostics. Acquire the original real-world data for full Experiment V reruns from the official sources below. Preprocessing fits feature means, standard deviations and the response intercept on the training set; the fixed split is supplied with the code.

## Official sources and frozen versions

| Key | Required final file | Version / bytes |
| --- | --- | ---: |
| `expression` | `sanger1018_brainarray_ensemblgene_rma.txt.gz` | GDSC release-6.0; 141,390,873 |
| `response` | `GDSC2_fitted_dose_response_24Jul22.csv` | GDSC release-8.4; 39,834,719 |
| `year` | `YearPredictionMSD.txt` | UCI dataset 203; 448,576,698 |

Exact GDSC expression download:

```text
https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/release-6.0/sanger1018_brainarray_ensemblgene_rma.txt.gz
```

Exact GDSC2 response download:

```text
https://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/release-8.4/GDSC2_fitted_dose_response_24Jul22.csv
```

Official YearPredictionMSD dataset page and download:

```text
https://archive.ics.uci.edu/dataset/203/yearpredictionmsd
https://archive.ics.uci.edu/static/public/203/yearpredictionmsd.zip
```

The Year download is a **211,011,981-byte ZIP**. Its exact member name is `YearPredictionMSD.txt`; the acquisition command extracts that member to the target directory. The ZIP and extracted TXT have separate checksums. File sizes, SHA-256 values, URLs and target paths are recorded in [provenance/data_sources.json](../provenance/data_sources.json).

These checksums identify the frozen research inputs; they are not provider-signed checksums. The provenance records report that complete official downloads matched the GDSC files on October 16, 2026 and the UCI ZIP on October 17, 2026. HTTPS HEAD checks on October 27, 2026 checked download reachability and headers, rather than repeating full-download hash verification.

```text
expression SHA256
90fe07de1a72fa9f4fdcbdfc0c0bb23c70b1435bac2adad7e99c2f2bb154ca93

response SHA256
9d6dc82b9a072bb00b6139dcd6c4c11de1e047f210382fb726e92ab8dd0eae2a

year TXT SHA256
4b6f8e50235b359e01689ae7fb33ad0f89677e9a15f25f3d6259327a6bb927bb

year ZIP SHA256
06f801af323bb7798e800583acce4ea1ed2697ac12c23f4424aea0a7a3d09e11
```

## Download and check

Run the root `run.py` from the repository directory. The acquisition layer uses the Python standard library.

```text
python run.py data download --dataset gdsc
python run.py data download --dataset year
python run.py data check --dataset all
```

`--dataset all` is the default. The check runs offline and verifies the three final files and the fixed GDSC ID list.

For a different package/data root, use the module interface, which additionally accepts `--root PATH`:

```text
python -m repro1026.data_sources check --dataset all --root PATH
```

Data paths then resolve under `PATH/Data/...`; the GDSC ID list must be at `PATH/provenance/exp5_inputs/gdsc_split.json`. The module defaults to the repository root containing its source.

The three final data paths are:

```text
Data/real_data_20261016/raw/gdsc/expression_release_6.0/sanger1018_brainarray_ensemblgene_rma.txt.gz
Data/real_data_20261016/raw/gdsc/response_release_8.4/GDSC2_fitted_dose_response_24Jul22.csv
Data/real_data_20261016/raw/yearpredictionmsd/yearpredictionmsd/YearPredictionMSD.txt
```

These final files total approximately 600.63 MiB. Automatic Year acquisition also retains the approximately 201.24 MiB official ZIP for verification and extraction. Downloaded data remain in the Git-ignored `Data/` tree.

## Manual download and reuse of existing files

Files downloaded through a browser can be placed unchanged at the paths above and checked with `python run.py data check --dataset all`. Preserve the original bytes: resaving CSV files, converting line endings, recompressing files or rewriting TXT files changes their checksums.

For files stored elsewhere, `check --file` verifies those paths without copying them; `download --file` verifies and imports them to the standard locations. Supported keys are `expression`, `response`, `year` and `year_archive`; repeat `--file` for multiple inputs:

```text
python run.py data check --dataset gdsc --file "expression=D:/data/sanger1018_brainarray_ensemblgene_rma.txt.gz" --file "response=D:/data/GDSC2_fitted_dose_response_24Jul22.csv"

python run.py data download --dataset year --file "year_archive=D:/data/yearpredictionmsd.zip"

python run.py data download --dataset year --file "year=D:/data/YearPredictionMSD.txt"
```

The second command verifies a local official ZIP and extracts the target TXT without downloading it again. The third imports an existing official TXT after verification.

A successful `check` requires all final raw files for the selected datasets. Supplying only `year_archive` does not make a missing TXT count as ready. Commands report JSON and return exit code 0 on success, or 1 otherwise.

## Existing files, interrupted transfers and fixed splits

Existing valid files are checked and skipped. A size or SHA mismatch raises an error and preserves the existing file. Downloading, importing and extraction first write a `.part` file, then publish it only after size and checksum verification. After interruption, inspect and move aside any residual `.part` file before retrying. Downloads use HTTPS with system TLS certificate verification.

Publication uses a same-directory hard link to avoid overwriting an existing destination. NTFS and common local file systems support this operation. On a file system without this support, the command retains the verified `.part` file and reports an error; move it manually to the intended filename, then run `check`. A checksum mismatch may also mean that the provider replaced a file under the same name. Check the source version before changing any manifest.

The small [gdsc_split.json](../provenance/exp5_inputs/gdsc_split.json) records drug ID 1862, the 937 matched cell IDs and their fixed 749/188 training/test order. It contains no expression or response values. Acquisition checks its size, SHA-256 and complete disjoint partition; reruns use the supplied selection and split. Year uses the official order: the first 463,715 rows for training and the following 51,630 for testing.

The acquisition module also exposes `load_manifest()`, `required_files(dataset)`, `check_data(root, dataset)` and `download_data(root, dataset)` for programmatic use.
