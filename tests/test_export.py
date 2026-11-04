import csv
import os
import tempfile
import unittest

from app import export
from app.db import RECORD_FIELDS


class ExportTests(unittest.TestCase):
    def test_escape_formula_cells(self):
        self.assertEqual(export.safe_cell("=HYPERLINK(\"x\")"), "'=HYPERLINK(\"x\")")
        self.assertEqual(export.safe_cell("@SUM(A1)"), "'@SUM(A1)")
        self.assertEqual(export.safe_cell("-1+1"), "'-1+1")
        self.assertEqual(export.safe_cell("Juan Dela Cruz"), "Juan Dela Cruz")

    def test_phone_numbers_stay_readable(self):
        # Generated phone numbers start with "+" but are not formulas.
        self.assertEqual(export.safe_cell("+63 917 123 4567"), "+63 917 123 4567")
        self.assertEqual(export.safe_cell("+1+cmd|' /C calc'!A0"), "'+1+cmd|' /C calc'!A0")

    def test_write_csv(self):
        rows = [{f: f"{f}-1" for f in RECORD_FIELDS}, {f: "=evil()" for f in RECORD_FIELDS}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            self.assertEqual(export.write_csv(path, rows), 2)
            with open(path, newline="", encoding="utf-8-sig") as fh:
                data = list(csv.reader(fh))
        self.assertEqual(data[0], list(export.HEADERS))
        self.assertEqual(len(data), 3)
        self.assertTrue(all(cell.startswith("'=") for cell in data[2]))


if __name__ == "__main__":
    unittest.main()
