import contextlib
import csv
import gc
import io
import tempfile
import tracemalloc
import unittest
from pathlib import Path

from dq_scan import scan


class StreamingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "data.csv"

    def scan_rows(self, rows, delim=","):
        with self.path.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file, delimiter=delim).writerows(rows)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = scan(self.path, delim=delim)
        return status, stdout.getvalue()

    def test_weighted_numeric_summary(self):
        status, output = self.scan_rows([["amount"], ["1"], ["1"], ["1"], ["9"]])
        self.assertEqual(status, 0)
        self.assertTrue(output.startswith("4 rows, 1 columns\n"))
        self.assertIn("nulls=0      dupes=2      unique=2", output)
        self.assertIn("numeric: min=1.0 max=9.0 mean=3.00", output)

    def test_mean_preserves_cancellation_precision(self):
        status, output = self.scan_rows([["amount"], ["1e16"], ["1"], ["-1e16"]])
        self.assertEqual(status, 0)
        self.assertIn("mean=0.33", output)

    def test_mean_does_not_overflow_for_large_finite_values(self):
        status, output = self.scan_rows([["amount"], ["1e308"], ["1e308"]])
        self.assertEqual(status, 0)
        self.assertIn(f"mean={1e308:.2f}", output)

    def test_empty_and_missing_cells_keep_distinct_counts(self):
        status, output = self.scan_rows([["id", "name"], ["1", ""], ["2"], ["3", ""]])
        self.assertEqual(status, 0)
        summary = next(line for line in output.splitlines() if line.startswith("• name"))
        self.assertIn("nulls=3      dupes=1      unique=2", summary)
        self.assertIn("top: []", output)

    def test_top_values_keep_counts_and_first_seen_tie_order(self):
        status, output = self.scan_rows([["name"], *[[v] for v in ["x", "y", "z", "x", "y", "w"]]])
        self.assertEqual(status, 0)
        self.assertIn("top: [('x', 2), ('y', 2), ('z', 1)]", output)

    def test_mixed_column_stays_categorical(self):
        status, output = self.scan_rows([["amount"], ["1"], ["2"], ["unknown"], ["2"]])
        self.assertEqual(status, 0)
        self.assertNotIn("numeric:", output)
        self.assertIn("top: [('2', 2), ('1', 1), ('unknown', 1)]", output)

    def test_existing_nonfinite_behavior_is_preserved(self):
        for values, expected in [(["NaN", "1"], "min=nan max=nan mean=nan"),
                                 (["1", "inf", "inf"], "min=1.0 max=inf mean=inf"),
                                 (["-inf", "inf"], "min=-inf max=inf mean=nan")]:
            with self.subTest(values=values):
                status, output = self.scan_rows([["value"], *[[v] for v in values]])
                self.assertEqual(status, 0)
                self.assertIn(expected, output)

    def test_delimiter_quotes_and_multiline_fields(self):
        status, output = self.scan_rows([["name", "amount"], ["a;b\nc", "2"], ["other", "4"]], delim=";")
        self.assertEqual(status, 0)
        self.assertTrue(output.startswith("2 rows, 2 columns\n"))
        self.assertIn("a;b\\nc", output)
        self.assertIn("numeric: min=2.0 max=4.0 mean=3.00", output)

    def test_empty_and_header_only_files(self):
        for rows in ([], [["value"]]):
            with self.subTest(rows=rows):
                status, output = self.scan_rows(rows)
                self.assertEqual(status, 1)
                self.assertEqual(output, "empty file (no rows / no header)\n")

    def test_duplicate_headers_keep_existing_last_field_behavior(self):
        status, output = self.scan_rows([["value", "value"], ["ignored", "1"], ["ignored", "3"]])
        self.assertEqual(status, 0)
        self.assertTrue(output.startswith("2 rows, 1 columns\n"))
        self.assertEqual(output.count("• value"), 1)
        self.assertIn("numeric: min=1.0 max=3.0 mean=2.00", output)

    def test_repeated_rows_do_not_accumulate_in_memory(self):
        def peak_memory(row_count):
            with self.path.open("w", encoding="utf-8") as file:
                file.write("id,amount,currency\n")
                for _ in range(row_count):
                    file.write("1,12.50,EUR\n")
            gc.collect()
            tracemalloc.start()
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(scan(self.path), 0)
                return tracemalloc.get_traced_memory()[1]
            finally:
                tracemalloc.stop()

        small_peak = peak_memory(1000)
        large_peak = peak_memory(20000)
        self.assertLess(large_peak, small_peak * 3 + 65536)


if __name__ == "__main__":
    unittest.main()
