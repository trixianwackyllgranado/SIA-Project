"""Email sending over SMTP (Gmail with an App Password by default)."""
import mimetypes
import os
import re
import smtplib
import ssl
from email.message import EmailMessage

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")
MAX_SUBJECT = 150
MAX_BODY = 10_000
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
TIMEOUT = 15


class MailError(Exception):
    """A message that is safe to show to the user."""


def check_recipient(text):
    address = (text or "").strip()
    if not EMAIL_RE.fullmatch(address) or len(address) > 254:
        raise MailError("Enter one valid email address, like name@example.com.")
    return address


def check_subject(text):
    subject = (text or "").strip()
    if not subject:
        raise MailError("Add a subject.")
    if "\n" in subject or "\r" in subject:
        raise MailError("The subject must be a single line.")
    if len(subject) > MAX_SUBJECT:
        raise MailError(f"Subject is too long (max {MAX_SUBJECT} characters).")
    return subject


def check_body(text):
    body = (text or "").strip()
    if not body:
        raise MailError("Type a message first.")
    if len(body) > MAX_BODY:
        raise MailError(f"Message is too long (max {MAX_BODY:,} characters).")
    return body


def build_message(sender, recipient, subject, body, attachment_path=None):
    """Validate every part and return an EmailMessage ready to send."""
    message = EmailMessage()
    message["From"] = sender
    message["To"] = check_recipient(recipient)
    message["Subject"] = check_subject(subject)
    message.set_content(check_body(body))
    if attachment_path:
        _attach(message, attachment_path)
    return message


def _attach(message, path):
    try:
        size = os.path.getsize(path)
        if size > MAX_ATTACHMENT_BYTES:
            raise MailError("The attachment is larger than 5 MB.")
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        raise MailError("The attachment couldn't be read.") from None
    kind = mimetypes.guess_type(path)[0] or "application/octet-stream"
    maintype, subtype = kind.split("/", 1)
    message.add_attachment(data, maintype=maintype, subtype=subtype,
                           filename=os.path.basename(path))


def send_email(settings, recipient, subject, body, attachment_path=None):
    """Send one email. Returns the recipient. Raises MailError on any failure."""
    user, password = settings.get("SMTP_USER"), settings.get("SMTP_APP_PASSWORD")
    if not user or not password:
        raise MailError("Email is not set up. Add SMTP_USER and SMTP_APP_PASSWORD to the .env file.")
    try:
        port = int(settings.get("SMTP_PORT", "587"))
    except ValueError:
        raise MailError("SMTP_PORT in .env must be a number.") from None
    message = build_message(user, recipient, subject, body, attachment_path)

    try:
        with smtplib.SMTP(settings.get("SMTP_HOST", "smtp.gmail.com"), port, timeout=TIMEOUT) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user, password)
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError:
        raise MailError("The mail server rejected the login. "
                        "Check SMTP_USER and SMTP_APP_PASSWORD in .env.") from None
    except smtplib.SMTPRecipientsRefused:
        raise MailError("The mail server refused that recipient address.") from None
    except smtplib.SMTPException as exc:
        raise MailError(f"The mail server reported an error ({type(exc).__name__}).") from None
    except OSError:
        raise MailError("Couldn't reach the mail server. Check your internet connection.") from None
    return message["To"]
