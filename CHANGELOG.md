# Changelog

## 2026-11-04
### Added
- SQLite storage (`app/db.py`): `users` and `records` tables, records scoped per user, parameterized queries, cascade delete.
- Auth (`app/auth.py`): salted PBKDF2-SHA256 (600,000 iterations), `hmac.compare_digest`, username/password validation, duplicate-username handling, same error for unknown user and wrong password.
- Fake data generator (`app/generator.py`, `app/ph_data.py`): 10 PH-style fields per record, 10 to 1000 records per run, stdlib only.
- CSV export (`app/export.py`) with formula-injection escaping.
- UI (`app/ui/`): login/register screen, dashboard with Treeview table, generate, search, delete selected, export CSV, record count, empty states, logout, light/dark theme saved per user, window icon.
- Tests (`tests/`): db, auth, generator, export.
