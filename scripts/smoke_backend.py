from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"


def ensure_test_runtime() -> None:
    try:
        import fastapi  # noqa: F401
        from fastapi.testclient import TestClient as _TestClient  # noqa: F401
    except (ImportError, RuntimeError) as exc:
        venv_python = REPO_ROOT / "venv" / "bin" / "python"

        if (
            venv_python.is_file()
            and Path(sys.executable).resolve()
            != venv_python.resolve()
        ):
            os.execv(
                str(venv_python),
                [
                    str(venv_python),
                    str(Path(__file__).resolve()),
                    *sys.argv[1:],
                ],
            )

        raise SystemExit(
            "FastAPI TestClient runtime is unavailable. "
            "Install app/requirements.txt and httpx2. "
            f"Original error: {exc}"
        ) from exc


ensure_test_runtime()

os.chdir(APP_DIR)
sys.path.insert(0, str(APP_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from backend.api.main import app  # noqa: E402


Validator = Callable[[Any], None]


def require_mapping(payload: Any) -> None:
    assert isinstance(payload, dict), "expected a JSON object"


def run_get(
    client: TestClient,
    path: str,
    *,
    params: dict[str, str] | None = None,
    validate: Validator = require_mapping,
) -> None:
    response = client.get(path, params=params)
    assert response.status_code == 200, (
        f"GET {path} returned {response.status_code}: {response.text[:300]}"
    )
    payload = response.json()
    validate(payload)
    print(f"PASS  GET {response.request.url.path} -> {response.status_code}")


def main() -> None:
    route_paths = {getattr(route, 'path', None) for route in app.routes if getattr(route, 'path', None)}
    passed = 0
    skipped = 0

    with TestClient(app) as client:
        run_get(client, "/")
        passed += 1

        run_get(client, "/health")
        passed += 1

        if "/stations" in route_paths:
            run_get(client, "/stations", params={"q": "PNBE"})
            passed += 1
        else:
            print("SKIP  GET /stations -> route not available")
            skipped += 1

        run_get(
            client,
            "/search",
            params={"source": "PNBE", "destination": "NDLS"},
        )
        passed += 1

    print(f"Backend smoke test complete: {passed} passed, {skipped} skipped")


if __name__ == "__main__":
    main()
