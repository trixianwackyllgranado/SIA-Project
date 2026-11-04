"""CSV export with protection against spreadsheet formula injection."""
import csv
import re

from app.db import RECORD_FIELDS

HEADERS = (
    "Full Name", "Address", "Birthdate", "Mobile Number", "Email",
    "Gender", "Civil Status", "Occupation", "Company", "Username",
)

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
_PHONE_RE = re.compile(r"^\+63 9\d{2} \d{3} \d{4}$")


def safe_cell(value):
    """Prefix a ' to cells Excel would treat as a formula (except PH phone numbers)."""
    text = str(value)
    if text.startswith(_FORMULA_START) and not _PHONE_RE.fullmatch(text):
        return "'" + text
    return text


def write_csv(path, records):
    """Write records (dicts or sqlite rows) to path. Returns the number of rows."""
    count = 0
    # utf-8-sig so Excel shows ñ correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADERS)
        for rec in records:
            writer.writerow([safe_cell(rec[f]) for f in RECORD_FIELDS])
            count += 1
    return count
