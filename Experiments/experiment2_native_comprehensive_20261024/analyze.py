from common import HERE,OUT,ROOT,save,load
from native import METHODS,RULES
import numpy as np,pandas as pd
from scipy import stats
import os
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'outputs/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import json,shutil
COLORS=dict(UNI='#667085',NORM='#0077B6',LEV='#E69F00',OPT='#C23B45')
MARKERS=dict(UNI='o',NORM='s',LEV='^',OPT='D')

def primary_tests(means):
    rows=[]
    for method in METHODS:
        p=means[(means.method==method)&(means.budget==150)].pivot(index='data_id',columns='rule',values='relative_gap')
        for rule in RULES[:3]:
            d=p.OPT-p[rule];n=len(d);se=d.std(ddof=1)/np.sqrt(n);mean=d.mean()
            t,pv=stats.ttest_1samp(d,0);q=stats.t.ppf(.975,n-1);qs=stats.t.ppf(1-.05/36,n-1)
            rows.append(dict(method=method,baseline=rule,n=n,mean_difference=mean,se=se,
                             ci_low=mean-q*se,ci_high=mean+q*se,simultaneous_low=mean-qs*se,simultaneous_high=mean+qs*se,
                             t=t,p_raw=pv,ratio=p.OPT.mean()/p[rule].mean(),datasets_OPT_lower=int((d<0).sum())))
    df=pd.DataFrame(rows);order=np.argsort(df.p_raw.to_numpy());adjusted=np.maximum.accumulate((len(df)-np.arange(len(df)))*df.p_raw.to_numpy()[order]);vals=np.empty(len(df));vals[order]=np.minimum(adjusted,1)
    df['p_holm']=vals;df['decision']=np.where((df.p_holm<.05)&(df.mean_difference<0),'lower',np.where((df.p_holm<.05)&(df.mean_difference>0),'higher','inconclusive'))
    return df

def panels():
    fig,axs=plt.subplots(2,3,figsize=(9.3,5.9));fig.subplots_adjust(left=.08,right=.985,bottom=.13,top=.90,wspace=.30,hspace=.40)
    for ax,method in zip(axs.flat,METHODS):
        ax.set_title(method,fontsize=12,fontweight='semibold');ax.grid(True,alpha=.18,linewidth=.5);ax.tick_params(labelsize=9)
    return fig,axs
def finish(fig,name,handles=None,labels=None):
    if handles:fig.legend(handles,labels,loc='upper center',ncol=4,frameon=False,fontsize=10,bbox_to_anchor=(.52,1.005))
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    for ext in ['pdf','png','svg']:fig.savefig(folder/(name+'.'+ext),dpi=220,metadata={'Creator':'native Experiment II'} if ext=='pdf' else None)
    plt.close(fig)

def curve_plot(curves,metric,name,ylabel,log=True,reference=False):
    fig,axs=panels();handles=[]
    for mi,(ax,method) in enumerate(zip(axs.flat,METHODS)):
        for rule in RULES:
            s=curves[(curves.method==method)&(curves.rule==rule)&(curves.metric==metric)].sort_values('budget')
            h,=ax.plot(s.budget,s['mean'],color=COLORS[rule],marker=MARKERS[rule],ms=3,lw=1.4,label=rule)
            lower=s.ci_low.to_numpy();upper=s.ci_high.to_numpy()
            if log:lower=np.maximum(lower,np.maximum(s['mean'].to_numpy()*1e-6,1e-15))
            ax.fill_between(s.budget,lower,upper,color=COLORS[rule],alpha=.13,lw=0)
            if mi==0:handles.append(h)
        if reference:ax.axhline(1,color='#222',ls=':',lw=1)
        if log:ax.set_yscale('log')
        ax.set_xscale('log');ax.set_xticks([30,60,150,300,600]);ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.set_xlabel('Sampling budget r',fontsize=10);ax.set_ylabel(ylabel,fontsize=10)
    finish(fig,name,handles,RULES)

def main():
    execution=json.loads((OUT/'execution.json').read_text(encoding='utf8'));assert execution['completed']
    config=json.loads((OUT/'protocol.json').read_text(encoding='utf8'));df=pd.read_csv(OUT/'results.csv');extra=pd.read_csv(OUT/'sensitivity_results.csv')
    assert len(df)==config['replication_counts']['main'];assert not df.select_dtypes('number').isna().any().any()
    assert np.isfinite(df.select_dtypes('number')).all().all(), 'Retain failures but do not produce success-only inferential means'
    metrics=['absolute_gap','relative_gap','true_coef_rel_sq','design_signal_rel_sq','population_signal_rel_sq','population_response_mse','design_spike_rel_sq','design_background_rel_sq','residual_norm']
    means=df.groupby(['data_id','method','rule','budget'])[metrics].mean().reset_index();means.to_csv(OUT/'dataset_means.csv',index=False)
    curves=[]
    for (method,rule,r),g in means.groupby(['method','rule','budget']):
        for metric in metrics:
            x=g[metric];se=x.std(ddof=1)/np.sqrt(len(x));q=stats.t.ppf(.975,len(x)-1)
            curves.append(dict(method=method,rule=rule,budget=r,metric=metric,n=len(x),mean=x.mean(),se=se,ci_low=x.mean()-q*se,ci_high=x.mean()+q*se))
    curves=pd.DataFrame(curves);curves.to_csv(OUT/'summary_curves.csv',index=False)
    tests=primary_tests(means);tests.to_csv(OUT/'primary_comparisons.csv',index=False)
    ratios=[]
    for (method,r),g in means.groupby(['method','budget']):
        p=g.pivot(index='data_id',columns='rule',values='relative_gap')
        for rule in RULES[:3]:
            loo=(p.OPT.sum()-p.OPT)/(p[rule].sum()-p[rule]);ratios.append(dict(method=method,budget=r,baseline=rule,ratio=p.OPT.mean()/p[rule].mean(),datasets_lower=int((p.OPT<p[rule]).sum()),loo_min=loo.min(),loo_max=loo.max()))
    ratios=pd.DataFrame(ratios);ratios.to_csv(OUT/'mean_ratios_and_leave_one_out.csv',index=False)
    tails=[]
    for (method,rule,r),g in df.groupby(['method','rule','budget']):
        x=g.relative_gap.to_numpy();top=max(1,int(np.ceil(.01*len(x))))
        tails.append(dict(method=method,rule=rule,budget=r,n=len(x),mean=x.mean(),median=np.median(x),p90=np.quantile(x,.9),p95=np.quantile(x,.95),p99=np.quantile(x,.99),maximum=x.max(),top_1pct_share=np.sort(x)[-top:].sum()/x.sum()))
    tails=pd.DataFrame(tails);tails.to_csv(OUT/'tails.csv',index=False)
    df.nlargest(60,'relative_gap').to_csv(OUT/'extreme_records.csv',index=False)
    ref=pd.read_csv(OUT/'full_reference.csv');tr=pd.read_csv(OUT/'local_trace.csv')
    residual=df[['data_id','method','rule','budget','rep','residual_norm']].copy()
    for did in config['data_ids']:
        with np.load(HERE/'data'/f'data_{did:02d}.npz') as a:noise=.5*np.linalg.norm(a['standard_noise'])
        residual.loc[residual.data_id==did,'noise_norm']=noise
    residual['full_ratio']=residual.residual_norm/residual.noise_norm
    residual['diagnostic_dp_met']=residual.full_ratio<=1.01+1e-12
    residual.to_csv(OUT/'residual_diagnostics.csv',index=False)
    residual.groupby(['method','rule','budget']).agg(n=('diagnostic_dp_met','size'),met=('diagnostic_dp_met','sum'),rate=('diagnostic_dp_met','mean'),mean_ratio=('full_ratio','mean'),max_ratio=('full_ratio','max')).to_csv(OUT/'residual_summary.csv')
    bound_rows=[]
    for did in config['data_ids']:
        h=json.loads((OUT/f'data_{did:02d}/main/bound_history.json').read_text(encoding='utf8'))
        bound_rows.append(dict(data_id=did,trials=len(h),initial_L=h[0]['L'],final_L=h[-1]['L'],required=h[-1]['required']))
    pd.DataFrame(bound_rows).to_csv(OUT/'bound_construction.csv',index=False)
    ref.groupby('method')[['alpha','steps','dt','T','target_norm_sq']].agg(['min','mean','max']).reindex(METHODS).to_csv(OUT/'parameter_summary.csv')
    trace_rat=tr.pivot(index=['data_id','method'],columns='rule',values='local_trace');trace_rat=trace_rat.div(trace_rat.OPT,axis=0).groupby('method').mean().reindex(METHODS)
    trace_rat.to_csv(OUT/'local_trace_ratios.csv')
    risk=df[df.budget==600].groupby(['method','rule'])[metrics].mean().reset_index();risk.to_csv(OUT/'risk_r600.csv',index=False)
    exmeans=extra.groupby(['arm','data_id','method','rule','budget'])[metrics].mean().reset_index();exmeans.to_csv(OUT/'sensitivity_dataset_means.csv',index=False)
    exrat=[]
    for (arm,method,r),g in exmeans[exmeans.arm!='zero_response'].groupby(['arm','method','budget']):
        p=g.pivot(index='data_id',columns='rule',values='relative_gap')
        for rule in RULES[:3]:exrat.append(dict(arm=arm,method=method,budget=r,baseline=rule,ratio=p.OPT.mean()/p[rule].mean(),datasets_lower=int((p.OPT<p[rule]).sum()),n=len(p)))
    exrat=pd.DataFrame(exrat);exrat.to_csv(OUT/'sensitivity_ratios.csv',index=False)
    cal=means.merge(tr[['data_id','method','rule','normalized_trace']],on=['data_id','method','rule']);cal['calibration']=cal.relative_gap*cal.budget/cal.normalized_trace
    cal.to_csv(OUT/'first_order_calibration.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    curve_plot(curves,'relative_gap','01_target_approximation','Relative target MSE')
    curve_plot(curves,'true_coef_rel_sq','03_true_coefficient_risk','Relative coefficient risk',log=False,reference=True)
    curve_plot(curves,'design_signal_rel_sq','04_design_signal_risk','Relative in-design\nsignal risk',log=False,reference=True)
    curve_plot(curves,'population_response_mse','05_population_response_mse','Future response MSE',log=False,reference=False)
    fig,axs=panels();handles=[]
    for mi,(ax,method) in enumerate(zip(axs.flat,METHODS)):
        for rule in RULES[:3]:
            s=ratios[(ratios.method==method)&(ratios.baseline==rule)].sort_values('budget');h,=ax.plot(s.budget,s.ratio,color=COLORS[rule],marker=MARKERS[rule],ms=3,lw=1.4)
            ax.fill_between(s.budget,s.loo_min,s.loo_max,color=COLORS[rule],alpha=.13)
            if mi==0:handles.append(h)
        ax.axhline(1,color='#222',ls=':',lw=1);ax.set_xscale('log');ax.set_xticks([30,60,150,300,600]);ax.xaxis.set_major_formatter(ScalarFormatter());ax.set_xlabel('Sampling budget r',fontsize=10);ax.set_ylabel('OPT / baseline mean MSE',fontsize=10)
    finish(fig,'02_mean_ratios',handles,RULES[:3])
    fig,axs=panels();handles=[]
    for mi,(ax,method) in enumerate(zip(axs.flat,METHODS)):
        for rule in RULES:
            x=np.sort(df[(df.method==method)&(df.rule==rule)&(df.budget==150)].relative_gap.to_numpy());surv=(len(x)-np.arange(len(x)))/len(x)
            h,=ax.step(x,surv,where='post',color=COLORS[rule],lw=1.3)
            if mi==0:handles.append(h)
        ax.set_xscale('log');ax.set_yscale('log');ax.set_ylim(1/1600,1.05);ax.set_xlabel('Single-sketch relative gap',fontsize=10);ax.set_ylabel('Empirical survival at r = 150',fontsize=10)
    finish(fig,'06_untrimmed_tails',handles,RULES)
    fig,axs=panels();handles=[];armnames=[a['tag'] for a in config['arms'][1:-1]]
    for mi,(ax,method) in enumerate(zip(axs.flat,METHODS)):
        for j,rule in enumerate(RULES[:3]):
            s=exrat[(exrat.method==method)&(exrat.baseline==rule)&(exrat.budget==150)].set_index('arm').loc[armnames];h,=ax.plot(np.arange(len(armnames)),s.ratio,color=COLORS[rule],marker=MARKERS[rule],ms=4,linestyle='None')
            if mi==0:handles.append(h)
        ax.axhline(1,color='#222',ls=':',lw=1);ax.set_xticks(range(8));ax.set_xticklabels(['Noise .1','Noise 1','Scale .5','Scale 2','Floor .005','Floor .05','No spikes','Spike 12'],rotation=50,ha='right',fontsize=7);ax.set_ylabel('OPT / baseline at r = 150',fontsize=10)
    fig.subplots_adjust(bottom=.18,hspace=.85);finish(fig,'07_robustness',handles,RULES[:3])
    fig,axs=panels();handles=[]
    for mi,(ax,method) in enumerate(zip(axs.flat,METHODS)):
        for rule in RULES:
            s=cal[(cal.method==method)&(cal.rule==rule)].groupby('budget').calibration.mean();h,=ax.plot(s.index,s.values,color=COLORS[rule],marker=MARKERS[rule],ms=3,lw=1.4)
            if mi==0:handles.append(h)
        ax.axhline(1,color='#222',ls=':',lw=1);ax.set_xscale('log');ax.set_xticks([30,60,150,300,600]);ax.xaxis.set_major_formatter(ScalarFormatter());ax.set_xlabel('Sampling budget r',fontsize=10);ax.set_ylabel('Empirical / first-order MSE',fontsize=10)
    finish(fig,'08_first_order_calibration',handles,RULES)
    success=ratios.groupby(['method','budget']).ratio.max()<1
    summary=dict(main_rows=len(df),robustness_rows=int((extra.arm!='zero_response').sum()),zero_rows=int((extra.arm=='zero_response').sum()),
                 methods_budgets_OPT_lowest=int(success.sum()),method_budget_cells=len(success),
                 mean_reversals=ratios[ratios.ratio>=1].to_dict('records'),primary_decisions=tests.decision.value_counts().to_dict(),
                 main_statuses=df.status.value_counts().to_dict(),sensitivity_statuses=extra.status.value_counts().to_dict(),
                 undefined_relative_gaps=int(extra.relative_gap.isna().sum()),max_main_relative_gap=float(df.relative_gap.max()),
                 terminal_residual_diagnostic_not_met=int((~residual.diagnostic_dp_met).sum()),
                 main_execution_seconds=execution['seconds'],population_relative_equals_coefficient=True,zero_spike_draw_records=int((df.spike_draws==0).sum()),unique_rows_less_than_p=int((df.unique_rows<60).sum()),
                 opt_r600_risks=risk[risk.rule=='OPT'][['true_coef_rel_sq','design_signal_rel_sq','population_signal_rel_sq','population_response_mse','relative_gap']].mean().to_dict(),
                 full_target_risks=ref[['true_coef_rel_sq','design_signal_rel_sq','population_signal_rel_sq','population_response_mse']].mean().to_dict(),
                 robustness_mean_reversals=exrat[exrat.ratio>=1].to_dict('records'))
    save(OUT/'summary.json',summary)
    images='\n'.join(f'<section><h2>{p.stem}</h2><a href="figures/{p.stem}.pdf"><img src="figures/{p.name}"></a></section>' for p in sorted((OUT/'figures').glob('*.png')))
    (OUT/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Native Experiment II</title><style>body{max-width:1180px;margin:32px auto;font:16px system-ui;color:#202632}img{width:100%}section{margin:36px 0;border-top:1px solid #ddd}pre{white-space:pre-wrap}</style><h1>Experiment II: fixed-parameter native row sampling</h1><p>40 independent spiked-row data sets; 13 budgets; 40 paired sketches. Gram and response are both sampled. All outcomes retained. Population relative signal risk equals coefficient risk in this isotropic mixture. New draft only; historical versions preserved.</p><pre>'+json.dumps(summary,indent=2)+'</pre>'+images+'</html>',encoding='utf8')
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
