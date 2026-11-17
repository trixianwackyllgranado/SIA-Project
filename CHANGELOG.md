# Changelog

## 2026-11-17
### Added
- URL Shortener tool using the is.gd API (`app/shortener.py`, `app/ui/links_page.py`): link validation, saved history per user, copy/open, reuse of an already-shortened link, send a short link by email or SMS.
- Email tool over Gmail SMTP (`app/mailer.py`): one recipient, subject header-injection check, optional CSV attachment, sent/failed history.
- SMS tool using the TextBee API (`app/sms_gateway.py`): PH mobile number check and +63 conversion, 320-character limit with counter, sent/failed history.
- "Email CSV" on the Fake Data page attaches the shown records to a new email.
- `app/config.py` reads credentials from a gitignored `.env`; `.env.example` documents the names. Email and SMS pages show a setup notice until configured.
- `app/http_json.py`: one helper for JSON web API calls. `app/ui/common.py`: API calls run on a worker thread so the window never freezes.
- Database tables `short_links` and `messages`, both per user with cascade delete.
- Tests for config, http_json (local test server), shortener, mailer (fake SMTP), SMS (fake API), new database tables.

### Changed
- App renamed to Utility Hub: a sidebar switches between Fake Data, URL Shortener, Email and SMS (`app/ui/shell.py`). Theme toggle and logout moved to the sidebar.
- `app/ui/dashboard.py` moved to `app/ui/fakedata_page.py`.
- Database file renamed from `fakedata.db` to `utilities.db` (renamed automatically on first run).
- Plain buttons now have a visible border; disabled Delete buttons look disabled.

## 2026-11-04
### Added
- SQLite storage (`app/db.py`): `users` and `records` tables, records scoped per user, parameterized queries, cascade delete.
- Auth (`app/auth.py`): salted PBKDF2-SHA256 (600,000 iterations), `hmac.compare_digest`, username/password validation, duplicate-username handling, same error for unknown user and wrong password.
- Fake data generator (`app/generator.py`, `app/ph_data.py`): 10 PH-style fields per record, 10 to 1000 records per run, stdlib only.
- CSV export (`app/export.py`) with formula-injection escaping.
- UI (`app/ui/`): login/register screen, dashboard with Treeview table, generate, search, delete selected, export CSV, record count, empty states, logout, light/dark theme saved per user, window icon.
- Tests (`tests/`): db, auth, generator, export.
