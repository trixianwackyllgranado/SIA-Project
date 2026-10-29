"""Fake Philippine person records with 10 fields each (stdlib only)."""
import random
import re
import unicodedata
from datetime import date, timedelta

from app import ph_data

MIN_RECORDS = 10
MAX_RECORDS = 1000
MIN_AGE = 18
MAX_AGE = 65
CIVIL_STATUSES = ("Single", "Married", "Widowed", "Separated", "Annulled")


def _ascii_slug(text):
    """'Ibañez Dela Cruz' -> 'ibanezdelacruz' (for emails and usernames)."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", plain.lower())


def _subtract_years(day, years):
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # Feb 29 in a non-leap year
        return day.replace(year=day.year - years, day=28)


def _birthdate(rng, today):
    latest = _subtract_years(today, MIN_AGE)                              # just turned 18
    earliest = _subtract_years(today, MAX_AGE + 1) + timedelta(days=1)   # still 65
    return earliest + timedelta(days=rng.randint(0, (latest - earliest).days))


def _civil_status(rng, age):
    if age < 25:
        weights = (85, 14, 0, 1, 0)
    elif age < 45:
        weights = (35, 55, 2, 5, 3)
    else:
        weights = (15, 62, 13, 6, 4)
    return rng.choices(CIVIL_STATUSES, weights=weights)[0]


def generate_record(rng, today):
    gender = rng.choice(("Male", "Female"))
    names = ph_data.MALE_FIRST_NAMES if gender == "Male" else ph_data.FEMALE_FIRST_NAMES
    first = rng.choice(names)
    last = rng.choice(ph_data.LAST_NAMES)
    middle_initial = rng.choice(ph_data.LAST_NAMES)[0]
    full_name = f"{first} {middle_initial}. {last}"

    city, province = rng.choice(ph_data.CITIES)
    address = (
        f"{rng.randint(1, 999)} {rng.choice(ph_data.STREETS)} St., "
        f"Brgy. {rng.choice(ph_data.BARANGAYS)}, {city}, {province}"
    )

    birth = _birthdate(rng, today)
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    mobile = (
        f"+63 {rng.choice(ph_data.MOBILE_PREFIXES)} "
        f"{rng.randint(0, 999):03d} {rng.randint(0, 9999):04d}"
    )

    first_slug, last_slug = _ascii_slug(first), _ascii_slug(last)
    email = f"{first_slug}.{last_slug}{rng.randint(1, 999)}@{rng.choice(ph_data.EMAIL_DOMAINS)}"
    fake_username = rng.choice((
        f"{first_slug}_{last_slug}{rng.randint(1, 99)}",
        f"{first_slug[0]}{last_slug}{rng.randint(10, 9999)}",
        f"{last_slug}.{first_slug}{birth.year % 100:02d}",
    ))

    company = (
        f"{rng.choice(ph_data.COMPANY_WORDS)} {rng.choice(ph_data.COMPANY_KINDS)} "
        f"{rng.choice(ph_data.COMPANY_SUFFIXES)}"
    )

    return {
        "full_name": full_name,
        "address": address,
        "birthdate": birth.isoformat(),
        "mobile_number": mobile,
        "email": email,
        "gender": gender,
        "civil_status": _civil_status(rng, age),
        "occupation": rng.choice(ph_data.OCCUPATIONS),
        "company": company,
        "fake_username": fake_username,
    }


def generate_records(count=MIN_RECORDS, rng=None, today=None):
    """Return a list of `count` fake records (10 to 1000)."""
    if not isinstance(count, int) or not MIN_RECORDS <= count <= MAX_RECORDS:
        raise ValueError(f"Number of records must be between {MIN_RECORDS} and {MAX_RECORDS}.")
    rng = rng or random.Random()
    today = today or date.today()
    return [generate_record(rng, today) for _ in range(count)]
