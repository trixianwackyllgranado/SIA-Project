"""Settings for the Email and SMS tools, read from a local .env file.

The .env file holds real credentials, so it is gitignored. `.env.example`
lists the names. A real environment variable wins over the file.
"""
import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

DEFAULTS = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "",
    "SMTP_APP_PASSWORD": "",
    "TEXTBEE_API_KEY": "",
    "TEXTBEE_DEVICE_ID": "",  # optional: TextBee uses your default device if empty
}

EMAIL_REQUIRED = ("SMTP_USER", "SMTP_APP_PASSWORD")
SMS_REQUIRED = ("TEXTBEE_API_KEY",)


def read_env_file(path=ENV_PATH):
    """Parse KEY=VALUE lines. Blank lines and # comments are skipped."""
    values = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load(path=ENV_PATH):
    """Return every setting as a dict of strings."""
    settings = dict(DEFAULTS)
    from_file = read_env_file(path)
    for key in DEFAULTS:
        value = os.environ.get(key) or from_file.get(key)
        if value:
            settings[key] = value
    # Google shows app passwords as "abcd efgh ijkl mnop"; the spaces are not part of it.
    settings["SMTP_APP_PASSWORD"] = settings["SMTP_APP_PASSWORD"].replace(" ", "")
    return settings


def missing(settings, required):
    """Names from `required` that have no value yet."""
    return [name for name in required if not settings.get(name)]
