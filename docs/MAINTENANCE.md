# Repository maintenance

[Repository guide](../README.md) · [Paper result map](PAPER_RESULTS.md) · [Validation](../validation/README.md)

## Sources and evidence

Use the documented root adapters for I–IV and historical V, and current experiment guides for stable V and the Ridge comparisons. Some archived nested commands still refer to the original author workspace.

`provenance/frozen_scientific_sources.json` protects 54 historical scientific files. III/IV pilot records are execution hash gates. Separate reference-module copies may be imported independently even where their bytes are identical. Preserve these files and their bytes.

The `source_snapshot/`, `source_files` and `run_source_hashes` entries in saved evidence describe original runs. Current execution adapters can evolve under a new code release without rewriting those original hashes, snapshots or scientific records. The `v2026.11.02.1` changes concern directory compatibility, postprocessing and optional scheduling; release checks identify them separately.

## Inventories and versions

- `VERSION` identifies the code release. `MANIFEST.json` covers its tracked files and records the separate `review_data_version`.
- `provenance/review_data.json` fixes the historical data version, original URL, archive SHA-256, immutable source commit and all 545 member hashes. A new code release may reuse this descriptor unchanged.
- Installed review data remain ignored by Git and excluded from the core inventory. `evidence/experiment5/MANIFEST.json` covers the historical mix of helpers and installed evidence.
- Preserve scientific data hashes. If a current helper covered by a nested manifest changes, update only that helper's entry. Original evidence inventories are not manifests for the evolving execution adapters.
- Old release receipts belong in `validation/history/`; `validation/current_release.json` records the current code release's actual checks.

## Validate and package

Run relevant tests, then rebuild/check the inventory:

```text
python -B tools/test_latest_rerun_paths.py
python -B tools/test_ridge_standalone.py
python -B tools/test_release_versions.py
python tools/update_manifest.py
python tools/update_manifest.py --check
python run.py verify
python run.py preflight --experiment simulations
git diff --check
```

In a fresh extracted core, verify integrity, install the immutable review-data archive, verify members and rerun the saved-metric checks in the release notes. These checks are distinct from full scientific replication. Record the exact environment and checks performed.

```text
python tools/build_release.py --output ../release-dist-v2026.11.02.1
```

The builder packages the current core and reconstructs the old data archive byte-for-byte from its fixed source commit. `--source-dir /path/to/original-data-checkout` uses a local copy; every member and the final archive must match the descriptor. Build outputs belong outside the tracked checkout.

After local review, pushing a new `VERSION` to `main` runs `.github/workflows/release.yml`. The workflow validates the code and data, publishes the fixed tag and assets, and checks the public data download from a clean extracted core. Monitor its result and compare uploaded checksums before citing it. Never move a published tag or overwrite an existing asset.

中文：科学来源、原始数据、旧运行快照与当前适配器分开管理。代码版本可以更新而沿用旧数据版本。改动后运行对应回归测试和保存结果复核，记录实际验证范围，再发布新 tag；不要用旧版本号覆盖已发布内容。
