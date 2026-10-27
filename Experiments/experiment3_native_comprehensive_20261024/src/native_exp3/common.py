"""Data, metrics, weighted draws and fixed native targets for Experiment III."""
import os
for variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[variable] = '1'
from pathlib import Path
import csv
import hashlib
import json
import time
import numpy as np
from . import column_reference as col
from . import row_reference as row

HERE = Path(__file__).resolve().parents[2]
ROOT = HERE.parents[1]
METHODS = col.METHODS
DIRECTIONS = ['column', 'row']


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')


def write(path, rows):
    if not rows: return
    with Path(path).open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sources():
    return sorted([HERE/'run.py', HERE/'requirements.txt', HERE/'formal_protocol.json'] + list((HERE/'src').rglob('*.py')))


def base(seed, direction, did, dimension=60, objects=1200):
    rng = np.random.default_rng(np.random.SeedSequence([seed, DIRECTIONS.index(direction), did]))
    if direction == 'column':
        return dict(G=rng.normal(size=(dimension, objects)), scale_z=rng.normal(size=objects),
                    beta_direction=rng.normal(size=objects), standard_noise=rng.normal(size=dimension))
    mask = np.zeros(objects, dtype=bool)
    mask[rng.choice(objects, round(.03*objects), replace=False)] = True
    return dict(G=rng.normal(size=(objects, dimension)), spike_noise=rng.normal(size=(objects, dimension)),
                spike_mask=mask, beta_direction=rng.normal(size=dimension), standard_noise=rng.normal(size=objects))


def construct(raw, direction, arm):
    sigma = arm.get('sigma', .5)
    if direction == 'column':
        scales = np.exp(raw['scale_z'])
        scales = np.minimum(scales, np.quantile(scales, .98, method='linear'))
        scales /= np.sqrt(np.mean(scales**2))
        X = raw['G']*scales/np.sqrt(len(raw['standard_noise']))
        beta = raw['beta_direction']/np.linalg.norm(raw['beta_direction'])
        covariance = scales**2/len(X)
        mask = np.zeros(X.shape[1], dtype=bool)
    else:
        mask = raw['spike_mask']
        design = .25*raw['G']+8*raw['spike_noise']*mask[:, None]
        scale = np.sqrt(design.shape[1]/np.sum(design**2))
        X = scale*design
        beta = raw['beta_direction'].copy()
        beta /= np.linalg.norm(X @ beta)/np.sqrt(len(X))
        covariance = np.full(X.shape[1], scale**2*(.25**2+mask.mean()*8**2))
    y = X @ beta+sigma*raw['standard_noise']
    if arm.get('zero_response'): y = np.zeros_like(y)
    return dict(X=X, y=y, beta0=beta, covariance=covariance, spike_mask=mask,
                noise_norm=float(sigma*np.linalg.norm(raw['standard_noise'])), direction=direction)


def load(out, direction, did, arm):
    with np.load(Path(out)/'data'/f'{direction}_{did:02d}.npz') as raw:
        return construct(raw, direction, arm)


def setup(data, c=1.):
    X, y, direction = data['X'], data['y'], data['direction']
    atoms = X if direction == 'column' else X.T
    A = atoms @ atoms.T
    rhs = y if direction == 'column' else X.T @ y
    metric = A if direction == 'column' else np.eye(A.shape[0])
    N = atoms.shape[1]
    # UNI alone is used in this experiment. This deterministic atom bound
    # covers every possible with-replacement sketch, including repeated atoms.
    L = float(N*np.sum(atoms**2, axis=0).max())
    alpha = float(c*np.trace(A)/A.shape[0])
    models = {}
    for method in METHODS:
        par = col.parameters(method, alpha, L)
        target, J = (col.full if direction == 'column' else row.full)(X, A, y, par)
        centered = J-J.mean(axis=1, keepdims=True)
        covariance = N*(centered @ centered.T)
        den = float(target @ metric @ target)
        trace = float(np.sum(metric*covariance.T))
        assert trace >= -1e-12
        models[method] = dict(param=par, target=target, J=J, centered_J=centered,
                              trace=max(0., trace), denominator=den,
                              C=trace/den if den > 1e-24 else None)
    return A, rhs, metric, L, models


def weighted(data, counts):
    X = data['X']; N = counts.shape[1]
    weights = counts*(N/counts.sum(axis=1))[:, None]
    atoms = X if data['direction'] == 'column' else X.T
    As = np.array([(atoms*w) @ atoms.T for w in weights])
    cs = np.broadcast_to(data['y'], (len(counts), len(data['y']))).copy() if data['direction'] == 'column' else (weights*data['y']) @ X
    return As, cs, weights


def batch(data, As, cs, par):
    if data['direction'] == 'column': return col.batch(As, data['y'], par)
    return row.batch(As, cs, par)


def coefficients(data, states):
    return states @ data['X'] if data['direction'] == 'column' else states


def squared(states, metric):
    return np.einsum('bi,ij,bj->b', states, metric, states, optimize=True)


def measures(data, states, model, weights, metric):
    error = states-model['target']
    linear = (weights-1) @ model['J'].T
    remainder = error-linear
    absolute = squared(error, metric)
    lin = squared(linear, metric)
    rem = squared(remainder, metric)
    cross = 2*np.einsum('bi,ij,bj->b', linear, metric, remainder, optimize=True)
    den = model['denominator']
    norm = den if den > 1e-24 else np.nan
    B = coefficients(data, states)
    delta = B-data['beta0']
    signal = data['X'] @ data['beta0']
    signal_delta = delta @ data['X'].T
    future = np.sum(delta**2*data['covariance'], axis=1)
    return dict(absolute_gap=absolute, relative_gap=absolute/norm,
                linear_relative=lin/norm, remainder_relative=rem/norm, cross_relative=cross/norm,
                decomposition_absolute_error=np.abs(absolute-lin-rem-cross),
                true_coef_rel_sq=np.sum(delta**2, axis=1)/float(data['beta0'] @ data['beta0']),
                design_signal_rel_sq=np.sum(signal_delta**2, axis=1)/float(signal @ signal),
                population_signal_rel_sq=future/float(np.sum(data['beta0']**2*data['covariance'])),
                population_response_mse=future+float(data.get('sigma', .5))**2,
                residual_norm=np.linalg.norm(data['y']-B @ data['X'].T, axis=1))
