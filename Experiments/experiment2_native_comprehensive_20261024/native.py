"""Actual fixed-parameter ROW recurrences with coupled Gram/RHS tangents.

The integrator is a byte-identical local copy of the verified Experiment-I
kernel. Here the returned state IS beta, with sampled A AND sampled c.
"""
from integrator_reference import integrate, parameters, optimal, guard, METHODS, RULES, np, sla


def baselines(X, epsilon):
    A = X.T @ X
    norms = np.sum(X * X, axis=1)
    leverage = np.maximum(np.sum(X.T * sla.solve(A, X.T, assume_a='pos'), axis=0), 0)
    n = len(X)
    return A, dict(UNI=np.full(n, 1 / n),
                  NORM=(1-epsilon)*norms/norms.sum()+epsilon/n,
                  LEV=(1-epsilon)*leverage/leverage.sum()+epsilon/n)


def full(X, A, y, param, gram_only=False):
    c = X.T @ y
    if param['method'] == 'Ridge':
        T = A + param['alpha'] * np.eye(A.shape[0])
        beta = sla.solve(T, c, assume_a='pos')
        rhs = -X.T * (X @ beta)[None, :]
        if not gram_only:
            rhs += X.T * y[None, :]
        return beta, sla.solve(T, rhs, assume_a='pos')

    def force(W, t):
        Z = -A @ W
        Z[:, 0] += t * c
        Z[:, 1:] -= X.T * (X @ W[:, 0])[None, :]
        if not gram_only:
            Z[:, 1:] += t * X.T * y[None, :]
        return Z

    W = integrate(param, force, (X.shape[1], len(X)+1))
    return W[:, 0], W[:, 1:]


def batch(As, cs, param):
    if param['method'] == 'Ridge':
        return np.linalg.solve(As+param['alpha']*np.eye(As.shape[1]), cs[..., None])[..., 0]

    def force(B, t):
        return t*cs-np.einsum('bij,bj->bi', As, B, optimize=False)

    return integrate(param, force, cs.shape)


def setup(X, y, c=1., epsilon=.01):
    A, ps = baselines(X, epsilon)
    norms = np.sum(X*X, axis=1)
    alpha = c*np.trace(A)/X.shape[1]
    L = max(float(np.max(norms/pi)) for pi in ps.values())
    history = []
    for trial in range(10):
        models = {}
        required = L
        for method in METHODS:
            param = parameters(method, alpha, L)
            beta, J = full(X, A, y, param)
            scores = np.linalg.norm(J, axis=0)
            pi = optimal(scores, epsilon)
            models[method] = dict(param=param, beta=beta, J=J, scores=scores, pi=pi)
            if method != 'Ridge':
                required = max(required, float(np.max(norms/pi)))
        history.append(dict(trial=trial, L=L, required=required))
        if required <= L*(1+1e-12):
            return A, ps, models, history
        L = max(2*L, 1.01*required) if trial < 7 else len(X)/epsilon*norms.max()
    raise RuntimeError('Deterministic row-atom bound construction did not converge')


def matrices(X, y, pi, uniforms, spike_mask=None):
    cdf = np.cumsum(pi)
    cdf[-1] = 1.
    As, cs, unique, spike_draws = [], [], [], []
    for row in uniforms:
        ix = np.searchsorted(cdf, row, side='right')
        counts = np.bincount(ix, minlength=len(X))
        nz = np.flatnonzero(counts)
        weights = counts[nz]/(len(row)*pi[nz])
        Z = X[nz]*np.sqrt(weights)[:, None]
        As.append(Z.T @ Z)
        cs.append(X[nz].T @ (weights*y[nz]))
        unique.append(len(nz))
        spike_draws.append(int(spike_mask[ix].sum()) if spike_mask is not None else 0)
    return np.array(As), np.array(cs), np.array(unique), np.array(spike_draws)
