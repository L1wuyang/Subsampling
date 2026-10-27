"""Descriptive first-order calibration, uncertainty, tails and separate risks."""
from .common import *
import pandas as pd
from scipy import stats
os.environ.setdefault('MPLCONFIGDIR', str(HERE/'outputs/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

COLOR = {'column':'#1765a3', 'row':'#b14a20'}


def main(args):
    out = Path(args.output).resolve() if args.output else HERE/'outputs/formal_01'
    assert json.loads((out/'execution.json').read_text(encoding='utf8'))['completed']
    main_frame = pd.read_csv(out/'results.csv')
    extra = pd.read_csv(out/'sensitivity_results.csv')
    frame = pd.concat([main_frame, extra], ignore_index=True)
    reference = pd.concat([pd.read_csv(out/'full_reference.csv'), pd.read_csv(out/'sensitivity_full_reference.csv')], ignore_index=True)
    refs = reference.set_index(['direction', 'data_id', 'arm', 'method'])
    rows, tails = [], []
    def all_mean(a):
        values = np.asarray(a)
        return float(np.mean(values)) if np.isfinite(values).all() else np.nan
    for key, group in frame.groupby(['direction', 'data_id', 'arm', 'method', 'budget'], sort=False):
        direction, did, arm, method, budget = key
        ref = refs.loc[(direction, did, arm, method)]
        errors = group.relative_gap.to_numpy()
        count = len(errors); finite = np.isfinite(errors)
        mean = all_mean(errors)
        se = float(errors.std(ddof=1)/np.sqrt(count)) if finite.all() else np.nan
        half = float(stats.t.ppf(.975, count-1)*se)
        theory = float(ref.C/budget) if np.isfinite(ref.C) and ref.C > 0 else np.nan
        record = dict(direction=direction, data_id=int(did), arm=arm, method=method, budget=int(budget),
                      count=count, finite_relative_count=int(finite.sum()), numerical_failures=int((group.status == 'numerical_failure').sum()),
                      mean=mean, se=se, halfwidth95=half, low95=mean-half, high95=mean+half,
                      C=ref.C, theory=theory, ratio=mean/theory,
                      ratio_low95=(mean-half)/theory, ratio_high95=(mean+half)/theory,
                      linear_mean=all_mean(group.linear_relative), remainder_mean=all_mean(group.remainder_relative), cross_mean=all_mean(group.cross_relative))
        for component in ['linear', 'remainder', 'cross']:
            record[component+'_ratio'] = record[component+'_mean']/theory
        for metric in ['absolute_gap', 'true_coef_rel_sq', 'design_signal_rel_sq', 'population_signal_rel_sq', 'population_response_mse', 'residual_norm']:
            record[metric] = all_mean(group[metric])
        with np.load(out/f'{direction}_{did:02d}'/arm/f'raw_r{budget}.npz') as raw, np.load(out/f'{direction}_{did:02d}'/arm/'native_states.npz') as state:
            delta = raw[method+'_state'].mean(axis=0)-state[method+'_target']
            bias_sq = float(delta @ state['metric'] @ delta)
            record['mc_mean_error_sq_relative'] = bias_sq/ref.target_norm_sq if ref.target_norm_sq > 1e-24 else np.nan
        rows.append(record)
        if arm != 'zero_response':
            sorted_errors = np.sort(errors)
            top = max(1, int(np.ceil(.01*count)))
            tails.append(dict(direction=direction, data_id=int(did), arm=arm, method=method, budget=int(budget),
                              mean=mean, median=float(np.median(errors)), p95=float(np.quantile(errors, .95)),
                              p99=float(np.quantile(errors, .99)), maximum=float(np.max(errors)),
                              top1pct_share=float(sorted_errors[-top:].sum()/errors.sum()),
                              min_unique=int(group.unique_objects.min()), mean_unique=float(group.unique_objects.mean()),
                              unique_below_60=int((group.unique_objects < 60).sum()), zero_spike_records=int((group.spike_draws == 0).sum())))
    summary_frame = pd.DataFrame(rows)
    summary_frame.to_csv(out/'mse_summary.csv', index=False)
    pd.DataFrame(tails).to_csv(out/'tails.csv', index=False)
    # Per-sketch extremes are archived; their inclusion is unconditional.
    main_frame.nlargest(50, 'relative_gap').to_csv(out/'extreme_records.csv', index=False)
    primary = summary_frame[(summary_frame.arm == 'main')&(summary_frame.data_id == 1)].copy()
    robust = summary_frame[(summary_frame.arm == 'main')&(summary_frame.budget.isin([1200, 19200]))]
    robustness = robust.groupby(['direction', 'method', 'budget']).agg(
        data_sets=('ratio', 'size'), minimum=('ratio', 'min'), median=('ratio', 'median'), maximum=('ratio', 'max'),
        mean=('ratio', 'mean'), remainder_median=('remainder_ratio', 'median')).reset_index()
    robustness.to_csv(out/'robustness_summary.csv', index=False)
    primary[primary.budget == 38400].to_csv(out/'endpoint_decomposition.csv', index=False)
    primary[primary.budget.isin([30, 1200, 38400])][['direction','method','budget','true_coef_rel_sq','design_signal_rel_sq','population_signal_rel_sq','population_response_mse']].to_csv(out/'separate_risks.csv', index=False)
    reference[reference.arm == 'main'].groupby(['direction', 'method'])[['alpha', 'L', 'steps', 'dt', 'T', 'C']].agg(['min', 'median', 'max']).to_csv(out/'parameter_summary.csv')
    figdir = out/'figures'; figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'axes.spines.top':False, 'axes.spines.right':False,
                         'pdf.fonttype':42, 'ps.fonttype':42, 'font.size':9})
    def finish(fig, name):
        for suffix in ['pdf', 'svg', 'png']:
            fig.savefig(figdir/(name+'.'+suffix), dpi=170, bbox_inches='tight')
        plt.close(fig)
    def paired_panels(name, ratio=False):
        fig, axes = plt.subplots(3, 4, figsize=(13.1, 8.6), constrained_layout=True)
        for mi, method in enumerate(METHODS):
            for di, direction in enumerate(DIRECTIONS):
                ax = axes[mi//2, (mi%2)*2+di]
                g = primary[(primary.method == method)&(primary.direction == direction)].sort_values('budget')
                color = COLOR[direction]
                values = g.ratio if ratio else g['mean']
                widths = g.halfwidth95/g.theory if ratio else g.halfwidth95
                ax.errorbar(g.budget, values, yerr=widths, color=color, marker='o', ms=3, lw=1.15, capsize=2, label='Native simulation')
                if ratio: ax.axhline(1, color='#333', ls='--', lw=1)
                else: ax.plot(g.budget, g.theory, color='#343434', ls='--', lw=1.2, label='First order C/r')
                ax.set_xscale('log'); ax.set_yscale('log')
                ax.set_xticks([30, 600, 1200, 38400]); ax.xaxis.set_major_formatter(ScalarFormatter())
                ax.tick_params(axis='x', labelsize=7, rotation=25)
                ax.set_title(method+' / '+direction, fontsize=10)
                ax.set_xlabel('Draws r'); ax.set_ylabel('Empirical / first order' if ratio else 'Relative target MSE')
                ax.grid(alpha=.15)
                if mi == 0 and di == 0 and not ratio: ax.legend(fontsize=7, loc='lower left')
        finish(fig, name)
    paired_panels('01_mse_absolute_compact')
    paired_panels('02_mse_ratio', True)
    for direction in DIRECTIONS:
        fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.4), constrained_layout=True)
        for ax, method in zip(axes.flat, METHODS):
            g = primary[(primary.direction == direction)&(primary.method == method)].sort_values('budget')
            for field, color, label, marker in [('ratio', '#222222', 'Total', 'o'), ('linear_ratio', '#1765a3', 'Linear', 's'),
                                                ('remainder_ratio', '#c25d1b', 'Squared remainder', '^'), ('cross_ratio', '#6b499c', 'Cross', 'v')]:
                ax.plot(g.budget, g[field], color=color, marker=marker, ms=3, lw=1.1, label=label)
            ax.axhline(0, color='#888', lw=.6); ax.axhline(1, color='#888', ls=':', lw=.7)
            ax.set_xscale('log'); ax.set_yscale('symlog', linthresh=.08)
            ax.set_yticks([-1, -.1, 0, .1, 1, 2])
            ax.set_yticklabels(['-1', '-0.1', '0', '0.1', '1', '2'])
            ax.set_title(method); ax.set_xlabel('Draws r'); ax.set_ylabel('Component / (C/r)')
            ax.grid(alpha=.15)
        axes.flat[0].legend(fontsize=7, ncol=2)
        finish(fig, '03_decomposition_column' if direction == 'column' else '04_decomposition_row')
    fig, axes = plt.subplots(1, 2, figsize=(11.3, 4.1), constrained_layout=True)
    for ax, direction in zip(axes, DIRECTIONS):
        for bi, budget in enumerate([1200, 19200]):
            values = robust[(robust.direction == direction)&(robust.budget == budget)]
            color = ['#1765a3','#b14a20'][bi]
            for mi, method in enumerate(METHODS):
                vals = values[values.method == method].ratio.to_numpy()
                x = mi+(bi-.5)*.23
                ax.scatter(x+np.linspace(-.035,.035,len(vals)), vals, s=12, color=color, alpha=.55, label=f'r = {budget}' if mi == 0 else None)
                ax.plot([x-.07, x+.07], [np.median(vals)]*2, color=color, lw=2)
        ax.axhline(1, color='#222', ls='--', lw=1); ax.set_xticks(range(6)); ax.set_xticklabels(METHODS, rotation=25)
        ax.set_title(direction.capitalize()+' / 20 independent data sets'); ax.set_ylabel('Empirical / first order'); ax.legend(fontsize=8)
    finish(fig, '05_between_dataset_calibration')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.1), constrained_layout=True)
    for ax, direction in zip(axes, DIRECTIONS):
        for method in METHODS:
            g = main_frame[(main_frame.direction == direction)&(main_frame.data_id == 1)&(main_frame.method == method)&(main_frame.budget == 1200)]
            x = np.sort(g.relative_gap.to_numpy()); survival = (len(x)-np.arange(len(x)))/len(x)
            ax.step(x, survival, where='post', lw=1.1, label=method)
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_title(direction.capitalize()+' / r = 1200')
        ax.set_xlabel('Single-sketch relative target error'); ax.set_ylabel('Empirical survival'); ax.legend(fontsize=7)
    finish(fig, '06_untrimmed_tails')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.3), constrained_layout=True)
    sensitivity = summary_frame[(summary_frame.arm.isin(['c_low','c_high']))&(summary_frame.budget == 19200)]
    for ax, direction in zip(axes, DIRECTIONS):
        for ai, (arm, label) in enumerate([('c_low','c = 0.5'),('c_high','c = 2')]):
            for mi, method in enumerate(METHODS):
                vals = sensitivity[(sensitivity.direction == direction)&(sensitivity.arm == arm)&(sensitivity.method == method)].ratio
                ax.scatter(np.full(len(vals), mi+(ai-.5)*.2), vals, color=['#1765a3','#b14a20'][ai], s=30,
                           label=label if mi == 0 else None)
        ax.axhline(1, color='#222', ls='--', lw=1); ax.set_xticks(range(6)); ax.set_xticklabels(METHODS, rotation=25)
        ax.set_title(direction.capitalize()+' / two data sets, r = 19200'); ax.set_ylabel('Empirical / first order'); ax.legend(fontsize=8)
    finish(fig, '07_scale_sensitivity')
    ranges = {}
    for direction in DIRECTIONS:
        ranges[direction] = {}
        for budget in [30, 1200, 19200, 38400]:
            g = primary[(primary.direction == direction)&(primary.budget == budget)]
            ranges[direction][str(budget)] = dict(min=float(g.ratio.min()), max=float(g.ratio.max()))
    summary = dict(main_rows=len(main_frame), sensitivity_rows=int((extra.arm != 'zero_response').sum()),
                   zero_rows=int((extra.arm == 'zero_response').sum()), total_rows=len(frame),
                   main_statuses=main_frame.status.value_counts().to_dict(), extra_statuses=extra.status.value_counts().to_dict(),
                   undefined_relative_gaps=int(frame.relative_gap.isna().sum()), primary_ratio_ranges=ranges,
                   maximum_main_relative_error=float(main_frame.relative_gap.max()),
                   numerical_failures=int((frame.status == 'numerical_failure').sum()),
                   maximum_absolute_decomposition_residual=float(frame.decomposition_absolute_error.max()),
                   primary_endpoint=primary[primary.budget == 38400][['direction','method','mean','theory','ratio','ratio_low95','ratio_high95','linear_ratio','remainder_ratio','cross_ratio']].to_dict('records'),
                   pointwise_intervals='Student t over all 500 conditional sketches, no simultaneous coverage or selection adjustment',
                   population_row_relative_equals_coefficient=True, figures=7,
                   interpretation='Native finite-grid targets and joint tangents; no fitted constants, no universal finite-budget claim, no speedup claim.')
    save(out/'summary.json', summary)
    images = '\n'.join(f'<section><h2>{p.stem}</h2><a href="figures/{p.stem}.pdf"><img src="figures/{p.name}"></a></section>' for p in sorted(figdir.glob('*.png')))
    (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Native Experiment III</title><style>body{max-width:1250px;margin:30px auto;font:16px system-ui;color:#202632}img{width:100%}section{margin:36px 0;border-top:1px solid #ddd}pre{white-space:pre-wrap}</style><h1>Experiment III: native first-order MSE calibration</h1><p>Six methods; uniform replacement sampling; column and row directions; fresh data. Both row Gram and response are sampled. Every native state and multiplicity retained. Theoretical C is computed from frozen native tangents before sketches.</p><pre>'+json.dumps(summary, indent=2)+'</pre>'+images+'</html>', encoding='utf8')
    print('ANALYSIS_COMPLETE', len(frame), json.dumps(ranges), flush=True)
