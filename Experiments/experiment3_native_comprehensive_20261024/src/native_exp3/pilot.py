"""Native numerical checks before freezing or generating formal data."""
from .common import *
from scipy.integrate import solve_ivp
import shutil


def main(args):
    if args.command == 'freeze': return freeze()
    col.guard()
    out = Path(args.output) if args.output else HERE/'outputs/pilot_01'
    out.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, error, tolerance, **key):
        checks.append(dict(check=name, error=float(error), tolerance=tolerance, passed=bool(error < tolerance), **key))
    rng = np.random.default_rng(202610240701)
    for direction in DIRECTIONS:
        X = rng.normal(size=(6, 15) if direction == 'column' else (15, 6))
        y = rng.normal(size=len(X)); atoms = X if direction == 'column' else X.T
        A = atoms @ atoms.T
        rhs = y if direction == 'column' else X.T @ y
        N = atoms.shape[1]; L = N*np.sum(atoms**2, axis=0).max()
        metric = A if direction == 'column' else np.eye(6)
        data = dict(X=X, y=y, direction=direction)
        for method in METHODS:
            par = col.parameters(method, np.trace(A)/6, L)
            target, J = (col.full if direction == 'column' else row.full)(X, A, y, par)
            direct = batch(data, A[None], rhs[None], par)[0]
            key = dict(direction=direction, method=method)
            check('full_batch_agreement', np.linalg.norm(target-direct), 1e-10, **key)
            for i in [0, N//2, N-1]:
                atom = np.outer(atoms[:, i], atoms[:, i]); d = 1e-4
                perturb = np.zeros_like(rhs) if direction == 'column' else X[i]*y[i]
                if direction == 'column':
                    plus = col.batch((A+d*atom)[None], y, par)[0]
                    minus = col.batch((A-d*atom)[None], y, par)[0]
                else:
                    plus = row.batch((A+d*atom)[None], (rhs+d*perturb)[None], par)[0]
                    minus = row.batch((A-d*atom)[None], (rhs-d*perturb)[None], par)[0]
                fd = (plus-minus)/(2*d)
                check('fixed_parameter_joint_finite_difference', np.linalg.norm(fd-J[:, i])/max(np.linalg.norm(J[:, i]), 1e-15), 2e-6, atom=i, **key)
            if direction == 'row':
                gram = row.full(X, A, y, par, gram_only=True)[1]
                fraction = np.linalg.norm(J-gram)/np.linalg.norm(J)
                check('RHS_omission_detected', 1/max(fraction, 1e-30), 1000., **key)
            # Exact finite-atom covariance, from all possible one-draw influences.
            centered = J-J.mean(axis=1, keepdims=True)
            C = float(N*np.sum(metric*(centered @ centered.T).T))
            deviations = N*J.T-J.sum(axis=1)
            enumerated = float(squared(deviations, metric).mean())
            check('centered_trace_exact_enumeration', abs(C-enumerated)/max(C, 1e-30), 1e-12, **key)
            if method != 'Ridge':
                zero = batch(data, np.zeros((1, 6, 6)), rhs[None], par)[0]
                if method == 'Landweber': factor = par['dt']*par['steps']
                elif method == 'Nesterov': factor = par['dt']*(par['steps']+1)*(par['steps']+2)/6
                elif method == 'Showalter': factor = par['T']
                elif method == 'HBF': factor = (par['eta']*par['T']-1+np.exp(-par['eta']*par['T']))/par['eta']**2
                else: factor = par['T']**2/6
                check('natural_zero_Gram_gain', np.linalg.norm(zero-factor*rhs), 1e-7, **key)
            if method in ['Showalter', 'HBF', 'SOAR']:
                if method == 'Showalter':
                    fun = lambda t, z: rhs-A @ z
                    initial = np.zeros(6)
                else:
                    fun = lambda t, z: np.r_[z[6:], (t*rhs if method == 'SOAR' else rhs)-A @ z[:6]-(par['eta']*z[6:] if method == 'HBF' else 0)]
                    initial = np.zeros(12)
                independent = solve_ivp(fun, (0, par['T']), initial, rtol=1e-11, atol=1e-13).y[:6, -1]
                if method == 'SOAR': independent /= par['T']
                check('independent_adaptive_ODE', np.linalg.norm(target-independent)/max(np.linalg.norm(independent), 1e-30), 1e-4, **key)
        counts = rng.multinomial(13, np.full(N, 1/N), size=4)
        As, cs, weights = weighted(data, counts)
        for rep, ct in enumerate(counts):
            ix = np.repeat(np.arange(N), ct)
            Z = atoms[:, ix]*np.sqrt(N/13)
            explicit_rhs = y if direction == 'column' else (X[ix]*np.sqrt(N/13)).T @ (y[ix]*np.sqrt(N/13))
            check('expanded_draw_weights', max(np.linalg.norm(As[rep]-Z @ Z.T), np.linalg.norm(cs[rep]-explicit_rhs)), 1e-10, direction=direction, rep=rep)
    # Real 60x1200 and 1200x60 production-shape tests use pilot-only streams.
    for direction in DIRECTIONS:
        for did in [1, 2]:
            data = construct(base(202610240702, direction, did), direction, {})
            tick = time.perf_counter()
            A, rhs, metric, L, models = setup(data)
            print('PILOT_SETUP', direction, did, 'seconds', time.perf_counter()-tick, 'L', L, flush=True)
            for budget in [30, 1200]:
                counts = rng.multinomial(budget, np.full(1200, 1/1200), size=4)
                As, cs, weights = weighted(data, counts)
                for method, model in models.items():
                    tick = time.perf_counter()
                    U = batch(data, As, cs, model['param'])
                    elapsed = time.perf_counter()-tick
                    key = dict(direction=direction, data_id=did, method=method, budget=budget)
                    single = batch(data, As[:1], cs[:1], model['param'])[0]
                    check('production_shape_batch', np.linalg.norm(U[0]-single), 1e-8, seconds=elapsed, steps=model['param']['steps'], **key)
                    mm = measures(data, U, model, weights, metric)
                    check('production_decomposition', np.max(mm['decomposition_absolute_error']), 1e-7, **key)
                    if method in ['Showalter', 'HBF', 'SOAR']:
                        fine = model['param'].copy(); fine['steps'] *= 2; fine['dt'] /= 2
                        refined = batch(data, As[:1], cs[:1], fine)[0]
                        check('production_grid_halving', np.linalg.norm(refined-single)/max(np.linalg.norm(refined), 1e-30), 1e-4, **key)
            zero_data = {**data, 'y': np.zeros_like(data['y'])}
            for method, model in models.items():
                zero = batch(zero_data, A[None], np.zeros_like(rhs)[None], model['param'])
                check('zero_response_state', np.max(np.abs(zero)), 1e-30, direction=direction, data_id=did, method=method)
    result = dict(passed=all(x['passed'] for x in checks), checks=checks, checks_count=len(checks), spectral_guard_active=True)
    save(out/'verification.json', result)
    snapshot = out/'source_snapshot'; snapshot.mkdir()
    for path in (HERE/'src').rglob('*.py'):
        target = snapshot/path.relative_to(HERE); target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    save(out/'frozen_sources.json', {str(p.relative_to(HERE)): sha(p) for p in (HERE/'src').rglob('*.py')})
    print('PILOT_RESULT', result['passed'], 'checks', len(checks), flush=True)
    assert result['passed'], [x for x in checks if not x['passed']]


def freeze():
    pilot = HERE/'outputs/pilot_01'
    verification = json.loads((pilot/'verification.json').read_text(encoding='utf8'))
    assert verification['passed']
    frozen = json.loads((pilot/'frozen_sources.json').read_text(encoding='utf8'))
    assert all(sha(HERE/k) == v for k, v in frozen.items())
    config = dict(name='Experiment III: native fixed-target first-order MSE calibration', date='2026-10-24',
                  data_seed=202610240704, sampling_seed=202610240703,
                  directions=DIRECTIONS, dimension=60, objects=1200, data_ids=list(range(1, 21)),
                  methods=METHODS, probability='UNI only; no OPT ranking or probability selection',
                  main=dict(data_id=1, budgets=[30, 60, 90, 150, 240, 360, 600, 1200, 2400, 4800, 9600, 19200, 38400], repetitions=500),
                  robustness=dict(data_ids=list(range(2, 21)), budgets=[1200, 19200], repetitions=500),
                  sensitivity=dict(data_ids=[1, 2], budgets=[1200, 19200], repetitions=100, c_values=[.5, 2.]),
                  zero_response=dict(data_ids=[1, 2], budgets=[30, 1200, 38400], repetitions=5),
                  data_model='Same column heterogeneous Gaussian and spiked-row Gaussian distributions as native I/II; fresh independent draws. Column beta norm=1; row signal RMS=1; sigma=.5.',
                  parameters='c=1 main. alpha=c trace(A)/60. L=N max squared atom norm, valid for every UNI sketch. Copy actual I/II six-method formulas, full finite-grid targets/tangents. Steps, grid and times fixed before counts; derivatives freeze all calibrated parameters. This is a new UNI-specific protocol, not identical to I/II self-consistent four-probability L.',
                  sampling='Counts ~ Multinomial(r,1/N), independent budgets. SeedSequence[sampling_seed,direction_index,data_id,stream,budget]. Exact with-replacement law, identical counts shared across all six methods. Row Gram AND RHS reweighted; column beta=X.T u.',
                  theory='J_i from actual full fixed-parameter recurrence/RK4, joint Gram/RHS for rows. C=N trace(Q J_centered J_centered.T)/target_norm_sq, Q=XX.T column and I row. Exact linear error Z=sum_i J_i(N_i*N/r-1), actual error e, remainder R=e-Z. Preserve e^2=Z^2+R^2+2<Z,R>. No curve fitting.',
                  inference='Conditional pointwise Student-t499 Monte Carlo mean intervals for 500 draws; sensitivity t99. Empirical/theory ratio is descriptive. No pass/fail gate based on ratio closeness, no extrapolated universal agreement. Robustness min/median/max over 20 independent data, not confidence intervals. No CLT or Gaussianity verification claimed.',
                  boundaries='No residual-event stopping or execution cap. All repeated draws, low coverage, extreme states and nonfinite failures retained. Zero-response relative gaps and calibration ratios NaN. Covariance trace zero is explicit. Separate coefficient and prediction risk. Large r>N only explores fixed-data limit, not acceleration. IV and real data not run.',
                  verification='Audit all rows from saved native states; replay all full targets, selected ordinary and extreme sketches; independent one-vector recurrences/RK4; fixed-parameter finite differences on data1/10/20 each direction, all six methods; grid refinement at data1/10/20 r30(if present)/1200/19200; expanded-draw weighting and centered covariance checks.',
                  replication_counts=dict(main=306000, sensitivity=9600, zero_response=360),
                  pilot=dict(path='outputs/pilot_01', checks=verification['checks_count'], verification_sha256=sha(pilot/'verification.json')))
    path = HERE/'formal_protocol.json'
    with path.open('x', encoding='utf8') as stream:
        stream.write(json.dumps(config, ensure_ascii=False, indent=2)+'\n')
    print('PROTOCOL_FROZEN', sha(path), flush=True)
