"""Regression checks for Ridge launch gates; synthetic fixtures are not paper runs.

Run from the repository root: python -B tools/test_ridge_standalone.py
The two miniature CLI runs use 5-by-12 inputs and 60 scalar outcomes each.
"""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Experiments/ridge_liniu_ablation_20261101"
sys.path.insert(0, str(SOURCE))
import core
import run_experiment


class StandaloneRidgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ridge_launch_test_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.prepared = self.root / "prepared"
        (self.prepared / "states").mkdir(parents=True)
        (self.prepared / "source_snapshot").mkdir()
        # The formal scope exercises the production launch branch. The test
        # version, small dimensions and temporary paths identify this fixture.
        self.config = dict(version="test-only-ridge-launch-v1",
                           scope="formal_reused_inputs_ablation", data_ids=[1, 2],
                           budgets=[3, 7], repetitions=3, sampling_seed=481516,
                           rules=list(core.RULES), primary=dict(budget=3))
        core.save(self.prepared / "protocol.json", self.config)
        rng = core.np.random.default_rng(314159)
        diagnostics = []
        for data_id in self.config["data_ids"]:
            state, rows = core.setup(rng.normal(size=(5, 12)), rng.normal(size=5), 1.7, .01)
            core.save_npz(self.prepared / "states" / f"data_{data_id:02d}.npz", **state)
            diagnostics.extend(dict(data_id=data_id, **row) for row in rows)
        core.write_rows(self.prepared / "score_diagnostics.csv", diagnostics)
        self.sources = {name: core.digest(SOURCE / name) for name in core.SOURCE_FILES}
        for name in core.SOURCE_FILES:
            shutil.copy2(SOURCE / name, self.prepared / "source_snapshot" / name)
        self.seal()
        self.pilot = self.root / "synthetic_pilot.json"
        core.save(self.pilot, dict(passed=True, sources=self.sources,
                                   scope="launch-test fixture, not scientific certification"))
        self.output = self.root / "output"

    def seal(self):
        files = {path.relative_to(self.prepared).as_posix(): core.digest(path)
                 for path in self.prepared.rglob("*")
                 if path.is_file() and path.name != "seal.json"}
        core.save(self.prepared / "seal.json", dict(
            files=files, sources=self.sources, source_directory=str(SOURCE)))

    def launch(self, predecessor=None):
        with contextlib.redirect_stdout(io.StringIO()):
            run_experiment.run(self.prepared, self.output, predecessor, self.pilot, 1)

    def complete_predecessor(self):
        predecessor = self.root / "synthetic_predecessor"
        core.save(predecessor / "protocol.json", dict(version=core.V_VERSION))
        core.save(predecessor / "status.json", dict(completed=True))
        core.save(predecessor / "results.json", dict(completed=True, records=12720))
        core.save(predecessor / "support_gate.json", dict(passed=True))
        core.save(predecessor / "independent_validation.json",
                  dict(passed=True, records=12720, tasks=530, opt_lowest_cells=0))
        for name in ("RESULTS.md", "old_new_comparison.csv", "target_changes.csv",
                     "old_new_comparison.png"):
            (predecessor / name).write_text("synthetic gate fixture only", encoding="utf-8")
        return predecessor

    def run_cli(self, output, predecessor=None):
        command = [sys.executable, "-B", str(SOURCE / "run_experiment.py"), "run",
                   "--prepared", str(self.prepared), "--output", str(output),
                   "--pilot", str(self.pilot), "--workers", "1"]
        if predecessor is not None:
            command += ["--predecessor", str(predecessor)]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(core.read(output / "execution.json")["completed"])
        self.assertEqual(core.read(output / "independent_validation.json")["rows"], 60)

    def test_standalone_cli_and_optional_queue_keep_identical_sampling(self):
        self.run_cli(self.output)
        receipt = core.read(self.output / "release_gate.json")
        self.assertEqual(receipt["mode"], "standalone")
        self.assertIsNone(receipt["predecessor"])
        self.assertEqual(receipt["files"], {})
        predecessor = self.complete_predecessor()
        queued_output = self.root / "queued_output"
        self.run_cli(queued_output, predecessor)
        queued_receipt = core.read(queued_output / "release_gate.json")
        self.assertEqual(queued_receipt["mode"], "optional_predecessor")
        self.assertEqual(len(queued_receipt["files"]), 6)
        self.assertEqual((self.output / "metrics.csv").read_bytes(),
                         (queued_output / "metrics.csv").read_bytes())
        for data_id in self.config["data_ids"]:
            for budget in self.config["budgets"]:
                name = core.task_key(data_id, budget) + ".npz"
                with core.np.load(self.output / "tasks" / name) as standalone, \
                     core.np.load(queued_output / "tasks" / name) as queued:
                    for key in standalone.files:
                        core.np.testing.assert_array_equal(standalone[key], queued[key])

    def test_failed_pilot_still_blocks_standalone(self):
        core.save(self.pilot, dict(passed=False, sources=self.sources))
        with self.assertRaisesRegex(ValueError, "Pilot not passed"):
            self.launch()
        self.assertFalse(self.output.exists())

    def test_pilot_from_other_sources_still_blocks_standalone(self):
        core.save(self.pilot, dict(passed=True, sources={}))
        with self.assertRaisesRegex(ValueError, "Pilot not passed"):
            self.launch()
        self.assertFalse(self.output.exists())

    def test_prepared_input_protocol_and_source_tampering_are_rejected(self):
        for name in ("states/data_01.npz", "protocol.json", "source_snapshot/core.py"):
            with self.subTest(name=name):
                path = self.prepared / name
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b" ")
                    with self.assertRaisesRegex(ValueError, "Prepared artifact changed"):
                        self.launch()
                    self.assertFalse(self.output.exists())
                finally:
                    path.write_bytes(original)

    def test_pilot_scope_cannot_launch_formal_execution(self):
        self.config["scope"] = "pilot_only"
        core.save(self.prepared / "protocol.json", self.config)
        self.seal()
        with self.assertRaisesRegex(ValueError, "Only the frozen formal protocol"):
            self.launch()

    def test_explicit_missing_predecessor_is_not_ignored(self):
        with self.assertRaisesRegex(ValueError, "Predecessor release gate closed"):
            self.launch(self.root / "missing")
        self.assertFalse(self.output.exists())

    def test_explicit_failed_predecessor_is_not_ignored(self):
        predecessor = self.complete_predecessor()
        core.save(predecessor / "support_gate.json", dict(passed=False))
        with self.assertRaisesRegex(ValueError, "Predecessor release gate closed"):
            self.launch(predecessor)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
