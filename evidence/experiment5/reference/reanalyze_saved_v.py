"""Two-sided review of saved V records, without importing/running any estimator.

Requires the full project archive, not just the paper's source ZIP.
Original protocols, one-sided statistics and formal outputs are read only.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t, ttest_rel

METHODS = ['Ridge', 'Landweber', 'Showalter', 'HBF', 'Nesterov', 'SOAR']


def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def holm(values):
    p = np.asarray(values, dtype=float)
    order = np.argsort(p, kind='stable')
    out = np.empty_like(p)
    out[order] = np.minimum(1., np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New review directory')
    args = parser.parse_args()
    root = args.project_root.resolve()
    folder = root/'Experiments/experiment5_native_realdata_20261025'
    formal = folder/'outputs/formal_01'
    files = sorted((formal/'draws').glob('*/*.csv'))
    assert len(files) == 530
    input_hashes = {p.relative_to(root).as_posix(): sha(p) for p in files}
    for p in [folder/'formal_protocol.json', formal/'protocol.json', formal/'primary_comparisons.csv']:
        input_hashes[p.relative_to(root).as_posix()] = sha(p)
    f = pd.concat([pd.read_csv(p, float_precision='round_trip') for p in files], ignore_index=True)
    keys = ['dataset', 'budget', 'rep', 'method', 'rule']
    assert len(f) == 12720 and not f.duplicated(keys).any()
    assert (f.status == 'complete').all()
    rows = []
    for tag, budget, reps in [('gdsc', 749, 30), ('year', 5000, 50)]:
        for method in METHODS:
            g = f[(f.dataset == tag) & (f.budget == budget) & (f.method == method)]
            a = g[g.rule == 'OPT'].set_index('rep').relative_coefficient_error.sort_index()
            assert a.index.tolist() == list(range(reps))
            for rule in ['UNI', 'NORM', 'LEV']:
                b = g[g.rule == rule].set_index('rep').relative_coefficient_error.sort_index()
                assert a.index.equals(b.index)
                delta = a.to_numpy()-b.to_numpy()
                assert np.isfinite(delta).all()
                se = float(delta.std(ddof=1)/np.sqrt(reps))
                width = float(t.ppf(.975, reps-1)*se)
                test = ttest_rel(a.to_numpy(), b.to_numpy(), alternative='two-sided')
                assert np.isfinite(test.pvalue)
                one_sided = ttest_rel(a.to_numpy(), b.to_numpy(), alternative='less')
                rows.append(dict(dataset=tag, budget=budget, method=method, comparison='OPT-minus-'+rule,
                                 n=reps, difference=float(delta.mean()), se=se,
                                 lower=float(delta.mean()-width), upper=float(delta.mean()+width),
                                 t_statistic=float(test.statistic), p_raw=float(test.pvalue),
                                 original_one_sided_p=float(one_sided.pvalue)))
    result = pd.DataFrame(rows)
    result['p_holm'] = holm(result.p_raw)
    result['supports_OPT_lower'] = (result.difference < 0) & (result.p_holm < .05)
    old = pd.read_csv(formal/'primary_comparisons.csv', float_precision='round_trip')
    ix = ['dataset', 'budget', 'method', 'comparison']
    merged = result.merge(old, on=ix, suffixes=('_review', '_original'), validate='one_to_one')
    assert len(merged) == 36
    assert np.allclose(merged.original_one_sided_p, merged.p_raw_original, rtol=2e-12, atol=0)
    assert np.allclose(merged.difference_review, merged.difference_original, rtol=2e-12, atol=2e-15)
    assert result.supports_OPT_lower.all()
    assert all(sha(root/name) == digest for name, digest in input_hashes.items())
    out = args.output.resolve()
    assert not out.exists(), 'Keep previous review outputs; use a new directory'
    out.mkdir(parents=True)
    result.to_csv(out/'paired_comparisons_two_sided.csv', index=False, float_format='%.17g')
    report = dict(date='2026-10-25',analysis_type='post-audit two-sided reporting revision; not a new experiment',
                  original_analysis='one-sided less; original records and analysis outputs preserved',
                  protocol_note='Budgets and the 36-pair family were specified; the frozen prose did not specify sidedness.',
                  inference='conditional paired Student t, two-sided, Holm over all 36 pairs, difference OPT-minus-baseline',
                  intervals='unadjusted pointwise two-sided 95% intervals; not simultaneous',
                  family_includes_gdsc_norm_uni_duplicate=True,draw_csv_files=len(files),saved_records=len(f),
                  comparisons=len(result),supports_OPT_lower=int(result.supports_OPT_lower.sum()),
                  max_two_sided_holm_p=float(result.p_holm.max()),
                  no_estimator_execution=True,no_random_draws_generated=True,all_inputs_unchanged=True,
                  input_hashes=input_hashes)
    (out/'inference_revision.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'}, indent=2))


if __name__ == '__main__':
    main()
