#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Any


FRONTEND_URL = os.getenv(
    "RAILYATRA_FRONTEND_URL",
    "https://raily-yatra.vercel.app",
).rstrip("/")

BACKEND_URL = os.getenv(
    "RAILYATRA_BACKEND_URL",
    "https://railyyatra-backend.onrender.com",
).rstrip("/")

SOURCE = os.getenv("RAILYATRA_SMOKE_SOURCE", "NDLS")
DESTINATION = os.getenv(
    "RAILYATRA_SMOKE_DESTINATION",
    "PNBE",
)

JOURNEY_DATE = os.getenv(
    "RAILYATRA_SMOKE_DATE",
    (date.today() + timedelta(days=5)).isoformat(),
)

TIMEOUT_SECONDS = int(
    os.getenv("RAILYATRA_SMOKE_TIMEOUT", "120")
)

failures: list[str] = []
warnings: list[str] = []


def request(
    url: str,
) -> tuple[int, dict[str, str], bytes, float]:
    started = time.perf_counter()

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RailYatra-Production-Smoke/1.0",
            "Accept": "application/json,text/html,*/*",
        },
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=TIMEOUT_SECONDS,
        ) as response:
            body = response.read()
            elapsed = time.perf_counter() - started

            headers = {
                key.lower(): value
                for key, value in response.headers.items()
            }

            return (
                response.status,
                headers,
                body,
                elapsed,
            )

    except urllib.error.HTTPError as error:
        body = error.read()
        elapsed = time.perf_counter() - started

        headers = {
            key.lower(): value
            for key, value in error.headers.items()
        }

        return (
            error.code,
            headers,
            body,
            elapsed,
        )


def request_json(
    url: str,
) -> tuple[
    int,
    dict[str, str],
    dict[str, Any],
    float,
]:
    status, headers, body, elapsed = request(url)

    try:
        payload = json.loads(
            body.decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {
            "_invalid_json": True,
            "_body_preview": body[:300].decode(
                "utf-8",
                errors="replace",
            ),
        }

    return status, headers, payload, elapsed


def pass_check(
    name: str,
    detail: str = "",
) -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"PASS: {name}{suffix}")


def fail_check(
    name: str,
    detail: str,
) -> None:
    failures.append(f"{name}: {detail}")
    print(f"FAIL: {name} — {detail}")


def warning(
    name: str,
    detail: str,
) -> None:
    warnings.append(f"{name}: {detail}")
    print(f"WARN: {name} — {detail}")


def find_number(
    value: Any,
    accepted_keys: set[str],
) -> int | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()

            if (
                normalized_key in accepted_keys
                and isinstance(item, (int, float))
            ):
                return int(item)

        for item in value.values():
            result = find_number(
                item,
                accepted_keys,
            )

            if result is not None:
                return result

    if isinstance(value, list):
        for item in value:
            result = find_number(
                item,
                accepted_keys,
            )

            if result is not None:
                return result

    return None


print("=" * 72)
print("RailYatra production smoke test")
print("=" * 72)
print("Frontend:", FRONTEND_URL)
print("Backend :", BACKEND_URL)
print(
    "Journey :",
    SOURCE,
    "→",
    DESTINATION,
    "on",
    JOURNEY_DATE,
)
print()


# Frontend
frontend_status, _, frontend_body, frontend_time = request(
    f"{FRONTEND_URL}/?smoke={int(time.time())}"
)

if frontend_status == 200:
    pass_check(
        "Frontend reachable",
        f"{frontend_time:.2f}s",
    )
else:
    fail_check(
        "Frontend reachable",
        f"HTTP {frontend_status}",
    )

if b"<html" in frontend_body.lower():
    pass_check("Frontend returned HTML")
else:
    warning(
        "Frontend content",
        "Response did not clearly contain an HTML document",
    )


# Backend health
health_status, _, health, health_time = request_json(
    f"{BACKEND_URL}/health"
)

if health_status == 200:
    pass_check(
        "Backend health endpoint",
        f"{health_time:.2f}s",
    )
else:
    fail_check(
        "Backend health endpoint",
        f"HTTP {health_status}: {health}",
    )

if health.get("ok") is False:
    fail_check(
        "Backend health payload",
        str(health),
    )
else:
    pass_check("Backend health payload")


# Real data health
data_status, _, data_health, data_time = request_json(
    f"{BACKEND_URL}/data-quality/health"
)

if data_status == 200:
    pass_check(
        "Data-quality endpoint",
        f"{data_time:.2f}s",
    )
else:
    fail_check(
        "Data-quality endpoint",
        f"HTTP {data_status}: {data_health}",
    )

station_count = find_number(
    data_health,
    {
        "staging_stations",
        "station_count",
        "stations",
    },
)

train_count = find_number(
    data_health,
    {
        "staging_trains",
        "train_count",
        "trains",
    },
)

stop_count = find_number(
    data_health,
    {
        "staging_train_stops",
        "train_stop_count",
        "train_stops",
        "stops",
    },
)

data_checks = [
    ("Railway stations", station_count, 8000),
    ("Railway trains", train_count, 5000),
    ("Railway train stops", stop_count, 400000),
]

for label, count, minimum in data_checks:
    if count is None:
        fail_check(
            label,
            "Count missing from data-health response",
        )
    elif count >= minimum:
        pass_check(
            label,
            f"{count:,}",
        )
    else:
        fail_check(
            label,
            f"{count:,}; expected at least {minimum:,}",
        )


# Recommendation request
query = (
    f"source={SOURCE}"
    f"&destination={DESTINATION}"
    f"&journey_date={JOURNEY_DATE}"
    f"&direct_limit=5"
    f"&transfer_limit=3"
)

recommendation_url = (
    f"{BACKEND_URL}/recommend-v2?{query}"
)

cache_results: list[str] = []
recommendation_payload: dict[str, Any] = {}

for request_number in range(1, 4):
    (
        recommend_status,
        recommend_headers,
        payload,
        elapsed,
    ) = request_json(recommendation_url)

    cache_value = recommend_headers.get(
        "x-cache",
        "MISSING",
    ).upper()

    cache_results.append(cache_value)

    print(
        f"Recommendation request {request_number}: "
        f"HTTP {recommend_status}, "
        f"{elapsed:.2f}s, "
        f"X-Cache={cache_value}"
    )

    if request_number == 1:
        recommendation_payload = payload

    if recommend_status != 200:
        fail_check(
            "Recommendation endpoint",
            f"HTTP {recommend_status}: {payload}",
        )
        break

if recommendation_payload.get("status") == "ok":
    pass_check("Recommendation payload status")
else:
    fail_check(
        "Recommendation payload status",
        str(recommendation_payload.get("status")),
    )

recommendation_count = recommendation_payload.get(
    "count"
)

if (
    isinstance(recommendation_count, int)
    and recommendation_count > 0
):
    pass_check(
        "Recommendation results",
        str(recommendation_count),
    )
else:
    fail_check(
        "Recommendation results",
        f"Invalid count: {recommendation_count}",
    )

for required_field in [
    "duplicate_route_count",
    "rejected_transfer_count",
    "ranking_policy",
    "deduplication_policy",
]:
    if required_field in recommendation_payload:
        pass_check(
            f"Recommendation field {required_field}"
        )
    else:
        fail_check(
            f"Recommendation field {required_field}",
            "Missing",
        )

returned_date = recommendation_payload.get(
    "journey_date"
)

if returned_date == JOURNEY_DATE:
    pass_check(
        "Journey date propagation",
        returned_date,
    )
else:
    fail_check(
        "Journey date propagation",
        f"Expected {JOURNEY_DATE}, received {returned_date}",
    )

best_available = (
    recommendation_payload
    .get("summary", {})
    .get("best_available")
)

if isinstance(best_available, dict):
    pass_check(
        "Best recommendation available",
        str(best_available.get("route_type")),
    )
else:
    fail_check(
        "Best recommendation available",
        "summary.best_available missing",
    )


# Cache
if "HIT" in cache_results:
    pass_check(
        "Recommendation memory cache",
        " → ".join(cache_results),
    )
else:
    fail_check(
        "Recommendation memory cache",
        "No HIT observed: "
        + " → ".join(cache_results),
    )

cache_status_code, _, cache_status, cache_time = (
    request_json(
        f"{BACKEND_URL}/recommend-v2/cache-status"
    )
)

if cache_status_code == 200:
    pass_check(
        "Cache-status endpoint",
        f"{cache_time:.2f}s",
    )
else:
    fail_check(
        "Cache-status endpoint",
        f"HTTP {cache_status_code}: {cache_status}",
    )

ttl_seconds = (
    cache_status.get("ttl_seconds")
    if isinstance(cache_status, dict)
    else None
)

if ttl_seconds == 300:
    pass_check(
        "Cache TTL",
        "300 seconds",
    )
else:
    fail_check(
        "Cache TTL",
        f"Expected 300, received {ttl_seconds}",
    )


print()
print("=" * 72)
print("Smoke-test summary")
print("=" * 72)
print("Failures:", len(failures))
print("Warnings:", len(warnings))

if warnings:
    print("\nWarnings:")

    for item in warnings:
        print(" -", item)

if failures:
    print("\nFailures:")

    for item in failures:
        print(" -", item)

    print("\nRESULT: NOT READY")
    sys.exit(1)

print("\nRESULT: READY")
sys.exit(0)
