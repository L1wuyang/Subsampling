"""Frozen paired row experiment; refuse to overwrite any existing run."""
from common import *
from concurrent.futures import ProcessPoolExecutor, as_completed


def run_arm(did, arm, config):
    start = time.perf_counter()
    folder = OUT/f'data_{did:02d}'/arm['tag']
    folder.mkdir(parents=True, exist_ok=False)
    X, y, b0, mask, cov, scale = load(did, arm)
    A, ps, models, history = setup(X, y, arm['c'], arm['floor'])
    print('SETUP_DONE', did, arm['tag'], 'seconds', time.perf_counter()-start, 'L', history[-1]['L'], flush=True)
    save(folder/'bound_history.json', history)
    refs, traces, costs = [], [], []
    states = dict(**ps, y=y, spike_mask=mask, beta0=b0, covariance_scalar=cov, training_scale=scale)
    for method, m in models.items():
        b, J, score, pi, par = m['beta'], m['J'], m['scores'], m['pi'], m['param']
        mm = metrics(b[None], b, X, y, b0, mask, cov, arm['sigma'])
        refs.append(dict(data_id=did, arm=arm['tag'], method=method,
                         **{k:v for k,v in par.items() if k != 'method'},
                         target_norm_sq=float(b @ b), covariance_scalar=cov, training_scale=scale,
                         status='zero_target' if b @ b <= 1e-24 else 'complete',
                         **{k:float(v[0]) for k,v in mm.items()}))
        center = float(np.sum(J.sum(axis=1)**2))
        local = []
        for rule, prob in {**ps, 'OPT':pi}.items():
            val = float(np.sum(score**2/prob)-center)
            local.append(val)
            traces.append(dict(data_id=did, arm=arm['tag'], method=method, rule=rule, local_trace=val,
                               normalized_trace=val/float(b @ b) if b @ b > 1e-24 else np.nan))
        assert local[-1] <= min(local)+1e-8*max(1, max(local))
        states[method+'_beta'] = b
        states[method+'_J'] = J
        states[method+'_pi'] = pi
        states[method+'_scores'] = score
    np.savez_compressed(folder/'native_states.npz', **states)
    write(folder/'full_reference.csv', refs)
    write(folder/'local_trace.csv', traces)
    save(folder/'parameters.json', {method:m['param'] for method,m in models.items()})
    rows = []
    for r in arm['budgets']:
        uniforms = np.random.default_rng(np.random.SeedSequence([config['sampling_seed'], did, r, arm['stream']])).random((arm['repetitions'], r))
        shared = {rule:matrices(X, y, pi, uniforms, mask) for rule,pi in ps.items()}
        raw = dict(uniforms=uniforms)
        for method, m in models.items():
            tick = time.perf_counter()
            packs = [shared[rule] for rule in RULES[:3]]+[matrices(X, y, m['pi'], uniforms, mask)]
            As = np.concatenate([x[0] for x in packs])
            cs = np.concatenate([x[1] for x in packs])
            unique = np.concatenate([x[2] for x in packs])
            spike_draws = np.concatenate([x[3] for x in packs])
            B = batch(As, cs, m['param'])
            raw[method+'_beta'] = B
            mm = metrics(B, m['beta'], X, y, b0, mask, cov, arm['sigma'])
            finite = np.isfinite(B).all(axis=1)
            for ri, rule in enumerate(RULES):
                for rep in range(arm['repetitions']):
                    i = ri*arm['repetitions']+rep
                    status = 'zero_target' if m['beta'] @ m['beta'] <= 1e-24 else 'complete'
                    if not finite[i]: status = 'numerical_failure'
                    rows.append(dict(data_id=did, arm=arm['tag'], budget=r, method=method, rule=rule, rep=rep,
                                     status=status, executed_steps=m['param']['steps'], dt=m['param']['dt'],
                                     unique_rows=int(unique[i]), spike_draws=int(spike_draws[i]),
                                     **{k:float(v[i]) for k,v in mm.items()}))
            costs.append(dict(data_id=did, arm=arm['tag'], method=method, budget=r, seconds=time.perf_counter()-tick,
                              trajectory_labels=len(B), updates=int(len(B)*m['param']['steps']),
                              rhs_evaluations=int(len(B)*m['param']['steps']*(4 if method in ['Showalter','HBF','SOAR'] else 1)),
                              direct_solves=int(len(B)) if method == 'Ridge' else 0))
        np.savez_compressed(folder/f'raw_r{r}.npz', **raw)
        print('BUDGET_DONE', did, arm['tag'], r, flush=True)
    write(folder/'results.csv', rows)
    write(folder/'costs.csv', costs)
    result = dict(data_id=did, arm=arm['tag'], rows=len(rows), seconds=time.perf_counter()-start)
    save(folder/'completion.json', result)
    return result


def worker(did, config):
    guard()
    return [run_arm(did, arm, config) for arm in config['arms'] if did in arm['data_ids']]


def aggregate(config, completions, seconds):
    import pandas as pd
    for name in ['results', 'full_reference', 'local_trace', 'costs']:
        groups = [[], []]
        for did in config['data_ids']:
            for arm in config['arms']:
                if did in arm['data_ids']:
                    folder = OUT/f'data_{did:02d}'/arm['tag']
                    assert (folder/'completion.json').exists()
                    groups[int(arm['tag'] != 'main')].append(pd.read_csv(folder/(name+'.csv')))
        for tag, frames in zip(['', 'sensitivity_'], groups):
            pd.concat(frames, ignore_index=True).to_csv(OUT/(tag+name+'.csv'), index=False)
    frozen = json.loads((OUT/'frozen_sources.json').read_text(encoding='utf8'))
    assert all(digest(HERE/k) == v for k,v in frozen.items())
    protected = json.loads((HERE/'protected_before.json').read_text(encoding='utf8'))
    assert all(digest(ROOT/k) == v for k,v in protected.items())
    save(OUT/'execution.json', dict(completed=True, seconds=seconds, completions=completions,
                                   frozen_sources_unchanged=True, protected_files_unchanged=len(protected), spectral_guard_active=True))


def main():
    guard()
    config = json.loads((HERE/'formal_protocol.json').read_text(encoding='utf8'))
    pilot = json.loads((HERE/'outputs/pilot_02/verification.json').read_text(encoding='utf8'))
    assert pilot['passed']
    for name in ['native.py', 'integrator_reference.py', 'common.py']:
        assert digest(HERE/name) == digest(HERE/'outputs/pilot_02/source_snapshot'/name)
    OUT.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    protected = json.loads((HERE/'protected_before.json').read_text(encoding='utf8'))
    assert all(digest(ROOT/k) == v for k,v in protected.items())
    snapshot = OUT/'source_snapshot'
    snapshot.mkdir()
    names = ['native.py', 'integrator_reference.py', 'common.py', 'pilot.py', 'run_formal.py', 'formal_protocol.json']
    for name in names: shutil.copy2(HERE/name, snapshot/name)
    save(OUT/'frozen_sources.json', {name:digest(HERE/name) for name in names})
    save(OUT/'protocol.json', config)
    save(OUT/'pilot_acceptance.json', pilot)
    (HERE/'data').mkdir(exist_ok=False)
    inputs = []
    for did in config['data_ids']:
        path = HERE/'data'/f'data_{did:02d}.npz'
        np.savez_compressed(path, **make_base(config['data_seed'], did, config['n'], config['p']))
        inputs.append(dict(data_id=did, sha256=digest(path)))
    save(OUT/'data_manifest.json', inputs)
    completions = []
    with ProcessPoolExecutor(max_workers=config['workers']) as pool:
        futures = [pool.submit(worker, did, config) for did in config['data_ids']]
        for future in as_completed(futures):
            completions.extend(future.result())
            print('DATA_DONE', completions[-1], flush=True)
    aggregate(config, completions, time.perf_counter()-start)
    print('ALL_COMPLETE', time.perf_counter()-start, flush=True)


if __name__ == '__main__': main()
