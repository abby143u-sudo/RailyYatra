import re
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "railyatra.db"

DAY_NAMES = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]

DAY_SHORTS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

DAY_ALIASES = {
    "MON": "MONDAY",
    "MONDAY": "MONDAY",
    "1": "MONDAY",

    "TUE": "TUESDAY",
    "TUES": "TUESDAY",
    "TUESDAY": "TUESDAY",
    "2": "TUESDAY",

    "WED": "WEDNESDAY",
    "WEDNESDAY": "WEDNESDAY",
    "3": "WEDNESDAY",

    "THU": "THURSDAY",
    "THUR": "THURSDAY",
    "THURS": "THURSDAY",
    "THURSDAY": "THURSDAY",
    "4": "THURSDAY",

    "FRI": "FRIDAY",
    "FRIDAY": "FRIDAY",
    "5": "FRIDAY",

    "SAT": "SATURDAY",
    "SATURDAY": "SATURDAY",
    "6": "SATURDAY",

    "SUN": "SUNDAY",
    "SUNDAY": "SUNDAY",
    "7": "SUNDAY",
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_day_info(journey_date):
    if not journey_date:
        return None

    parsed = datetime.strptime(journey_date, "%Y-%m-%d").date()
    weekday_index = parsed.weekday()

    return {
        "date": parsed.isoformat(),
        "day_name": DAY_NAMES[weekday_index],
        "day_short": DAY_SHORTS[weekday_index],
        "day_number": weekday_index + 1,
    }


def get_train_row(train_no):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(trains)")
        columns = [row["name"] for row in cursor.fetchall()]

        if not columns:
            return None

        train_no_columns = [
            col for col in columns
            if col.lower() in {"train_no", "train_number", "number"}
        ]

        if not train_no_columns:
            return None

        train_col = train_no_columns[0]

        cursor.execute(
            f"SELECT * FROM trains WHERE {train_col} = ? LIMIT 1",
            (str(train_no),),
        )

        row = cursor.fetchone()
        return dict(row) if row else None

    except Exception:
        return None

    finally:
        conn.close()


def train_runs_on_date(train_no, journey_date):
    day_info = get_day_info(journey_date)
    row = get_train_row(train_no)

    if not day_info:
        return {
            "train_no": train_no,
            "runs": True,
            "confidence": "unknown",
            "reason": "Journey date not provided",
        }

    if not row:
        return {
            "train_no": train_no,
            "date": day_info["date"],
            "day_name": day_info["day_name"],
            "runs": True,
            "confidence": "unknown",
            "reason": "Train running-day data not found",
        }

    parsed_days = extract_running_days(row)

    if not parsed_days:
        return {
            "train_no": train_no,
            "date": day_info["date"],
            "day_name": day_info["day_name"],
            "runs": True,
            "confidence": "unknown",
            "reason": "Running-day column not available",
        }

    runs = day_info["day_name"] in parsed_days

    return {
        "train_no": train_no,
        "date": day_info["date"],
        "day_name": day_info["day_name"],
        "runs": runs,
        "confidence": "high",
        "reason": (
            f"Train runs on {day_info['day_name']}"
            if runs
            else f"Train may not run on {day_info['day_name']}"
        ),
        "running_days": sorted(parsed_days, key=DAY_NAMES.index),
    }


def extract_running_days(row):
    boolean_days = extract_boolean_day_columns(row)
    if boolean_days:
        return boolean_days

    text_day_columns = [
        "running_days",
        "runs_on",
        "run_days",
        "days",
        "days_of_run",
        "available_days",
        "schedule_days",
    ]

    for column in text_day_columns:
        if column in row and row.get(column):
            parsed = parse_days_value(row.get(column))
            if parsed:
                return parsed

    return set()


def extract_boolean_day_columns(row):
    found = set()

    column_map = {
        "mon": "MONDAY",
        "monday": "MONDAY",
        "runs_monday": "MONDAY",

        "tue": "TUESDAY",
        "tues": "TUESDAY",
        "tuesday": "TUESDAY",
        "runs_tuesday": "TUESDAY",

        "wed": "WEDNESDAY",
        "wednesday": "WEDNESDAY",
        "runs_wednesday": "WEDNESDAY",

        "thu": "THURSDAY",
        "thur": "THURSDAY",
        "thursday": "THURSDAY",
        "runs_thursday": "THURSDAY",

        "fri": "FRIDAY",
        "friday": "FRIDAY",
        "runs_friday": "FRIDAY",

        "sat": "SATURDAY",
        "saturday": "SATURDAY",
        "runs_saturday": "SATURDAY",

        "sun": "SUNDAY",
        "sunday": "SUNDAY",
        "runs_sunday": "SUNDAY",
    }

    for column, day_name in column_map.items():
        if column not in row:
            continue

        value = str(row.get(column) or "").strip().lower()

        if value in {"1", "true", "yes", "y", "run", "runs"}:
            found.add(day_name)

    return found


def parse_days_value(value):
    text = str(value or "").strip().upper()

    if not text:
        return set()

    if text in {"DAILY", "ALL", "ALL DAYS", "EVERYDAY", "EVERY DAY"}:
        return set(DAY_NAMES)

    compact = re.sub(r"[^01]", "", text)

    if len(compact) == 7:
        return {
            DAY_NAMES[index]
            for index, flag in enumerate(compact)
            if flag == "1"
        }

    tokens = re.split(r"[^A-Z0-9]+", text)
    found = set()

    for token in tokens:
        if not token:
            continue

        day_name = DAY_ALIASES.get(token)
        if day_name:
            found.add(day_name)

    return found


def extract_train_numbers(item_type, data):
    if item_type == "direct":
        return [data.get("train_no")]

    if item_type == "one_transfer":
        return [data.get("first_train"), data.get("second_train")]

    if item_type == "multi_transfer":
        return [
            leg.get("train_no")
            for leg in data.get("train_legs", [])
        ]

    return []


def build_running_day_info(item_type, data, journey_date):
    if not journey_date:
        return None

    train_numbers = [
        str(train_no)
        for train_no in extract_train_numbers(item_type, data or {})
        if train_no
    ]

    if not train_numbers:
        return {
            "date": journey_date,
            "available": True,
            "status": "unknown",
            "label": "Running day unknown",
            "checks": [],
        }

    checks = [
        train_runs_on_date(train_no, journey_date)
        for train_no in train_numbers
    ]

    unavailable = [
        check for check in checks
        if check.get("runs") is False
    ]

    unknown = [
        check for check in checks
        if check.get("confidence") == "unknown"
    ]

    if unavailable:
        return {
            "date": journey_date,
            "available": False,
            "status": "not_running",
            "label": "Some trains may not run on selected date",
            "checks": checks,
        }

    if unknown:
        return {
            "date": journey_date,
            "available": True,
            "status": "unknown",
            "label": "Running day data not fully verified",
            "checks": checks,
        }

    return {
        "date": journey_date,
        "available": True,
        "status": "running",
        "label": "All trains run on selected date",
        "checks": checks,
    }
