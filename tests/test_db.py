import sqlite3
import unittest

from app.db import Database, RECORD_FIELDS


def sample_record(name="Juan Dela Cruz"):
    rec = {field: f"{field}-value" for field in RECORD_FIELDS}
    rec["full_name"] = name
    return rec


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_schema_creates_tables(self):
        names = {
            row["name"]
            for row in self.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        self.assertIn("users", names)
        self.assertIn("records", names)

    def test_foreign_keys_enabled(self):
        self.assertEqual(self.db.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_create_and_get_user(self):
        uid = self.db.create_user("trixian", "ab" * 16, "cd" * 32)
        user = self.db.get_user("trixian")
        self.assertEqual(user["id"], uid)
        self.assertEqual(user["theme"], "light")

    def test_username_unique_case_insensitive(self):
        self.db.create_user("Gabriel", "ab" * 16, "cd" * 32)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_user("gabriel", "ab" * 16, "cd" * 32)
        self.assertIsNotNone(self.db.get_user("GABRIEL"))

    def test_sql_injection_text_is_stored_literally(self):
        evil = "x'); DROP TABLE users;--"
        self.db.create_user(evil, "ab" * 16, "cd" * 32)
        self.assertEqual(self.db.get_user(evil)["username"], evil)
        self.assertIsNotNone(self.db.get_user(evil))

    def test_records_are_scoped_per_user(self):
        a = self.db.create_user("alice", "ab" * 16, "cd" * 32)
        b = self.db.create_user("bob", "ab" * 16, "cd" * 32)
        self.db.insert_records(a, [sample_record("A One"), sample_record("A Two")])
        self.db.insert_records(b, [sample_record("B One")])
        self.assertEqual(len(self.db.list_records(a)), 2)
        self.assertEqual([r["full_name"] for r in self.db.list_records(b)], ["B One"])
        self.assertEqual(self.db.count_records(a), 2)

    def test_cannot_delete_another_users_records(self):
        a = self.db.create_user("alice", "ab" * 16, "cd" * 32)
        b = self.db.create_user("bob", "ab" * 16, "cd" * 32)
        self.db.insert_records(b, [sample_record("B One")])
        bob_id = self.db.list_records(b)[0]["id"]
        self.assertEqual(self.db.delete_records(a, [bob_id]), 0)
        self.assertEqual(self.db.count_records(b), 1)
        self.assertEqual(self.db.delete_records(b, [bob_id]), 1)
        self.assertEqual(self.db.count_records(b), 0)

    def test_search_filters_and_escapes_wildcards(self):
        a = self.db.create_user("alice", "ab" * 16, "cd" * 32)
        self.db.insert_records(a, [sample_record("Maria Santos"), sample_record("Jose 100% Rizal")])
        self.assertEqual(len(self.db.list_records(a, "santos")), 1)
        self.assertEqual(len(self.db.list_records(a, "%")), 1)  # literal %, not a wildcard
        self.assertEqual(len(self.db.list_records(a, "zzz")), 0)

    def test_theme_roundtrip_and_check(self):
        uid = self.db.create_user("alice", "ab" * 16, "cd" * 32)
        self.db.set_theme(uid, "dark")
        self.assertEqual(self.db.get_user("alice")["theme"], "dark")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.set_theme(uid, "purple")

    def test_missing_field_rejected(self):
        uid = self.db.create_user("alice", "ab" * 16, "cd" * 32)
        rec = sample_record()
        del rec["email"]
        with self.assertRaises(KeyError):
            self.db.insert_records(uid, [rec])


if __name__ == "__main__":
    unittest.main()
