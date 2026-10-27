"""Separate local subtraction floors, selected replays and tail concentration.

This analysis writes a new diagnostic directory. It never rewrites formal
states, gap means, sampling laws, or paper figures. False floor flags or small
selected replay differences are not numerical-accuracy certificates.

    python -m repro1026.iv_diagnostics --output runs/IV_diagnostics
"""
from __future__ import annotations
import os
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
import pandas as pd
from numba import njit

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_INPUT=ROOT/'Experiments/experiment4_native_comprehensive_20261025/outputs/formal_01'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


@njit(cache=False)
def dense_nesterov(A,c,steps,h):
    state=np.zeros(len(c));previous=np.zeros(len(c))
    for j in range(1,steps+1):
        extrapolated=state+max(j-2,0)/j*(state-previous)
        updated=extrapolated+h*(c-A@extrapolated)
        previous=state
        state=updated
    return state


def save(path,value):
    def default(q):
        if isinstance(q,np.generic):return q.item()
        if isinstance(q,np.ndarray):return q.tolist()
        raise TypeError(type(q).__name__)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=default)+'\n',encoding='utf8')


def diagnose(input_dir: Path, output: Path, *, replay: str='dense', warning_ratio: float=.1) -> dict:
    input_dir=input_dir.expanduser().resolve();output=output.expanduser().resolve()
    if not input_dir.is_dir():raise FileNotFoundError(input_dir)
    for name in ['Experiments','Data','Paper_Versions','provenance','repro1026']:
        protected=ROOT/name
        if output==protected or output.is_relative_to(protected):
            raise ValueError(f'Diagnostic output is inside protected package input: {output}')
    if output==input_dir or output.is_relative_to(input_dir) or output==ROOT or ROOT.is_relative_to(output):
        raise ValueError('Diagnostic output must be outside its inputs and package parents')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError(f'Diagnostic output must be new or empty: {output}')
    output.mkdir(parents=True,exist_ok=True)
    tick=time.perf_counter();manifest={}
    def mark(path):manifest[path.relative_to(input_dir).as_posix()]=sha(path)
    protocol=json.loads((input_dir/'protocol.json').read_text(encoding='utf8'));mark(input_dir/'protocol.json')
    parameters=pd.read_csv(input_dir/'parameters.csv',float_precision='round_trip');mark(input_dir/'parameters.csv')
    frames=[];replays=[];record_diagnostics=[]
    archived=None
    if replay=='saved':
        verification=input_dir/'verification.json'
        if not verification.is_file():raise FileNotFoundError('Saved replay mode requires verification.json; use --replay dense for new smoke outputs.')
        archived=json.loads(verification.read_text(encoding='utf8')).get('dense_native_replays',[])
        mark(verification)
    for folder in sorted(input_dir.glob('*_0[1-9]')):
        direction=folder.name.rsplit('_',1)[0];did=int(folder.name.rsplit('_',1)[1])
        if direction not in ['column','row']:continue
        datafile=folder/'data.npz';setupfile=folder/'setup.json'
        if not datafile.is_file():continue
        with np.load(datafile) as raw:X=raw['X'];y=raw['y']
        mark(datafile);mark(setupfile)
        for csvpath in sorted(folder.glob('*/r*_c*.csv')):
            f=pd.read_csv(csvpath,float_precision='round_trip');frames.append(f)
            mark(csvpath);npz=csvpath.with_suffix('.npz');meta=csvpath.with_suffix('.json');mark(npz);mark(meta)
            start=json.loads(meta.read_text(encoding='utf8'))['rep_start']
            with np.load(npz) as raw:
                for q in f.itertuples():
                    offset=int(q.rep)-start;state=raw[q.method+'_state'][offset];ls=raw['ls_state'][offset]
                    beta=X.T@state if direction=='column' else state
                    betaLS=X.T@ls if direction=='column' else ls
                    gap=float(np.linalg.norm(beta-betaLS))
                    floor=float(64*np.finfo(float).eps*max(1.,np.linalg.norm(beta),np.linalg.norm(betaLS)))
                    item=dict(direction=direction,data_id=did,arm=q.arm,method=q.method,budget=int(q.budget),rep=int(q.rep),
                        local_floor_flag=bool(gap<=floor),local_floor=floor,observed_gap_norm=gap,
                        replay_tested=False,replay_warning=None,replay_change_over_gap=None,diagnostic_status='not_replayed',
                        accuracy_certified=False)
                    # This predesignated set matches the original audit and
                    # adds a group warning without pretending all 100 samples
                    # have been independently replayed.
                    if did==1 and q.arm=='main' and q.budget==38400 and q.rep==0 and q.method=='Nesterov':
                        if replay=='dense':
                            counts=raw['counts'][offset];ix=np.flatnonzero(counts)
                            weights=counts[ix]*(len(counts)/q.budget)
                            Z=(X if direction=='column' else X.T)[:,ix]*np.sqrt(weights)
                            A=Z@Z.T;c=y if direction=='column' else Z@(y[ix]*np.sqrt(weights))
                            par=parameters[(parameters.direction==direction)&(parameters.data_id==did)&
                                (parameters.arm==q.arm)&(parameters.budget==q.budget)&(parameters.method==q.method)]
                            if len(par)!=1:raise ValueError('Expected one frozen Nesterov parameter row')
                            p=par.iloc[0]
                            other=dense_nesterov(A,c,int(p.steps),float(p['dt']))
                            beta2=X.T@other if direction=='column' else other
                            change=float(np.linalg.norm(beta2-beta))
                            ratio=change/max(gap,1e-300)
                        else:
                            matches=[v for v in archived if v['direction']==direction and v['budget']==38400 and v['method']=='Nesterov']
                            if len(matches)!=1:raise ValueError('Expected one saved predesignated dense replay per direction')
                            ratio=float(matches[0]['replay_change_over_gap']);change=float(matches[0]['coefficient_difference_norm'])
                        item.update(replay_tested=True,replay_warning=bool(ratio>warning_ratio),replay_change_over_gap=ratio,
                                    diagnostic_status='unresolved' if ratio>warning_ratio else 'selected_replay_agreement_only')
                        replays.append(dict(direction=direction,data_id=did,arm=q.arm,method=q.method,budget=int(q.budget),rep=int(q.rep),
                            source='fresh_literal_dense_recurrence' if replay=='dense' else 'archived_dense_replay_diagnostic',
                            coefficient_change=change,observed_gap_norm=gap,change_over_gap=ratio,
                            warning=bool(ratio>warning_ratio),exceeds_observed_gap=bool(ratio>1),accuracy_certified=False))
                    record_diagnostics.append(item)
    if not frames:raise ValueError('No IV result chunks found')
    frame=pd.concat(frames,ignore_index=True)
    keys=['direction','data_id','arm','method','budget','rep']
    if frame.duplicated(keys).any():raise ValueError('Duplicate formal IV record keys')
    diagnostics=pd.DataFrame(record_diagnostics)
    groupkeys=keys[:-1];groups=[]
    for key,f in frame.groupby(groupkeys,sort=True):
        d=diagnostics
        for column,value in zip(groupkeys,key):d=d[d[column]==value]
        values=np.sort(f.scaled_squared_gap.to_numpy());n=len(values)
        all_finite=bool(np.isfinite(values).all())
        average=float(np.mean(values)) if all_finite else None
        se=float(np.std(values,ddof=1)/np.sqrt(n)) if all_finite and n>1 else 0. if all_finite else None
        positive_total=float(values.sum()) if all_finite else None
        share=float(values[-max(1,math.ceil(n*.01)):].sum()/positive_total) if positive_total and positive_total>0 else 0. if all_finite else None
        relative_se=se/average if average and average>0 else None
        tail=key[2]=='tails'
        tail_warning=bool(tail and (not all_finite or (share is not None and share>.5) or (relative_se is not None and relative_se>.25)))
        selected_warning=bool(d.replay_warning.eq(True).any())
        status='selected_replay_warning' if selected_warning else 'tail_mean_concentration_warning' if tail_warning else 'not_certified'
        groups.append(dict(zip(groupkeys,key))|dict(n=n,mean_scaled_squared_gap=average,standard_error=se,all_finite=all_finite,
            relative_standard_error=relative_se,top_one_percent_share=share,tail_concentration_warning=tail_warning,
            local_floor_count=int(d.local_floor_flag.sum()),replay_tested_count=int(d.replay_tested.sum()),
            selected_replay_warning=selected_warning,accuracy_status=status,accuracy_certified=False))
    diagnostics.to_csv(output/'resolution_records.csv',index=False)
    pd.DataFrame(groups).to_csv(output/'resolution_groups.csv',index=False)
    tailgroups=[q for q in groups if q['arm']=='tails']
    formal=not protocol.get('run_mode')=='smoke'
    # Fresh executions can produce different diagnostic values. Report them;
    # never require reproduction of the historical warning conclusions.
    result=dict(completed=True,formal_input=formal,input_records=len(frame),
        local_floor_flags=int(diagnostics.local_floor_flag.sum()),
        selected_replays=replays,tail_groups=tailgroups,replay_warning_threshold=warning_ratio,
        tail_warning_thresholds=dict(top_one_percent_share=.5,relative_standard_error=.25),
        semantics=dict(local_floor_flag='Diagnostic for close-vector subtraction only; false is not an error certificate.',
            replay_warning='A selected independent replay changes the output by more than the stated fraction of its observed gap; untested records remain null.',
            tail_concentration_warning='Descriptive threshold for an extreme-sample-dominated mean; not a population-tail theorem or valid-coverage claim.',
            accuracy_certified='Always false here: selected numerical comparisons are not end-to-end rounding proofs.'),
        records_or_formal_means_replaced=False,seconds=time.perf_counter()-tick)
    save(output/'resolution_report.json',result)
    save(output/'input_sha256.json',manifest)
    for relative,digest in manifest.items():
        if sha(input_dir/relative)!=digest:raise AssertionError('An input changed during read-only diagnostics')
    print(json.dumps(dict(completed=True,records=len(frame),replays=len(replays),tail_warning_groups=sum(q['tail_concentration_warning'] for q in tailgroups),output=str(output))),flush=True)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True,help='Your newly generated IV results; the Lite package has no archived formal states.')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',choices=['dense','saved'],default='dense')
    parser.add_argument('--warning-ratio',type=float,default=.1)
    args=parser.parse_args(argv)
    if not args.warning_ratio>0:parser.error('--warning-ratio must be positive')
    diagnose(args.input,args.output,replay=args.replay,warning_ratio=args.warning_ratio)


if __name__=='__main__':main()
