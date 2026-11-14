import os
import tempfile
import unittest
from unittest import mock

from app import config

ENV_TEXT = """
# comment line
SMTP_USER = someone@gmail.com
SMTP_APP_PASSWORD="abcd efgh ijkl mnop"
not a setting line
TEXTBEE_API_KEY=key-from-file
UNKNOWN_NAME=ignored
"""


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, ".env")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(ENV_TEXT)
        # Keep the real environment out of these tests.
        patcher = mock.patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_reads_values_and_keeps_defaults(self):
        settings = config.load(self.path)
        self.assertEqual(settings["SMTP_USER"], "someone@gmail.com")
        self.assertEqual(settings["SMTP_HOST"], "smtp.gmail.com")
        self.assertEqual(settings["SMTP_PORT"], "587")
        self.assertNotIn("UNKNOWN_NAME", settings)

    def test_app_password_spaces_and_quotes_removed(self):
        self.assertEqual(config.load(self.path)["SMTP_APP_PASSWORD"], "abcdefghijklmnop")

    def test_environment_wins_over_file(self):
        with mock.patch.dict(os.environ, {"TEXTBEE_API_KEY": "key-from-env"}):
            self.assertEqual(config.load(self.path)["TEXTBEE_API_KEY"], "key-from-env")

    def test_missing_file_gives_defaults(self):
        settings = config.load(os.path.join(self.tmp.name, "nope.env"))
        self.assertEqual(config.missing(settings, config.EMAIL_REQUIRED),
                         ["SMTP_USER", "SMTP_APP_PASSWORD"])
        self.assertEqual(config.missing(settings, config.SMS_REQUIRED), ["TEXTBEE_API_KEY"])

    def test_nothing_missing_when_set(self):
        settings = config.load(self.path)
        self.assertEqual(config.missing(settings, config.EMAIL_REQUIRED), [])
        self.assertEqual(config.missing(settings, config.SMS_REQUIRED), [])


if __name__ == "__main__":
    unittest.main()
