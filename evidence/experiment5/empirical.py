"""Verify saved Experiment V metrics and reproduce the current empirical figures.

Usage: python -B evidence/experiment5/empirical.py --output runs/exp5_empirical
No model fitting, sampling, p-values or mean confidence intervals are generated.
Historical one-/two-sided analyses remain accessible through reanalyze.py.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
sys.path.insert(0, str(REPOSITORY))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    immutable = ('Experiments', 'Data', 'provenance', 'repro1026', 'docs',
                 'validation', 'simulations', 'evidence', 'tools', '.git')
    if output.exists() or REPOSITORY.is_relative_to(output) or any(output.is_relative_to(REPOSITORY/name) for name in immutable):
        raise ValueError('Use a new output directory outside repository input directories')
    from reanalyze import verify_archive, FORMAL
    payloads, _ = verify_archive()
    import pandas as pd
    from repro1026.empirical_v import report, save
    files = sorted(name for name in payloads if name.startswith(FORMAL.as_posix()+'/draws/') and name.endswith('.csv'))
    frame = pd.concat([pd.read_csv(io.BytesIO(payloads[name]), float_precision='round_trip') for name in files], ignore_index=True)
    if len(files) != 530 or len(frame) != 12720:
        raise ValueError('Expected the frozen 530 CSVs and 12,720 records')
    config = json.loads(payloads[FORMAL.as_posix()+'/protocol.json'])
    from repro1026.empirical_v import METHODS
    targets = {(tag, method): json.loads(payloads[FORMAL.as_posix()+f'/targets/{tag}/{method}/summary.json'])
               for tag in ('gdsc', 'year') for method in METHODS}
    reference = json.loads((HERE/'paper_plot_reference.json').read_text(encoding='utf8'))
    output.mkdir(parents=True, exist_ok=False)
    result = report(frame, output, config=config, reference=reference, targets=targets)
    if result['method_budget_cells'] != 78 or result['opt_strictly_lowest_empirical_mean_cells'] != 78 or result['visible_target_points'] != 276:
        raise ValueError('Empirical summaries differ from the manuscript')
    save(output/'saved_evidence_verification.json', dict(archive_verified=True,
        archive_sha256=hashlib.sha256((HERE/'saved_records.tar.gz').read_bytes()).hexdigest(),
        archive_members=len(payloads), draw_csv_files=len(files), records=len(frame),
        frozen_sources_modified=False, numerical_trajectories_executed=0,
        reference_sha256=hashlib.sha256((HERE/'paper_plot_reference.json').read_bytes()).hexdigest(),
        historical_mean_tests_used_as_current_evidence=False))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
