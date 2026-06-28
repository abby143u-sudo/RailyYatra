import sys
from backend.services.fare_csv_importer import import_fares_from_csv


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_fares.py data/raw/fares.csv")
        sys.exit(1)

    file_path = sys.argv[1]

    result = import_fares_from_csv(file_path)

    print("Fare CSV import completed")
    print(f"File: {result['file']}")
    print(f"Imported: {result['imported']}")
    print(f"Skipped: {result['skipped']}")

    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"Row {error['row']}: {error['error']}")


if __name__ == "__main__":
    main()
