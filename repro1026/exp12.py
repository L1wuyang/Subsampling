"""Portable I/II execution adapter around the unchanged scientific sources.

python -m repro1026.exp12 --experiment 1 --output runs/I --mode formal
python -m repro1026.exp12 --experiment 2 --output runs/II-smoke --mode smoke
python -m repro1026.exp12 --experiment 1 --action analyze --source runs/I --output runs/I-analysis

Output is always a new directory. Historical protection manifests and their
unrelated workspace dependencies are replaced by explicit source hashes and
input manifests; the original run_arm, setup, tangents and batch code is used.
"""
from __future__ import annotations

import os
for _key in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[_key] = '1'

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys
import time

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    1: {
        'native.py': '16c0edbf6f96d78246b39e9d4bae87711fb8c8937ecaba9b549df5720f5f39e5',
        'run_formal.py': '0287b64e028edb3b972eeb45e913885acc90dde6206324603c53ecb1941793a3',
        'formal_protocol.json': 'ce7db8676d60470625c5c1913a1e754b0c16ef6be98cce9e8bea727f464844e9',
    },
    2: {
        'native.py': 'b746470ca2b2f2b9e66183bc8467058568be1af67e58dd66921a8f9467df1555',
        'integrator_reference.py': '16c0edbf6f96d78246b39e9d4bae87711fb8c8937ecaba9b549df5720f5f39e5',
        'common.py': '089ef00c5ad072d95f241f11de38a01c2bdb7ca014dcf20e796b20e753ad9b84',
        'run_formal.py': 'b7f4f8a08fca0d9aa8c8ad1463148a0ad07404f2a2cfb17bd249cdf8c24c069d',
        'formal_protocol.json': '6f45f4e4479f476bfefd22562f2ebbc23ba7eb8a62c33bcffacc6b30ef149e13',
    },
}


def _digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def _save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False)+'\n', encoding='utf8')


def _source_directory(experiment, source_root):
    if experiment not in (1, 2):
        raise ValueError('experiment must be 1 or 2')
    return Path(source_root)/'Experiments'/f'experiment{experiment}_native_comprehensive_20261024'


def _validate_sources(experiment, source_root):
    directory = _source_directory(experiment, source_root)
    hashes = {}
    for name, expected in EXPECTED[experiment].items():
        actual = _digest(directory/name)
        if actual != expected:
            raise ValueError(f'Frozen scientific source differs: {directory/name}')
        hashes[name] = actual
    hashes['analyze.py'] = _digest(directory/'analyze.py')
    return directory, hashes


def _new_output(path, source_root):
    output = Path(path).expanduser().resolve()
    for base in {PACKAGE_ROOT, Path(source_root).resolve()}:
        for protected in ('Experiments', 'Data', 'Paper_Versions'):
            if output.is_relative_to(base/protected):
                raise ValueError(f'Output must be outside frozen {base/protected}')
    output.mkdir(parents=True, exist_ok=False)
    return output


@contextmanager
def _aliases(mapping):
    missing = object()
    previous = {name: sys.modules.get(name, missing) for name in mapping}
    try:
        sys.modules.update(mapping)
        yield
    finally:
        for name, old in previous.items():
            if old is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


@lru_cache(maxsize=8)
def _runtime(experiment, source_root, run_root):
    """Load legacy modules under isolated names, then redirect their IO globals."""
    source, _ = _validate_sources(experiment, source_root)
    run_root = Path(run_root)
    formal = run_root/'outputs/formal_01'
    prefix = f'_repro1026_exp{experiment}_{len(sys.modules)}'
    alias = {}
    if experiment == 2:
        integrator = _module(prefix+'_integrator', source/'integrator_reference.py')
        alias['integrator_reference'] = integrator
    with _aliases(alias):
        native = _module(prefix+'_native', source/'native.py')
    alias['native'] = native
    if experiment == 2:
        with _aliases(alias):
            common = _module(prefix+'_common', source/'common.py')
        common.HERE, common.OUT, common.ROOT = run_root, formal, run_root
        alias['common'] = common
    with _aliases(alias):
        driver = _module(prefix+'_driver', source/'run_formal.py')
    driver.HERE, driver.OUT, driver.ROOT = run_root, formal, run_root
    return native, driver, alias, source


@contextmanager
def _spectral_guard(native):
    """Use the original production guard, restoring global libraries afterward."""
    blocked = [
        (native.np.linalg, ('eig', 'eigh', 'eigvals', 'eigvalsh', 'svd', 'matrix_power')),
        (native.sla, ('eig', 'eigh', 'eigvals', 'eigvalsh', 'svd', 'svdvals', 'expm', 'funm', 'fractional_matrix_power')),
    ]
    saved = [(obj, name, getattr(obj, name)) for obj, names in blocked for name in names]
    try:
        native.guard()
        yield
    finally:
        for obj, name, original in saved:
            setattr(obj, name, original)


def _worker(experiment, source_root, run_root, did, config):
    native, driver, _, _ = _runtime(experiment, source_root, run_root)
    with _spectral_guard(native):
        return [driver.run_arm(did, arm, config) for arm in config['arms'] if did in arm['data_ids']]


def _configuration(experiment, source, mode):
    original = json.loads((source/'formal_protocol.json').read_text('utf8'))
    config = deepcopy(original)
    if mode == 'smoke':
        config['name'] = f'SMOKE ONLY: Experiment {experiment} portable execution check'
        config['n'], config['p'] = (8, 24) if experiment == 1 else (64, 8)
        config['data_ids'] = [1, 2]
        config['workers'] = 1
        for arm in config['arms']:
            arm['data_ids'] = [1, 2]
            arm['budgets'] = [30, 150, 600]
            arm['repetitions'] = 1 if arm['tag'] == 'zero_response' else 2
        config['replication_counts'] = dict(main=288, sensitivity=2304, zero_response=144)
        config['smoke_only'] = True
        config['smoke_changes'] = dict(dimensions=[config['n'], config['p']], datasets=2,
            budgets=[30, 150, 600], repetitions=2, zero_repetitions=1,
            warning='Reduced engineering check. No smoke number is a paper result or confirmatory inference.')
    return original, config


def _generate_inputs(experiment, config, run_root):
    import numpy as np
    data = run_root/'data'
    data.mkdir(exist_ok=False)
    manifest = []
    for did in config['data_ids']:
        n, p = config['n'], config['p']
        rng = np.random.default_rng(np.random.SeedSequence([config['data_seed'], did]))
        if experiment == 1:
            G, z, beta = rng.normal(size=(n, p)), rng.normal(size=p), rng.normal(size=p)
            beta /= np.linalg.norm(beta)
            arrays = dict(G=G, scale_z=z, beta0=beta, standard_noise=rng.normal(size=n))
        else:
            mask = np.zeros(n, dtype=bool)
            mask[rng.choice(n, int(round(.03*n)), replace=False)] = True
            arrays = dict(G=rng.normal(size=(n, p)), spike_noise=rng.normal(size=(n, p)),
                spike_mask=mask, beta_direction=rng.normal(size=p), standard_noise=rng.normal(size=n))
        target = data/f'data_{did:02d}.npz'
        np.savez_compressed(target, **arrays)
        manifest.append(dict(data_id=did, sha256=_digest(target)))
    return manifest


def _aggregate(run_root, config):
    import pandas as pd
    out = run_root/'outputs/formal_01'
    for name in ('results', 'full_reference', 'local_trace', 'costs'):
        groups = [[], []]
        for did in config['data_ids']:
            for arm in config['arms']:
                if did in arm['data_ids']:
                    folder = out/f'data_{did:02d}'/arm['tag']
                    if not (folder/'completion.json').is_file():
                        raise RuntimeError(f'Unfinished arm: {folder}')
                    groups[int(arm['tag'] != 'main')].append(pd.read_csv(folder/(name+'.csv')))
        for prefix, frames in zip(('', 'sensitivity_'), groups):
            pd.concat(frames, ignore_index=True).to_csv(out/(prefix+name+'.csv'), index=False)


def _analyze(experiment, source_root, run_root):
    # All analyze writes, including matplotlib's cache, stay within the new run.
    os.environ['MPLCONFIGDIR'] = str(Path(run_root)/'outputs/matplotlib_cache')
    _, driver, alias, source = _runtime(experiment, str(source_root), str(run_root))
    with _aliases({**alias, 'run_formal': driver}):
        analysis = _module(f'_repro1026_analysis_{experiment}_{len(sys.modules)}', source/'analyze.py')
    formal = Path(run_root)/'outputs/formal_01'
    with (formal/'analysis.log').open('w', encoding='utf8') as log, redirect_stdout(log):
        analysis.main()
    config = json.loads((formal/'protocol.json').read_text('utf8'))
    summary_path = formal/'summary.json'
    summary = json.loads(summary_path.read_text('utf8'))
    summary['reproduction_mode'] = 'smoke' if config.get('smoke_only') else 'formal'
    summary['paper_results'] = not config.get('smoke_only', False)
    _save(summary_path, summary)
    if config.get('smoke_only'):
        path = formal/'index.html'
        text = path.read_text('utf8')
        text = text.replace('40 independent data sets; 13 budgets; 40 paired sketches.',
                            'SMOKE ONLY: 2 data sets; 3 budgets; 2 paired sketches.')
        text = text.replace('40 independent spiked-row data sets; 13 budgets; 40 paired sketches.',
                            'SMOKE ONLY: 2 spiked-row data sets; 3 budgets; 2 paired sketches.')
        text = text.replace('<h1>', '<p><strong>SMOKE: reduced engineering check, not paper results.</strong></p><h1>', 1)
        path.write_text(text, 'utf8')
    print('ANALYSIS_COMPLETE', experiment, summary['reproduction_mode'],
          summary['main_rows'], summary['robustness_rows'], summary['zero_rows'], flush=True)


def run(experiment, output, mode='formal', workers=1, analyze=True, source_root=PACKAGE_ROOT):
    """Generate seeded inputs and complete the unchanged I/II assigned arms."""
    if mode not in ('smoke', 'formal') or workers < 1:
        raise ValueError('mode must be smoke/formal and workers must be positive')
    source_root = Path(source_root).resolve()
    source, hashes = _validate_sources(experiment, source_root)
    original, config = _configuration(experiment, source, mode)
    run_root = _new_output(output, source_root)
    formal = run_root/'outputs/formal_01'
    formal.mkdir(parents=True)
    snapshot = formal/'source_snapshot'
    snapshot.mkdir()
    for name in hashes:
        shutil.copy2(source/name, snapshot/name)
    _save(formal/'frozen_sources.json', hashes)
    _save(formal/'protocol.json', config)
    _save(formal/'protocol_original.json', original)
    _save(run_root/'adapter_provenance.json', dict(experiment=experiment, mode=mode,
        scientific_sources=hashes, adapter_sha256=_digest(__file__),
        original_production_main_not_called=True,
        source_guard='Explicit frozen source hashes; no project-history protection dependency.',
        actual_workers=workers, formal_protocol_changed=(mode=='smoke'),
        inference='formal reproduction' if mode=='formal' else 'SMOKE engineering check only'))
    start = time.perf_counter()
    try:
        manifest = _generate_inputs(experiment, config, run_root)
        _save(formal/'data_manifest.json', manifest)
        completions = []
        args = (experiment, str(source_root), str(run_root))
        if workers == 1:
            for did in config['data_ids']:
                completions.extend(_worker(*args, did, config))
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                jobs = [pool.submit(_worker, *args, did, config) for did in config['data_ids']]
                for job in as_completed(jobs):
                    completions.extend(job.result())
        _aggregate(run_root, config)
        if _validate_sources(experiment, source_root)[1] != hashes:
            raise RuntimeError('Scientific sources changed during execution')
        _save(formal/'execution.json', dict(completed=True, seconds=time.perf_counter()-start,
            completions=completions, frozen_sources_unchanged=True, spectral_guard_active=True,
            actual_workers=workers, portable_adapter=True, mode=mode))
        import numpy as np
        import scipy
        import pandas as pd
        _save(run_root/'environment.json', dict(python=sys.version, platform=platform.platform(),
            numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__,
            numerical_threads={k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')}))
        if analyze:
            _analyze(experiment, source_root, run_root)
        _save(run_root/'completion.json', dict(completed=True, experiment=experiment, mode=mode,
            rows=sum(x['rows'] for x in completions), seconds=time.perf_counter()-start,
            analyzed=analyze, output=str(run_root)))
    except BaseException as error:
        _save(run_root/'adapter_failure.json', dict(completed=False, type=type(error).__name__,
            message=str(error), seconds=time.perf_counter()-start, partial_outputs_retained=True))
        raise
    return run_root


def analyze_saved(experiment, source, output, source_root=PACKAGE_ROOT):
    """Analyze saved I/II CSVs in a new directory without running any trajectory.

    source is an experiment/run root containing data/ and outputs/formal_01/.
    Only required inputs, aggregate CSVs and bound-history JSONs are copied.
    Frozen source archives are never analysis output destinations.
    """
    source = Path(source).resolve()
    origin = source/'outputs/formal_01'
    source_root = Path(source_root).resolve()
    _validate_sources(experiment, source_root)
    config = json.loads((origin/'protocol.json').read_text('utf8'))
    if not json.loads((origin/'execution.json').read_text('utf8')).get('completed'):
        raise ValueError('Saved execution is not complete')
    run_root = _new_output(output, source_root)
    formal = run_root/'outputs/formal_01'
    formal.mkdir(parents=True)
    (run_root/'data').mkdir()
    for name in ('protocol.json', 'execution.json', 'results.csv', 'sensitivity_results.csv',
                 'full_reference.csv', 'local_trace.csv'):
        shutil.copy2(origin/name, formal/name)
    for did in config['data_ids']:
        shutil.copy2(source/'data'/f'data_{did:02d}.npz', run_root/'data'/f'data_{did:02d}.npz')
        folder = formal/f'data_{did:02d}/main'
        folder.mkdir(parents=True)
        shutil.copy2(origin/f'data_{did:02d}/main/bound_history.json', folder/'bound_history.json')
    _save(run_root/'analysis_source.json', dict(source=str(source), experiment=experiment,
        trajectories_executed=0, copied_aggregate_hashes={name:_digest(formal/name) for name in
            ('results.csv','sensitivity_results.csv','full_reference.csv','local_trace.csv')}))
    _analyze(experiment, source_root, run_root)
    _save(run_root/'completion.json', dict(completed=True, experiment=experiment,
        action='analyze saved records', trajectories_executed=0))
    return run_root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', required=True, type=int, choices=(1, 2))
    parser.add_argument('--output', required=True, type=Path, help='New directory; existing paths are refused')
    parser.add_argument('--action', choices=('run','analyze'), default='run')
    parser.add_argument('--mode', choices=('smoke','formal'), default='formal')
    parser.add_argument('--workers', type=int, default=1, help='Ordinary dataset worker processes; numerical kernels use one thread')
    parser.add_argument('--no-analyze', action='store_true', help='Generate native outputs only; analyze later')
    parser.add_argument('--source', type=Path, help='Saved experiment/run root for --action analyze')
    parser.add_argument('--source-root', type=Path, default=PACKAGE_ROOT,
                        help='Root containing unchanged Experiments/ sources; default is this delivery root')
    args = parser.parse_args(argv)
    if args.action == 'analyze':
        if args.source is None:
            parser.error('--source is required for --action analyze')
        result = analyze_saved(args.experiment, args.source, args.output, args.source_root)
    else:
        if args.source is not None:
            parser.error('--source is only used with --action analyze')
        result = run(args.experiment, args.output, args.mode, args.workers, not args.no_analyze, args.source_root)
    print(json.dumps(dict(completed=True, output=str(result)), ensure_ascii=False))


if __name__ == '__main__':
    main()
