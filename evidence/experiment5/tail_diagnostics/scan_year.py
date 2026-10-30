"""All-support scan and log-domain single-atom-event bounds; no eigendecomposition."""
import os
for key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']:os.environ[key]='1'
from pathlib import Path
import argparse
import sys
sys.dont_write_bytecode = True
from verify_witnesses import verify
import json, math, tarfile, io, hashlib
import numpy as np
import pandas as pd
from scipy.special import logsumexp
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--restored',type=Path,required=True,help='Output of restore_year.py')
parser.add_argument('--output',type=Path,required=True,help='New report directory')
parser.add_argument('--repository-root',type=Path,default=HERE.parents[2])
args=parser.parse_args()
BASE=args.restored.resolve();OUT=args.output.resolve();ROOT=args.repository_root.resolve()
if OUT.exists(): raise FileExistsError('Use a new --output directory')
OUT.mkdir(parents=True)
array_manifest=json.loads((BASE/'array_manifest.json').read_text(encoding='utf-8'))
for name,digest in array_manifest.items():
    if name.startswith('inputs/year/') or name.endswith('_probability.npy') or name.endswith(('target.npy','M.npy','parameters.json')):
        if name.endswith('preprocessing.npz'): continue
        with (BASE/name).open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                raise ValueError('Restored array hash mismatch: '+name)
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
assert json.loads((BASE/'restoration_validation.json').read_text())['restoration_matches_historical_summaries']
folder=BASE/'targets/year';dest=folder/'Landweber'
X=np.load(BASE/'inputs/year/X.npy',mmap_mode='r');y=np.load(BASE/'inputs/year/y.npy')
beta=np.load(dest/'target.npy');p=json.loads((dest/'parameters.json').read_text())
h=p['dt'];k=p['steps'];D=float(beta@beta);n=len(y);s=np.sum(X*X,axis=1)
assert (s>0).all() and D<64
b=(X@beta)/np.sqrt(s);v=y/np.sqrt(s)
evidence=ROOT/'evidence/experiment5'
with (evidence/'saved_records.tar.gz').open('rb') as stream:
    if hashlib.file_digest(stream,'sha256').hexdigest()!='e1355e6de8ba6103bc1e72460e915cb1d6fa98fe3b9154ceae1f006417a63d2a':
        raise ValueError('Frozen saved-records archive SHA256 mismatch')
frames=[]
with tarfile.open(evidence/'saved_records.tar.gz') as archive:
    for member in archive:
        if '/draws/year/' in member.name and member.name.endswith('.csv'):
            frames.append(pd.read_csv(io.BytesIO(archive.extractfile(member).read())))
records=pd.concat(frames,ignore_index=True);records=records[records.method=='Landweber']
assert len(records)==1400
means=records.groupby(['budget','rule']).relative_coefficient_error.agg(['mean','count'])
means.to_csv(OUT/'recomputed_saved_means.csv')
budgets=sorted(set(records.budget));stability=[];bounds=[];witnesses=[]
for rule in ['UNI','NORM','LEV','OPT']:
    pi=np.load(dest/'OPT_probability.npy' if rule=='OPT' else folder/(rule+'_probability.npy'))
    assert np.all(pi>0) and abs(pi.sum()-1)<2e-14
    lam=s/pi;q=1-h*lam
    with np.errstate(divide='ignore',invalid='ignore'):
        logq=k*np.log(np.abs(q));signq=np.sign(q)**k
        # a-b = (v-b) - v*q**k, a is the estimator's coefficient on z/||z||.
        logdiff,_=logsumexp(np.stack([np.log(np.abs(v-b)),np.log(np.abs(v))+logq]),b=np.stack([np.sign(v-b),-np.sign(v)*signq]),axis=0,return_sign=True)
        orth=np.maximum(D-b*b,0)
        logerr=np.logaddexp(2*logdiff,np.log(orth))-math.log(D)
        logone,_=logsumexp(np.stack([np.zeros(n),logq]),b=np.stack([np.ones(n),-signq]),axis=0,return_sign=True)
        lognorm=np.log(np.abs(v))+logone
        # A more conservative bound needs only ||original beta_m|| <= 8.
        loglower=np.full(n,-np.inf);large=lognorm>math.log(8)
        loglower[large]=2*(lognorm[large]+np.log1p(-np.exp(math.log(8)-lognorm[large]))-math.log(8))
    imax=int(np.argmax(lam));B=float(lam[imax])
    stability.append(dict(rule=rule,B=B,hB=h*B,B_over_L=B/p['L'],max_atom_index_zero_based=imax,raw_row_one_based=imax+1,amplifying_atoms=int(np.sum(h*lam>2)),amplifying_atoms_with_nonzero_response=int(np.sum((h*lam>2)&(y!=0))),probability_mass_amplifying_atoms=float(pi[h*lam>2].sum()),probability_sum=float(pi.sum()),minimum_probability=float(pi.min()),maximum_probability=float(pi.max())))
    for N in budgets:
        logs=N*np.log(pi)+logerr;loglb=N*np.log(pi)+loglower
        top=np.argsort(logs)[-5:][::-1];idx=int(top[0]);lower_idx=int(np.argmax(loglb))
        mean=float(means.loc[(N,rule),'mean'])
        record=dict(rule=rule,N=int(N),reported_mean=mean,max_single_event_log10_contribution=float(logs[idx]/math.log(10)),sum_disjoint_single_events_log10_lower_bound=float(logsumexp(logs)/math.log(10)),max_event_atom_index_zero_based=idx,max_event_raw_row_one_based=idx+1,log10_lower_bound_over_reported_mean=float((logsumexp(logs)-math.log(mean))/math.log(10)),conservative_norm8_log10_lower_bound=float(loglb[lower_idx]/math.log(10)) if np.isfinite(loglb[lower_idx]) else None,conservative_norm8_witness_index=lower_idx if np.isfinite(loglb[lower_idx]) else None)
        bounds.append(record)
        for i in top:
            i=int(i);witnesses.append(dict(rule=rule,N=int(N),atom_index_zero_based=i,raw_row_one_based=i+1,pi=float(pi[i]),norm_squared=float(s[i]),centered_response=float(y[i]),lambda_i=float(lam[i]),h_lambda=float(h*lam[i]),q=float(q[i]),target_projection=float(b[i]),log10_event_probability=float(N*math.log10(pi[i])),log10_relative_squared_error=float(logerr[i]/math.log(10)),log10_contribution=float(logs[i]/math.log(10)),conservative_norm8_log10_bound=float(loglb[i]/math.log(10)) if np.isfinite(loglb[i]) else None))
pd.DataFrame(stability).to_csv(OUT/'support_stability.csv',index=False)
pd.DataFrame(bounds).to_csv(OUT/'event_bounds.csv',index=False)
pd.DataFrame(witnesses).to_csv(OUT/'event_witnesses.csv',index=False)
report=dict(parameters=p,target_norm_squared=D,target_norm_bound_used_for_conservative_witness=8,rows=n,dimension=X.shape[1],stability=stability,bounds=bounds,scope='Original frozen Year/Landweber map only. Exact arithmetic analytic event risk with reconstructed stored arrays; not an interval certificate for all native floating point trajectories. NORM full-support contraction excludes exponential unstable modes, but does not certify Monte Carlo accuracy for all other tails.',formula='beta(E_i)=(y_i/s_i)*(1-(1-h*s_i/pi_i)^k)*z_i; P(E_i)=pi_i^N; distinct E_i disjoint. Norm-8 conservative bound uses ||beta_m||<=8 and hence relative error >=max(||beta(E_i)||/8-1,0)^2.')
write(OUT/'diagnosis.json',report)
print(pd.DataFrame(stability).to_string(index=False))
print(pd.DataFrame(bounds)[['rule','N','reported_mean','max_single_event_log10_contribution','conservative_norm8_log10_lower_bound']].to_string(index=False))

# Export compact witnesses from this restoration and re-run both high-precision paths.
# The immutable bundled witnesses remain unchanged; regeneration is a separate output.
compact=json.loads((HERE/'witness_inputs.json').read_text(encoding='utf-8'))
indices=sorted({w['index_zero_based'] for w in compact['witnesses']})
compact['rows']={str(i):dict(coordinates_hex=[float(v).hex() for v in X[i]],response_hex=float(y[i]).hex()) for i in indices}
compact['landweber_target_hex']=[float(v).hex() for v in beta]
matrix=np.load(folder/'M.npy')
L=float(32*np.linalg.norm(matrix,np.inf))
for w in compact['witnesses']:
    if w['method']=='Landweber':
        probability=np.load(dest/'OPT_probability.npy' if w['rule']=='OPT' else folder/'UNI_probability.npy',mmap_mode='r')
        w['probability_hex']=float(probability[w['index_zero_based']]).hex()
        step=p['dt'];count=p['steps']
    else:
        alpha=float((.001 if w['method']=='Showalter' else .00001)*np.trace(matrix)/len(matrix))
        step=.9/L
        if w['method']=='Showalter':
            endpoint=1/alpha;count=math.ceil(endpoint/step);step=endpoint/count
        else:
            count=max(1,math.ceil((-3+math.sqrt(1+24/(alpha*step)))/2))
    w['step_hex']=float(step).hex();w['steps']=count
    # Other BLAS/library builds can change regenerated low-order bits.
    # Historical summary tolerance is enforced by restore_year.py; no byte identity is asserted.
    w['reference_log10_bounds']={}
compact['scope']+=' These compact inputs were regenerated by scan_year.py; compare to the bundled reference as a tolerance-based reconstruction, not as historical byte identity.'
write(OUT/'witness_inputs.json',compact)
write(OUT/'verified_witnesses.json',verify(OUT/'witness_inputs.json'))
print('High-precision and interval verification passed for all four regenerated witnesses.')
