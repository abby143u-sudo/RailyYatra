from pathlib import Path

_app_backend = Path(__file__).resolve().parent.parent / "app" / "backend"

if _app_backend.exists():
    __path__.append(str(_app_backend))
