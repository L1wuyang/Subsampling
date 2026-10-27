from native import *
from pathlib import Path
import hashlib, json, csv, shutil, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE/'outputs/formal_01'


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')


def write(path, rows):
    with Path(path).open('w', newline='', encoding='utf8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def make_base(seed, did, n=1200, p=60):
    rng = np.random.default_rng(np.random.SeedSequence([seed, did]))
    mask = np.zeros(n, dtype=bool)
    mask[rng.choice(n, int(round(.03*n)), replace=False)] = True
    return dict(G=rng.normal(size=(n, p)), spike_noise=rng.normal(size=(n, p)),
                spike_mask=mask, beta_direction=rng.normal(size=p), standard_noise=rng.normal(size=n))


def construct(base, arm):
    mask = base['spike_mask']
    raw = .25*base['G']+arm['spike_scale']*base['spike_noise']*mask[:, None]
    p = raw.shape[1]
    scale = np.sqrt(p/np.sum(raw*raw))
    X = scale*raw
    beta = base['beta_direction'].copy()
    beta /= np.linalg.norm(X @ beta)/np.sqrt(len(X))
    y = X @ beta+arm['sigma']*base['standard_noise']
    if arm.get('zero_response'):
        y = np.zeros_like(y)
    # New independent rows: 3% Gaussian-spike mixture, with training scale fixed.
    covariance_scalar = scale**2*(.25**2+float(mask.mean())*arm['spike_scale']**2)
    return X, y, beta, mask, covariance_scalar, scale


def load(did, arm):
    with np.load(HERE/'data'/f'data_{did:02d}.npz') as a:
        return construct(a, arm)


def metrics(B, target, X, y, beta0, mask, covariance_scalar, sigma):
    delta = B-beta0
    signal = X @ beta0
    signal_error = delta @ X.T
    gap = np.sum((B-target)**2, axis=1)
    norm = float(target @ target)
    true_sq = np.sum(delta**2, axis=1)
    den = float(beta0 @ beta0)
    return dict(absolute_gap=gap,
                relative_gap=gap/norm if norm > 1e-24 else np.full(len(B), np.nan),
                true_coef_rel_sq=true_sq/den,
                design_signal_rel_sq=np.sum(signal_error**2, axis=1)/float(signal @ signal),
                population_signal_rel_sq=true_sq/den,
                population_response_mse=covariance_scalar*true_sq+sigma**2,
                design_spike_rel_sq=np.sum(signal_error[:, mask]**2, axis=1)/float(signal[mask] @ signal[mask]),
                design_background_rel_sq=np.sum(signal_error[:, ~mask]**2, axis=1)/float(signal[~mask] @ signal[~mask]),
                residual_norm=np.linalg.norm(y-B @ X.T, axis=1))
