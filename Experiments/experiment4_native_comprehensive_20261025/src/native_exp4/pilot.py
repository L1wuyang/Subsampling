"""Independent small checks and actual-size feasibility before freezing."""
from .common import *
from .kernel import solve,reduce
from .column_reference import integrate
from scipy.integrate import solve_ivp

def main(args):
    if args.command=='freeze':return freeze()
    guard();out=Path(args.output).resolve() if args.output else HERE/'outputs/pilot_01';out.mkdir(parents=True,exist_ok=False)
    checks=[];bench=[]
    def check(name,ok,**details):
        checks.append(dict(name=name,passed=bool(ok),**details))
        assert ok,(name,details)
    for direction in DIRECTIONS:
        data=dataset(202610250801,direction,1,d=5,N=24)
        setup=full_setup(data);count=counts_for(202610250802,direction,1,30,1,N=24)[0]
        M,rhs,Z,ix,weights=sketch(data,count);ls,rank=ls_reference(data,rhs,Z,ix,weights)
        check(direction+'_ls_normal',np.linalg.norm(M@ls-rhs)<1e-9*max(1.,np.linalg.norm(rhs)))
        for r in [30,150]:
            for method in METHODS:
                p=parameters(setup,r,method);state=solve(M,rhs,p)
                if method=='Ridge':ref=np.linalg.solve(M+p['alpha']*np.eye(len(rhs)),rhs)
                else:
                    ref=integrate(p,lambda x,t:t*rhs-M@x,rhs.shape)
                error=np.linalg.norm(state-ref)/max(1.,np.linalg.norm(ref))
                check(f'{direction}_{r}_{method}_dense',error<3e-9,relative_error=float(error),steps=p['steps'])
                check(f'{direction}_{r}_{method}_zero',np.count_nonzero(solve(M,np.zeros_like(rhs),p))==0)
                if method in ['Showalter','HBF','SOAR']:
                    refined=solve(M,rhs,parameters(setup,r,method,2))
                    error=np.linalg.norm(state-refined)/max(1.,np.linalg.norm(refined))
                    check(f'{direction}_{r}_{method}_refine',error<1e-5,relative_error=float(error))
                    if method=='Showalter':
                        adaptive=solve_ivp(lambda t,x:rhs-M@x,[0,p['T']],np.zeros(len(rhs)),method='DOP853',rtol=2e-11,atol=2e-12).y[:,-1]
                    else:
                        n=len(rhs)
                        def f(t,s):return np.r_[s[n:],(t*rhs if method=='SOAR' else rhs)-M@s[:n]-(p['eta']*s[n:] if method=='HBF' else 0)]
                        adaptive=solve_ivp(f,[0,p['T']],np.zeros(2*n),method='DOP853',rtol=2e-11,atol=2e-12).y[:n,-1]
                        if method=='SOAR':adaptive/=p['T']
                    error=np.linalg.norm(state-adaptive)/max(1.,np.linalg.norm(adaptive))
                    check(f'{direction}_{r}_{method}_adaptive',error<1e-5,relative_error=float(error))
        # Singular sketches retain the column null response and row joint weighting.
        count=np.zeros(24,dtype=np.int32);count[:2]=[17,13]
        M,rhs,Z,ix,weights=sketch(data,count);ls,rank=ls_reference(data,rhs,Z,ix,weights)
        check(direction+'_singular_rank',rank==2)
        check(direction+'_ls_stationarity',np.linalg.norm(M@(M@ls-rhs))<2e-8*max(1.,np.linalg.norm(M)*np.linalg.norm(rhs)))
        expanded=np.repeat(np.arange(24),count);W=atoms(data)[:,expanded]*np.sqrt(24/30)
        check(direction+'_expanded_gram',np.allclose(M,W@W.T,rtol=2e-13,atol=2e-13))
        if direction=='row':check('row_expanded_rhs',np.allclose(rhs,W@(data['y'][expanded]*np.sqrt(24/30))))
        for method in METHODS:
            p=parameters(setup,30,method);state=solve(M,rhs,p)
            ref=np.linalg.solve(M+p['alpha']*np.eye(5),rhs) if method=='Ridge' else integrate(p,lambda x,t:t*rhs-M@x,rhs.shape)
            error=np.linalg.norm(state-ref)/max(1.,np.linalg.norm(ref))
            check(direction+'_'+method+'_singular',error<2e-8,relative_error=float(error))
    # One independent actual-size output at a modest and the largest budget.
    for direction in DIRECTIONS:
        data=dataset(202610250801,direction,2);setup=full_setup(data)
        for r in [30,38400]:
            count=counts_for(202610250802,direction,2,r,1)[0];M,rhs,Z,ix,weights=sketch(data,count);reduced=reduce(M)
            for method in METHODS:
                p=parameters(setup,r,method);tick=time.perf_counter();u=solve(M,rhs,p,reduced)
                secs=time.perf_counter()-tick
                check(f'actual_{direction}_{r}_{method}_finite',np.isfinite(u).all())
                bench.append(dict(direction=direction,budget=r,method=method,seconds=secs,steps=p['steps'],a=setup['a'],L=setup['L']))
                print('PILOT_BENCH',bench[-1],flush=True)
    manifest={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in scientific()}
    save(out/'frozen_sources.json',manifest)
    save(out/'verification.json',dict(passed=True,checks=checks,benchmark=bench,check_count=len(checks)))
    print('PILOT_PASSED',len(checks),flush=True)

def freeze():
    out=HERE/'outputs/pilot_02';pilot=read(out/'verification.json');assert pilot['passed']
    gate=read(out/'frozen_sources.json');assert all(sha(HERE/k)==v for k,v in gate.items())
    path=HERE/'formal_protocol.json';assert not path.exists()
    config=dict(version='native_IV_20261025_v1',purpose='Actual native outputs versus the same-draw QR LS; changing regularization paths; not an OPT experiment',
        data_seed=202610250804,sampling_seed=202610250803,dimension=60,objects=1200,data_ids=[1,2,3,4,5],methods=METHODS,directions=DIRECTIONS,
        main=dict(budgets=[30,60,90,150,240,360,600,1200,2400,4800,9600,19200,38400],repetitions=100,data_ids=[1]),
        robustness=dict(budgets=[1200,19200],repetitions=30,data_ids=[2,3,4,5]),
        tails=dict(budgets=[60],repetitions=1000,data_ids=[1],methods=['HBF','Nesterov','SOAR'],stream=1),
        zero_response=dict(budgets=[30,1200],repetitions=3,data_ids=[1],stream=2),
        parameters='Full-data Cholesky SPD bracket a=lower/2; b=||A||inf+a; h=.9/max(b,N max atom-norm-squared). Six historical 1/r paths with this common frozen window and safe h. RK4 .9/L or .2/sqrt(L).',
        iteration='Householder tridiagonal orthogonal coordinates, every prescribed recurrence/RK4 stage; float64 without fastmath; actual output then explicit LS subtraction; no eig/SVD/analytic residual trajectories',
        LS='GELSY pivoted-QR complete orthogonal least squares; 1e-12 sampling-atom relative threshold, column minimum norm Gram solution via two solves, row jointly weighted design/response',
        stopping='All steps precomputed from full data and budget; no discrepancy stopping and no iteration cap; numerical failures retained',
        resolution='64 eps max(1, coefficient norms) diagnostic; half-grid and dense independent checks reported separately, no fabricated below-resolution accuracy',
        inference='Pointwise t99 Monte Carlo intervals for primary conditional means; t29 robustness within each data set; no selection for favorable decline; tail arms separate; no speedup claim',
        pilot=dict(directory='outputs/pilot_02',verification_sha256=sha(out/'verification.json'),checks=pilot['check_count']),
        preregistration='Frozen only after pilot and before any formal data/sketch; no OPT/tangents/C because IV targets same-draw LS, not a fixed full-data generator')
    save(path,config);print('FROZEN',sha(path),flush=True)
