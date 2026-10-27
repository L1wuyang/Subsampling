"""A separate support-bounded V protocol; it never replaces frozen paper results.

Plan preserves UNI/NORM/LEV, enlarges the common L, and then recomputes
every target, native derivative, constrained OPT and contrast before sampling.
"""
from __future__ import annotations
import argparse, math, time
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from . import exp5

RHO=.98

def protocol():
    return {
      'protocol_id':'V_support_baselines_preserved_20261027',
      'status':'prospective separate protocol; not an externally preregistered study and not completed formal paper evidence',
      'full_support_claim':'For every count vector, exact-arithmetic lambda_max(M_N)<=max_i ||z_i||^2/pi_i<=L_star; no end-to-end floating-point error certificate.',
      'step_policy':'Common L_star=max(32||M_complete||inf, max_baseline max_i norm_upper_i/pi_i /rho, sum(norm_upper)/(rho*.98)), rounded outward; rho=.98. All native steps/grids are recalibrated from L_star before any draw.',
      'probability_policy':'UNI/NORM/LEV unchanged. OPT minimizes the newly recomputed coefficient covariance with pi_i>=max(.01/N0,norm_upper_i/(rho*L_star)). Recompute full native targets, influences, scores and constants with new L_star; never reuse old-map OPT scores.',
      'rho':RHO,'norm_bounds':'Positive squared-norm summation gamma bound, outward nextafter and extra 1e-12 scale margin; this is not interval certification of all later BLAS/RK4 arithmetic.',
      'formal_sampling_seed':202610270907,'validation_sampling_seed':202610270908,
      'validation_only_override':'Small validation uses c=1, small raw subsets, and minimum L_star=2*old_L to exercise recalibration. None of these overrides applies to formal mode.',
      'formal_budgets':{'gdsc':[75,187,374,749,1498,2996],'year':[500,1000,2000,5000,10000,20000,50000]},
      'formal_repetitions':{'gdsc':30,'year':50},
      'inference':'Two-sided paired t on OPT-minus-UNI/NORM/LEV, primary budgets 749/5000, one joint Holm across 36 comparisons; pointwise 95% intervals; all failures/tails retained.',
      'historical_c_retained':True,'historical_test_exploration_remains':True,
      'publication_rule':'Representative validation is implementation evidence only. Do not replace original paper V or claim risk/significance improvement before full formal execution and audit.',
    }

def norm_upper(Z):
    """Bound exact squared norms of stored binary64 atoms under normal arithmetic."""
    dimension,count=Z.shape;norms=np.empty(count);positive=float('inf')
    for left in range(0,count,10000):
        A=Z[:,left:left+10000];norms[left:left+10000]=np.sum(A*A,axis=0)
        nonzero=np.abs(A[A!=0])
        if len(nonzero):positive=min(positive,float(nonzero.min()))
    if not np.isfinite(norms).all() or (norms<0).any():raise ValueError('Invalid squared norms')
    unit=2.**-53;k=2*dimension+2
    if k*unit>=.01:raise ValueError('Dimension exceeds the stated roundoff bound')
    gamma=np.nextafter((k*unit)/(1-k*unit),np.inf)
    # Nonzero data here are far above underflow; record and check that precondition.
    if not np.isfinite(positive):positive=0.
    if positive and positive<np.sqrt(np.finfo(float).tiny):raise ValueError('Subnormal products need a stronger norm-bound implementation')
    denominator=np.nextafter(1-gamma,-np.inf)
    upper=np.nextafter((norms/denominator)*(1+1e-12),np.inf)
    return norms,upper,{'dimension':dimension,'gamma':float(gamma),'minimum_nonzero_atom_coordinate':float(positive),'additional_relative_margin':1e-12}

def plan_bounds(M,Z,base,old_parameters,minimum_L_multiplier=1.):
    norms,upper,roundoff=norm_upper(Z);population=Z.shape[1]
    old_L=float(old_parameters['Ridge']['L'])
    baseline_B={rule:float(np.max(upper/pi)) for rule,pi in base.items()}
    trace_upper=float(np.nextafter(upper.sum()*(1+1e-10),np.inf))
    new_L=float(np.nextafter(max(minimum_L_multiplier*old_L,max(baseline_B.values())/RHO,trace_upper/(RHO*.98))*(1+1e-12),np.inf))
    floor=np.maximum(.01/population,np.nextafter(upper/(RHO*new_L),np.inf))
    if not floor.sum()<1:raise ValueError('Infeasible support floor')
    for pi in base.values():
        if np.max(upper/pi)>RHO*new_L*(1+1e-12):raise AssertionError('A preserved baseline exceeds common support ceiling')
    return norms,upper,floor,{'old_L':old_L,'L_star':new_L,'L_ratio':new_L/old_L,
       'baseline_support_bounds':baseline_B,'baseline_B_over_L_star':{r:b/new_L for r,b in baseline_B.items()},
       'probability_floor_sum':float(floor.sum()),'trace_upper':trace_upper,'minimum_L_multiplier':minimum_L_multiplier,'squared_norm_roundoff':roundoff}

def constrained_optimum(scores,floor):
    scores=np.asarray(scores,dtype=float);floor=np.asarray(floor,dtype=float)
    if scores.ndim!=1 or scores.shape!=floor.shape or not len(scores):
        raise ValueError('Scores and lower bounds must be matching nonempty vectors')
    if not np.isfinite(scores).all() or not np.isfinite(floor).all() or (scores<0).any() or (floor<0).any():
        raise ValueError('Scores and lower bounds must be finite and nonnegative')
    if floor.sum()>=1:raise ValueError('Infeasible probability floor')
    if np.max(scores)==0:pi=floor+(1-floor.sum())/len(floor)
    else:
        # Normalize by the largest score first, to avoid overflowing the sum.
        weights=scores/np.max(scores);weights=weights/weights.sum()
        # Floating normalization need not sum to exactly one. hi=1 can put
        # both Brent endpoints below zero even for equal positive scores.
        scale=brentq(lambda t:np.maximum(floor,t*weights).sum()-1,0.,2.,xtol=1e-15,rtol=1e-14)
        pi=np.maximum(floor,scale*weights)
    pi=pi/pi.sum()
    if not np.all(pi>=floor*(1-1e-12)):raise AssertionError('OPT violates lower constraints')
    return pi

def build_targets(out,tag,config,mods):
    """Recompute every new-map target and derivative before releasing any draw."""
    folder=Path(out)/tag;folder.mkdir(parents=True,exist_ok=False)
    data=mods['data'].load(mods['setup'].HERE/'inputs',tag)
    M,rhs,C,Z,base,rank=mods['setup'].basis(data)
    c_values=mods['setup'].HISTORIC_C[tag]
    old_L=float(config['step_infinity_factor']*np.linalg.norm(M,np.inf))
    old_params={m:mods['kernel'].parameters(m,c_values[m]*np.trace(M)/len(M),old_L) for m in exp5.METHODS}
    norms,upper,floor,plan=plan_bounds(M,Z,base,old_params,2. if config.get('reproduction_mode')=='smoke' else 1.)
    np.save(folder/'M.npy',M);np.save(folder/'C.npy',C);np.save(folder/'atom_norm_upper.npy',upper)
    np.save(folder/'probability_lower_bounds.npy',floor)
    for rule,pi in base.items():np.save(folder/(rule+'_probability.npy'),pi)
    report={'tag':tag,'direction':data['direction'],'n':len(data['X']),'p':data['X'].shape[1],'rank':rank,
            'L':plan['L_star'],'support_plan':plan,'models':{},'all_full_targets_and_native_derivatives_recomputed':True}
    for method in exp5.METHODS:
        start=time.perf_counter();alpha=c_values[method]*np.trace(M)/len(M)
        params=mods['kernel'].parameters(method,alpha,plan['L_star'])
        dest=folder/method;dest.mkdir()
        target,J=mods['kernel'].influences(M,rhs,params,Z,None if tag=='gdsc' else data['y'],C,dest/'influences.npy',qbatch=config['adjoint_batch'],block=config['checkpoint_block'],progress=True)
        squared=np.sum(J*J,axis=0);scores=np.sqrt(np.maximum(squared,0));pi=constrained_optimum(scores,floor)
        sumJ=J.sum(axis=1);den=float(np.sum((C@target)**2))
        constants={rule:max(0.,float(np.sum(squared/p)-sumJ@sumJ))/den for rule,p in {**base,'OPT':pi}.items()}
        if constants['OPT']>min(constants.values())*(1+1e-10):raise AssertionError('Constrained OPT objective exceeds a feasible baseline')
        support_ratio=float(np.max(upper/pi)/params['L'])
        if support_ratio>1.:raise AssertionError('OPT support bound exceeds common L')
        prediction=data['E']@data['X'].T@target if tag=='gdsc' else data['E']@target
        design=M@target if tag=='gdsc' else data['X']@target
        full={'response_test_mse':float(np.mean((prediction-data['ey'])**2)),'response_test_rmse':float(np.sqrt(np.mean((prediction-data['ey'])**2))),'coefficient_norm_squared':den}
        for name,value in [('target',target),('influences',J),('scores',scores),('OPT_probability',pi),('test_prediction',prediction),('design_prediction',design)]:
            if name!='influences':np.save(dest/(name+'.npy'),value)
        exp5.write(dest/'parameters.json',params)
        summary={'c':c_values[method],'full':full,'constants':constants,'seconds':time.perf_counter()-start,
                 'minimum_opt_probability':float(pi.min()),'maximum_atom_to_probability':float(np.max(norms/pi)),
                 'upper_support_bound_over_L':support_ratio,'old_steps':old_params[method]['steps'],'new_steps':params['steps'],
                 'target_and_derivative_role':'new common-support map, not reused historical values'}
        exp5.write(dest/'summary.json',summary);report['models'][method]={'parameters':params,**summary}
        print('SUPPORT_TARGET_RECOMPUTED',tag,method,params['steps'],flush=True);del J
    exp5.write(folder/'setup.json',report)
    return report

def cost_plan(project_root,output,inputs=None):
    project_root=Path(project_root).resolve();output=exp5.new_output(output,project_root)
    original=project_root/'Experiments'/exp5.EXPERIMENT
    if inputs is None:
        inputs=output/'inputs'
        exp5.prepare_inputs(project_root,inputs,'formal')
    else:
        inputs=Path(inputs).expanduser().resolve()
        if not all((inputs/tag/'X.npy').is_file() for tag in ['gdsc','year']):
            raise FileNotFoundError('Expected prepared inputs/gdsc and inputs/year; prepare these from the official raw data first.')
    config=exp5.read(original/'formal_protocol.json')
    mods=exp5.scientific_modules(project_root,output);report={'status':'cost plan only; no changed-map targets or efficacy results','protocol':protocol(),'datasets':{}}
    for tag in ['gdsc','year']:
        data=mods['data'].load(inputs,tag)
        M,rhs,C,Z,base,rank=mods['setup'].basis(data)
        old_L=float(config['step_infinity_factor']*np.linalg.norm(M,np.inf))
        old={m:mods['kernel'].parameters(m,mods['setup'].HISTORIC_C[tag][m]*np.trace(M)/len(M),old_L) for m in exp5.METHODS}
        _,_,_,entry=plan_bounds(M,Z,base,old);entry['methods']={}
        for method in exp5.METHODS:
            new=mods['kernel'].parameters(method,old[method]['alpha'],entry['L_star'])
            entry['methods'][method]={'old_steps':old[method]['steps'],'proposed_steps':new['steps'],
               'step_count_multiplier':new['steps']/old[method]['steps'] if old[method]['steps'] else 1.,'new_parameters':new}
        report['datasets'][tag]=entry
    report['old_map_constants_recomputed_from_inputs']=True
    report['historical_targets_required']=False
    exp5.write(output/'support_cost_plan.json',report);print(report,flush=True);return report

def stress_extremes(output,project_root):
    output=Path(output);formal=output/'formal';mods=exp5.scientific_modules(project_root,output);checks=[]
    for tag in ['gdsc','year']:
        X=np.load(output/'inputs'/tag/'X.npy',mmap_mode='r');y=np.load(output/'inputs'/tag/'y.npy');Z=X if tag=='gdsc' else X.T;f=formal/'targets'/tag;upper=np.load(f/'atom_norm_upper.npy')
        for method in exp5.METHODS:
            params=exp5.read(f/method/'parameters.json')
            for rule in exp5.RULES:
                pi=np.load(f/method/'OPT_probability.npy' if rule=='OPT' else f/(rule+'_probability.npy'))
                i=int(np.argmax(upper/pi));z=Z[:,i];M=np.outer(z,z)/pi[i];rhs=y if tag=='gdsc' else z*y[i]/pi[i]
                state,_=mods['kernel'].trajectory(M,rhs,params)
                item={'dataset':tag,'method':method,'rule':rule,'atom':i,'all_draws_same_atom':True,
                      'support_bound_over_L':float(upper[i]/pi[i]/params['L']),'finite':bool(np.isfinite(state).all()),'steps':params['steps']}
                if item['support_bound_over_L']>1 or not item['finite']:raise AssertionError(item)
                checks.append(item)
    result={'role':'representative implementation and deterministic extreme-support check, not full formal risk evidence','checks':checks,'passed':True,'floating_point_error_certified':False}
    exp5.write(output/'representative_support_validation.json',result);return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--action',choices=['plan','validate','formal'],default='plan');parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--project-root',type=Path,default=exp5.PACKAGE_ROOT);parser.add_argument('--inputs',type=Path)
    args=parser.parse_args()
    if args.workers<1:parser.error('--workers must be positive')
    if args.action=='plan':cost_plan(args.project_root,args.output,args.inputs)
    else:
        exp5.run(args.output,'smoke' if args.action=='validate' else 'formal',args.workers,args.project_root,stable=True)
        stress_extremes(args.output,args.project_root)

if __name__=='__main__':main()
