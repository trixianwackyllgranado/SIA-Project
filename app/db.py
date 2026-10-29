"""SQLite storage: schema creation and every query the app runs.

All queries use ``?`` placeholders. Record queries always filter by
``user_id`` so one user can never read or delete another user's rows.
"""
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "fakedata.db"

# The 10 generated fields, in display order. "fake_username" is the
# generated username (shown as "Username"), not the login username.
RECORD_FIELDS = (
    "full_name",
    "address",
    "birthdate",
    "mobile_number",
    "email",
    "gender",
    "civil_status",
    "occupation",
    "company",
    "fake_username",
)

# Fields the search box looks at.
SEARCH_FIELDS = (
    "full_name",
    "address",
    "mobile_number",
    "email",
    "occupation",
    "company",
    "fake_username",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    salt          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    theme         TEXT NOT NULL DEFAULT 'light' CHECK (theme IN ('light', 'dark')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS records (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    full_name     TEXT NOT NULL,
    address       TEXT NOT NULL,
    birthdate     TEXT NOT NULL,
    mobile_number TEXT NOT NULL,
    email         TEXT NOT NULL,
    gender        TEXT NOT NULL,
    civil_status  TEXT NOT NULL,
    occupation    TEXT NOT NULL,
    company       TEXT NOT NULL,
    fake_username TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_records_user ON records (user_id);
"""

_COLUMNS = ", ".join(RECORD_FIELDS)
_PLACEHOLDERS = ", ".join("?" for _ in RECORD_FIELDS)
_INSERT_SQL = f"INSERT INTO records (user_id, {_COLUMNS}) VALUES (?, {_PLACEHOLDERS})"
_SELECT_SQL = f"SELECT id, {_COLUMNS}, created_at FROM records WHERE user_id = ?"
_SEARCH_SQL = " AND (" + " OR ".join(f"{f} LIKE ? ESCAPE '\\'" for f in SEARCH_FIELDS) + ")"


def _like_pattern(text):
    """Turn user text into a LIKE pattern where % and _ are literal."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class Database:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    # ---- users -------------------------------------------------------
    def create_user(self, username, salt_hex, hash_hex):
        """Insert a user. Raises sqlite3.IntegrityError if the name is taken."""
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                (username, salt_hex, hash_hex),
            )
        return cur.lastrowid

    def get_user(self, username):
        return self.conn.execute(
            "SELECT id, username, salt, password_hash, theme FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    def set_theme(self, user_id, theme):
        with self.conn:
            self.conn.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user_id))

    # ---- records -----------------------------------------------------
    def insert_records(self, user_id, records):
        """Insert many records for one user. Every field is required."""
        rows = [(user_id, *(rec[f] for f in RECORD_FIELDS)) for rec in records]
        with self.conn:
            self.conn.executemany(_INSERT_SQL, rows)
        return len(rows)

    def list_records(self, user_id, search=""):
        sql, params = _SELECT_SQL, [user_id]
        search = (search or "").strip()
        if search:
            sql += _SEARCH_SQL
            params += [_like_pattern(search)] * len(SEARCH_FIELDS)
        sql += " ORDER BY id DESC"
        return self.conn.execute(sql, params).fetchall()

    def count_records(self, user_id):
        return self.conn.execute(
            "SELECT COUNT(*) FROM records WHERE user_id = ?", (user_id,)
        ).fetchone()[0]

    def delete_records(self, user_id, record_ids):
        """Delete only rows that belong to user_id. Returns how many were deleted."""
        before = self.conn.total_changes
        with self.conn:
            self.conn.executemany(
                "DELETE FROM records WHERE id = ? AND user_id = ?",
                [(int(rid), user_id) for rid in record_ids],
            )
        return self.conn.total_changes - before
