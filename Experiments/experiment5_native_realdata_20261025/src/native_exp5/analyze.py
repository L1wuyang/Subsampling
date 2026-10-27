"""All-draw summaries, paired inference, and separate target/prediction criteria."""
from .common import *
import pandas as pd
from scipy.stats import t,ttest_rel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator,FuncFormatter,NullLocator
import csv,html
COLORS=dict(UNI='#59606b',NORM='#8661a9',LEV='#248ac1',OPT='#c63e35')
METRICS=['relative_coefficient_error','relative_design_target_error','test_target_prediction_mse','test_response_mse','test_response_rmse']

def load_records(out):return pd.concat([pd.read_csv(p,float_precision='round_trip') for p in sorted((Path(out)/'draws').glob('*/*.csv'))],ignore_index=True)

def summarize(f):
    rows=[]
    for keys,g in f.groupby(['dataset','method','rule','budget'],sort=True):
        row=dict(zip(['dataset','method','rule','budget'],keys));row['n']=len(g);row['failures']=int((g.status!='complete').sum())
        for name in METRICS:
            a=g[name].to_numpy();mean=float(a.mean());se=float(a.std(ddof=1)/np.sqrt(len(a)));half=float(t.ppf(.975,len(a)-1)*se)
            row.update({name+'_mean':mean,name+'_se':se,name+'_lower':mean-half,name+'_upper':mean+half})
        a=g.relative_coefficient_error.to_numpy();row.update(median=float(np.median(a)),p99=float(np.quantile(a,.99)),maximum=float(a.max()),
            top_one_percent_share=float(np.sort(a)[-max(1,math.ceil(.01*len(a))):].sum()/a.sum()) if a.sum()>0 else 0.,
            theoretical_relative_mse=float(g.theoretical_relative_mse.iloc[0]),calibration=float(a.mean()/g.theoretical_relative_mse.iloc[0]),
            mean_unique_objects=float(g.unique_objects.mean()),step_bound_violation_fraction=float((~g.step_bound_observed).mean()))
        rows.append(row)
    return pd.DataFrame(rows)

def primary(f):
    rows=[]
    for tag,r in [('gdsc',749),('year',5000)]:
        for method in METHODS:
            g=f[(f.dataset==tag)&(f.budget==r)&(f.method==method)].set_index(['rule','rep'])
            a=g.loc['OPT','relative_coefficient_error'].sort_index().to_numpy()
            for rule in ['UNI','NORM','LEV']:
                b=g.loc[rule,'relative_coefficient_error'].sort_index().to_numpy();delta=a-b
                se=float(delta.std(ddof=1)/np.sqrt(len(delta)));width=float(t.ppf(.975,len(delta)-1)*se)
                p=float(ttest_rel(a,b,alternative='less').pvalue)
                if not np.isfinite(p):p=1. if np.all(delta==0) else (0. if delta.mean()<0 else 1.)
                rows.append(dict(dataset=tag,budget=r,method=method,comparison='OPT-minus-'+rule,n=len(delta),difference=float(delta.mean()),se=se,lower=float(delta.mean()-width),upper=float(delta.mean()+width),p_raw=p))
    order=np.argsort([q['p_raw'] for q in rows]);running=0.
    for j,i in enumerate(order):running=max(running,(len(rows)-j)*rows[i]['p_raw']);rows[i]['p_holm']=min(1.,running);rows[i]['supports_OPT_lower']=rows[i]['difference']<0 and rows[i]['p_holm']<.05
    return pd.DataFrame(rows)

def tail_figure(f):
    fig,axes=plt.subplots(3,4,figsize=(12,8.4),layout='constrained')
    for i,method in enumerate(METHODS):
        for j,(tag,r) in enumerate([('gdsc',749),('year',5000)]):
            ax=axes[i//2,(i%2)*2+j]
            for rule in RULES:
                if tag=='gdsc' and rule=='NORM':continue
                a=np.sort(f[(f.dataset==tag)&(f.method==method)&(f.rule==rule)&(f.budget==r)].relative_coefficient_error.to_numpy())
                ax.step(a,np.arange(len(a),0,-1)/len(a),where='post',color=COLORS[rule],label=rule)
            ax.set(title=method+' / '+tag,xscale='log',yscale='log',xlabel='Relative target squared error',ylabel='Empirical survival');ax.grid(alpha=.2)
            lo,hi=ax.get_xlim()
            ax.xaxis.set_major_locator(FixedLocator(np.geomspace(lo,hi,3)))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:.3g}'))
            ax.xaxis.set_minor_locator(NullLocator())
    handles,labels=axes.flat[-1].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=4,frameon=False)
    return fig

def main(args):
    out=Path(args.output).resolve() if args.output else HERE/'outputs/formal_01';assert read(out/'execution.json')['completed']
    f=load_records(out);assert len(f)==12720 and not f.duplicated(['dataset','method','rule','budget','rep']).any()
    if not np.isfinite(f[METRICS]).all().all():
        save(out/'failure_summary.json',dict(failed_records=int((f.status!='complete').sum()),unconditional_means_not_replaced_by_success_subset=True))
        raise RuntimeError('Nonfinite formal outputs retained: report unconditional failure before publishing finite-only curves.')
    s=summarize(f);s.to_csv(out/'summary.csv',index=False);pairs=primary(f);pairs.to_csv(out/'primary_comparisons.csv',index=False)
    wins=[]
    for keys,g in s.groupby(['dataset','method','budget']):
        best=g.loc[g.relative_coefficient_error_mean.idxmin()];opt=g[g.rule=='OPT'].iloc[0]
        wins.append(dict(dataset=keys[0],method=keys[1],budget=int(keys[2]),best_rule=best.rule,opt_lowest=bool(opt.relative_coefficient_error_mean<=g.relative_coefficient_error_mean.min()*(1+1e-13))))
    summary=dict(completed=True,records=len(f),status=f.status.value_counts().to_dict(),opt_lowest_cells=sum(q['opt_lowest'] for q in wins),method_budget_cells=len(wins),
        primary_comparisons=len(pairs),primary_holm_supports_lower=int(pairs.supports_OPT_lower.sum()),maximum_relative_target_error=float(f.relative_coefficient_error.max()),
        observed_step_bound_violations=int((~f.step_bound_observed).sum()),all_outputs_retained=True,known_true_coefficient=False,
        note='New native protocol; historical c and previously explored test split. Coefficient target error and test response risk are distinct. Not a speed benchmark.')
    save(out/'summary.json',summary);save(out/'rankings.json',wins)
    figs=out/'figures';figs.mkdir(exist_ok=True);plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'svg.fonttype':'none'})
    def emit(fig,name):
        for ext in ['pdf','svg','png']:fig.savefig(figs/(name+'.'+ext),bbox_inches='tight',dpi=150)
        plt.close(fig)
    for tag in ['gdsc','year']:
        fig,axes=plt.subplots(2,3,figsize=(10,6.2),layout='constrained')
        for ax,method in zip(axes.flat,METHODS):
            for rule in RULES:
                if tag=='gdsc' and rule=='NORM':continue
                g=s[(s.dataset==tag)&(s.method==method)&(s.rule==rule)].sort_values('budget')
                ax.plot(g.budget,g.relative_coefficient_error_mean,'o-',ms=3,color=COLORS[rule],label=rule)
                ax.fill_between(g.budget,np.maximum(g.relative_coefficient_error_lower,1e-300),g.relative_coefficient_error_upper,color=COLORS[rule],alpha=.12)
            ax.set(title=method,xscale='log',yscale='log',xlabel='Draws r',ylabel='Relative coefficient target MSE');ax.grid(alpha=.2)
        handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=4,frameon=False)
        emit(fig,'01_gdsc_target' if tag=='gdsc' else '02_year_target')
    fig,axes=plt.subplots(3,4,figsize=(12,8.4),layout='constrained')
    for i,method in enumerate(METHODS):
        for j,tag in enumerate(['gdsc','year']):
            ax=axes[i//2,(i%2)*2+j]
            for rule in RULES:
                if tag=='gdsc' and rule=='NORM':continue
                g=s[(s.dataset==tag)&(s.method==method)&(s.rule==rule)].sort_values('budget')
                ax.plot(g.budget,g.calibration,'o-',ms=2,color=COLORS[rule],label=rule)
            ax.axhline(1,color='black',ls='--',lw=.7);ax.set(title=method+' / '+tag,xscale='log',xlabel='Draws r',ylabel='Empirical MSE / (C/r)');ax.grid(alpha=.2)
    handles,labels=axes.flat[-1].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=4,frameon=False);emit(fig,'03_calibration')
    fig,axes=plt.subplots(3,4,figsize=(12,8.4),layout='constrained')
    for i,method in enumerate(METHODS):
        for j,tag in enumerate(['gdsc','year']):
            ax=axes[i//2,(i%2)*2+j];full=read(out/'targets'/tag/method/'summary.json')['full']['response_test_rmse']
            for rule in RULES:
                if tag=='gdsc' and rule=='NORM':continue
                g=s[(s.dataset==tag)&(s.method==method)&(s.rule==rule)].sort_values('budget')
                ax.plot(g.budget,g.test_response_rmse_mean,'o-',ms=2,color=COLORS[rule],label=rule)
            ax.axhline(full,color='black',ls='--',lw=.7,label='Matched full');ax.set(title=method+' / '+tag,xscale='log',xlabel='Draws r',ylabel='Mean individual test RMSE');ax.grid(alpha=.2)
    handles,labels=axes.flat[-1].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=5,frameon=False);emit(fig,'04_prediction')
    emit(tail_figure(f),'05_untrimmed_errors')
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for ax,tag in zip(axes,['gdsc','year']):
        for rule in RULES:
            if tag=='gdsc' and rule=='NORM':continue
            g=s[(s.dataset==tag)&(s.rule==rule)].groupby('budget',as_index=False).mean(numeric_only=True)
            ax.plot(g.budget,g.mean_unique_objects/g.budget,'o-',ms=3,label=rule,color=COLORS[rule])
        ax.set(title=tag,xscale='log',xlabel='Draws r',ylabel='Unique objects / draws');ax.grid(alpha=.2);ax.legend(fontsize=8)
    emit(fig,'06_coverage')
    page='<html><meta charset="utf-8"><title>Native real data V</title><body><h1>Native real-data experiment V</h1><pre>'+html.escape(json.dumps(summary,indent=2))+'</pre>'
    for p in sorted(figs.glob('*.png')):page+='<h2>'+p.stem+'</h2><img style="max-width:100%" src="figures/'+p.name+'">'
    (out/'index.html').write_text(page+'</body></html>',encoding='utf8');print('ANALYSIS_COMPLETE',summary,flush=True)
