from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def require(condition, description):
    if not condition:
        raise SystemExit(
            f"FAIL: {description}"
        )

    print(f"PASS: {description}")


def read(path):
    require(path.exists(), f"{path} exists")
    return path.read_text(encoding="utf-8")


def vercel_config_path():
    candidates = [
        ROOT / "frontend/vercel.json",
        ROOT / "vercel.json",
    ]

    existing = [
        path for path in candidates if path.exists()
    ]

    require(
        len(existing) == 1,
        "exactly one Vercel configuration",
    )

    return existing[0]


def static_checks():
    index = read(ROOT / "frontend/index.html")
    main = read(ROOT / "frontend/src/main.jsx")
    app = read(ROOT / "frontend/src/App.jsx")
    boundary = read(
        ROOT
        / "frontend/src/components/AppErrorBoundary.jsx"
    )
    feedback = read(
        ROOT
        / "frontend/src/components/BetaFeedbackWidget.jsx"
    )
    diagnostics = read(
        ROOT
        / "frontend/src/utils/frontendDiagnostics.js"
    )
    security = read(
        ROOT
        / "frontend/public/.well-known/security.txt"
    )

    config = json.loads(
        read(vercel_config_path())
    )

    require(
        'name="robots"' in index,
        "SEO robots metadata",
    )
    require(
        'rel="preconnect"' in index,
        "API preconnect metadata",
    )
    require(
        "og:image:width" in index,
        "social image dimensions",
    )
    require(
        "installGlobalFrontendDiagnostics" in main,
        "global diagnostics installed",
    )
    require(
        "recordFrontendError" in boundary,
        "React error boundary diagnostics",
    )
    require(
        "sessionStorage" in diagnostics,
        "privacy-conscious session diagnostics",
    )
    require(
        "from \"../config/api.js\"" in feedback,
        "public feedback uses shared API config",
    )
    require(
        "https://api.railbay.xyz/fares"
        not in app,
        "fare admin has no hardcoded API URL",
    )
    require(
        "Canonical: https://railbay.xyz/"
        in security,
        "security.txt canonical URL",
    )

    header_names = {
        header["key"]
        for rule in config.get("headers", [])
        for header in rule.get("headers", [])
    }

    for header_name in [
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Strict-Transport-Security",
        "Cache-Control",
    ]:
        require(
            header_name in header_names,
            f"{header_name} configured",
        )

    print(
        "PASS: Phase 40 static production "
        "launch contract completed"
    )


def fetch(url):
    request = Request(
        url,
        headers={
            "User-Agent":
                "RailBay-Launch-Smoke/1.0",
        },
    )

    with urlopen(request, timeout=25) as response:
        return (
            response.status,
            {
                key.lower(): value
                for key, value
                in response.headers.items()
            },
            response.read().decode(
                "utf-8",
                errors="replace",
            ),
        )


def live_checks():
    status, headers, body = fetch(
        "https://railbay.xyz/"
    )

    require(status == 200, "live frontend HTTP 200")
    require(
        "<title>RailBay" in body,
        "live RailBay title",
    )

    for header_name in [
        "content-security-policy",
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "permissions-policy",
        "strict-transport-security",
    ]:
        require(
            header_name in headers,
            f"live {header_name} header",
        )

    for path, marker in [
        (
            "/robots.txt",
            "Sitemap: https://railbay.xyz/sitemap.xml",
        ),
        (
            "/sitemap.xml",
            "<loc>https://railbay.xyz/</loc>",
        ),
        (
            "/site.webmanifest",
            '"name": "RailBay"',
        ),
        (
            "/.well-known/security.txt",
            "Canonical: https://railbay.xyz/",
        ),
    ]:
        asset_status, _, asset_body = fetch(
            f"https://railbay.xyz{path}"
        )

        require(
            asset_status == 200,
            f"live {path} HTTP 200",
        )
        require(
            marker in asset_body,
            f"live {path} content",
        )

    api_status, _, api_body = fetch(
        "https://api.railbay.xyz/health"
    )

    require(
        api_status == 200,
        "live backend HTTP 200",
    )
    require(
        "status" in api_body.lower(),
        "live backend health payload",
    )

    print(
        "PASS: Phase 40 live production "
        "launch contract completed"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
    )
    args = parser.parse_args()

    static_checks()

    if args.live:
        live_checks()


if __name__ == "__main__":
    main()
