from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "app": ROOT / "frontend/src/App.jsx",
    "main": ROOT / "frontend/src/main.jsx",
    "app_css": ROOT / "frontend/src/App.css",
    "index_css": ROOT / "frontend/src/index.css",
    "account_css": ROOT / "frontend/src/components/UserAccountPanel.css",
    "station": ROOT / "frontend/src/components/SafeStationInput.jsx",
}


def read_file(name: str) -> str:
    path = FILES[name]

    if not path.exists():
        raise SystemExit(f"FAIL: missing file: {path}")

    return path.read_text(encoding="utf-8")


def require_text(
    content: str,
    marker: str,
    description: str,
) -> None:
    if marker not in content:
        raise SystemExit(
            f"FAIL: {description}\nMissing marker: {marker}"
        )

    print(f"PASS: {description}")


def require_regex(
    content: str,
    pattern: str,
    description: str,
) -> None:
    if not re.search(pattern, content, flags=re.DOTALL):
        raise SystemExit(
            f"FAIL: {description}\nMissing pattern: {pattern}"
        )

    print(f"PASS: {description}")


def main() -> None:
    app = read_file("app")
    main_source = read_file("main")
    app_css = read_file("app_css")
    index_css = read_file("index_css")
    account_css = read_file("account_css")
    station = read_file("station")

    print("RailBay Phase 39 mobile accessibility smoke test")

    require_text(
        app,
        'className="skip-link"',
        "keyboard skip link",
    )
    require_text(
        app,
        'aria-label="Primary navigation"',
        "primary navigation label",
    )
    require_text(
        app,
        'aria-label="RailBay railway route search"',
        "route-search form label",
    )
    require_text(
        app,
        "aria-busy={loading}",
        "search busy state",
    )
    require_text(
        app,
        'aria-label="Swap departure and destination stations"',
        "swap-button accessible name",
    )
    require_text(
        app,
        'aria-label="Popular route shortcuts"',
        "popular routes accessible label",
    )
    require_text(
        app,
        'role="alert"',
        "search error alert",
    )
    require_text(
        app,
        'aria-label="RailBay route recommendations"',
        "results landmark label",
    )

    require_text(
        station,
        'role="combobox"',
        "station combobox role",
    )
    require_text(
        station,
        'role="listbox"',
        "station listbox role",
    )
    require_text(
        station,
        'role="option"',
        "station option role",
    )
    require_text(
        station,
        "aria-activedescendant",
        "active suggestion announcement",
    )
    require_text(
        station,
        "onKeyDown={handleKeyDown}",
        "station keyboard navigation",
    )
    require_text(
        station,
        "htmlFor={inputId}",
        "station label association",
    )
    require_text(
        station,
        'event.key === "ArrowDown"',
        "arrow-down navigation",
    )
    require_text(
        station,
        'event.key === "ArrowUp"',
        "arrow-up navigation",
    )
    require_text(
        station,
        'event.key === "Escape"',
        "escape closes suggestions",
    )

    require_regex(
        main_source,
        r"showInternalTools\s*&&\s*<AdminBetaFeedbackPanel",
        "admin feedback remains gated",
    )
    require_regex(
        app,
        r"showInternalTools\s*&&\s*renderFareAdminPanel",
        "fare admin remains gated",
    )
    require_text(
        app,
        'className="internal-tools-shell"',
        "internal panels remain gated",
    )

    require_text(
        app_css,
        ".skip-link",
        "skip-link styling",
    )
    require_text(
        app_css,
        ":focus-visible",
        "visible keyboard focus styling",
    )
    require_text(
        app_css,
        "prefers-reduced-motion",
        "reduced-motion support",
    )
    require_text(
        app_css,
        "forced-colors",
        "forced-colour support",
    )
    require_text(
        app_css,
        'button[aria-selected="true"]',
        "active autocomplete styling",
    )
    require_text(
        app_css,
        "@media (max-width: 560px)",
        "small-screen layout",
    )
    require_text(
        account_css,
        "min-height: 44px",
        "account touch targets",
    )
    require_text(
        index_css,
        "overflow-x: hidden",
        "horizontal overflow protection",
    )

    print(
        "PASS: Phase 39 mobile accessibility "
        "contract completed"
    )


if __name__ == "__main__":
    main()
