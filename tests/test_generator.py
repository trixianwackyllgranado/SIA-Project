import random
import re
import unittest
from datetime import date

from app import generator
from app.db import RECORD_FIELDS

MOBILE_RE = re.compile(r"^\+63 9\d{2} \d{3} \d{4}$")
EMAIL_RE = re.compile(r"^[a-z0-9._]+@[a-z0-9.]+\.[a-z]{2,}$")
USERNAME_RE = re.compile(r"^[a-z0-9_.]+$")
TODAY = date(2026, 11, 5)


def age_on(birth, today):
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.records = generator.generate_records(200, rng=random.Random(42), today=TODAY)

    def test_default_is_ten_records(self):
        self.assertEqual(len(generator.generate_records()), 10)

    def test_count_limits(self):
        with self.assertRaises(ValueError):
            generator.generate_records(9)
        with self.assertRaises(ValueError):
            generator.generate_records(generator.MAX_RECORDS + 1)
        self.assertEqual(len(generator.generate_records(generator.MAX_RECORDS)), generator.MAX_RECORDS)

    def test_every_record_has_all_ten_fields(self):
        for rec in self.records:
            self.assertEqual(set(rec), set(RECORD_FIELDS))
            for field, value in rec.items():
                self.assertTrue(str(value).strip(), field)

    def test_field_formats(self):
        for rec in self.records:
            self.assertRegex(rec["mobile_number"], MOBILE_RE)
            self.assertRegex(rec["email"], EMAIL_RE)
            self.assertRegex(rec["fake_username"], USERNAME_RE)
            self.assertIn(rec["gender"], ("Male", "Female"))
            self.assertIn(rec["civil_status"], generator.CIVIL_STATUSES)
            self.assertRegex(rec["full_name"], r"^\S.* [A-Z]\. \S.*$")  # First M. Last
            self.assertEqual(rec["address"].count(","), 3)     # street, brgy, city, province

    def test_birthdates_are_adults_18_to_65(self):
        for rec in self.records:
            birth = date.fromisoformat(rec["birthdate"])
            self.assertTrue(18 <= age_on(birth, TODAY) <= 65, rec["birthdate"])

    def test_seeded_runs_are_repeatable(self):
        a = generator.generate_records(10, rng=random.Random(7), today=TODAY)
        b = generator.generate_records(10, rng=random.Random(7), today=TODAY)
        self.assertEqual(a, b)

    def test_variety(self):
        self.assertGreater(len({r["full_name"] for r in self.records}), 150)


if __name__ == "__main__":
    unittest.main()
