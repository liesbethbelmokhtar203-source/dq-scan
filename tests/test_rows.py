import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from dq_scan import scan


class RaggedRowsTests(unittest.TestCase):
    def scan_csv(self, contents):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text(contents, encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = scan(path)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_extra_fields_in_first_or_later_row(self):
        for rows in ("1,Alice,extra\n2,Bob\n", "1,Alice\n2,Bob,extra\n"):
            with self.subTest(rows=rows):
                status, output, warning = self.scan_csv("id,name\n" + rows)
                self.assertEqual(status, 0)
                self.assertTrue(output.startswith("2 rows, 2 columns\n"))
                self.assertIn("top: [('Alice', 1), ('Bob', 1)]", output)
                self.assertIn("warning: 1 row(s)", warning)
                self.assertIn("extra fields ignored", warning)

    def test_missing_fields_are_nulls(self):
        status, output, warning = self.scan_csv("id,name\n1,Alice\n2\n3\n")
        self.assertEqual(status, 0)
        name_summary = next(line for line in output.splitlines() if line.startswith("• name"))
        self.assertIn("nulls=2", name_summary)
        self.assertIn("dupes=1", name_summary)
        self.assertIn("unique=2", name_summary)
        self.assertIn("warning: 2 row(s)", warning)

    def test_extra_and_missing_fields_in_same_file(self):
        status, output, warning = self.scan_csv("id,name\n1,Alice,extra\n2\n3,Charlie\n")
        self.assertEqual(status, 0)
        self.assertTrue(output.startswith("3 rows, 2 columns\n"))
        self.assertIn("warning: 2 row(s)", warning)
        self.assertIn("top: [('Alice', 1), ('Charlie', 1)]", output)

    def test_all_rows_have_extra_fields(self):
        status, output, warning = self.scan_csv("id\n1,a,b\n2,c,d\n")
        self.assertEqual(status, 0)
        self.assertTrue(output.startswith("2 rows, 1 columns\n"))
        self.assertIn("numeric: min=1.0 max=2.0 mean=1.50", output)
        self.assertIn("warning: 2 row(s)", warning)

    def test_empty_cells_and_quoted_delimiters_are_not_malformed(self):
        status, output, warning = self.scan_csv('id,name\n1,"Alice, Smith"\n2,\n')
        self.assertEqual(status, 0)
        self.assertEqual(warning, "")
        self.assertIn("Alice, Smith", output)
        self.assertIn("nulls=1", output)

    def test_empty_and_header_only_files(self):
        for contents in ("", "id,name\n"):
            with self.subTest(contents=contents):
                status, output, warning = self.scan_csv(contents)
                self.assertEqual(status, 1)
                self.assertEqual(output, "empty file (no rows / no header)\n")
                self.assertEqual(warning, "")

    def test_duplicate_headers_keep_existing_last_field_behavior(self):
        status, output, warning = self.scan_csv("value,value\nignored,1\nignored,3\n")
        self.assertEqual(status, 0)
        self.assertTrue(output.startswith("2 rows, 1 columns\n"))
        self.assertEqual(output.count("• value"), 1)
        self.assertIn("numeric: min=1.0 max=3.0 mean=2.00", output)
        self.assertEqual(warning, "")


if __name__ == "__main__":
    unittest.main()
