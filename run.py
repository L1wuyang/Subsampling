"""Companion experimental materials: verify saved records or run the frozen protocols."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'NUMBA_NUM_THREADS']:
    os.environ[name] = '1'
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
os.environ.setdefault('NUMBA_CACHE_DIR', str(ROOT/'runs/.numba-cache'))
DIRECTORIES = {
    1: 'experiment1_native_comprehensive_20261024',
    2: 'experiment2_native_comprehensive_20261024',
    3: 'experiment3_native_comprehensive_20261024',
    4: 'experiment4_native_comprehensive_20261025',
    5: 'experiment5_native_realdata_20261025',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def numbers(experiment):
    return list(range(1, 6)) if experiment == 'all' else list(range(1, 5)) if experiment == 'simulations' else [int(experiment)]


def new_output(path):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT.is_relative_to(path):
        raise ValueError('Output cannot replace the package or one of its parents')
    for name in ['Experiments', 'Data', 'provenance', 'repro1026', 'docs', 'validation', 'simulations', 'evidence', 'tools']:
        if path.is_relative_to(ROOT/name):
            raise ValueError(f'Output is inside a package input directory: {path}')
    if path.exists():
        raise FileExistsError(f'Choose a new output directory: {path}')
    path.mkdir(parents=True)
    return path


def verify():
    manifest = json.loads((ROOT/'MANIFEST.json').read_text('utf8'))
    for relative, record in manifest['files'].items():
        path = (ROOT/relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or sha(path) != record['sha256']:
            raise ValueError(f'Package checksum mismatch: {relative}')
    frozen = json.loads((ROOT/'provenance/frozen_scientific_sources.json').read_text('utf8'))
    for relative, digest in frozen.items():
        if sha(ROOT/relative) != digest:
            raise ValueError(f'Frozen scientific source changed: {relative}')
    return dict(passed=True, package_scope='core', files=len(manifest['files']), frozen_scientific_sources=len(frozen),
                review_data_descriptor='provenance/review_data.json',
                raw_real_data_bundled=manifest.get('raw_real_data_bundled', False),
                simulation_inputs_bundled=manifest.get('simulation_inputs_bundled', False),
                formal_results_bundled=manifest.get('historical_formal_results_bundled', False))


def check_gate(number):
    folder = ROOT/'Experiments'/DIRECTORIES[number]
    config = json.loads((folder/'formal_protocol.json').read_text('utf8'))
    pilot = folder/('outputs/pilot_01' if number == 3 else config['pilot']['directory'])
    verification = json.loads((pilot/'verification.json').read_text('utf8'))
    if not verification.get('passed') or sha(pilot/'verification.json') != config['pilot']['verification_sha256']:
        raise ValueError(f'Pilot acceptance gate failed: experiment {number}')
    files = json.loads((pilot/'frozen_sources.json').read_text('utf8'))
    for relative, digest in files.items():
        path = folder/relative.replace('\\', '/')
        if sha(path) != digest:
            raise ValueError(f'Pilot scientific hash mismatch: {path}')
    return dict(passed=True, source_files=len(files), historical_acceptance_only=True)


def preflight(selected, require_data=True):
    result = dict(package=verify(), experiments=selected, gates={}, dependencies={})
    for package in ['numpy', 'scipy', 'pandas', 'numba', 'matplotlib', 'mpmath']:
        try:
            result['dependencies'][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            raise RuntimeError(f'Missing {package}; run python -m pip install -r requirements-lock.txt')
    for number in selected:
        if number in [3, 4]:
            result['gates'][str(number)] = check_gate(number)
    if 5 in selected and require_data:
        from repro1026.data_sources import check_data
        result['data'] = check_data(ROOT)
        if not result['data']['passed']:
            raise FileNotFoundError('Experiment V needs separately acquired official files. Run python run.py data download --dataset all; see docs/DATA_SOURCES.md.')
    result['passed'] = True
    return result


def call(arguments):
    result = subprocess.run([sys.executable, '-B', *map(str, arguments)], cwd=ROOT, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def experiment_run(number, mode, output, workers):
    if number in [1, 2]:
        args = ['-m', 'repro1026.exp12', '--experiment', number]
    elif number in [3, 4]:
        args = ['-m', 'repro1026.exp34', '--experiment', number]
    else:
        args = ['-m', 'repro1026.exp5']
    call([*args, '--mode', mode, '--output', output, '--workers', workers])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('verify', help='Check the source package and immutable scientific sources; no raw data required')
    p.add_argument('--data', action='store_true', help='Also require/check separately acquired experiment V data')
    p = subs.add_parser('preflight', help='Check dependencies, protocol gates and required files without launching any trajectories')
    p.add_argument('--experiment', choices=['all', 'simulations', '1', '2', '3', '4', '5'], default='all')
    p.add_argument('--no-data', action='store_true', help='Inspect the code and protocols before acquiring V data')
    p = subs.add_parser('data', help='Download/check the exact official experiment V files')
    p.add_argument('action', choices=['download', 'check'])
    p.add_argument('--dataset', choices=['all', 'gdsc', 'year'], default='all')
    p.add_argument('--file', action='append', default=[], help='Reuse a local file: expression=PATH, response=PATH, year=PATH or year_archive=PATH')
    p.add_argument('--timeout', type=float, default=90.)
    p = subs.add_parser('review-data', help='Download, install or verify the separate paper review-data package')
    p.add_argument('action', choices=['download', 'install', 'verify'])
    p.add_argument('--file', type=Path, help='Local review-data ZIP; required for install')
    p.add_argument('--timeout', type=float, default=90.)
    for command in ['smoke', 'formal']:
        p = subs.add_parser(command, help='Run actual algorithms into a new directory; V needs official data')
        p.add_argument('--experiment', choices=['all', 'simulations', '1', '2', '3', '4', '5'], default='all')
        p.add_argument('--output', type=Path, required=True)
        p.add_argument('--workers', type=int, default=2)
    p = subs.add_parser('analyze', help='Analyze your newly generated complete run directory')
    p.add_argument('--experiment', choices=['all', 'simulations', '1', '2', '3', '4', '5'], default='all')
    p.add_argument('--results', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = subs.add_parser('simulation-data', help='Verify or summarize the released I-IV inputs and repetition metrics')
    p.add_argument('action', choices=['verify', 'summarize'])
    p.add_argument('--experiment', choices=['all', '1', '2', '3', '4'], default='all')
    p.add_argument('--output', type=Path, help='New directory; required for summarize')
    p = subs.add_parser('iv-diagnostics', help='Diagnose your new IV outputs, without replacing their means')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if getattr(args, 'workers', 1) < 1:
        parser.error('--workers must be positive')
    if args.command == 'verify':
        result = verify()
        if args.data:
            from repro1026.data_sources import check_data
            result['data'] = check_data(ROOT)
            result['passed'] = result['data']['passed']
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        if not result['passed']:
            raise SystemExit(1)
    elif args.command == 'preflight':
        print(json.dumps(preflight(numbers(args.experiment), not args.no_data), indent=2), flush=True)
    elif args.command == 'data':
        arguments = ['-m', 'repro1026.data_sources', args.action, '--dataset', args.dataset]
        for value in args.file:
            arguments += ['--file', value]
        if args.action == 'download':
            arguments += ['--timeout', args.timeout]
        call(arguments)
    elif args.command == 'review-data':
        arguments = ['-m', 'repro1026.review_data', args.action]
        if args.file is not None:
            arguments += ['--file', args.file.resolve()]
        if args.action == 'download':
            arguments += ['--timeout', args.timeout]
        call(arguments)
    elif args.command in ['smoke', 'formal']:
        selected = numbers(args.experiment)
        checked = preflight(selected)
        output = new_output(args.output)
        write(output/'preflight.json', checked)
        write(output/'run_manifest.json', dict(mode=args.command, selected_experiments=selected,
              completed=False, paper_results=args.command=='formal', source_package_sha256=sha(ROOT/'MANIFEST.json')))
        for number in selected:
            experiment_run(number, args.command, output/f'exp{number}', args.workers)
        write(output/'run_manifest.json', dict(mode=args.command, selected_experiments=selected,
              completed=True, paper_results=args.command=='formal', source_package_sha256=sha(ROOT/'MANIFEST.json')))
    elif args.command == 'analyze':
        selected = numbers(args.experiment)
        verify()
        results = args.results.expanduser().resolve()
        if not results.is_dir():
            raise FileNotFoundError(results)
        output = new_output(args.output)
        for number in selected:
            call(['-m', 'repro1026.reporting', '--experiment', number, '--results', results,
                  '--output', output/f'exp{number}'])
        write(output/'analysis_manifest.json', dict(completed=True, results=str(results),
              selected_experiments=selected, source_results_modified=False))
    elif args.command == 'simulation-data':
        if args.action == 'summarize' and args.output is None:
            parser.error('simulation-data summarize requires --output')
        arguments = ['-m', 'repro1026.simulation_data', args.action, '--experiment', args.experiment]
        if args.output is not None:
            arguments += ['--output', args.output.resolve()]
        call(arguments)
    elif args.command == 'iv-diagnostics':
        call(['-m', 'repro1026.iv_diagnostics', '--input', args.input.resolve(), '--output', args.output.resolve()])


if __name__ == '__main__':
    main()
