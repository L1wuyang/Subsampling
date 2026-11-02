"""Read historical V outputs without changing their files or scientific values."""
import hashlib
from pathlib import Path


def historical_paths(root):
    """Return (experiment_root, formal_output) for public and original layouts.

    The public root CLI adds exp5/; its module writes inputs/ and formal/.
    The original experiment used inputs/ and outputs/formal_01/.
    """
    root = Path(root).expanduser().resolve()
    matches = []
    for base in (root, root / 'exp5'):
        if not (base / 'inputs/data_manifest.json').is_file():
            continue
        for formal in (base / 'formal', base / 'outputs/formal_01'):
            if (formal / 'target_manifest.json').is_file():
                matches.append((base, formal))
    if not matches:
        raise FileNotFoundError(
            f'No complete historical V layout found under {root}. Expected inputs/ '
            'and formal/ (root CLI: exp5/) or inputs/ and outputs/formal_01/. '
            'Run python run.py formal --experiment 5 --output NEW_DIRECTORY first.')
    if len(matches) != 1:
        raise ValueError(f'Ambiguous historical V outputs under {root}: '
                         + ', '.join(str(formal) for _, formal in matches))
    return matches[0]


def historical_summary(formal):
    """Normalize only the historical calibration column name for comparison."""
    import numpy as np
    import pandas as pd

    frame = pd.read_csv(Path(formal) / 'summary.csv')
    old, current = 'calibration', 'empirical_to_first_order'
    if old in frame and current in frame:
        if not np.allclose(frame[old], frame[current], rtol=1e-12, atol=1e-14):
            raise ValueError('Historical summary has conflicting calibration columns')
    elif old not in frame and current in frame:
        frame = frame.rename(columns={current: old})
    elif old not in frame:
        raise ValueError('Historical summary is missing calibration / empirical_to_first_order')
    required = ['dataset', 'method', 'rule', 'budget',
                'relative_coefficient_error_mean', old]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f'Historical summary is missing columns: {sorted(missing)}')
    return frame


def verify_historical_sources(manifest, repository, native_source):
    """Handle both manifest path conventions, checking every retained source.

    The original launcher, requirements and candidate protocol are not imported
    by the portable runner and are absent from the public core. All historical
    native Python sources and the final protocol must still match when listed.
    """
    portable = any(key.startswith(('Experiments/', 'repro1026/')) for key in manifest)
    base = Path(repository if portable else native_source).resolve()
    unavailable_launch_files = {'run.py', 'requirements.txt', 'protocol_candidate.json'}
    receipts = []
    for relative, expected in manifest.items():
        path = (base / relative).resolve()
        if not path.is_relative_to(base):
            raise ValueError(f'Historical source path escapes its root: {relative}')
        if not portable and relative in unavailable_launch_files and not path.exists():
            continue
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError(f'Historical scientific source changed: {path}')
        receipts.append(dict(path=str(path), sha256=actual))
    if not receipts:
        raise ValueError('Historical manifest did not identify any retained source')
    return receipts
