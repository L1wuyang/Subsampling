"""Check I/II report presentation through the public analysis adapter, without estimators."""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repro1026 import exp12


class PublicReportTests(unittest.TestCase):
    def test_formal_and_smoke_reports_after_frozen_analysis(self):
        root = Path(__file__).resolve().parents[1]
        for experiment, source, note, population in (
            (1, 'experiment1_native_comprehensive_20261024',
             'New draft only; historical manuscripts preserved.', 'data sets'),
            (2, 'experiment2_native_comprehensive_20261024',
             'New draft only; historical versions preserved.', 'spiked-row data sets'),
        ):
            frozen = (root/'Experiments'/source/'analyze.py').read_bytes()
            self.assertIn(note.encode(), frozen)
            for smoke in (False, True):
                with self.subTest(experiment=experiment, smoke=smoke), tempfile.TemporaryDirectory() as folder:
                    run = Path(folder)
                    formal = run/'outputs/formal_01'
                    formal.mkdir(parents=True)
                    (formal/'protocol.json').write_text(json.dumps({'smoke_only': smoke}))
                    original_summary = {'main_rows': 9, 'robustness_rows': 4, 'zero_rows': 1,
                                        'mean_reversals': [{'ratio': 1.25}], 'primary_p': 0.2984}
                    html = (f'<h1>Experiment {experiment}</h1><p>40 independent {population}; '
                            f'13 budgets; 40 paired sketches. All outcomes retained. {note}</p>'
                            '<pre>{"primary_p": 0.2984, "ratio": 1.25}</pre>'
                            '<a href="figures/result.pdf">Results</a>')

                    def analysis_main():
                        (formal/'summary.json').write_text(json.dumps(original_summary))
                        (formal/'index.html').write_text(html, encoding='utf-8')

                    with patch.object(exp12, '_runtime', return_value=(None, object(), {}, root)), \
                         patch.object(exp12, '_module', return_value=SimpleNamespace(main=analysis_main)), \
                         patch.dict(os.environ):
                        exp12._analyze(experiment, root, run)
                    rendered = (formal/'index.html').read_text(encoding='utf-8')
                    self.assertNotIn('New draft only', rendered)
                    self.assertNotIn('historical manuscripts preserved', rendered)
                    self.assertNotIn('historical versions preserved', rendered)
                    self.assertIn('All outcomes retained.', rendered)
                    self.assertIn('<pre>{"primary_p": 0.2984, "ratio": 1.25}</pre>', rendered)
                    self.assertIn('href="figures/result.pdf"', rendered)
                    self.assertEqual('SMOKE: reduced engineering check' in rendered, smoke)
                    self.assertIn('2 paired sketches.' if smoke else '40 paired sketches.', rendered)
                    summary = json.loads((formal/'summary.json').read_text())
                    self.assertEqual({k: summary[k] for k in original_summary}, original_summary)
                    self.assertEqual(summary['reproduction_mode'], 'smoke' if smoke else 'formal')
                    self.assertEqual(summary['paper_results'], not smoke)
            self.assertEqual((root/'Experiments'/source/'analyze.py').read_bytes(), frozen)


if __name__ == '__main__':
    unittest.main()
