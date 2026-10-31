import contextlib
import csv
import errno
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import dq_scan


SCRIPT = Path(__file__).resolve().parents[1] / "dq_scan.py"


class CliInputTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def assert_input_error(self, result, path):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("error:"), result.stderr)
        self.assertIn(str(path), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_file(self):
        path = self.directory / "missing.csv"
        self.assert_input_error(self.run_cli(path), path)

    def test_directory_instead_of_file(self):
        self.assert_input_error(self.run_cli(self.directory), self.directory)

    def test_csv_parser_error(self):
        path = self.directory / "oversized.csv"
        path.write_text("value\n" + "x" * (csv.field_size_limit() + 1) + "\n")
        result = self.run_cli(path)
        self.assert_input_error(result, path)
        self.assertIn("invalid CSV", result.stderr)
        self.assertIn("field larger than field limit", result.stderr)

    def test_permission_denied(self):
        stderr = io.StringIO()
        error = PermissionError(errno.EACCES, "Permission denied", "private.csv")
        with mock.patch("builtins.open", side_effect=error):
            with contextlib.redirect_stderr(stderr):
                status = dq_scan.main(["private.csv"])
        self.assertEqual(status, 1)
        self.assertEqual(stderr.getvalue(),
                         "error: unable to read private.csv: Permission denied\n")

    @unittest.skipIf(os.name == "nt", "POSIX file permissions required")
    def test_unreadable_file_in_subprocess(self):
        path = self.directory / "private.csv"
        path.write_text("value\n1\n")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o600)
        if os.access(path, os.R_OK):
            self.skipTest("current user can read files despite mode 000")
        self.assert_input_error(self.run_cli(path), path)

    def test_read_error(self):
        stderr = io.StringIO()
        with mock.patch.object(dq_scan, "scan", side_effect=OSError(errno.EIO, "Input/output error")):
            with contextlib.redirect_stderr(stderr):
                status = dq_scan.main(["data.csv"])
        self.assertEqual(status, 1)
        self.assertIn("Input/output error", stderr.getvalue())

    def test_programming_errors_are_not_hidden(self):
        with mock.patch.object(dq_scan, "scan", side_effect=ValueError("unexpected bug")):
            with self.assertRaisesRegex(ValueError, "unexpected bug"):
                dq_scan.main(["data.csv"])

    def test_no_arguments_preserves_usage(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "usage: dq-scan <file.csv>\n")
        self.assertEqual(result.stderr, "")

    def test_valid_file_preserves_summary(self):
        path = self.directory / "data.csv"
        path.write_text("amount\n1\n3\n")
        result = self.run_cli(path)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("2 rows, 1 columns\n"))
        self.assertIn("numeric: min=1.0 max=3.0 mean=2.00", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
