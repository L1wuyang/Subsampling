"""Finite-repetition Experiment V summaries and figures; no mean inference.

The frozen estimators and historical t/Holm analysis remain unchanged. This
module reports the realized draws, without estimating the full conditional MSE
or attaching confidence intervals to their means.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

METHODS = ['Ridge', 'Landweber', 'Showalter', 'HBF', 'Nesterov', 'SOAR']
RULES = ['UNI', 'NORM', 'LEV', 'OPT']
METRICS = ['relative_coefficient_error', 'relative_design_target_error',
           'test_target_prediction_mse', 'test_response_mse', 'test_response_rmse']
KEYS = ['dataset', 'method', 'rule', 'budget']
SCOPE = ('Finite-repetition empirical summaries of realized subsamples. '
         'They do not establish the ordering of the full conditional MSE. '
         'Observed stability checks apply only to the realized matrices. '
         'Prediction comparisons use previously explored test sets.')


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf8')


def load_records(folder):
    files = sorted((Path(folder)/'draws').glob('*/*.csv'))
    if not files:
        raise ValueError('No saved draw CSV files were found')
    return pd.concat([pd.read_csv(p, float_precision='round_trip') for p in files], ignore_index=True)


def load_targets(folder):
    """Load actual matched full-model outputs; never fabricate a reference line."""
    return {(tag, method): json.loads((Path(folder)/'targets'/tag/method/'summary.json').read_text(encoding='utf8'))
            for tag in ('gdsc', 'year') for method in METHODS}


def summarize(frame, output, config=None):
    if frame.empty or frame.duplicated(KEYS+['rep']).any():
        raise ValueError('Missing or duplicate Experiment V records')
    required = set(KEYS+['rep', 'status', 'step_bound_observed', 'unique_objects']+METRICS+['theoretical_relative_mse'])
    if required-set(frame):
        raise ValueError('Missing fields: '+', '.join(sorted(required-set(frame))))
    if set(frame.dataset) != {'gdsc', 'year'} or set(frame.method) != set(METHODS) or set(frame.rule) != set(RULES):
        raise ValueError('Expected both datasets, six methods and four rules')
    finite = np.isfinite(frame[METRICS].to_numpy()).all(axis=1)
    failed = frame.status.to_numpy() != 'complete'
    if failed.any() or not finite.all():
        save(output/'failure_summary.json', dict(records=len(frame), failed_records=int(failed.sum()),
             nonfinite_metric_records=int((~finite).sum()), all_records_retained=True,
             successful_only_means_reported=False))
        raise ValueError('Failed/nonfinite records retained; no successful-only summaries are produced')
    observed = frame.step_bound_observed.astype(str).str.lower()
    if not observed.isin(['true', 'false']).all():
        raise ValueError('Invalid observed stability-check values')
    if not np.isfinite(frame.unique_objects).all() or not frame.unique_objects.between(1, frame.budget).all():
        raise ValueError('Invalid distinct-atom counts')
    rows = []
    for key, group in frame.groupby(KEYS, sort=True):
        tag, method, rule, budget = key
        if config is not None:
            expected = config[tag]['repetitions']
            if len(group) != expected or set(group.rep) != set(range(expected)):
                raise ValueError(f'Unexpected repetitions: {key}')
        row = dict(zip(KEYS, key)) | dict(n=len(group))
        for metric in METRICS:
            row[metric+'_mean'] = float(group[metric].to_numpy().mean())
        first = group.theoretical_relative_mse.to_numpy()
        if not np.isfinite(first).all() or (first <= 0).any() or not np.all(first == first[0]):
            raise ValueError(f'Invalid/inconsistent first-order proxy: {key}')
        row.update(first_order_relative_value=float(first[0]),
                   empirical_to_first_order=float(row['relative_coefficient_error_mean']/first[0]),
                   mean_unique_objects=float(group.unique_objects.to_numpy().mean()))
        rows.append(row)
    grouped = pd.DataFrame(rows)
    for tag in ('gdsc', 'year'):
        budgets = set(config[tag]['budgets']) if config else set(frame[frame.dataset == tag].budget)
        expected = {(method, rule, budget) for method in METHODS for rule in RULES for budget in budgets}
        actual = set(grouped[grouped.dataset == tag][['method', 'rule', 'budget']].itertuples(index=False, name=None))
        if actual != expected:
            raise ValueError(f'Missing or unexpected method/rule/budget cells for {tag}')
    # GDSC NORM is hidden only when its retained means coincide with UNI.
    gdsc = grouped[grouped.dataset == 'gdsc'].set_index(['method', 'budget', 'rule'])
    for method, budget in gdsc.index.droplevel('rule').unique():
        for metric in METRICS:
            a, b = (gdsc.loc[(method, budget, rule), metric+'_mean'] for rule in ('UNI', 'NORM'))
            if a != b:
                raise ValueError('GDSC NORM and UNI differ; do not hide the NORM curve')
    rankings = []
    for key, group in grouped.groupby(['dataset', 'method', 'budget'], sort=True):
        values = group.set_index('rule').relative_coefficient_error_mean
        rankings.append(dict(dataset=key[0], method=key[1], budget=int(key[2]),
            opt_strictly_lowest_empirical_mean=bool(values['OPT'] < values.drop('OPT').min())))
    report = dict(completed=True, records=len(frame), method_budget_cells=len(rankings),
        opt_strictly_lowest_empirical_mean_cells=sum(r['opt_strictly_lowest_empirical_mean'] for r in rankings),
        observed_step_bound_violations=int((observed == 'false').sum()),
        all_outputs_retained=True, full_conditional_mse_ordering_inferred=False,
        mean_confidence_intervals_reported=False, mean_tests_used_as_current_evidence=False,
        support_wide_stability_certified=False, formal_trajectories_rerun=False, scope=SCOPE)
    grouped.to_csv(output/'summary.csv', index=False, float_format='%.17g')
    save(output/'rankings.json', rankings)
    save(output/'summary.json', report)
    return grouped, report


def render_targets(grouped, output, reference=None, smoke=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter, LogLocator, LogFormatterMathtext
    colors = dict(zip(RULES, ['#667085', '#0077B6', '#E69F00', '#D7263D']))
    markers = dict(zip(RULES, ['o', 's', '^', 'D']))
    styles = dict(zip(RULES, ['-', (0, (4, 2)), (0, (1, 1.3)), (0, (4, 1.5, 1, 1.5))]))
    style = {'font.family': 'DejaVu Sans', 'font.size': 8.5,
        'axes.titlesize': 8.5, 'axes.titleweight': 'normal', 'axes.labelsize': 9,
        'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5, 'legend.fontsize': 8.5,
        'axes.linewidth': .65, 'axes.spines.top': False, 'axes.spines.right': False,
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
        'mathtext.fontset': 'dejavusans', 'savefig.facecolor': 'white', 'axes.formatter.useoffset': False}
    folder = output/'figures'
    folder.mkdir(exist_ok=True)
    audit = {}
    with plt.rc_context(style):
        for tag, name in [('gdsc', 'r5_01_gdsc_target'), ('year', 'r5_02_year_target')]:
            rules = ['UNI', 'LEV', 'OPT'] if tag == 'gdsc' else RULES
            fig, axes = plt.subplots(2, 3, figsize=(156.8/25.4, 3.12))
            fig.subplots_adjust(left=.10, right=.973, bottom=.155, top=.855, wspace=.40, hspace=.48)
            points, panels = [], []
            for mi, method in enumerate(METHODS):
                ax = axes.flat[mi]
                ax.set_xscale('log'); ax.set_yscale('log')
                ax.xaxis.set_minor_locator(NullLocator()); ax.yaxis.set_minor_locator(NullLocator())
                ax.yaxis.set_major_locator(LogLocator(base=10, numticks=4))
                ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
                ax.tick_params(axis='both', which='major', length=2.5, width=.65, pad=2)
                ax.grid(which='major', color='#b9c1c9', alpha=.35, linewidth=.45)
                ax.set_axisbelow(True)
                for rule in rules:
                    g = grouped[(grouped.dataset == tag)&(grouped.method == method)&(grouped.rule == rule)].sort_values('budget')
                    values = g.relative_coefficient_error_mean.to_numpy()
                    if (values <= 0).any():
                        raise ValueError('Log-scale paper figures require strictly positive empirical means')
                    ax.plot(g.budget, values, color=colors[rule], marker=markers[rule],
                            ls=styles[rule], lw=1.05, ms=2.5, markeredgewidth=0, zorder=3)
                    points.extend(dict(dataset=tag, method=method, rule=rule, budget=int(b), mean=float(v))
                                  for b, v in zip(g.budget, values))
                if reference:
                    panel = reference['figures'][name]['panels'][mi]
                    if panel['method'] != method:
                        raise ValueError('Reference panel order differs')
                    ax.set_xlim(*panel['xlim']); ax.set_ylim(*panel['ylim'])
                    ax.xaxis.set_major_locator(FixedLocator([100, 1000] if tag == 'gdsc' else [1000, 10000]))
                else:
                    budgets = sorted(grouped[grouped.dataset == tag].budget.unique())
                    ax.xaxis.set_major_locator(FixedLocator(budgets if len(budgets) <= 3 else [budgets[0], budgets[len(budgets)//2], budgets[-1]]))
                ax.xaxis.set_major_formatter(ScalarFormatter())
                ax.tick_params(axis='x', labelbottom=mi >= 3)
                ax.set_title(method, pad=4)
                if ax.collections:
                    raise AssertionError('Empirical target plots must not contain interval shading')
                panels.append(dict(method=method, xlim=list(ax.get_xlim()), ylim=list(ax.get_ylim()),
                                   curve_count=len(ax.lines), collection_count=0))
            if reference:
                expected = reference['figures'][name]['points']
                if [tuple(p[k] for k in ('dataset', 'method', 'rule', 'budget')) for p in points] != [tuple(p[k] for k in ('dataset', 'method', 'rule', 'budget')) for p in expected]:
                    raise ValueError('Saved-record plot identities differ from the paper reference')
                np.testing.assert_allclose([p['mean'] for p in points], [p['mean'] for p in expected], rtol=2e-12, atol=0)
            handles = [Line2D([], [], color=colors[r], marker=markers[r], ls=styles[r], lw=1.05,
                       ms=2.8, markeredgewidth=0, label='UNI (= NORM)' if tag == 'gdsc' and r == 'UNI' else r) for r in rules]
            fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.53, .995), ncol=len(handles),
                       frameon=False, handlelength=2, columnspacing=1.15, handletextpad=.45, borderaxespad=0)
            fig.supxlabel('Sampling budget $N$', y=.013, fontsize=9)
            fig.supylabel('Empirical mean relative squared error', x=.003)
            if smoke:
                fig.text(.5, .055, 'SMOKE: reduced engineering check only', ha='center', color='#a00000', fontsize=7)
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            box = fig.legends[0].get_window_extent(renderer)
            if any(box.overlaps(ax.title.get_window_extent(renderer)) for ax in axes[0]):
                raise AssertionError('Legend overlaps panel title')
            for ext in ('pdf', 'svg', 'png'):
                fig.savefig(folder/(name+'.'+ext), dpi=220)
            plt.close(fig)
            pd.DataFrame(points).to_csv(output/(name+'_plotted_points.csv'), index=False, float_format='%.17g')
            audit[name] = dict(visible_points=len(points), panels=panels, interval_shading=False,
                paper_means_exact=all(a['mean'] == b['mean'] for a,b in zip(points, expected)) if reference else None,
                paper_reference_checked=reference is not None,
                pdf_sha256=hashlib.sha256((folder/(name+'.pdf')).read_bytes()).hexdigest())
    save(output/'figure_validation.json', audit)
    return audit


def render_auxiliary(frame, grouped, targets, output, smoke=False):
    """Retain the four descriptive diagnostics without mean-based inference."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator, NullFormatter
    colors = dict(zip(RULES, ['#667085', '#0077B6', '#E69F00', '#D7263D']))
    folder = output/'figures'
    diagnostics = {}
    refs = []
    for (tag, method), summary in targets.items():
        value = float(summary['full']['response_test_rmse'])
        refs.append(dict(dataset=tag, method=method, matched_full_test_rmse=value))
    pd.DataFrame(refs).to_csv(output/'full_prediction_reference.csv', index=False, float_format='%.17g')

    def emit(fig, name, description):
        if smoke:
            fig.suptitle('SMOKE: reduced engineering check only; not paper results', fontsize=10)
        for extension in ('pdf', 'svg', 'png'):
            fig.savefig(folder/(name+'.'+extension), dpi=180)
        plt.close(fig)
        diagnostics[name] = dict(description=description, finite_repetition_descriptive_only=True,
                                 mean_confidence_intervals=False, mean_tests=False)

    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'}):
        for name, field, label in [
            ('03_calibration', 'empirical_to_first_order', 'Empirical mean / (C/N)'),
            ('04_prediction', 'test_response_rmse_mean', 'Mean individual test RMSE')]:
            fig, axes = plt.subplots(3, 4, figsize=(12, 8.4), layout='constrained')
            for i, method in enumerate(METHODS):
                for j, tag in enumerate(('gdsc', 'year')):
                    ax = axes[i//2, (i%2)*2+j]
                    for rule in RULES:
                        if tag == 'gdsc' and rule == 'NORM':
                            continue
                        g = grouped[(grouped.dataset == tag)&(grouped.method == method)&(grouped.rule == rule)].sort_values('budget')
                        ax.plot(g.budget, g[field], 'o-', ms=2.5, color=colors[rule], label=rule)
                    value = 1 if name == '03_calibration' else float(targets[(tag, method)]['full']['response_test_rmse'])
                    ax.axhline(value, color='#343434', ls='--', lw=.8)
                    ax.set(title=method+' / '+tag, xscale='log', xlabel='Sampling budget N', ylabel=label)
                    ax.grid(alpha=.2)
            handles = [Line2D([], [], color=colors[r], marker='o', ls='-', ms=3, label=r) for r in RULES]
            handles.append(Line2D([], [], color='#343434', ls='--', lw=.8,
                                  label='Ratio one' if name == '03_calibration' else 'Matched full'))
            fig.legend(handles=handles, loc='outside lower center', ncol=5, frameon=False)
            emit(fig, name, 'Observed means divided by their first-order proxy; not full-MSE calibration.'
                 if name == '03_calibration' else 'Mean individual test RMSE and actual matched full-model references; previously explored test sets.')

        selected = {tag: preferred if preferred in set(frame[frame.dataset == tag].budget)
                    else int(frame[frame.dataset == tag].budget.min())
                    for tag, preferred in [('gdsc', 749), ('year', 5000)]}
        survival_points = []
        fig, axes = plt.subplots(3, 4, figsize=(12, 8.4), layout='constrained')
        for i, method in enumerate(METHODS):
            for j, tag in enumerate(('gdsc', 'year')):
                ax = axes[i//2, (i%2)*2+j]
                budget = selected[tag]
                for rule in RULES:
                    if tag == 'gdsc' and rule == 'NORM':
                        continue
                    values = np.sort(frame[(frame.dataset == tag)&(frame.method == method)&(frame.rule == rule)&(frame.budget == budget)].relative_coefficient_error.to_numpy())
                    survival = np.arange(len(values), 0, -1)/len(values)
                    ax.step(values, survival, where='post', color=colors[rule], label=rule)
                    survival_points.extend(dict(dataset=tag, method=method, rule=rule, budget=budget,
                        observed_error=float(value), empirical_survival=float(probability)) for value, probability in zip(values, survival))
                ax.set(title=f'{method} / {tag}, N={budget}', xscale='log', yscale='log',
                       xlabel='Relative squared target error', ylabel='Empirical survival')
                lo, hi = ax.get_xlim()
                ax.xaxis.set_major_locator(FixedLocator(np.geomspace(lo, hi, 3)))
                ax.xaxis.set_major_formatter(FuncFormatter(lambda value, pos: f'{value:.3g}'))
                ax.xaxis.set_minor_locator(NullLocator())
                ax.xaxis.set_minor_formatter(NullFormatter())
                ax.grid(alpha=.2)
        handles, labels = axes.flat[-1].get_legend_handles_labels()
        fig.legend(handles, labels, loc='outside lower center', ncol=4, frameon=False)
        emit(fig, '05_untrimmed_errors', 'Untrimmed empirical survival on realized draws; no population-tail or confidence-bound claim.')
        pd.DataFrame(survival_points).to_csv(output/'empirical_survival_points.csv', index=False, float_format='%.17g')

        fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), layout='constrained')
        coverage_points = []
        for ax, tag in zip(axes, ('gdsc', 'year')):
            for rule in RULES:
                if tag == 'gdsc' and rule == 'NORM':
                    continue
                g = grouped[(grouped.dataset == tag)&(grouped.rule == rule)].groupby('budget', as_index=False).mean(numeric_only=True)
                values = g.mean_unique_objects/g.budget
                ax.plot(g.budget, values, 'o-', ms=3, label=rule, color=colors[rule])
                coverage_points.extend(dict(dataset=tag, rule=rule, budget=int(budget),
                    mean_distinct_atoms_per_draw=float(value)) for budget, value in zip(g.budget, values))
            ax.set(title=tag, xscale='log', xlabel='Sampling budget N', ylabel='Mean distinct atoms / draws')
            ax.grid(alpha=.2); ax.legend(fontsize=8)
        emit(fig, '06_coverage', 'Distinct sampled atoms divided by draws, averaged equally over methods; not predictive or confidence-interval coverage.')
        pd.DataFrame(coverage_points).to_csv(output/'coverage_points.csv', index=False, float_format='%.17g')
    save(output/'auxiliary_figure_validation.json', diagnostics)
    return diagnostics


def report(frame, output, config=None, reference=None, smoke=False, targets=None):
    output = Path(output)
    targets = load_targets(output) if targets is None else targets
    if set(targets) != {(tag, method) for tag in ('gdsc', 'year') for method in METHODS}:
        raise ValueError('All 12 matched full-target summaries are required for prediction references')
    if any(not np.isfinite(float(s['full']['response_test_rmse'])) or float(s['full']['response_test_rmse']) < 0 for s in targets.values()):
        raise ValueError('Invalid matched full-model RMSE')
    grouped, summary = summarize(frame, output, config)
    figures = render_targets(grouped, output, reference, smoke)
    auxiliary = render_auxiliary(frame, grouped, targets, output, smoke)
    summary.update(smoke_only=bool(smoke), reporting='finite-repetition empirical summaries',
                   visible_target_points=sum(x['visible_points'] for x in figures.values()),
                   auxiliary_figures=list(auxiliary), matched_full_prediction_references=12)
    save(output/'summary.json', summary)
    content = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Experiment V empirical summaries</title><body><h1>Experiment V: finite-repetition summaries</h1><p>'+html.escape(SCOPE)+'</p>'
    if smoke:
        content += '<p><strong>SMOKE ONLY: reduced engineering check, not paper evidence.</strong></p>'
    content += '<pre>'+html.escape(json.dumps(summary, indent=2))+'</pre>'
    for name in list(figures)+list(auxiliary):
        if name in auxiliary:
            content += '<p>'+html.escape(auxiliary[name]['description'])+'</p>'
        content += '<img style="max-width:100%" alt="Experiment V descriptive figure" src="figures/'+name+'.png">'
    (output/'index.html').write_text(content+'</body></html>', encoding='utf8')
    return summary


def analyze_records(output, config=None, smoke=False):
    return report(load_records(output), Path(output), config=config, smoke=smoke)
