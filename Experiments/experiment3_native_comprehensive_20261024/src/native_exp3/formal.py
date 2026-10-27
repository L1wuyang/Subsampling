"""Frozen UNI native calculation; all six methods use exactly the same draws."""
from .common import *
from concurrent.futures import ProcessPoolExecutor, as_completed
import shutil
import pandas as pd


def arms_for(config, did):
    main = config['main'] if did == 1 else config['robustness']
    yield dict(tag='main', c=1., sigma=.5, stream=1, budgets=main['budgets'], repetitions=main['repetitions'])
    if did in config['sensitivity']['data_ids']:
        for idx, c in enumerate(config['sensitivity']['c_values']):
            yield dict(tag='c_low' if c < 1 else 'c_high', c=c, sigma=.5, stream=10+idx,
                       budgets=config['sensitivity']['budgets'], repetitions=config['sensitivity']['repetitions'])
    if did in config['zero_response']['data_ids']:
        spec = config['zero_response']
        yield dict(tag='zero_response', c=1., sigma=.5, stream=30, zero_response=True,
                   budgets=spec['budgets'], repetitions=spec['repetitions'])


def draw_counts(config, direction, did, arm, budget):
    rng = np.random.default_rng(np.random.SeedSequence([config['sampling_seed'], DIRECTIONS.index(direction), did, arm['stream'], budget]))
    return rng.multinomial(budget, np.full(config['objects'], 1/config['objects']), size=arm['repetitions']).astype(np.int32)


def run_arm(out, config, direction, did, arm):
    folder = Path(out)/f'{direction}_{did:02d}'/arm['tag']
    folder.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    data = load(out, direction, did, arm)
    data['sigma'] = arm['sigma']
    A, rhs, metric, L, models = setup(data, arm['c'])
    print('SETUP_DONE', direction, did, arm['tag'], 'seconds', round(time.perf_counter()-start, 3), 'L', L, flush=True)
    pars = {method: m['param'] for method, m in models.items()}
    save(folder/'parameters.json', dict(L=L, alpha=next(iter(pars.values()))['alpha'], methods=pars))
    states = dict(A=A, rhs=rhs, metric=metric)
    references = []
    for method, model in models.items():
        states[method+'_target'] = model['target']
        states[method+'_J'] = model['J']
        references.append(dict(direction=direction, data_id=did, arm=arm['tag'], method=method,
                               **{k:v for k, v in model['param'].items() if k != 'method'},
                               L=L, target_norm_sq=model['denominator'], trace=model['trace'], C=model['C'],
                               zero_target=model['denominator'] <= 1e-24,
                               zero_influence=model['trace'] <= 1e-24))
    np.savez_compressed(folder/'native_states.npz', **states)
    write(folder/'full_reference.csv', references)
    records, costs = [], []
    for budget in arm['budgets']:
        counts = draw_counts(config, direction, did, arm, budget)
        As, cs, weights = weighted(data, counts)
        coverage = np.count_nonzero(counts, axis=1)
        spike_draws = counts @ data['spike_mask'].astype(int)
        raw = dict(counts=counts)
        for method, model in models.items():
            tick = time.perf_counter()
            U = batch(data, As, cs, model['param'])
            raw[method+'_state'] = U
            values = measures(data, U, model, weights, metric)
            finite = np.isfinite(U).all(axis=1)
            for rep in range(len(U)):
                status = 'complete' if model['denominator'] > 1e-24 else 'zero_target'
                if not finite[rep]: status = 'numerical_failure'
                records.append(dict(direction=direction, data_id=did, arm=arm['tag'], method=method,
                                    budget=budget, rep=rep, status=status, unique_objects=int(coverage[rep]),
                                    spike_draws=int(spike_draws[rep]), executed_steps=model['param']['steps'],
                                    **{key:float(val[rep]) for key, val in values.items()}))
            costs.append(dict(direction=direction, data_id=did, arm=arm['tag'], method=method, budget=budget,
                              seconds=time.perf_counter()-tick, trajectory_labels=len(U),
                              updates=len(U)*model['param']['steps'],
                              rhs_evaluations=len(U)*model['param']['steps']*(4 if method in ['Showalter', 'HBF', 'SOAR'] else 1),
                              direct_solves=len(U) if method == 'Ridge' else 0))
        np.savez_compressed(folder/f'raw_r{budget}.npz', **raw)
        print('BUDGET_DONE', direction, did, arm['tag'], budget, flush=True)
    write(folder/'results.csv', records)
    write(folder/'costs.csv', costs)
    completion = dict(direction=direction, data_id=did, arm=arm['tag'], rows=len(records), seconds=time.perf_counter()-start)
    save(folder/'completion.json', completion)
    return completion


def worker(out, config, direction, did):
    col.guard()
    return [run_arm(out, config, direction, did, arm) for arm in arms_for(config, did)]


def main(args):
    col.guard()
    config = json.loads((HERE/'formal_protocol.json').read_text(encoding='utf8'))
    pilot = json.loads((HERE/'outputs/pilot_01/verification.json').read_text(encoding='utf8'))
    assert pilot['passed'] and sha(HERE/'outputs/pilot_01/verification.json') == config['pilot']['verification_sha256']
    pilot_sources = json.loads((HERE/'outputs/pilot_01/frozen_sources.json').read_text(encoding='utf8'))
    assert all(sha(HERE/k) == v for k, v in pilot_sources.items())
    out = Path(args.output).resolve() if args.output else HERE/'outputs/formal_01'
    out.mkdir(parents=True, exist_ok=False)
    tick = time.perf_counter()
    snapshot = out/'source_snapshot'; snapshot.mkdir()
    scientific = [HERE/'run.py', HERE/'formal_protocol.json', HERE/'requirements.txt'] + list((HERE/'src').rglob('*.py'))
    frozen = {}
    for path in scientific:
        dest = snapshot/path.relative_to(HERE); dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        frozen[str(path.relative_to(HERE)).replace('\\', '/')] = sha(path)
    save(out/'frozen_sources.json', frozen)
    save(out/'protocol.json', config)
    save(out/'pilot_acceptance.json', pilot)
    (out/'data').mkdir()
    inputs = {}
    for direction in DIRECTIONS:
        for did in config['data_ids']:
            path = out/'data'/f'{direction}_{did:02d}.npz'
            np.savez_compressed(path, **base(config['data_seed'], direction, did, config['dimension'], config['objects']))
            inputs[str(path.relative_to(out)).replace('\\', '/')] = sha(path)
    save(out/'data_manifest.json', inputs)
    completions = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        tasks = [pool.submit(worker, out, config, direction, did) for direction in DIRECTIONS for did in config['data_ids']]
        for task in as_completed(tasks):
            completions.extend(task.result())
            print('DATA_DONE', completions[-1], flush=True)
    for filename in ['results', 'full_reference', 'costs']:
        groups = [[], []]
        for item in completions:
            path = out/f"{item['direction']}_{item['data_id']:02d}"/item['arm']/(filename+'.csv')
            groups[int(item['arm'] != 'main')].append(pd.read_csv(path))
        for prefix, frames in zip(['', 'sensitivity_'], groups):
            pd.concat(frames, ignore_index=True).to_csv(out/(prefix+filename+'.csv'), index=False)
    assert all(sha(HERE/k) == v for k, v in frozen.items())
    assert all(sha(out/k) == v for k, v in inputs.items())
    counts = config['replication_counts']
    observed = sum(item['rows'] for item in completions)
    assert observed == sum(counts.values()), (observed, counts)
    save(out/'execution.json', dict(completed=True, seconds=time.perf_counter()-tick, workers=args.workers,
                                    completions=completions, total_records=observed, spectral_guard_active=True,
                                    frozen_sources_unchanged=True, input_hashes_unchanged=True))
    print('FORMAL_COMPLETE', observed, 'seconds', time.perf_counter()-tick, flush=True)
