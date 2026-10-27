# 1026 experiments — lightweight source release

This package reruns Experiments I–V from their frozen protocols using the actual recurrences and fixed-grid RK4 maps, matching numerical derivatives and sampling probabilities. It includes only necessary sources, seeds, configuration, the frozen GDSC ID split and provenance. Raw data, processed arrays, saved scientific results, paper files and generated figures are not bundled.

See [the detailed Chinese guide](README_CN.md) and [official data sources and exact file checksums](docs/DATA_SOURCES_CN.md). Python 3.11 or 3.12 is recommended; validation used Python 3.12.7.

```text
python -m pip install -r requirements-lock.txt
python run.py verify
python run.py preflight --experiment all --no-data
python run.py smoke --experiment simulations --output runs/smoke --workers 2
python run.py analyze --experiment simulations --results runs/smoke --output runs/smoke_analysis
```

`simulations` selects I–IV, whose inputs are regenerated from fixed seeds. Smoke results are engineering checks, not paper results. To acquire the three exact official real-data files, then run V:

```text
python run.py data download --dataset all
python run.py data check --dataset all
python run.py smoke --experiment 5 --output runs/v_smoke --workers 2
```

You may instead download manually or import existing files using `data download --file KEY=PATH`; see the data guide. The acquisition module uses only the standard library, HTTPS certificate validation, byte counts and SHA-256 checks. Data are stored separately in `Data/`.

To regenerate every formal experiment and its current analysis:

```text
python run.py formal --experiment all --output runs/formal --workers 8
python run.py analyze --experiment all --results runs/formal --output runs/analysis
```

Use `--experiment 1` through `5` for individual experiments. Every output directory must be new. Formal runs can be very expensive: original IV alone has approximately 40.5 billion iterative updates. Removing the stored results does not remove the cost of rerunning them. `analyze` requires your generated results; this package cannot redraw the original full results without running the experiments first.

The portable adapters retain the numerical methods and frozen parameters. III/IV retain four small historical gate JSONs required by their original formal runners; no trajectory or formal result archive is bundled. Source hashes and release hashes are recorded in `provenance/` and `MANIFEST.json`. Use the root entry point, not the nested historical paper/delivery commands.

IV diagnostics/high-precision replay require your new IV directory via `--input`. The separate `stable-v` extension rebuilds all targets and probabilities with support bounds. Its full formal study and every high-precision IV repetition have not been executed in this packaging task. Representative checks are not uniform floating-point certificates. V keeps two-sided paired tests with one joint 36-test Holm family; historical test exploration and oracle probability-design costs remain explicit limitations.

No original paper or scientific result was changed. See `validation/acceptance_summary.json` for the checks actually performed. Validation was on Windows; Linux/macOS were not executed, and cross-platform last-bit equality is not promised. TeX is not needed to run this code. Unzip this release into a GitHub repository; `.gitignore` excludes acquired data and newly generated runs. Keep `.gitattributes` so Git preserves frozen source bytes instead of converting line endings and invalidating their hashes.
