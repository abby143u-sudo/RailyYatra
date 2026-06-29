from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parent


def get_migration_path(filename: str = "001_ingestion_metadata.sql") -> Path:
    return MIGRATIONS_DIR / filename


__all__ = ["MIGRATIONS_DIR", "get_migration_path"]
