"""Focused offline checks for the Brás transfer queue and restart behavior."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("transfer_bras.py")
spec = importlib.util.spec_from_file_location("transfer_bras", SCRIPT)
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class TransferBrasTests(unittest.TestCase):
    def test_manifest_maps_every_capture_once(self):
        _, jobs = transfer.load_jobs()
        self.assertEqual(len(jobs), 649)
        self.assertEqual(len({job[0] for job in jobs}), len(jobs))
        raw = next(job for job in jobs if job[0] == "2025-11-09-07-24-24-340:raw")
        images = next(job for job in jobs if job[0] == "2025-11-09-07-24-24-340:images")
        self.assertTrue(raw[2].endswith("D1P1/2025-11-09-07-24-24-340"))
        self.assertTrue(images[2].endswith("20251109-072424340"))
        self.assertTrue(images[3].endswith("2025-11-09-07-24-24-340"))

    def test_failed_job_remains_pending_and_restart_skips_completed_job(self):
        digest, all_jobs = transfer.load_jobs()
        jobs = all_jobs[:3]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.multiple(
                transfer,
                HERE=root,
                STATE=root / "state.json",
                LOCK=root / "lock",
                LOG_DIR=root / "logs",
            ):
                responses = [mock.Mock(returncode=0), mock.Mock(returncode=3)]
                with mock.patch.object(transfer.subprocess, "run", side_effect=responses) as run:
                    self.assertEqual(transfer.run_jobs(digest, jobs, minutes=5, max_jobs=None), 3)
                    self.assertEqual(run.call_count, 2)
                self.assertEqual(transfer.load_state(digest, {job[0] for job in jobs}), {"gpkg"})
                with mock.patch.object(transfer.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
                    self.assertEqual(transfer.run_jobs(digest, jobs, minutes=5, max_jobs=None), 0)
                    self.assertEqual(run.call_count, 2)
                    self.assertIn("/raw/", run.call_args_list[0].args[0][3])
                self.assertEqual(len(transfer.load_state(digest, {job[0] for job in jobs})), 3)

    def test_soft_time_cutoff_does_not_mark_a_job_complete(self):
        digest, all_jobs = transfer.load_jobs()
        jobs = all_jobs[:1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.multiple(
                transfer,
                HERE=root,
                STATE=root / "state.json",
                LOCK=root / "lock",
                LOG_DIR=root / "logs",
            ):
                with mock.patch.object(transfer.subprocess, "run", return_value=mock.Mock(returncode=10)) as run:
                    self.assertEqual(transfer.run_jobs(digest, jobs, minutes=5, max_jobs=None), 0)
                    self.assertIn("--cutoff-mode", run.call_args.args[0])
                    self.assertIn("SOFT", run.call_args.args[0])
                self.assertFalse((root / "state.json").exists())


if __name__ == "__main__":
    unittest.main()
