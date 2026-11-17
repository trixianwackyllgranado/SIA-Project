# Utility Hub

ITL313-18 (SIA 2 Lab) mini project by Trixian Wackyll Granado and Gabriel Antonino.

A Tkinter desktop app with a login system (SQLite + hashlib) and the four 3B Utilities tools.
Each user's data is saved in SQLite and only visible to them.

| Tool | What it does | API |
|---|---|---|
| Fake Data | Generates 10 to 1000 Philippine sample records (10 fields each), search, export CSV, email CSV | none (generated locally) |
| URL Shortener | Shortens a link, keeps a history, copy/open, send the short link by email or SMS | [is.gd](https://is.gd/apishorteningreference.php) (free, no key) |
| Email | Sends one email at a time, optional CSV attachment, sent/failed history | Gmail SMTP via Python `smtplib` |
| SMS | Sends one text at a time to a PH mobile number, sent/failed history | [TextBee](https://textbee.dev/docs/sending-sms/sending-sms) (uses your Android phone's SIM) |

No third-party Python packages: everything uses the standard library.

## Run
```
python main.py
```
The database `utilities.db` is created next to `main.py` on first run (gitignored).
If you used the older version, `fakedata.db` is renamed to `utilities.db` automatically, so accounts and records stay.

Fake Data works offline. URL Shortener, Email and SMS need internet.

## Test
```
python -m unittest discover -s tests -v
```
The tests never send real emails or texts: SMTP and the APIs are replaced with fakes.

## Setting up Email and SMS (once per computer)
Copy `.env.example` to `.env` in the same folder as `main.py`, then fill it in.
`.env` is gitignored. Never commit it, screenshot it, or paste its values anywhere.

### Email (Gmail)
1. Turn on 2-Step Verification on the Google account you'll send from.
2. Google Account > Security > 2-Step Verification > App passwords. Create one (name it "Utility Hub").
3. In `.env`: `SMTP_USER` = that Gmail address, `SMTP_APP_PASSWORD` = the 16-character app password.

### SMS (TextBee)
1. Create an account at textbee.dev.
2. Install the TextBee app on an Android phone with a SIM and load, and link it to your account (follow the dashboard's instructions).
3. Create an API key in the dashboard and put it in `.env` as `TEXTBEE_API_KEY`.
4. The phone must be on and online when you send. Messages are sent from that SIM, so normal SMS charges apply.

In the app, open Email or SMS and click **Check again** after editing `.env`.

## How the code is organized
| File | Job |
|---|---|
| `main.py` | Starts the window, switches between login and the main screen, theme |
| `app/db.py` | Every SQL query: users, records, short_links, messages |
| `app/auth.py` | Password hashing (salted PBKDF2-SHA256), register, login |
| `app/generator.py`, `app/ph_data.py` | Fake record generation |
| `app/export.py` | CSV export with spreadsheet formula escaping |
| `app/http_json.py` | The one helper that calls web APIs |
| `app/shortener.py` | is.gd API |
| `app/mailer.py` | SMTP email |
| `app/sms_gateway.py` | TextBee API |
| `app/config.py` | Reads `.env` |
| `app/ui/shell.py` | Sidebar and switching between tools |
| `app/ui/common.py` | Shared page parts and running API calls in the background |
| `app/ui/*_page.py`, `app/ui/message_pages.py` | One screen per tool |

## Limits on purpose
- One recipient per email or SMS, and a confirmation before each send. No bulk sending.
- Only `http`/`https` links can be shortened. A link you already shortened reuses the saved short link (is.gd asks clients not to resubmit).
- Generated fake data is never used as a recipient: the numbers and emails are random and could belong to real people.
