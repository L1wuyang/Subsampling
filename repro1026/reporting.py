"""Analyze explicitly supplied new I--V runs and draw figures using budget N.

The release includes saved simulation and Experiment V evidence. This entry
point analyzes explicitly supplied runs. Experiment V defaults to finite-
repetition empirical reporting; historical mean tests are not current evidence.
Example::

    python -m repro1026.reporting --experiment 3 --results runs/formal --output analysis/exp3

``--results`` accepts a run-tree root containing exp1 ... exp5, an individual
experiment run, or its direct records directory. Outputs always go to a new
directory. Smoke summaries are marked as engineering checks throughout.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import html
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {
    1: 'experiment1_native_comprehensive_20261024',
    2: 'experiment2_native_comprehensive_20261024',
    3: 'experiment3_native_comprehensive_20261024',
    4: 'experiment4_native_comprehensive_20261025',
    5: 'experiment5_native_realdata_20261025',
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(path, value):
    def default(item):
        if hasattr(item, 'item'):
            return item.item()
        raise TypeError(type(item).__name__)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False, default=default)+'\n', encoding='utf8')


@contextmanager
def current_labels(smoke=False):
    """Change only figure text; the frozen scientific sources stay untouched."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.text import Text
    from matplotlib.figure import Figure
    original = Text.set_text
    original_savefig = Figure.savefig

    def translated(self, value):
        if isinstance(value, str):
            for old, new in [
                ('Sampling budget r', 'Sampling budget N'), ('Draws r', 'Draws N'),
                ('C/r', 'C/N'), ('r = 150', 'N = 150'), ('r=60', 'N=60'),
                (r'$r\,', r'$N\,'), ('$r$', '$N$'),
            ]:
                value = value.replace(old, new)
            value = re.sub(r'\br\s*=\s*(?=\d)', 'N = ', value)
        return original(self, value)

    Text.set_text = translated
    def marked_savefig(self, *args, **kwargs):
        if smoke:
            self.text(.5, .995, 'SMOKE ONLY: reduced engineering check; not paper results',
                      ha='center', va='top', fontsize=8,
                      gid='_repro1026_smoke_label') if not any(
                          q.get_gid() == '_repro1026_smoke_label' for q in self.texts) else None
        return original_savefig(self, *args, **kwargs)
    Figure.savefig = marked_savefig
    try:
        yield
    finally:
        Text.set_text = original
        Figure.savefig = original_savefig


def resolve_results(experiment: int, results: Path):
    """Resolve only within the user-supplied tree; never consult Full records."""
    if experiment not in DIRECTORIES:
        raise ValueError('experiment must be between 1 and 5')
    supplied = Path(results).expanduser().resolve()
    if not supplied.is_dir():
        raise FileNotFoundError(f'Results directory does not exist: {supplied}')
    for base in (supplied/f'exp{experiment}', supplied):
        if experiment in (1, 2):
            candidates = [base/'outputs/formal_01', base]
        elif experiment == 5:
            candidates = [base/'formal', base/'outputs/formal_01', base]
        else:
            candidates = [base, base/'outputs/formal_01']
        for records in candidates:
            if (records/'protocol.json').is_file() and (records/'execution.json').is_file():
                if experiment in (1, 2):
                    if records.name != 'formal_01' or records.parent.name != 'outputs':
                        raise ValueError('I/II records must retain the run/outputs/formal_01 layout')
                    run = records.parents[1]
                    if not (run/'data').is_dir():
                        raise FileNotFoundError(f'I/II analysis also needs its generated data/: {run}')
                else:
                    run = base if records != base else records
                config = read(records/'protocol.json')
                if not read(records/'execution.json').get('completed'):
                    raise ValueError(f'Execution is incomplete: {records}')
                smoke = bool(config.get('smoke_only') or config.get('run_mode') == 'smoke'
                             or config.get('reproduction_mode') == 'smoke')
                return records, run, config, 'smoke' if smoke else 'formal'
    raise FileNotFoundError(f'No experiment {experiment} protocol.json and execution.json under {supplied}')


def check_output(output: Path, source: Path):
    output = Path(output).expanduser().resolve()
    if output == ROOT or ROOT.is_relative_to(output):
        raise ValueError('Analysis output cannot replace the package or its parent')
    for name in ('Experiments', 'Data', 'Paper_Versions', 'provenance', 'repro1026', 'docs'):
        if output.is_relative_to(ROOT/name):
            raise ValueError(f'Analysis output is inside immutable package inputs: {output}')
    if output == source or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('Analysis output must be separate from the supplied experiment inputs')
    if output.exists():
        raise FileExistsError(f'Use a new analysis directory: {output}')
    return output


def copy_analysis_inputs(source: Path, output: Path, experiment: int):
    output.mkdir(parents=True, exist_ok=False)
    names = ['protocol.json', 'execution.json']
    if experiment == 3:
        names += ['results.csv', 'sensitivity_results.csv', 'full_reference.csv',
                  'sensitivity_full_reference.csv']
    if experiment == 4:
        names += ['parameters.csv']
    for name in names:
        shutil.copy2(source/name, output/name)
    patterns = {
        3: ['*_*/*/native_states.npz', '*_*/*/raw_r*.npz'],
        4: ['*_*/*/r*_c*.csv'],
        5: ['draws/*/*.csv', 'targets/*/*/summary.json'],
    }[experiment]
    manifest = {}
    for pattern in patterns:
        for path in source.glob(pattern):
            target = output/path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    for path in output.rglob('*'):
        if path.is_file():
            with path.open('rb') as stream:
                manifest[path.relative_to(output).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
    save(output/'analysis_input_sha256.json', manifest)


def scientific_analysis(experiment):
    folder = ROOT/'Experiments'/DIRECTORIES[experiment]
    sys.path.insert(0, str(folder/'src'))
    name = 'analyze' if experiment == 5 else 'analysis'
    module = importlib.import_module(f'native_exp{experiment}.{name}')
    if not Path(module.__file__).resolve().is_relative_to(folder):
        raise RuntimeError('A scientific analysis module was imported from outside this Lite release')
    return module


def historical_two_sided(frame, output: Path, budgets=None):
    """Legacy analysis only; not called by the current reporting entry point.

    This historical mean-based calculation does not establish the ordering of
    the full conditional MSE. The archived original analysis is also available
    through evidence/experiment5/reanalyze.py.
    """
    from .exp5 import paired_comparisons
    budgets = budgets or {'gdsc': 749, 'year': 5000}
    old = output/'primary_comparisons.csv'
    if old.is_file():
        shutil.copy2(old, output/'primary_comparisons_original_one_sided.csv')
    else:
        paired_comparisons(frame, budgets, 'less').to_csv(
            output/'primary_comparisons_original_one_sided.csv', index=False)
    result = paired_comparisons(frame, budgets, 'two-sided')
    if len(result) != 36:
        raise ValueError('Expected six methods, two datasets and three comparisons: one 36-pair family')
    for name in ('primary_comparisons.csv', 'paired_comparisons_two_sided.csv'):
        result.to_csv(output/name, index=False, float_format='%.17g')
    summary_path = output/'summary.json'
    summary = read(summary_path)
    summary.update(primary_sidedness='two-sided', primary_holm_family=36,
                   primary_holm_supports_lower=int(result.supports_OPT_lower.sum()),
                   maximum_two_sided_holm_p=float(result.p_holm.max()),
                   predictive_inference='descriptive; historical test exploration',
                   support_wide_stability_certified=False)
    save(summary_path, summary)
    save(output/'inference_revision.json', dict(
        analysis='two-sided paired t, one joint Holm over all 36 comparisons',
        conditional_on_fixed_data_and_parameters=True, pointwise_intervals_not_simultaneous=True,
        comparisons=36, primary_holm_family=36, primary_sidedness='two-sided',
        original_one_sided_preserved_separately=True,
        historical_exploration_not_adjusted=True))
    return result


def _emit(fig, output, name):
    import matplotlib.pyplot as plt
    fig.suptitle('SMOKE: reduced execution check only; not paper results', fontsize=11)
    folder = output/'figures'
    folder.mkdir(exist_ok=True)
    for extension in ('pdf', 'svg', 'png'):
        fig.savefig(folder/(name+'.'+extension), dpi=145, bbox_inches='tight')
    plt.close(fig)


def _smoke_page(output, experiment, summary):
    images = ''.join('<h2>'+html.escape(p.stem)+'</h2><img style="max-width:100%" src="figures/'+p.name+'">'
                     for p in sorted((output/'figures').glob('*.png')))
    (output/'index.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Smoke analysis</title>'
        '<body><h1>Experiment '+str(experiment)+': SMOKE ONLY</h1>'
        '<p>Reduced engineering check. No smoke number or test is formal paper evidence.</p><pre>'
        +html.escape(json.dumps(summary, indent=2))+'</pre>'+images+'</body></html>', encoding='utf8')


def smoke_III(module, output):
    """Use the frozen record definitions with the actual reduced budgets."""
    import numpy as np
    import pandas as pd
    from scipy.stats import t
    import matplotlib.pyplot as plt
    main = pd.read_csv(output/'results.csv')
    extra = pd.read_csv(output/'sensitivity_results.csv')
    frame = pd.concat([main, extra], ignore_index=True)
    keys = ['direction', 'data_id', 'arm', 'method', 'budget']
    if frame.duplicated(keys+['rep']).any():
        raise ValueError('Duplicate III result records')
    references = pd.concat([pd.read_csv(output/'full_reference.csv'),
                            pd.read_csv(output/'sensitivity_full_reference.csv')], ignore_index=True)
    refs = references.set_index(keys[:-1])
    rows = []
    for key, group in frame.groupby(keys, sort=True):
        ref = refs.loc[key[:-1]]
        values = group.relative_gap.to_numpy()
        finite = bool(np.isfinite(values).all())
        mean = float(values.mean()) if finite else np.nan
        se = float(values.std(ddof=1)/np.sqrt(len(values))) if finite and len(values)>1 else np.nan
        half = float(t.ppf(.975, len(values)-1)*se) if len(values)>1 else np.nan
        theory = float(ref.C/key[-1]) if np.isfinite(ref.C) and ref.C>0 else np.nan
        row = dict(zip(keys, key)) | dict(count=len(values), finite_relative_count=int(np.isfinite(values).sum()),
            mean=mean, se=se, halfwidth95=half, theory=theory, ratio=mean/theory)
        for metric in ['linear_relative', 'remainder_relative', 'cross_relative', 'absolute_gap',
                       'true_coef_rel_sq', 'design_signal_rel_sq', 'population_signal_rel_sq',
                       'population_response_mse', 'residual_norm']:
            a=group[metric].to_numpy()
            row[metric+'_mean'] = float(a.mean()) if np.isfinite(a).all() else np.nan
        direction, did, arm, method, budget = key
        with np.load(output/f'{direction}_{did:02d}'/arm/f'raw_r{budget}.npz') as raw, \
             np.load(output/f'{direction}_{did:02d}'/arm/'native_states.npz') as state:
            delta = raw[method+'_state'].mean(axis=0)-state[method+'_target']
            bias = float(delta@state['metric']@delta)
            row['mc_mean_error_sq_relative'] = bias/ref.target_norm_sq if ref.target_norm_sq>1e-24 else np.nan
        rows.append(row)
    summary_frame = pd.DataFrame(rows)
    summary_frame.to_csv(output/'mse_summary.csv', index=False)
    primary = summary_frame[summary_frame.arm=='main']
    for name, field, label in [('01_mse_absolute_compact', 'mean', 'Relative target MSE'),
                               ('02_mse_ratio', 'ratio', 'Empirical / first order')]:
        fig, axes = plt.subplots(3, 4, figsize=(12, 8.2), layout='constrained')
        for i, method in enumerate(module.METHODS):
            for j, direction in enumerate(module.DIRECTIONS):
                ax=axes[i//2, (i%2)*2+j]
                g=primary[(primary.method==method)&(primary.direction==direction)].sort_values('budget')
                ax.plot(g.budget, g[field], 'o-', ms=3)
                if field=='mean': ax.plot(g.budget, g.theory, '--', color='black', label='C/N')
                else: ax.axhline(1, color='black', ls='--', lw=.7)
                ax.set(xscale='log', yscale='log', title=method+' / '+direction,
                       xlabel='Draws N', ylabel=label)
                ax.grid(alpha=.2)
        _emit(fig, output, name)
    summary = dict(completed=True, main_rows=len(main), sensitivity_rows=int((extra.arm!='zero_response').sum()),
                   zero_rows=int((extra.arm=='zero_response').sum()), total_rows=len(frame),
                   numerical_failures=int((frame.status=='numerical_failure').sum()),
                   undefined_relative_gaps=int(frame.relative_gap.isna().sum()),
                   pointwise_intervals='Student t over the actual reduced repeat count; smoke only')
    save(output/'summary.json', summary)
    return summary


def smoke_IV(module, output, config):
    import pandas as pd
    import matplotlib.pyplot as plt
    frame = module.load_records(output)
    if len(frame)!=read(output/'execution.json')['records']:
        raise ValueError('IV record count differs from execution.json')
    keys=['direction', 'data_id', 'arm', 'method', 'budget']
    if frame.duplicated(keys+['rep']).any():
        raise ValueError('Duplicate IV result records')
    rows=[]
    for key, g in frame.groupby(keys, sort=True):
        rows.append(dict(zip(keys, key)) | module.stats(g.scaled_squared_gap) | dict(
            relative_mean=float(g.relative_squared_gap.mean()) if g.relative_squared_gap.notna().any() else None,
            local_floor_fraction=float(g.resolution_limited.mean()),
            rank_deficient_fraction=float((g['rank']<config['dimension']).mean())))
    grouped=pd.DataFrame(rows)
    grouped.to_csv(output/'gap_summary.csv', index=False)
    primary=grouped[grouped.arm=='main']
    fig, axes=plt.subplots(3, 4, figsize=(12, 8.2), layout='constrained')
    for i, method in enumerate(module.METHODS):
        for j, direction in enumerate(module.DIRECTIONS):
            ax=axes[i//2, (i%2)*2+j]
            g=primary[(primary.method==method)&(primary.direction==direction)].sort_values('budget')
            ax.plot(g.budget, g['mean'], 'o-', ms=3)
            ax.set(xscale='log', yscale='log', title=method+' / '+direction,
                   xlabel='Draws N', ylabel='N mean squared gap to same-draw LS')
            ax.grid(alpha=.2)
    _emit(fig, output, '01_scaled_gap')
    summary=dict(completed=True, records=len(frame), main_records=int((frame.arm=='main').sum()),
                 zero_records=int((frame.arm=='zero_response').sum()), tail_records=int((frame.arm=='tails').sum()),
                 numerical_failure_records=int((frame.status=='numerical_failure').sum()),
                 accuracy_certified=False)
    save(output/'summary.json', summary)
    return summary


def smoke_V(module, output, config):
    """Reduced engineering output with the same empirical-only interpretation."""
    from .empirical_v import analyze_records
    return analyze_records(output, config=config, smoke=True)


def attach_IV_diagnostics(source, output):
    from .iv_diagnostics import diagnose
    diagnostics=diagnose(source, output/'diagnostics', replay='dense')
    summary=read(output/'summary.json')
    warnings={(q['direction'], q['method']) for q in diagnostics['selected_replays'] if q['warning']}
    tested={(q['direction'], q['method']) for q in diagnostics['selected_replays']}
    for endpoint in summary.get('primary_endpoint_comparisons', []):
        key=(endpoint['direction'], endpoint['method'])
        endpoint['local_floor_fraction_at_38400']=endpoint.pop('resolution_limited_at_38400')
        endpoint['selected_replay_status']=('unresolved' if key in warnings else
                                             'selected_replay_agreement_only' if key in tested else 'not_replayed')
        endpoint['accuracy_certified']=False
    summary.update(accuracy_certified=False,
        local_floor_semantics='Subtraction scale only; false does not certify accumulated accuracy',
        selected_independent_replay_warnings=len(warnings),
        diagnostic_trajectories_executed=len(diagnostics['selected_replays']),
        tail_concentration_warning_groups=sum(q['tail_concentration_warning'] for q in diagnostics['tail_groups']))
    save(output/'summary.json', summary)
    endpoints_path=output/'endpoint_comparison.csv'
    if endpoints_path.is_file():
        import pandas as pd
        frame=pd.read_csv(endpoints_path).rename(columns={'resolution_limited_at_38400':'local_floor_fraction_at_38400'})
        frame['selected_replay_status']=['unresolved' if (q.direction,q.method) in warnings else
            'selected_replay_agreement_only' if (q.direction,q.method) in tested else 'not_replayed'
            for q in frame.itertuples()]
        frame['accuracy_certified']=False
        frame.to_csv(endpoints_path, index=False)
    return len(diagnostics['selected_replays'])


def analyze(experiment: int, output: Path, results: Path):
    source, run_root, config, mode=resolve_results(experiment, results)
    output=check_output(output, run_root)
    os.environ['MPLCONFIGDIR']=str(output.parent/'.matplotlib-cache')
    replay_count=0
    with current_labels(smoke=(mode=='smoke' and experiment in (1,2))):
        if experiment in (1,2):
            from .exp12 import analyze_saved
            analyze_saved(experiment, run_root, output, source_root=ROOT)
            analysis=output/'outputs/formal_01'
        else:
            copy_analysis_inputs(source, output, experiment)
            if experiment == 5:
                from .empirical_v import analyze_records
                analyze_records(output, config=config, smoke=(mode == 'smoke'))
            else:
                module=scientific_analysis(experiment)
                if mode=='smoke':
                    if experiment==3:smoke_III(module, output)
                    elif experiment==4:smoke_IV(module, output, config)
                else:
                    module.main(SimpleNamespace(output=str(output)))
            analysis=output
            if experiment==4:replay_count=attach_IV_diagnostics(source, output)
        summary=read(analysis/'summary.json')
        summary.update(reproduction_mode=mode, smoke_only=(mode=='smoke'),
                       role='reduced engineering check only; not paper results' if mode=='smoke' else 'new formal-run analysis',
                       draw_budget='N', atom_population='N_0')
        save(analysis/'summary.json', summary)
        if mode=='smoke' and experiment in (3,4,5):_smoke_page(output, experiment, summary)
    note=dict(experiment=experiment, supplied_results=str(Path(results).expanduser().resolve()),
              source=str(source), analysis=str(analysis), reproduction_mode=mode,
              smoke_only=(mode=='smoke'), formal_trajectories_rerun=False,
              diagnostic_trajectories_executed=replay_count, draw_budget='N', atom_population='N_0',
              bundled_results_required=False, manuscript_builder_included=False,
              original_sources_and_outputs_modified=False)
    save(output/'current_reporting.json', note)
    return analysis


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', type=int, choices=range(1,6), required=True)
    parser.add_argument('--results', type=Path, required=True,
                        help='Explicit new run tree, experiment run, or direct records directory')
    parser.add_argument('--output', type=Path, required=True, help='New analysis directory')
    args=parser.parse_args(argv)
    print(analyze(args.experiment, args.output, args.results), flush=True)


if __name__=='__main__':
    main()
