#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "frontend" / "src" / "config" / "api.js"
COMPONENTS_DIR = REPO_ROOT / "frontend" / "src" / "components"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
DEPLOYMENT_NOTES = REPO_ROOT / "docs" / "DEPLOYMENT_NOTES.md"


def main() -> int:
    print("RailYatra frontend API config smoke test")
    print("Mode: static frontend config check")

    if not CONFIG_PATH.exists():
        print("FAIL: frontend/src/config/api.js missing")
        return 1

    if not ENV_EXAMPLE.exists():
        print("FAIL: .env.example missing")
        return 1

    if not DEPLOYMENT_NOTES.exists():
        print("FAIL: docs/DEPLOYMENT_NOTES.md missing")
        return 1

    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    env_text = ENV_EXAMPLE.read_text(encoding="utf-8")
    notes_text = DEPLOYMENT_NOTES.read_text(encoding="utf-8")

    required_config_phrases = [
        "VITE_RAILYATRA_API_BASE",
        "fallbackApiBase",
        "http://127.0.0.1:8000",
        "export const API_BASE",
        "export function apiUrl",
    ]

    for phrase in required_config_phrases:
        print(f"api config phrase {phrase}: {'yes' if phrase in config_text else 'missing'}")
        if phrase not in config_text:
            print(f"FAIL: missing api config phrase {phrase}")
            return 1

    if "VITE_RAILYATRA_API_BASE=http://127.0.0.1:8000" not in env_text:
        print("FAIL: .env.example missing VITE_RAILYATRA_API_BASE")
        return 1

    if "VITE_RAILYATRA_API_BASE=https://your-backend-domain.example.com" not in notes_text:
        print("FAIL: deployment notes missing production frontend API base instruction")
        return 1

    component_paths = sorted(COMPONENTS_DIR.glob("Phase*.jsx"))
    if not component_paths:
        print("FAIL: no Phase components found")
        return 1

    source_hardcoded_violations = []
    missing_imports = []

    for path in component_paths:
        text = path.read_text(encoding="utf-8")

        if 'const API_BASE = "http://127.0.0.1:8000"' in text:
            source_hardcoded_violations.append(str(path.relative_to(REPO_ROOT)))

        if 'const API_BASE = "http://localhost:8000"' in text:
            source_hardcoded_violations.append(str(path.relative_to(REPO_ROOT)))

        if "API_BASE" in text and 'import { API_BASE } from "../config/api.js";' not in text:
            missing_imports.append(str(path.relative_to(REPO_ROOT)))

    print(f"phase component count: {len(component_paths)}")
    print(f"hardcoded local API base violations: {len(source_hardcoded_violations)}")
    print(f"missing API_BASE config imports: {len(missing_imports)}")

    if source_hardcoded_violations:
        print("FAIL: component hardcoded API base found")
        for item in source_hardcoded_violations:
            print(f"  {item}")
        return 1

    if missing_imports:
        print("FAIL: component uses API_BASE without config import")
        for item in missing_imports:
            print(f"  {item}")
        return 1

    print("Frontend API base env configured: yes")
    print("Local fallback preserved: yes")
    print("Deployment frontend backend URL documented: yes")
    print("PASS: frontend API config smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
