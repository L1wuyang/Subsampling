"""Regression tests for independently versioned code and immutable review data."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import build_release as release


class ReleaseVersionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'repo'
        self.source = self.base / 'data'
        (self.root / 'provenance').mkdir(parents=True)
        (self.root / 'docs').mkdir()
        (self.source / 'simulations').mkdir(parents=True)
        self.payload = b'fixed historical numerical records\n'
        (self.source / 'simulations/example.csv').write_bytes(self.payload)
        files = {'simulations/example.csv': self.record(self.payload)}
        data_archive = self.base / 'original.zip'
        release.write_zip(data_archive, files, lambda name: (self.source / name).read_bytes())
        self.value = {'schema': 1, 'version': 'v2026.10.30.2', 'source_commit': 'a' * 40,
                      'archive': {'name': 'Subsampling-review-data-v2026.10.30.2.zip',
                                  'url': 'https://github.com/L1wuyang/Subsampling/releases/download/v2026.10.30.2/Subsampling-review-data-v2026.10.30.2.zip',
                                  **self.record(data_archive.read_bytes())}, 'files': files}
        self.write('VERSION', b'v2026.11.02.1\n')
        self.write('provenance/review_data.json', json.dumps(self.value).encode())
        self.write('README.md', b'# Repository guide\n')
        self.write('docs/PAPER_RESULTS.md', b'# Paper result map\n')
        self.write('docs/RELEASE_NOTES.md', (
            b'# v2026.11.02.1\n'
            b'[Guide](../README.md) [Map](PAPER_RESULTS.md#figures) '
            b'[External](https://example.org/paper) [Section](#verification)\n'))
        self.write('run.py', b'print("fixture")\n')
        core = {str(p.relative_to(self.root)).replace('\\', '/'): self.record(p.read_bytes())
                for p in self.root.rglob('*') if p.is_file()}
        self.write('MANIFEST.json', json.dumps({'files': core}).encode())

    @staticmethod
    def record(payload):
        return {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}

    def write(self, name, payload):
        (self.root / name).write_bytes(payload)

    def test_new_code_release_retains_exact_old_data(self):
        output = self.base / 'release'
        report = release.build(output, self.source, root=self.root)
        self.assertEqual(report['version'], 'v2026.11.02.1')
        self.assertEqual(report['review_data_version'], 'v2026.10.30.2')
        self.assertEqual(report['data_source_commit'], 'a' * 40)
        self.assertEqual((output / self.value['archive']['name']).read_bytes(),
                         (self.base / 'original.zip').read_bytes())
        notes = (output / 'release_notes.md').read_text(encoding='utf-8')
        self.assertIn('https://github.com/L1wuyang/Subsampling/blob/v2026.11.02.1/README.md', notes)
        self.assertIn('https://github.com/L1wuyang/Subsampling/blob/v2026.11.02.1/docs/PAPER_RESULTS.md#figures', notes)
        self.assertIn('[External](https://example.org/paper) [Section](#verification)', notes)
        self.assertIn('[Guide](../README.md)', (self.root / 'docs/RELEASE_NOTES.md').read_text())
        with zipfile.ZipFile(output / 'Subsampling-core-v2026.11.02.1.zip') as archive:
            self.assertEqual(archive.read('Subsampling-v2026.11.02.1/VERSION'), b'v2026.11.02.1\n')
            self.assertFalse(any('simulations/' in name for name in archive.namelist()))
        with self.assertRaisesRegex(ValueError, 'new release output'):
            release.build(output, self.source, root=self.root)

    def test_data_url_cannot_silently_follow_code_version(self):
        self.value['archive']['url'] = self.value['archive']['url'].replace('v2026.10.30.2', 'v2026.11.02.1')
        self.write('provenance/review_data.json', json.dumps(self.value).encode())
        with self.assertRaisesRegex(ValueError, 'asset name or URL'):
            release.descriptor(self.root)

    def test_invalid_data_version_rejected(self):
        self.value['version'] = '../latest'
        self.write('provenance/review_data.json', json.dumps(self.value).encode())
        with self.assertRaisesRegex(ValueError, 'schema or version'):
            release.descriptor(self.root)

    def test_changed_original_data_rejected(self):
        (self.source / 'simulations/example.csv').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            release.build(self.base / 'release', self.source, root=self.root)

    def test_changed_core_rejected(self):
        self.write('run.py', b'changed')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            release.build(self.base / 'release', self.source, root=self.root)

    def test_release_link_cannot_escape_repository(self):
        self.write('docs/RELEASE_NOTES.md', b'# v2026.11.02.1\n[Outside](../../secret.md)\n')
        with self.assertRaisesRegex(ValueError, 'escapes the repository'):
            release.release_notes(self.root, 'v2026.11.02.1')

    def test_missing_release_document_rejected(self):
        self.write('docs/RELEASE_NOTES.md', b'# v2026.11.02.1\n[Missing](MISSING.md)\n')
        with self.assertRaisesRegex(ValueError, 'Missing or unsafe'):
            release.release_notes(self.root, 'v2026.11.02.1')


if __name__ == '__main__':
    unittest.main()
