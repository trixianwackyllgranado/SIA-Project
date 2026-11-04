import unittest
from unittest import mock

from app import auth
from app.db import Database

# 600k iterations is slow on purpose; tests use a small count for speed.
FAST = mock.patch.object(auth, "ITERATIONS", 1_000)


class HashingTests(unittest.TestCase):
    def test_default_iterations_is_600k(self):
        self.assertEqual(auth.ITERATIONS, 600_000)

    @FAST
    def test_hash_roundtrip(self):
        salt, digest = auth.hash_password("Secret123")
        self.assertEqual(len(salt), 32)    # 16 bytes as hex
        self.assertEqual(len(digest), 64)  # sha256 as hex
        self.assertTrue(auth.verify_password("Secret123", salt, digest))
        self.assertFalse(auth.verify_password("secret123", salt, digest))

    @FAST
    def test_salt_is_unique_per_hash(self):
        a = auth.hash_password("Secret123")
        b = auth.hash_password("Secret123")
        self.assertNotEqual(a[0], b[0])
        self.assertNotEqual(a[1], b[1])


class ValidationTests(unittest.TestCase):
    def test_username_rules(self):
        self.assertIsNone(auth.validate_username("trix_01"))
        for bad in ["", "ab", "a" * 21, "has space", "semi;colon", "ñame"]:
            self.assertIsNotNone(auth.validate_username(bad), bad)

    def test_password_rules(self):
        self.assertIsNone(auth.validate_password("Secret123", "Secret123"))
        self.assertIsNotNone(auth.validate_password("Short1", "Short1"))
        self.assertIsNotNone(auth.validate_password("nodigitshere", "nodigitshere"))
        self.assertIsNotNone(auth.validate_password("12345678", "12345678"))
        self.assertIsNotNone(auth.validate_password("Secret123", "Secret124"))
        self.assertIsNotNone(auth.validate_password("A1" * 65, "A1" * 65))


@FAST
class RegisterLoginTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_register_then_login(self):
        uid = auth.register(self.db, "  trixian ", "Secret123", "Secret123")
        user = auth.login(self.db, "trixian", "Secret123")
        self.assertEqual(user["id"], uid)
        self.assertEqual(user["username"], "trixian")  # whitespace trimmed

    def test_login_is_case_insensitive_for_username(self):
        auth.register(self.db, "Gabriel", "Secret123", "Secret123")
        self.assertEqual(auth.login(self.db, "gabriel", "Secret123")["username"], "Gabriel")

    def test_duplicate_username(self):
        auth.register(self.db, "trixian", "Secret123", "Secret123")
        with self.assertRaises(auth.AuthError) as ctx:
            auth.register(self.db, "TRIXIAN", "Other1234", "Other1234")
        self.assertIn("taken", str(ctx.exception))

    def test_same_error_for_wrong_password_and_unknown_user(self):
        auth.register(self.db, "trixian", "Secret123", "Secret123")
        with self.assertRaises(auth.AuthError) as wrong:
            auth.login(self.db, "trixian", "Wrong1234")
        with self.assertRaises(auth.AuthError) as unknown:
            auth.login(self.db, "nobody", "Wrong1234")
        self.assertEqual(str(wrong.exception), str(unknown.exception))

    def test_empty_login_fields(self):
        with self.assertRaises(auth.AuthError):
            auth.login(self.db, "", "")

    def test_password_never_stored_in_plain_text(self):
        auth.register(self.db, "trixian", "Secret123", "Secret123")
        dump = "\n".join(self.db.conn.iterdump())
        self.assertNotIn("Secret123", dump)

    def test_invalid_input_does_not_create_user(self):
        with self.assertRaises(auth.AuthError):
            auth.register(self.db, "trixian", "short", "short")
        self.assertIsNone(self.db.get_user("trixian"))


if __name__ == "__main__":
    unittest.main()
