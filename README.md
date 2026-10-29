# Fake Data Generator

ITL313-18 (SIA 2 Lab) mini project by Trixian Wackyll Granado and Gabriel Antonino.
A Tkinter desktop app with a login system (SQLite + hashlib) that generates and stores fake Philippine person records.

## Run
```
python main.py
```
The database `fakedata.db` is created automatically next to `main.py` on first run (it's gitignored).

## Test
```
python -m unittest discover -s tests -v
```

## Features
- Register and log in. Passwords are hashed with salted PBKDF2-SHA256 (600,000 iterations); plain text is never stored.
- Generate 10 to 1000 records per run, 10 fields each: full name, address, birthdate, mobile number, email, gender, civil status, occupation, company, username.
- Each user only sees and deletes their own records.
- Search, delete selected (Delete key works too), export to CSV, light/dark mode saved per user.
