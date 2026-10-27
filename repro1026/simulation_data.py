"""Verify or summarize the published I--IV simulation inputs and saved metrics.

These commands read simulations/manifest.json and CSV.gz metric shards. They do
not execute trajectories or load saved algorithm states. Dataset means use all
records, and the second summary gives every data_id equal weight. A mean with
any NaN or infinity remains undefined instead of using a successful subset.

    python -m repro1026.simulation_data verify --experiment all --output runs/data-check
    python -m repro1026.simulation_data summarize --experiment all --output runs/data-summary
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'simulations/manifest.json'
IDENTITIES = ['record_set', 'direction', 'data_id', 'arm', 'budget', 'method', 'rule']
NONMETRICS = {'data_id', 'budget', 'rep', 'rep_start', 'rep_stop', 'chunk', 'seed'}


def _write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False)+'\n', encoding='utf8')


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _selected(experiment):
    if str(experiment) == 'all':
        return ['1', '2', '3', '4']
    if str(experiment) not in {'1', '2', '3', '4'}:
        raise ValueError('experiment must be all, 1, 2, 3 or 4')
    return [str(experiment)]


def _path(relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError(f'Manifest paths must be relative POSIX paths: {relative!r}')
    part = PurePosixPath(relative)
    if part.is_absolute() or any(q in ('..', '') for q in part.parts) or ':' in relative:
        raise ValueError(f'Manifest path escapes the package: {relative!r}')
    result = (ROOT/relative).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError(f'Manifest path resolves outside the package: {relative}')
    return result


def _fresh_output(output):
    target = Path(output).expanduser().resolve()
    if target == ROOT or ROOT.is_relative_to(target):
        raise ValueError('Output cannot replace this package or one of its parents')
    for name in ('simulations', 'Experiments', 'Data', 'provenance', 'repro1026', 'docs', 'validation'):
        if target.is_relative_to(ROOT/name):
            raise ValueError(f'Output is inside a package input directory: {target}')
    if target.exists():
        raise FileExistsError(f'Choose a new output directory: {target}')
    target.mkdir(parents=True)
    return target


def _manifest():
    if not MANIFEST.is_file():
        raise FileNotFoundError(f'Simulation-data manifest missing: {MANIFEST}')
    value = json.loads(MANIFEST.read_text(encoding='utf8'))
    if value.get('schema') != 1 or not isinstance(value.get('experiments'), dict):
        raise ValueError('Unsupported simulation-data manifest; expected schema=1 and experiments')
    if not {'1', '2', '3', '4'}.issubset(value['experiments']):
        raise ValueError('Simulation manifest must describe experiments 1 through 4')
    return value


def _check_file(record):
    path = _path(record['path'])
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != record['bytes']:
        raise ValueError(f'File length differs from manifest: {record["path"]}')
    actual = _sha(path)
    if actual != record['sha256']:
        raise ValueError(f'SHA-256 differs from manifest: {record["path"]}')
    return path


def verify(experiment='all', output=None):
    """Check every selected input/table and shard hash, schema and row count."""
    manifest = _manifest()
    selected = _selected(experiment)
    checks = {}
    for number in selected:
        description = manifest['experiments'][number]
        if not isinstance(description.get('files'), list) or not isinstance(description.get('record_sets'), list):
            raise ValueError(f'Experiment {number}: files and record_sets must be lists')
        files = []
        for item in description['files']:
            if not isinstance(item.get('kind'), str):
                raise ValueError(f'Experiment {number}: file kind is missing')
            _check_file(item)
            files.append(item['path'])
        sets = []
        seen = set()
        shard_paths = set()
        for records in description['record_sets']:
            name = records.get('id')
            if not isinstance(name, str) or not name or name in seen:
                raise ValueError(f'Experiment {number}: record-set id is missing or repeated')
            seen.add(name)
            columns = records.get('columns')
            if (not isinstance(columns, list) or not columns or
                    any(not isinstance(q, str) or not q for q in columns) or len(set(columns)) != len(columns)):
                raise ValueError(f'Experiment {number}/{name}: invalid declared columns')
            if not isinstance(records.get('parts'), list) or not records['parts']:
                raise ValueError(f'Experiment {number}/{name}: no record shards')
            if 'record_set' in columns:
                raise ValueError('record_set is reserved for the analysis provenance column')
            rows = 0
            for part in records['parts']:
                if part['path'] in shard_paths or not part['path'].endswith('.csv.gz'):
                    raise ValueError(f'Experiment {number}: shard is repeated or is not CSV.gz')
                shard_paths.add(part['path'])
                path = _check_file(part)
                count = 0
                with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as stream:
                    reader = csv.reader(stream)
                    header = next(reader, None)
                    if header != columns:
                        raise ValueError(f'CSV columns differ from manifest: {part["path"]}')
                    for row in reader:
                        if len(row) != len(columns):
                            raise ValueError(f'Malformed CSV row in {part["path"]}, record {count+1}')
                        count += 1
                if count != part['rows']:
                    raise ValueError(f'CSV row count differs from manifest: {part["path"]}')
                rows += count
            if rows != records['row_count']:
                raise ValueError(f'Experiment {number}/{name}: total row count differs from manifest')
            sets.append(dict(id=name, parts=len(records['parts']), rows=rows, columns=len(columns)))
        if not sets:
            raise ValueError(f'Experiment {number}: no record sets')
        declared_total = description.get('record_summary', {}).get('total')
        if declared_total is not None and declared_total != sum(q['rows'] for q in sets):
            raise ValueError(f'Experiment {number}: record_summary.total differs from shard rows')
        checks[number] = dict(files_checked=len(files), record_sets=sets,
                              rows=sum(q['rows'] for q in sets))
    result = dict(passed=True, schema=1, selected_experiments=selected,
                  manifest_sha256=_sha(MANIFEST), experiments=checks,
                  verification='All declared bytes/SHA-256; CSV.gz schemas and row counts',
                  trajectories_executed=0)
    if output is not None:
        directory = _fresh_output(output)
        _write(directory/'verification.json', result)
    return result


def _load(description):
    import pandas as pd
    sets = []
    for records in description['record_sets']:
        parts = [pd.read_csv(_path(part['path']), compression='gzip', float_precision='round_trip')
                 for part in records['parts']]
        frame = pd.concat(parts, ignore_index=True)
        if list(frame.columns) != records['columns'] or len(frame) != records['row_count']:
            raise ValueError(f'CSV parser result differs from manifest: {records["id"]}')
        frame.insert(0, 'record_set', records['id'])
        sets.append(frame)
    result = pd.concat(sets, ignore_index=True)
    keys = [q for q in IDENTITIES if q in result] + (['rep'] if 'rep' in result else [])
    if result.duplicated(keys).any():
        raise ValueError('Duplicate saved metric identities; refusing to double-weight records')
    if any(result[q].isna().any() for q in keys):
        raise ValueError('A grouping or replication identity is missing')
    return result


def _all_mean(values):
    import numpy as np
    a = np.asarray(values, dtype=float)
    return float(np.mean(a)) if len(a) and np.isfinite(a).all() else np.nan


def _summaries(frame):
    import numpy as np
    import pandas as pd
    from pandas.api.types import is_numeric_dtype
    groupkeys = [q for q in IDENTITIES if q in frame]
    if 'data_id' not in groupkeys:
        raise ValueError('Simulation records need data_id for equal-dataset summaries')
    metrics = [q for q in frame.columns if q not in groupkeys and q not in NONMETRICS
               and is_numeric_dtype(frame[q])]
    if not metrics:
        raise ValueError('No numerical saved metrics found')
    rows = []
    for key, group in frame.groupby(groupkeys, sort=True, dropna=False):
        base = dict(zip(groupkeys, key))
        values = group[metrics].to_numpy(dtype=float)
        finite = np.isfinite(values)
        for index, metric in enumerate(metrics):
            a = values[:, index]
            good = finite[:, index]
            n = len(a)
            se = float(a.std(ddof=1)/np.sqrt(n)) if good.all() and n>1 else np.nan
            rows.append(base | dict(metric=metric, n_records=n, n_finite=int(good.sum()),
                n_nan=int(np.isnan(a).sum()), n_posinf=int(np.isposinf(a).sum()),
                n_neginf=int(np.isneginf(a).sum()), mean=_all_mean(a), se_within_dataset=se))
    per_dataset = pd.DataFrame(rows)
    second_keys = [q for q in groupkeys if q != 'data_id'] + ['metric']
    rows = []
    for key, group in per_dataset.groupby(second_keys, sort=True, dropna=False):
        a = group['mean'].to_numpy(dtype=float)
        n = len(a)
        se = float(a.std(ddof=1)/np.sqrt(n)) if np.isfinite(a).all() and n>1 else np.nan
        rows.append(dict(zip(second_keys, key)) | dict(n_datasets=n,
            n_finite_dataset_means=int(np.isfinite(a).sum()),
            n_records=int(group.n_records.sum()), n_finite_records=int(group.n_finite.sum()),
            n_nan_records=int(group.n_nan.sum()),
            n_infinite_records=int(group.n_posinf.sum()+group.n_neginf.sum()),
            mean=_all_mean(a), se_between_datasets=se))
    equal_dataset = pd.DataFrame(rows)
    status_keys = groupkeys + (['status'] if 'status' in frame else [])
    statuses = frame.groupby(status_keys, sort=True, dropna=False).size().reset_index(name='n_records')
    return per_dataset, equal_dataset, statuses


def _plots(number, summary, destination):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    chosen = {'1':['relative_gap', 'true_coef_rel_sq'],
              '2':['relative_gap', 'true_coef_rel_sq'],
              '3':['relative_gap', 'linear_relative', 'remainder_relative', 'cross_relative'],
              '4':['scaled_squared_gap', 'relative_squared_gap']}[number]
    figures = []
    main = summary[summary.arm == 'main'] if 'arm' in summary else summary
    for metric in chosen:
        selected = main[main.metric == metric]
        if selected.empty:
            continue
        directions = sorted(selected.direction.unique()) if 'direction' in selected else ['']
        methods = list(dict.fromkeys(selected.method)) if 'method' in selected else ['']
        fig, axes = plt.subplots(len(directions), len(methods),
            figsize=(max(6, 2.35*len(methods)), max(3.2, 2.9*len(directions))),
            squeeze=False, layout='constrained')
        for di, direction in enumerate(directions):
            for mi, method in enumerate(methods):
                ax = axes[di, mi]
                group = selected
                if 'direction' in group:
                    group = group[group.direction == direction]
                if 'method' in group:
                    group = group[group.method == method]
                linekeys = [q for q in ('record_set', 'rule') if q in group]
                for key, line in group.groupby(linekeys, sort=True, dropna=False):
                    if not isinstance(key, tuple):key=(key,)
                    line = line.sort_values('budget')
                    label = ' / '.join(str(q) for q in key)
                    ax.plot(line.budget, line['mean'], 'o-', ms=3, lw=1, label=label)
                ax.set_xscale('log')
                values = group['mean'].to_numpy(dtype=float)
                finite = values[np.isfinite(values)]
                if len(finite) and np.all(finite>0):
                    ax.set_yscale('log')
                elif metric == 'cross_relative' and len(finite):
                    ax.axhline(0, color='#777', lw=.6)
                ax.set_title(method+(' / '+direction if direction else ''))
                ax.set_xlabel('Draw budget N')
                ax.set_ylabel(metric.replace('_', ' '))
                ax.grid(alpha=.2)
                if di==0 and mi==0:ax.legend(fontsize=7)
        fig.suptitle(f'Experiment {number}: saved metrics, equal weight per dataset', fontsize=11)
        folder = destination/'figures'
        folder.mkdir(exist_ok=True)
        name = f'{metric}.png'
        fig.savefig(folder/name, dpi=150, bbox_inches='tight')
        plt.close(fig)
        figures.append('figures/'+name)
    return figures


def summarize(experiment='all', output=None):
    """Produce metrics-only dataset means, equal-dataset summaries and curves."""
    if output is None:
        raise ValueError('summarize requires a new output directory')
    verified = verify(experiment)
    manifest = _manifest()
    destination = _fresh_output(output)
    os.environ.setdefault('MPLCONFIGDIR', str(destination/'.matplotlib-cache'))
    result = dict(completed=False, selected_experiments=_selected(experiment),
        manifest_sha256=verified['manifest_sha256'], trajectories_executed=0,
        summary_scope='Published saved metrics; not a trajectory or state-level verification',
        averaging='Within data_id over all records; then equal weight across data_id',
        nonfinite_policy='NaN/Inf propagate to undefined means; counts retained; no finite-only replacement',
        uncertainty='Descriptive standard errors only; no tests or simultaneous-coverage claim',
        state_analysis='Use the separate analyze command on complete new run outputs for full III decomposition and IV numerical diagnostics',
        experiments={})
    _write(destination/'verification.json', verified)
    for number in result['selected_experiments']:
        frame = _load(manifest['experiments'][number])
        folder = destination/f'exp{number}'
        folder.mkdir()
        per_dataset, equal_dataset, statuses = _summaries(frame)
        per_dataset.to_csv(folder/'dataset_means.csv', index=False, float_format='%.17g')
        equal_dataset.to_csv(folder/'equal_dataset_summary.csv', index=False, float_format='%.17g')
        statuses.to_csv(folder/'record_status_counts.csv', index=False)
        figures = _plots(number, equal_dataset, folder)
        result['experiments'][number] = dict(records=len(frame),
            dataset_metric_groups=len(per_dataset), summary_metric_groups=len(equal_dataset),
            status_count_groups=len(statuses), figures=figures,
            main_arms_only_in_figures=True)
        del frame, per_dataset, equal_dataset, statuses
    result['completed'] = True
    _write(destination/'summary_manifest.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify', 'summarize'])
    parser.add_argument('--experiment', choices=['all', '1', '2', '3', '4'], default='all')
    parser.add_argument('--output', type=Path, help='New output directory; required for summarize')
    args = parser.parse_args(argv)
    if args.action == 'summarize' and args.output is None:
        parser.error('--output is required for summarize')
    result = (verify if args.action=='verify' else summarize)(args.experiment, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__=='__main__':
    main()
