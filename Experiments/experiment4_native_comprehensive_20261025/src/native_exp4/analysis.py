"""Untrimmed statistics, resolution diagnostics, and separate real risks."""
from .common import *
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import html
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'svg.fonttype':'none'})
def load_records(out):
    files=sorted(out.glob('*_*/*/r*_c*.csv'))
    return pd.concat([pd.read_csv(p,float_precision='round_trip') for p in files],ignore_index=True)
def stats(values):
    a=np.asarray(values,float)
    assert np.isfinite(a).all(),'Nonfinite output retained in raw archive; an unconditional mean cannot be replaced by the successful subset.'
    if not len(a):return dict(n=0,mean=None,se=None,lower=None,upper=None,median=None,p99=None,maximum=None,top_one_percent_share=None)
    mean=float(np.mean(a));se=float(np.std(a,ddof=1)/np.sqrt(len(a))) if len(a)>1 else 0.;delta=float(t.ppf(.975,len(a)-1)*se) if len(a)>1 else 0.
    return dict(n=len(a),mean=mean,se=se,lower=mean-delta,upper=mean+delta,median=float(np.median(a)),p99=float(np.quantile(a,.99)),maximum=float(a.max()),top_one_percent_share=float(np.sort(a)[-max(1,math.ceil(.01*len(a))):].sum()/a.sum()) if a.sum()>0 else 0.)
def main(args):
    out=Path(args.output).resolve() if args.output else HERE/'outputs/formal_01';config=read(out/'protocol.json')
    execution=read(out/'execution.json');assert execution['completed']
    f=load_records(out);assert len(f)==execution['records']
    assert not f.duplicated(['direction','data_id','arm','budget','rep','method']).any()
    rows=[]
    for keys,g in f.groupby(['direction','data_id','arm','method','budget'],sort=True):
        base=dict(zip(['direction','data_id','arm','method','budget'],keys));base.update(stats(g.scaled_squared_gap))
        base.update(relative_mean=float(g.relative_squared_gap.mean()) if g.relative_squared_gap.notna().any() else None,
            resolution_limited_fraction=float(g.resolution_limited.mean()),rank_deficient_fraction=float((g['rank']<60).mean()),
            coefficient_risk=float(g.true_coef_rel_sq.mean()),design_risk=float(g.design_signal_rel_sq.mean()),population_risk=float(g.population_signal_rel_sq.mean()),response_mse=float(g.population_response_mse.mean()))
        rows.append(base)
    summary_frame=pd.DataFrame(rows);summary_frame.to_csv(out/'gap_summary.csv',index=False)
    primary=summary_frame[(summary_frame.arm=='main')&(summary_frame.data_id==1)]
    endpoints=[]
    for direction in DIRECTIONS:
        for method in METHODS:
            g=primary[(primary.direction==direction)&(primary.method==method)].set_index('budget')
            endpoints.append(dict(direction=direction,method=method,at_1200=float(g.loc[1200,'mean']),at_38400=float(g.loc[38400,'mean']),endpoint_ratio=float(g.loc[38400,'mean']/g.loc[1200,'mean']) if g.loc[1200,'mean']>0 else None,resolution_limited_at_38400=float(g.loc[38400,'resolution_limited_fraction'])))
    write(out/'endpoint_comparison.csv',endpoints)
    mainframe=f[f.arm=='main'];zero=f[f.arm=='zero_response'];tail=f[f.arm=='tails']
    groups=[]
    for keys,g in f.groupby(['direction','data_id','arm','budget'],sort=True):
        first=g[g.method==g.method.iloc[0]]
        groups.append(dict(zip(['direction','data_id','arm','budget'],keys))|dict(sketches=len(first),rank_deficient=int((first['rank']<60).sum()),minimum_rank=int(first['rank'].min()),minimum_unique=int(first.unique_objects.min())))
    write(out/'coverage_summary.csv',groups)
    report=dict(completed=True,records=len(f),main_records=len(mainframe),tail_records=len(tail),zero_records=len(zero),status=f.status.value_counts().to_dict(),
        zero_relative_undefined=int(zero.relative_squared_gap.isna().sum()),primary_endpoint_comparisons=endpoints,
        numerical_failure_records=int((f.status=='numerical_failure').sum()),maximum_main_scaled_gap=float(mainframe.scaled_squared_gap.max()),maximum_tail_scaled_gap=float(tail.scaled_squared_gap.max()),
        primary_repetitions=config['main']['repetitions'],robustness_repetitions=config['robustness']['repetitions'],tail_repetitions=config['tails']['repetitions'],
        prescribed_native_updates=int(f.executed_steps.sum()),RK4_rhs_evaluations=int(4*f[f.method.isin(['Showalter','HBF','SOAR'])].executed_steps.sum()),
        note='No trimming. Tiny direct subtractions are resolution diagnostics, not analytic residual estimates. Different frozen data/protocol from the legacy spectral study.')
    save(out/'summary.json',report)
    figdir=out/'figures';figdir.mkdir(exist_ok=True)
    def emit(fig,name):
        fig.savefig(figdir/(name+'.pdf'),bbox_inches='tight');fig.savefig(figdir/(name+'.svg'),bbox_inches='tight');fig.savefig(figdir/(name+'.png'),dpi=145,bbox_inches='tight');plt.close(fig)
    for name,field,label in [('01_scaled_gap','mean',r'$r\,\mathrm{mean}\|\widehat\beta-\widehat\beta_{LS}\|^2$'),('02_relative_gap','relative_mean','Relative squared gap to LS')]:
        fig,axes=plt.subplots(3,4,figsize=(12,8.2),layout='constrained')
        for i,method in enumerate(METHODS):
            for j,direction in enumerate(DIRECTIONS):
                ax=axes[i//2,(i%2)*2+j];g=primary[(primary.direction==direction)&(primary.method==method)].sort_values('budget')
                x=g.budget.to_numpy();y=g[field].to_numpy();color='#1669a6' if j==0 else '#ce5326'
                ax.plot(x,y,'o-',ms=3,color=color,lw=1);ax.set(xscale='log',yscale='log',title=method+' / '+direction,xlabel='Draws r',ylabel=label)
                if field=='mean':
                    for _,q in g.iterrows():
                        if q.lower>0:ax.vlines(q.budget,q.lower,q.upper,color=color,lw=.7)
                ax.grid(alpha=.18);ax.set_xticks([30,600,38400],['30','600','38400'])
                if method=='Nesterov':
                    ax.text(.03,.04,'Check replay / gap diagnostics',transform=ax.transAxes,fontsize=7,color='#6d2945')
        emit(fig,name)
    fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    for ax,direction in zip(axes,DIRECTIONS):
        for method in METHODS:
            g=primary[(primary.direction==direction)&(primary.method==method)].sort_values('budget')
            ax.plot(g.budget,g.resolution_limited_fraction,'o-',ms=3,label=method)
        ax.set(xscale='log',ylim=(-.03,1.03),title=direction,xlabel='Draws r',ylabel='Fraction at arithmetic resolution floor');ax.grid(alpha=.2);ax.legend(fontsize=7)
    emit(fig,'03_resolution')
    fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    for ax,direction in zip(axes,DIRECTIONS):
        for i,method in enumerate(METHODS):
            for did in config['data_ids']:
                g=summary_frame[(summary_frame.direction==direction)&(summary_frame.method==method)&(summary_frame.data_id==did)&(summary_frame.arm=='main')].set_index('budget')
                ratio=g.loc[19200,'mean']/g.loc[1200,'mean'];ax.scatter(i+.045*(did-3),ratio,s=20,color='#1669a6')
        ax.axhline(1,color='black',ls='--',lw=.8);ax.set(yscale='log',title=direction,xlabel='Method',ylabel=r'$D(19200)/D(1200)$');ax.set_xticks(range(6),METHODS,rotation=30);ax.grid(axis='y',alpha=.2)
    emit(fig,'04_between_dataset_decline')
    fig,axes=plt.subplots(2,3,figsize=(11,6),layout='constrained')
    for i,direction in enumerate(DIRECTIONS):
        for j,method in enumerate(config['tails']['methods']):
            ax=axes[i,j];g=tail[(tail.direction==direction)&(tail.method==method)];x=np.sort(g.scaled_squared_gap.to_numpy());s=np.arange(len(x),0,-1)/len(x)
            ax.step(x,s,where='post',lw=1,color='#1669a6');ax.set(xscale='log',yscale='log',title=method+' / '+direction,xlabel='Scaled squared gap, r=60',ylabel='Empirical survival');ax.grid(alpha=.2)
    emit(fig,'05_untrimmed_tails')
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    for ax,direction in zip(axes,DIRECTIONS):
        g=primary[(primary.direction==direction)&(primary.budget==38400)].set_index('method').loc[METHODS]
        ax.plot(range(6),g.coefficient_risk,'o-',label='Coefficient risk');ax.plot(range(6),g.design_risk,'s-',label='Design signal risk');ax.plot(range(6),g.population_risk,'^-',label='Population signal risk')
        ax.axhline(1,color='black',ls='--',lw=.7);ax.set(title=direction,xlabel='Method',ylabel='Relative squared risk',yscale='log');ax.set_xticks(range(6),METHODS,rotation=30);ax.grid(alpha=.2);ax.legend(fontsize=7)
    emit(fig,'06_separate_risks')
    text='<html><meta charset="utf-8"><title>Native experiment IV</title><body><h1>Native IV: actual trajectories versus same-draw QR LS</h1><p>All outputs retained. Numerical resolution and long-time integration checks are reported separately.</p><pre>'+html.escape(json.dumps(report,ensure_ascii=False,indent=2))+'</pre>'
    for p in sorted(figdir.glob('*.png')):text+='<h2>'+p.stem+'</h2><img style="max-width:100%" src="figures/'+p.name+'">'
    (out/'index.html').write_text(text+'</body></html>',encoding='utf8')
    print('ANALYSIS_COMPLETED',len(f),flush=True)
