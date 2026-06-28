import csv
from pathlib import Path

from backend.services.official_fare_service import (
    ensure_official_fare_table,
    upsert_official_fare,
)


REQUIRED_FIELDS = ["train_no", "source", "destination", "fare"]


def import_fares_from_csv(file_path, default_class_code="SL", source_type="csv"):
    ensure_official_fare_table()

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    imported = 0
    skipped = 0
    errors = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file has no header row")

        normalized_headers = {
            header: normalize_header(header)
            for header in reader.fieldnames
        }

        for row_number, row in enumerate(reader, start=2):
            normalized_row = normalize_row(row, normalized_headers)

            try:
                validate_row(normalized_row, row_number)

                train_no = normalized_row["train_no"]
                source = normalized_row["source"]
                destination = normalized_row["destination"]
                fare = int(float(normalized_row["fare"]))

                class_code = normalized_row.get("class_code") or default_class_code
                row_source_type = normalized_row.get("source_type") or source_type

                upsert_official_fare(
                    train_no=train_no,
                    source=source,
                    destination=destination,
                    class_code=class_code,
                    fare=fare,
                    source_type=row_source_type,
                )

                imported += 1

            except Exception as exc:
                skipped += 1
                errors.append({
                    "row": row_number,
                    "error": str(exc),
                    "data": normalized_row,
                })

    return {
        "file": str(path),
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20],
    }


def normalize_header(header):
    value = str(header or "").strip().lower()

    aliases = {
        "train": "train_no",
        "train_number": "train_no",
        "train no": "train_no",
        "train_no": "train_no",

        "from": "source",
        "src": "source",
        "source": "source",

        "to": "destination",
        "dest": "destination",
        "destination": "destination",

        "class": "class_code",
        "class_code": "class_code",
        "class code": "class_code",

        "price": "fare",
        "amount": "fare",
        "fare": "fare",

        "source_type": "source_type",
        "data_source": "source_type",
    }

    return aliases.get(value, value.replace(" ", "_"))


def normalize_row(row, normalized_headers):
    result = {}

    for original_header, value in row.items():
        normalized_key = normalized_headers.get(original_header)
        result[normalized_key] = normalize_value(value)

    return result


def normalize_value(value):
    return str(value or "").strip().upper()


def validate_row(row, row_number):
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            raise ValueError(f"Missing required field '{field}' at row {row_number}")

    try:
        fare = int(float(row["fare"]))
    except Exception:
        raise ValueError(f"Invalid fare at row {row_number}: {row.get('fare')}")

    if fare <= 0:
        raise ValueError(f"Fare must be greater than 0 at row {row_number}")
