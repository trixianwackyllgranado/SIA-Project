"""URL shortening through the is.gd API (free, no API key).

API reference: https://is.gd/apishorteningreference.php
"""
import urllib.parse

from app.http_json import NetworkError, request_json

API_URL = "https://is.gd/create.php"
SHORT_PREFIX = "https://is.gd/"
MAX_URL_LENGTH = 2000


class ShortenerError(Exception):
    """A message that is safe to show to the user."""


def clean_url(text):
    """Return a valid http(s) URL, or raise ShortenerError."""
    url = (text or "").strip()
    if not url:
        raise ShortenerError("Enter a link to shorten.")
    if any(ch.isspace() for ch in url):
        raise ShortenerError("A link can't contain spaces.")
    if len(url) > MAX_URL_LENGTH:
        raise ShortenerError(f"That link is too long (max {MAX_URL_LENGTH} characters).")
    if "://" not in url:
        url = "https://" + url  # allow "www.example.com"
    try:
        parts = urllib.parse.urlsplit(url)
        parts.port  # raises ValueError for a bad port
    except ValueError:
        raise ShortenerError("That doesn't look like a valid link.") from None
    if parts.scheme not in ("http", "https"):
        raise ShortenerError("Only http and https links can be shortened.")
    if not parts.hostname or "." not in parts.hostname:
        raise ShortenerError("That doesn't look like a valid link.")
    return url


def shorten(text):
    """Return (long_url, short_url). Raises ShortenerError with a friendly message."""
    long_url = clean_url(text)
    query = urllib.parse.urlencode({"format": "json", "url": long_url})
    try:
        _status, reply = request_json(f"{API_URL}?{query}")
    except NetworkError:
        raise ShortenerError("Couldn't reach is.gd. Check your internet connection.") from None

    if not isinstance(reply, dict):
        raise ShortenerError("is.gd sent a reply the app couldn't read.")
    short_url = reply.get("shorturl")
    if isinstance(short_url, str) and short_url.startswith(SHORT_PREFIX):
        return long_url, short_url
    if reply.get("errorcode") == 3:
        raise ShortenerError("is.gd is limiting requests right now. Wait a minute, then try again.")
    reason = reply.get("errormessage")
    if isinstance(reason, str) and reason:
        raise ShortenerError(f"is.gd couldn't shorten that link: {reason[:200]}")
    raise ShortenerError("is.gd couldn't shorten that link.")
