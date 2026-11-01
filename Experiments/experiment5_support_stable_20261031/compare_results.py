"""Independently validate and compare a completed support-stable V run."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
import pandas as pd


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--historical-root',type=Path,required=True)
    parser.add_argument('--wait',action='store_true')
    args=parser.parse_args();out=args.output;old=args.historical_root
    while args.wait and not (out/'results.json').exists():
        time.sleep(30)
    assert read(out/'results.json')['completed']
    assert read(out/'support_gate.json')['passed']
    for rel,expected in read(out/'target_manifest.json').items():
        with (out/rel).open('rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==expected,rel
    data=pd.concat([pd.read_csv(p) for p in (out/'draws').glob('*/*.csv')],ignore_index=True)
    assert len(data)==12720 and len(data.groupby(['dataset','budget','rep']))==530
    assert not data.duplicated(['dataset','method','rule','budget','rep']).any()
    assert data.status.eq('complete').all() and np.isfinite(data.relative_coefficient_error).all()
    assert (data.relative_coefficient_error>=0).all()
    for ds,rep in [('gdsc',30),('year',50)]:
        assert data.loc[data.dataset==ds].groupby(['method','rule','budget']).size().eq(rep).all()
    keys=['dataset','method','rule','budget']
    actual=data.groupby(keys,as_index=False).relative_coefficient_error.mean().rename(columns={'relative_coefficient_error':'new_mean'})
    history=pd.read_csv(old/'outputs/formal_01/summary.csv')
    merged=actual.merge(history[keys+['relative_coefficient_error_mean','calibration']],on=keys,validate='one_to_one')
    merged=merged.rename(columns={'relative_coefficient_error_mean':'old_mean','calibration':'old_calibration'})
    merged=merged.merge(pd.read_csv(out/'summary.csv')[keys+['empirical_to_first_order']],on=keys,validate='one_to_one')
    merged['new_over_old_mean']=merged.new_mean/merged.old_mean
    merged.to_csv(out/'old_new_comparison.csv',index=False)
    target_changes=[]
    for ds in ('gdsc','year'):
        C=np.load(out/'targets'/ds/'C.npy')
        for method in ['Ridge','Landweber','Showalter','HBF','Nesterov','SOAR']:
            before=np.load(old/'outputs/formal_01/targets'/ds/method/'target.npy')
            after=np.load(out/'targets'/ds/method/'target.npy')
            target_changes.append(dict(dataset=ds,method=method,
                relative_target_change=float(np.linalg.norm(C@(after-before))/np.linalg.norm(C@before))))
    pd.DataFrame(target_changes).to_csv(out/'target_changes.csv',index=False)
    wins=[]
    for key,g in actual.groupby(['dataset','method','budget']):
        wins.append(dict(dataset=key[0],method=key[1],budget=int(key[2]),
                         opt_lowest=bool(g.loc[g.rule=='OPT','new_mean'].iloc[0]<g.loc[g.rule!='OPT','new_mean'].min())))
    validation=dict(passed=True,records=len(data),tasks=530,cells=len(wins),
                    opt_lowest_cells=sum(x['opt_lowest'] for x in wins),
                    exceptions=[x for x in wins if not x['opt_lowest']],
                    full_conditional_mse_ordering_inferred=False)
    (out/'independent_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors={'UNI':'#3676b5','NORM':'#e39532','LEV':'#39965c','OPT':'#bd3f48'}
    fig,axes=plt.subplots(2,3,figsize=(13,7.5),layout='constrained')
    for row,ds in enumerate(('gdsc','year')):
        for col,method in enumerate(('Landweber','Showalter','Nesterov')):
            ax=axes[row,col]
            for rule,color in colors.items():
                v=merged[(merged.dataset==ds)&(merged.method==method)&(merged.rule==rule)].sort_values('budget')
                ax.loglog(v.budget,v.new_mean,'o-',color=color,label=rule+' stable')
                ax.loglog(v.budget,v.old_mean,'--',color=color,alpha=.5)
            ax.set_title(ds+' / '+method);ax.set_xlabel('Sampling budget');ax.set_ylabel('Empirical relative squared error');ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8)
    fig.savefig(out/'old_new_comparison.png',dpi=180);fig.savefig(out/'old_new_comparison.pdf')
    rows=merged[merged.rule.isin(['UNI','OPT'])].copy()
    rows=rows[rows.apply(lambda r:int(r.budget)==(2996 if r.dataset=='gdsc' else 50000),axis=1)]
    text=['# Stable Experiment V results', '',
          'Completed fresh full-size run: 12,720 metrics, 530 sketches, all support gates passed.',
          f'OPT has the lowest observed mean in {validation["opt_lowest_cells"]}/78 cells.', '',
          'The old and new runs use different seeds and, for three methods, different numerical targets. Mean changes cannot be attributed solely to the step size.', '',
          '| Data | Method | Rule | Old mean | New mean | New first-order ratio |',
          '|---|---|---|---:|---:|---:|']
    for r in rows.itertuples():
        text.append(f'| {r.dataset} | {r.method} | {r.rule} | {r.old_mean:.9g} | {r.new_mean:.9g} | {r.empirical_to_first_order:.6g} |')
    text+=['', 'Stability excludes the identified exponential numerical amplification. It does not by itself certify finite-budget full MSE ordering.', '',
           'See independent_validation.json, support_gate.json, old_new_comparison.csv and target_changes.csv.']
    (out/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print(json.dumps(validation,indent=2),flush=True)


if __name__=='__main__':main()
