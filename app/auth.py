"""Password hashing, input validation, register and login.

Passwords are hashed with salted PBKDF2-HMAC-SHA256 (hashlib) and never
stored or logged in plain text.
"""
import hashlib
import hmac
import os
import re
import sqlite3

ITERATIONS = 600_000
SALT_BYTES = 16
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
MIN_PASSWORD = 8
MAX_PASSWORD = 128
LOGIN_FAILED = "Invalid username or password."

_dummy = None  # (salt, hash) used to keep timing similar for unknown users


class AuthError(Exception):
    """A message that is safe to show to the user."""


def hash_password(password, salt=None):
    """Return (salt_hex, hash_hex). A fresh random salt is made if none is given."""
    if salt is None:
        salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return salt.hex(), digest.hex()


def verify_password(password, salt_hex, hash_hex):
    _, candidate = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, hash_hex)


def validate_username(username):
    """Return an error message, or None if the username is fine."""
    if not USERNAME_RE.fullmatch(username or ""):
        return "Username must be 3-20 characters: letters, numbers or underscore."
    return None


def validate_password(password, confirm):
    if len(password) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters."
    if len(password) > MAX_PASSWORD:
        return f"Password must be at most {MAX_PASSWORD} characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must include at least one letter and one number."
    if password != confirm:
        return "Passwords do not match."
    return None


def register(db, username, password, confirm):
    """Create a user and return its id. Raises AuthError with a friendly message."""
    username = (username or "").strip()
    error = validate_username(username) or validate_password(password, confirm)
    if error:
        raise AuthError(error)
    if db.get_user(username) is not None:
        raise AuthError("That username is already taken.")
    salt_hex, hash_hex = hash_password(password)
    try:
        return db.create_user(username, salt_hex, hash_hex)
    except sqlite3.IntegrityError:  # someone registered it in between
        raise AuthError("That username is already taken.") from None


def login(db, username, password):
    """Return the user row on success. Raises AuthError(LOGIN_FAILED) otherwise.

    The message is the same for an unknown user and a wrong password, and an
    unknown user still costs one hash, so neither reveals which usernames exist.
    """
    global _dummy
    username = (username or "").strip()
    if not username or not password:
        raise AuthError("Enter your username and password.")
    user = db.get_user(username)
    if user is None:
        if _dummy is None:
            _dummy = hash_password("dummy-password")
        verify_password(password, *_dummy)
        raise AuthError(LOGIN_FAILED)
    if not verify_password(password, user["salt"], user["password_hash"]):
        raise AuthError(LOGIN_FAILED)
    return user
