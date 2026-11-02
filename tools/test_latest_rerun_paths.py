"""Regression checks for public V -> stable V -> GDSC rerun handoffs.

Uses published scalar records and tiny synthetic target arrays, never formal
trajectories or real-data acquisition. Run: python -B tools/test_latest_rerun_paths.py
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STABLE = ROOT / 'Experiments/experiment5_support_stable_20261031'
sys.path.insert(0, str(STABLE))
from run_paths import historical_paths, historical_summary, verify_historical_sources

spec = importlib.util.spec_from_file_location(
    'gdsc_ln_run_for_test', ROOT / 'Experiments/experiment5_gdsc_liniu_20261101/run.py')
gdsc_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gdsc_run)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RerunHandoffs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='subsampling-path-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def layout(self, name, relative='formal', nested=False):
        root = self.base / name
        experiment = root / 'exp5' if nested else root
        formal = experiment / relative
        save(experiment / 'inputs/data_manifest.json', {})
        save(formal / 'target_manifest.json', {})
        save(formal / 'frozen_sources.json', {})
        return root, experiment, formal

    def test_public_cli_and_module_layouts(self):
        root, experiment, formal = self.layout('public', nested=True)
        self.assertEqual(historical_paths(root), (experiment, formal))
        self.assertEqual(historical_paths(experiment), (experiment, formal))

    def test_original_layout(self):
        root, experiment, formal = self.layout('original', 'outputs/formal_01')
        self.assertEqual(historical_paths(root), (experiment, formal))

    def test_missing_and_ambiguous_layouts_fail(self):
        with self.assertRaisesRegex(FileNotFoundError, 'No complete historical'):
            historical_paths(self.base)
        root, _, _ = self.layout('both')
        save(root / 'outputs/formal_01/target_manifest.json', {})
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            historical_paths(root)

    def test_calibration_alias_preserves_values_and_rejects_conflict(self):
        _, _, formal = self.layout('summary')
        row = dict(dataset='gdsc', method='Ridge', rule='OPT', budget=75,
                   relative_coefficient_error_mean=.25, empirical_to_first_order=1.2)
        pd.DataFrame([row]).to_csv(formal / 'summary.csv', index=False)
        self.assertEqual(historical_summary(formal).calibration.iloc[0], 1.2)
        row['calibration'] = 2.4
        pd.DataFrame([row]).to_csv(formal / 'summary.csv', index=False)
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            historical_summary(formal)

    def test_both_source_manifest_conventions_check_actual_sources(self):
        repo = self.base / 'repo'
        native = repo / 'Experiments/experiment5_native_realdata_20261025'
        source = native / 'src/native_exp5/kernel.py'
        source.parent.mkdir(parents=True)
        source.write_text('frozen source fixture\n', encoding='utf-8')
        legacy = {'src/native_exp5/kernel.py': digest(source), 'run.py': 'historical-only'}
        portable = {source.relative_to(repo).as_posix(): digest(source)}
        for manifest in (legacy, portable):
            self.assertEqual(len(verify_historical_sources(manifest, repo, native)), 1)
        source.write_text('changed source fixture\n', encoding='utf-8')
        for manifest in (legacy, portable):
            with self.assertRaisesRegex(ValueError, 'scientific source changed'):
                verify_historical_sources(manifest, repo, native)

    def test_gdsc_missing_validation_has_actionable_error(self):
        stable = self.base / 'stable'
        save(stable / 'protocol.json', {'version': 'v-fixture'})
        save(stable / 'results.json', {'completed': True})
        save(stable / 'support_gate.json', {'passed': True})
        with self.assertRaisesRegex(FileNotFoundError, 'compare_results.py'):
            gdsc_run.check_predecessor(stable, {'predecessor': 'v-fixture'})

    def test_comparison_cli_both_layouts_and_gdsc_handoff(self):
        evidence = ROOT / 'evidence/experiment5_stable'
        comparisons = []
        for layout, nested in [('outputs/formal_01', False), ('formal', True)]:
            with self.subTest(layout=layout):
                root, _, historical = self.layout('legacy' if not nested else 'portable', layout, nested)
                history = pd.read_csv(evidence / 'historical_summary_reference.csv')
                if nested:
                    history = history.rename(columns={'calibration': 'empirical_to_first_order'})
                history.to_csv(historical / 'summary.csv', index=False)
                stable = self.base / ('stable_' + str(nested))
                stable.mkdir()
                for name in ('protocol.json', 'results.json', 'support_gate.json', 'summary.csv'):
                    shutil.copy2(evidence / name, stable / name)
                (stable / 'draws/fixture').mkdir(parents=True)
                shutil.copy2(evidence / 'metrics.csv', stable / 'draws/fixture/metrics.csv')
                target_manifest = {}
                for dataset in ('gdsc', 'year'):
                    folder = stable / 'targets' / dataset
                    folder.mkdir(parents=True)
                    np.save(folder / 'C.npy', np.eye(2))
                    target_manifest[(folder / 'C.npy').relative_to(stable).as_posix()] = digest(folder / 'C.npy')
                    for method in ('Ridge', 'Landweber', 'Showalter', 'HBF', 'Nesterov', 'SOAR'):
                        old = historical / 'targets' / dataset / method / 'target.npy'
                        new = folder / method / 'target.npy'
                        old.parent.mkdir(parents=True)
                        new.parent.mkdir(parents=True)
                        np.save(old, np.array([1., 2.]))
                        np.save(new, np.array([1., 2.]) * (2 if method == 'Landweber' else 1))
                        target_manifest[new.relative_to(stable).as_posix()] = digest(new)
                save(stable / 'target_manifest.json', target_manifest)
                # Run from outside the repository: imports and paths must not depend on cwd.
                result = subprocess.run(
                    [sys.executable, '-B', str(STABLE / 'compare_results.py'),
                     '--output', str(stable), '--historical-root', str(root)],
                    cwd=self.base, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                receipt = json.loads((stable / 'independent_validation.json').read_text('utf-8'))
                self.assertEqual(receipt['records'], 12720)
                self.assertEqual(receipt['tasks'], 530)
                self.assertFalse(receipt['per_sketch_state_errors_recomputed'])
                for name in ('RESULTS.md', 'old_new_comparison.csv', 'old_new_comparison.png',
                             'old_new_comparison.pdf', 'target_changes.csv'):
                    self.assertTrue((stable / name).is_file(), name)
                targets = pd.read_csv(stable / 'target_changes.csv')
                self.assertTrue(targets.loc[targets.method == 'Landweber', 'relative_target_change'].eq(1).all())
                self.assertTrue(targets.loc[targets.method != 'Landweber', 'relative_target_change'].eq(0).all())
                gdsc_run.check_predecessor(stable, json.loads(
                    (ROOT / 'Experiments/experiment5_gdsc_liniu_20261101/protocol.json').read_text('utf-8')))
                comparisons.append(pd.read_csv(stable / 'old_new_comparison.csv'))
        pd.testing.assert_frame_equal(comparisons[0], comparisons[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
