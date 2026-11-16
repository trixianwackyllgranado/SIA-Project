import os
import smtplib
import tempfile
import unittest
from unittest import mock

from app import mailer

SETTINGS = {"SMTP_HOST": "smtp.example.com", "SMTP_PORT": "587",
            "SMTP_USER": "me@example.com", "SMTP_APP_PASSWORD": "app-password"}


class FakeSMTP:
    """Records what the mailer does instead of talking to a real server."""
    instances = []
    fail_with = None

    def __init__(self, host, port, timeout):
        self.host, self.port, self.sent, self.calls = host, port, [], []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append("login")
        if FakeSMTP.fail_with:
            raise FakeSMTP.fail_with

    def send_message(self, message):
        self.calls.append("send")
        self.sent.append(message)


class ValidationTests(unittest.TestCase):
    def test_recipient(self):
        self.assertEqual(mailer.check_recipient(" a.b+c@mail.example.ph "), "a.b+c@mail.example.ph")
        for bad in ["", "no-at-sign", "a@b", "a@@b.com", "a@b.com, c@d.com", "a b@c.com"]:
            with self.assertRaises(mailer.MailError, msg=bad):
                mailer.check_recipient(bad)

    def test_subject_rejects_header_injection(self):
        with self.assertRaises(mailer.MailError):
            mailer.check_subject("Hello\nBcc: victim@example.com")
        with self.assertRaises(mailer.MailError):
            mailer.check_subject("")

    def test_body(self):
        with self.assertRaises(mailer.MailError):
            mailer.check_body("  ")
        with self.assertRaises(mailer.MailError):
            mailer.check_body("x" * (mailer.MAX_BODY + 1))


@mock.patch.object(mailer.smtplib, "SMTP", FakeSMTP)
class SendTests(unittest.TestCase):
    def setUp(self):
        FakeSMTP.instances, FakeSMTP.fail_with = [], None

    def test_success_uses_tls_then_login(self):
        self.assertEqual(mailer.send_email(SETTINGS, "you@example.com", "Hi", "Body text"),
                         "you@example.com")
        server = FakeSMTP.instances[0]
        self.assertEqual((server.host, server.port), ("smtp.example.com", 587))
        self.assertEqual(server.calls, ["starttls", "login", "send"])
        sent = server.sent[0]
        self.assertEqual((sent["From"], sent["To"], sent["Subject"]),
                         ("me@example.com", "you@example.com", "Hi"))

    def test_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("Full Name\nJuan\n")
            mailer.send_email(SETTINGS, "you@example.com", "Data", "See file", attachment_path=path)
        attachments = list(FakeSMTP.instances[0].sent[0].iter_attachments())
        self.assertEqual([a.get_filename() for a in attachments], ["records.csv"])

    def test_missing_attachment(self):
        with self.assertRaisesRegex(mailer.MailError, "attachment"):
            mailer.send_email(SETTINGS, "you@example.com", "Hi", "Body", attachment_path="nope.csv")

    def test_not_configured_never_connects(self):
        with self.assertRaisesRegex(mailer.MailError, "SMTP_USER"):
            mailer.send_email({}, "you@example.com", "Hi", "Body")
        self.assertEqual(FakeSMTP.instances, [])

    def test_bad_login(self):
        FakeSMTP.fail_with = smtplib.SMTPAuthenticationError(535, b"bad")
        with self.assertRaisesRegex(mailer.MailError, "rejected the login"):
            mailer.send_email(SETTINGS, "you@example.com", "Hi", "Body")

    def test_no_internet(self):
        FakeSMTP.fail_with = OSError("down")
        with self.assertRaisesRegex(mailer.MailError, "internet"):
            mailer.send_email(SETTINGS, "you@example.com", "Hi", "Body")

    def test_password_never_in_error_text(self):
        FakeSMTP.fail_with = smtplib.SMTPException("app-password leaked?")
        with self.assertRaises(mailer.MailError) as ctx:
            mailer.send_email(SETTINGS, "you@example.com", "Hi", "Body")
        self.assertNotIn("app-password", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
